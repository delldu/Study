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
from collections import UserDict
import threading
import multiprocessing as mp
# from multiprocessing import Queue
# from multiprocessing import Process

import pdb


class ColorTasks(UserDict):
    """
    id, input, refimg, create_time, progress, update_time
    """

    def __repr__(self):
        '''Format Color Tasks'''
        outfmt = "{:32} {:16} {:16} {:20} {:16} {:20}"
        output = []
        output.append(
            outfmt.format(
                "task id",
                "input file",
                "ref image",
                "create time",
                "progress",
                "update time",
            )
        )
        output.append("-" * 124)
        for k, v in self.data.items():
            i = v["input"]
            r = v["refimg"]
            # c = time.ctime(v['create_time'])
            c = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v["create_time"]))
            p = v["progress"]
            # u = time.ctime(v['update_time'])
            u = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v["update_time"]))
            output.append(outfmt.format(k, i, r, c, f"{p:6.2f} %", u))
        return ("\n".join(output))


    @classmethod
    def task_id(cls, input_filename, refimg_filename):
        """
        e80b5017098950fc58aad83c8c14978e
        """
        s = input_filename + ":" + refimg_filename
        return hashlib.md5(s.encode(encoding="utf-8")).hexdigest()

    def create_task(self, input_filename, refimg_filename):
        def new_task(input_filename, refimg_filename):
            """time.ctime(time.time())"""
            return {
                "input": input_filename,
                "refimg": refimg_filename,
                "progress": 0,
                "create_time": time.time(),
                "update_time": time.time(),
            }

        id = self.task_id(input_filename, refimg_filename)
        '''Update'''
        self.data[id] = new_task(input_filename, refimg_filename)

    def update_progress(self, id, progress):
        d = self.data.get(id, None)
        if d is not None:
            d["progress"] = min(int(progress), 100)
            d["update_time"] = time.time()
            self.data[id] = d

    def availabe_taskid(self):
        for k, v in self.data.items():
            if int(v['progress']) == 0:
                return k
        return ""

class ColorTCPHandler(socketserver.StreamRequestHandler):
    """
    Color handler
    """

    def handle_message(self, data):
        # Here data is bytes, so we convert it to string at first
        message = data.strip().decode(encoding="utf-8")
        # echo back
        self.wfile.write(message.encode(encoding="utf-8"))

        # d = decode_message(message)
        # if d is None:
        #     # send back bad request message
        #     response_message = encode_badrequest_message(
        #         message.replace('"', "").replace("'", "")
        #     )
        #     self.wfile.write(response_message.encode(encoding="utf-8"))
        # else:
        #     # save message to netcat_recv_queue ?
        #     if d["method"] == "pub":
        #         save_recv_message(d["topic"], d["context"])
        #         # sendback public OK
        #         d["status"] = StatusCode_OK
        #         self.wfile.write(json.dumps(d).encode(encoding="utf-8"))
        #     else:
        #         # got clinet sub message, we should find message from queue and send back
        #         response_message = load_send_message(d["topic"])
        #         if len(response_message) == 0:
        #             d["context"] = "Not Found"
        #             d["status"] = StatusCode_NotFound
        #         else:
        #             d["context"] = response_message
        #             d["status"] = StatusCode_OK
        #         d["length"] = len(d["context"])
        #         self.wfile.write(json.dumps(d).encode(encoding="utf-8"))

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

    # Custom our members ...
    active_tasks = ColorTasks()
    active_children = set()
    max_children = 2
    progress_queue = mp.Queue()


    def update_progress(self):
        while not self.progress_queue.empty():
            m = self.progress_queue.get()
            self.active_tasks.update_progress(m['id'], m['progress'] + 1)
            # m.done_task()
        # print("Updated progress from message queue ...............")
        print(self.active_tasks)

    def collect_children(self):
        # if len(self.active_children) < 1:
        #     return
        while len(self.active_children) >= self.max_children:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
                if (pid < 1):
                    break
                self.active_children.discard(pid)
                # print("CheckPoing 1-3 ...", self.active_children)
            except ChildProcessError:
                # have not any children, we're done
                self.active_children.clear()
            except OSError:
                break

        # print("CheckPoing 2 ...", self.active_children)

        # # Checking all defunct children ...
        # for pid in self.active_children.copy():
        #     try:
        #         pid, _ = os.waitpid(pid, os.WNOHANG)
        #         # if the child hasn't exited yet, pid will be 0 and ignored
        #         self.active_children.discard(pid)
        #     except ChildProcessError:
        #         # someone else reaped it
        #         self.active_children.discard(pid)
        #     except OSError:
        #         pass

        # print("CheckPoint 3 ...", self.active_children)


    def handle_service(self, q, id, input_filename, refimg_filename):
        '''For real service, should be overridden '''
        for i in range(100):
            time.sleep(0.1)
            m = {'id' : id, 'progress': i + 1}
            q.put(m)

    def tasks_forever(self):
        while True:
            # idle or too busy ?
            id = self.active_tasks.availabe_taskid()
            if len(id) == 0 or len(self.active_children) >= self.max_children:
                self.update_progress()
                self.collect_children()
                # time.sleep(0.5)
                continue
            # there are tasks and also resource, we need for process to do task ...
            self.active_tasks.update_progress(id, 1)
            
            # print("Will start task ... ==> id = ", id)
            # print(self.active_tasks)
            running_task = self.active_tasks[id]
            pargs = (self.progress_queue, id, running_task['input'], running_task['refimg'])
            p = mp.Process(target = self.handle_service, args=pargs)
            # p.daemon = True
            p.start()
            self.active_children.add(p.pid)

