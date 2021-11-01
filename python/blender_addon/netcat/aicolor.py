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

import queue
import socketserver
import threading
import multiprocessing

import pdb


def task_id(value):
    """
    e80b5017098950fc58aad83c8c14978e
    """
    return hashlib.md5(value.encode(encoding="utf-8")).hexdigest()


class NCTasks(object):
    """
        id, content, create_time, progress, update_time, pid
    """

    def __init__(self):
        self.taskd = {}
        self.taskq = queue.Queue()

    def __getitem__(self, key):
        return self.taskd[key]

    def __setitem__(self, key, value):
        if not isinstance(key, str) or len(key) == 0:
            raise RuntimeError(f"Key must be string which length > 0")
        # repeat key not allowed in queue
        if key not in self.taskd:
            self.taskq.put(key)
        self.data[key] = value

    def __delitem__(self, key):
        if key in self.taskd:
            try:
                v = self.taskd[key]
                pid = v['pid']
                if isinstance(pid, int) and pid > 1:
                    os.kill(pid, signal.SIGKILL)
            except:
                pass

        # delete key from taskq
        bak = []
        while not self.taskq.empty():
            bak.append(self.taskq.get())
        try:
            bak.remove(key)
            del self.taskd[key]
        except:
            pass
        for e in bak:
            self.taskq.put(e)

    def __repr__(self):
        """Format Color Tasks"""
        outfmt = "{:32} {:40} {:16} {:12} {:16} {:7}"
        output = []
        output.append(
            outfmt.format(
                "task id",
                "content",
                "create time",
                "progress",
                "update time",
                "pid"
            )
        )
        output.append(
            outfmt.format(
                "-" * 32,
                "-" * 40,
                "-" * 16,
                "-" * 12,
                "-" * 16,
                "-" * 7
            )
        )
        # output.append("-" * 128)
        for k, v in self.taskd.items():
            i = v["content"]
            # c = time.ctime(v['create_time'])
            # c = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v["create_time"]))
            c = time.strftime("%H:%M:%S", time.localtime(v["create_time"]))
            p = v["progress"]
            u = time.strftime("%H:%M:%S", time.localtime(v["update_time"]))
            pid = v["pid"]
            output.append(outfmt.format(k, i, c, f"{p:6.2f} %", u, pid))
        return "\n".join(output)

    def update_progress(self, id, progress, pid):
        d = self.taskd.get(id, None)
        if d is not None:
            d["progress"] = max(0, min(progress, 100))
            d["update_time"] = time.time()
            d["pid"] = pid
            self.taskd[id] = d

    def queue_get(self):
        '''get task id from queue.'''
        return self.taskq.get()

    def queue_put(self, value):
        def new_task():
            return {
                "content": value,
                "progress": 0,
                "create_time": time.time(),
                "update_time": time.time(),
                "pid": 0
            }        
        key = task_id(value)
        if key not in self.taskd:
            self.taskq.put(key)
        self.taskd[key] = new_task()

    def queue_size(self):
        return self.taskq.qsize()


class ColorTCPHandler(socketserver.StreamRequestHandler):
    """
    Color handler
    """

    def handle_message(self, data):
        # Here data is bytes, so we convert it to string at first
        message = data.strip().decode(encoding="utf-8")
        # echo back
        message = str(self.server.active_tasks)

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
        #         save_recv_message(d["topic"], d["content"])
        #         # sendback public OK
        #         d["status"] = StatusCode_OK
        #         self.wfile.write(json.dumps(d).encode(encoding="utf-8"))
        #     else:
        #         # got clinet sub message, we should find message from queue and send back
        #         response_message = load_send_message(d["topic"])
        #         if len(response_message) == 0:
        #             d["content"] = "Not Found"
        #             d["status"] = StatusCode_NotFound
        #         else:
        #             d["content"] = response_message
        #             d["status"] = StatusCode_OK
        #         d["length"] = len(d["content"])
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


class NCServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    # Custom our members ...
    active_tasks = NCTasks()

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, max_children=2):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.maximum_children = max_children
        self.active_children = set()
        self.maximum_children = max_children
        self.progress_queue = multiprocessing.Queue()

    def update_progress(self):
        while not self.progress_queue.empty():
            m = self.progress_queue.get()
            self.active_tasks.update_progress(m["id"], m["progress"], m["pid"])

    def clean_children(self):
        ''' Clean zombie process'''
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
            if pid > 1:
                self.active_children.discard(pid)
        except ChildProcessError:
            # have not any children, we're done
            self.active_children.clear()
        except OSError:
            pass

    def handle_service(self, q, content):
        """For real service, should be overridden"""
        id = task_id(content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.5)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)

    def work_forever(self):
        while True:
            # idle or busy ?
            if (
                self.active_tasks.queue_size() == 0
                or len(self.active_children) >= self.maximum_children
            ):
                self.update_progress()
                self.clean_children()
                continue
            # Now there are tasks and running resource, create process to do job ...
            id = self.active_tasks.queue_get()
            t = self.active_tasks[id]
            pargs = (self.progress_queue, t["content"])
            p = multiprocessing.Process(target=self.handle_service, args=pargs)
            p.daemon = True
            p.start()
            self.active_children.add(p.pid)

    def serve_forever(self):
        t = threading.Thread(target=self.work_forever, args=())
        t.daemon = True
        t.start()
        return super().serve_forever()


def start_server(HOST="localhost", PORT=9999):
    server = NCServer((HOST, PORT), ColorTCPHandler)

    server.active_tasks.queue_put("color(input1.mp4,color1.png)")
    server.active_tasks.queue_put("cloor(input2.mp4,color2.png)")
    server.active_tasks.queue_put("color(input3.mp4,color3.png)")
    server.active_tasks.queue_put("color(input4.mp4,color4.png)")

    server.serve_forever()
    server.shutdown()


def client_connect(address, port, content, output_filename):
    print(f"Connect to {address}:{port} ...")
    print(f"Coloring {content} to {output_filename} ...")


if __name__ == "__main__":
    """Ai Color."""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-s", "--server", help="Run Server", action="store_true")
    parser.add_argument("-c", "--client", help="Run Client", action="store_true")
    parser.add_argument(
        "-a", "--address", type=str, default="localhost", help="server address"
    )
    parser.add_argument("-p", "--port", type=int, default=9999, help="service port")

    parser.add_argument("--input", type=str, default="input.mp4", help="input file")
    parser.add_argument(
        "--refimg", type=str, default="reference.png", help="reference image"
    )
    parser.add_argument("--output", type=str, default="output", help="output folder")
    args = parser.parse_args()
    print(args)

    if args.server:
        start_server(args.address, args.port)
    # else:
    #     client_connect(args.address, args.port, args.input, args.refimg, args.output)

    tasks = NCTasks()
    tasks.queue_put("color(input1.mp4,color1.png)")
    tasks.queue_put("color(input1.mp4,color1.png)")
    tasks.queue_put("color(input1.mp4,color1.png)")
    tasks.queue_put("color(input1.mp4,color1.png)")
    print(tasks)

    pdb.set_trace()
