"""Ai Color."""
# coding=utf-8
#
# /************************************************************************************
# ***
# ***    Copyright Dell 2020, All Rights Reserved.
# ***
# ***    File Author: Dell, 2020年 11月 02日 星期一 17:46:28 CST
# ***
# ************************************************************************************/
#
import argparse
import os
import time
import json
import hashlib

import socketserver
import multiprocessing
from collections import OrderedDict

# from multiprocessing import Queue
# from multiprocessing import Process

def task_id(input_filename, refimg_filename):
    '''
        e80b5017098950fc58aad83c8c14978e
    '''
    s = input_filename + ":" + refimg_filename
    return hashlib.md5(s.encode(encoding='utf-8')).hexdigest()

class ColorTasks:
    '''
        task list ...

        >>> import hashlib
        >>> hashlib.md5(b'123').hexdigest()

        input1.mp4, refimg1.png, progress1
        input2.mp4, refimg2.png, progress2

    key: hashlib.md5(input + ':' + refimg).hexdigest() 

    '''
    def __init__(self):
        self.task_list = OrderedDict()

    def add_task(self, input_filename, refimg_filename):
        def new_task(input_filename, refimg_filename):
            '''time.ctime(time.time())'''
            return {"input": input_filename, "refimg": refimg_filename, "progress": 0, "create_time": time.time(), "update_time": time.time()}

        id = task_id(input_filename, refimg_filename)
        if id in self.task_list:
            print("Color task {id} ({input_filename},{refimg_filename}) exist")
        else:
            self.task_list[id] = new_task(input_filename, refimg_filename)
        return id

    def del_task(self, id):
        del self.task_list[id]

    def update_progress(id, progress):
        d = self.task_list.get(id, None)
        if d is not None:
            d['progress'] = progress
            d['update_time'] = time.time()
            self.task_list[id] = d

    def dump(self):
        outfmt = "{:32} {:16} {:16} {:20} {:10} {:20}"
        print(outfmt.format("id", "input", "ref image", "create time", "progress", "update time"))
        print('-' * 118)
        for k, v in self.task_list.items():
            i = v['input']
            r = v['refimg']
            # c = time.ctime(v['create_time'])
            c = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(v['create_time'])) 
            p = v['progress']
            # u = time.ctime(v['update_time'])
            u = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(v['update_time']))
            print(outfmt.format(k, i, r, c, f"{p} %", u))


class ColorTCPHandler(socketserver.StreamRequestHandler):
    '''
        Color handler
    '''
    def handle_message(self, data):
        # Here data is bytes, so we convert it to string at first
        message = data.strip().decode(encoding="utf-8")
        d = decode_message(message)
        if d is None:
            # send back bad request message
            response_message = encode_badrequest_message(message.replace('"', "").replace("'", ""))
            self.wfile.write(response_message.encode(encoding="utf-8"))
        else:
            # save message to netcat_recv_queue ?
            if d["method"] == "pub":
                save_recv_message(d["topic"], d["context"])
                # sendback public OK
                d["status"] = StatusCode_OK
                self.wfile.write(json.dumps(d).encode(encoding="utf-8"))
            else:
                # got clinet sub message, we should find message from queue and send back
                response_message = load_send_message(d["topic"])
                if len(response_message) == 0:
                    d["context"] = "Not Found"
                    d["status"] = StatusCode_NotFound
                else:
                    d["context"] = response_message
                    d["status"] = StatusCode_OK
                d["length"] = len(d["context"])
                self.wfile.write(json.dumps(d).encode(encoding="utf-8"))

    def handle(self):
        while True:
            try:
                self.data = self.rfile.readline()
                if self.data and len(self.data) > 0:
                    # self.data is bytes including '\n'
                    self.handle_message(self.data)
                else:
                    break
            except ConnectionResetError as e:
                # print(f"{self.client_address} disconnected.")
                break


class ColorServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def start_server(HOST="localhost", PORT=9999):
    server = ColorServer((HOST, PORT), ColorTCPHandler)
    server.serve_forever()
    server.shutdown()

def client_connect(address, port, input_filename, refimg_filename, output_filename):
    print(f"Connect to {address}:{port} ...")
    print(f"Coloring {input_filename} with {refimg_filename} to {output_filename} ...")


def color(q, input_filename, refimg_file, output_filename):
    count = 1
    while count < 100:
        print(f"Coloring {input_filename} with {refimg_file} to {output_filename} ... {count}")
        count += 1
        q.put(count)
        time.sleep(1)


def test():
    q = Queue()
    i, r, o = "input.mp4", "refimg_file.png", "output.mp4"
    colorp = Process(target = color, args=(q, i, r, o))

    colorp.start()
    progress = 0

    while progress < 100:
        if not q.empty():
            progress = q.get()
            print("Color progress ... ", progress)

        time.sleep(0.5)


if __name__ == "__main__":
    """Ai Color."""

    # parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # parser.add_argument("-s", "--server", help="Run Server", action="store_true")
    # parser.add_argument("-c", "--client", help="Run Client", action="store_true")
    # parser.add_argument("-a", "--address", type=str, default="localhost", help="server address")
    # parser.add_argument("-p", "--port", type=int, default=9999, help="service port")

    # parser.add_argument("--input", type=str, default="input.mp4", help="input file")
    # parser.add_argument("--refimg", type=str, default="reference.png", help="reference image")
    # parser.add_argument("--output", type=str, default="output.mp4", help="output file")
    # args = parser.parse_args()
    # print(args)

    # if args.server:
    #     start_server(args.address, args.port)
    # else:
    #     client_connect(args.address, args.port, args.input, args.refimg, args.output)


    tasks = ColorTasks()
    tasks.dump()

    tasks.add_task("input1.mp4", "color1.png")
    tasks.add_task("input2.mp4", "color2.png")
    tasks.dump()