def start_server(HOST="localhost", PORT=9999):
    server = ColorServer((HOST, PORT), ColorTCPHandler)

    server.active_tasks.create_task("input1.mp4", "color1.png")
    server.active_tasks.create_task("input2.mp4", "color2.png")
    server.active_tasks.create_task("input3.mp4", "color3.png")
    server.active_tasks.create_task("input4.mp4", "color4.png")

    t = threading.Thread(target=server.tasks_forever, args=())
    t.start()
    # time.sleep(1)

    server.serve_forever()
    server.shutdown()


def client_connect(address, port, input_filename, refimg_filename, output_filename):
    print(f"Connect to {address}:{port} ...")
    print(f"Coloring {input_filename} with {refimg_filename} to {output_filename} ...")


def color(q, input_filename, refimg_file, output_filename):
    count = 1
    while count < 100:
        print(
            f"Coloring {input_filename} with {refimg_file} to {output_filename} ... {count}"
        )
        count += 1
        q.put(count)
        time.sleep(1)


def test():
    q = Queue()
    i, r, o = "input.mp4", "refimg_file.png", "output.mp4"
    colorp = Process(target=color, args=(q, i, r, o))

    colorp.start()
    progress = 0

    while progress < 100:
        if not q.empty():
            progress = q.get()
            print("Color progress ... ", progress)

        time.sleep(0.5)


if __name__ == "__main__":
    """Ai Color."""

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-s", "--server", help="Run Server", action="store_true")
    parser.add_argument("-c", "--client", help="Run Client", action="store_true")
    parser.add_argument("-a", "--address", type=str, default="localhost", help="server address")
    parser.add_argument("-p", "--port", type=int, default=9999, help="service port")

    parser.add_argument("--input", type=str, default="input.mp4", help="input file")
    parser.add_argument("--refimg", type=str, default="reference.png", help="reference image")
    parser.add_argument("--output", type=str, default="output.mp4", help="output file")
    args = parser.parse_args()
    print(args)

    if args.server:
        start_server(args.address, args.port)
    # else:
    #     client_connect(args.address, args.port, args.input, args.refimg, args.output)

    # tasks = ColorTasks()

    # print(tasks)

    # print(tasks)

    # pdb.set_trace()



