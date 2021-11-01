"""NC"""
# coding=utf-8
#
# /************************************************************************************
# ***
# ***    Copyright Dell 2020, All Rights Reserved.
# ***
# ***    File Author: Dell, 2020年 09月 09日 星期三 23:56:45 CST
# ***
# ************************************************************************************/
#
# https://docs.python.org/3/library/socketserver.html?highlight=tcpserver#socketserver.TCPServer

import os

# import sys
import time
import json
import hashlib
import argparse

import socket

import queue
import socketserver
import threading
import multiprocessing

import pdb


def nc_id(value):
    """
    nc_id like 'e80b5017098950fc58aad83c8c14978e'
    """
    return hashlib.md5(value.encode(encoding="utf-8")).hexdigest()


class NCTasks(object):
    """
    id, content, create_time, progress, update_time, pid
    """

    def __init__(self):
        self.taskd = {}
        self.taskq = queue.Queue()

    def __repr__(self):
        """Format Color Tasks"""
        outfmt = "{:32} {:40} {:16} {:12} {:16} {:7}"
        output = []
        output.append(
            outfmt.format(
                "task id", "content", "create time", "progress", "update time", "pid"
            )
        )
        output.append(
            outfmt.format("-" * 32, "-" * 40, "-" * 16, "-" * 12, "-" * 16, "-" * 7)
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

    def get(self, key):
        return self.taskd[key]

    def update_progress(self, id, progress, pid):
        d = self.taskd.get(id, None)
        if d is not None:
            d["progress"] = max(0, min(progress, 100))
            d["update_time"] = time.time()
            d["pid"] = pid
            self.taskd[id] = d

    def queue_get(self):
        """get task id from queue."""
        return self.taskq.get()

    def queue_put(self, value):
        def new_task():
            return {
                "content": value,
                "progress": 0,
                "create_time": time.time(),
                "update_time": time.time(),
                "pid": 0,
            }

        key = nc_id(value)
        if key not in self.taskd:
            self.taskq.put(key)
        self.taskd[key] = new_task()

    def queue_del(self, key):
        if key not in self.taskd:
            return False
        try:
            v = self.taskd[key]
            pid = v["pid"]
            if isinstance(pid, int) and pid > 1:
                os.kill(pid, signal.SIGKILL)
        except:
            pass

        qlist = []
        while not self.taskq.empty():
            qlist.append(self.taskq.get())
        try:
            qlist.remove(key)
            del self.taskd[key]
        except:
            pass
        for e in qlist:
            self.taskq.put(e)

        return True

    def queue_size(self):
        return self.taskq.qsize()


class NCMessage(object):
    StatusCode_OK = 200
    StatusCode_BadRequest = 400
    StatusCode_NotFound = 404
    StatusCode_ServerError = 500

    REQUEST_METHOD = ("GET", "PUT", "DELETE", "TRACE")
    RESPONSE_STATUS = (
        StatusCode_OK,
        StatusCode_BadRequest,
        StatusCode_NotFound,
        StatusCode_ServerError,
    )

    @classmethod
    def decode_request(cls, message):
        """Decode JSON string to dict object"""
        try:
            d = json.loads(message)
        except:
            return None
        if ("method" not in d) or (d["method"] not in NCMessage.REQUEST_METHOD):
            return None
        if ("content" not in d) or (not isinstance(d["content"], str)):
            return None
        if ("length" not in d) or (not isinstance(d["length"], int)):
            return None
        if len(d["content"]) != d["length"]:
            return None
        return d

    @classmethod
    def decode_response(cls, message):
        """Decode JSON string to dict object"""
        try:
            d = json.loads(message)
        except:
            return None
        if ("status" not in d) or (
            not isinstance(d["status"], int)
            or (d["status"] not in NCMessage.RESPONSE_STATUS)
        ):
            return None
        if ("content" not in d) or (not isinstance(d["content"], str)):
            return None
        if ("length" not in d) or (not isinstance(d["length"], int)):
            return None
        if len(d["content"]) != d["length"]:
            return None
        return d

    @classmethod
    def encode_request(cls, method, content):
        d = {"method": method, "content": content, "length": len(content)}
        return json.dumps(d)

    @classmethod
    def encode_response(cls, status, content):
        d = {"status": status, "content": content, "length": len(content)}
        return json.dumps(d)


class NCHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        super(NCHandler, self).__init__(request, client_address, server)
        t = self.server.tasks
        if not isinstance(t, NCTasks):
            print("NOT Found tasks (NCTask) in server")
            os._exit()

    def handle_get_message(self, dmsg):
        id = dmsg["content"]
        t = self.server.tasks.get(id)
        if t is None:
            return NCMessage.encode_response(NCMessage.StatusCode_NotFound, f"get {id}")
        # get progress status ?
        return NCMessage.encode_response(NCMessage.StatusCode_OK, str(t["progress"]))

    def handle_put_message(self, dmsg):
        msg = dmsg["content"]
        self.server.tasks.queue_put(msg)
        return NCMessage.encode_response(NCMessage.StatusCode_OK, f"put {msg}")

    def handle_delete_message(self, dmsg):
        # delete id ?
        status = NCMessage.StatusCode_OK
        id = dmsg["content"]
        if not self.server.tasks.queue_del(id):
            status = NCMessage.StatusCode_NotFound
        return NCMessage.encode_response(status, f"delete {id}")

    def handle_message(self, request_message):
        if request_message == "":
            return str(self.server.tasks)

        dmsg = NCMessage.decode_request(request_message)
        if dmsg is None:
            # send back bad request message
            # >>> ddd = {"A":"AAA", 'a':'aaa', 'B':123, "b":456}
            # {'A': 'AAA', 'a': 'aaa', 'B': 123, 'b': 456}
            # >>> json.dumps(ddd)
            # '{"A": "AAA", "a": "aaa", "B": 123, "b": 456}'
            response_message = NCMessage.encode_response(
                NCMessage.StatusCode_BadRequest, request_message.replace('"', "'")
            )
        else:
            # save message to netcat_recv_queue ?
            if dmsg["method"] == "GET":
                response_message = self.handle_get_message(dmsg)
            elif dmsg["method"] == "PUT":
                response_message = self.handle_put_message(dmsg)
            elif dmsg["method"] == "DELETE":
                response_message = self.handle_delete_message(dmsg)
            else:  # if d["method"] = "TRACE":
                response_message = NCMessage.encode_response(
                    NCMessage.StatusCode_OK, dmsg["content"]
                )
        # '\n' is for client readline style
        return response_message + "\n"

    def handle_request(self):
        try:
            self.data = self.rfile.readline()
            if self.data and len(self.data) > 0:
                # self.data is bytes, should be at least including '\n'
                request_message = self.data.strip().decode(encoding="utf-8")
                response_message = self.handle_message(request_message)
                self.wfile.write(response_message.encode(encoding="utf-8"))
                return True
        except ConnectionResetError as e:
            """Write error or client disconnected ..."""
            pass
        return False

    def handle(self):
        while self.handle_request():
            pass


class NCServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    # Custom our members ...

    def __init__(
        self,
        server_address,
        RequestHandlerClass,
        bind_and_activate=True,
        max_children=2,
    ):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.maximum_children = max_children
        self.active_children = set()
        self.maximum_children = max_children
        self.progress_queue = multiprocessing.Queue()
        self.tasks = NCTasks()

    def update_progress(self):
        while not self.progress_queue.empty():
            m = self.progress_queue.get()
            self.tasks.update_progress(m["id"], m["progress"], m["pid"])

    def clean_children(self):
        """Clean zombie process"""
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
        id = nc_id(content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.5)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)

    def work_forever(self):
        while True:
            # idle or busy ?
            if (
                self.tasks.queue_size() == 0
                or len(self.active_children) >= self.maximum_children
            ):
                self.update_progress()
                self.clean_children()
                continue
            # Now there are tasks and running resource, create process to do job ...
            id = self.tasks.queue_get()
            t = self.tasks.get(id)
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
    s = NCServer((HOST, PORT), NCHandler)
    s.tasks.queue_put("color(input1.mp4,color1.png)")
    s.tasks.queue_put("cloor(input2.mp4,color2.png)")
    s.tasks.queue_put("color(input3.mp4,color3.png)")
    s.tasks.queue_put("color(input4.mp4,color4.png)")
    s.serve_forever()
    server.shutdown()


class NC(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((host, port))
            self.socket.settimeout(2)
        except (OSError, socket.gaierror) as err:
            print(f"Connecting {host}:{port} error {str(err)}")

    def rpc(self, message):
        """Request and Response Model"""
        received_data = ""
        try:
            self.socket.sendall(bytes(message + "\n", "utf-8"))
            while True:
                data = self.socket.recv(1024)
                if data and len(data) > 0:
                    received_data += data.decode(encoding="utf-8")
                    if data.find(b"\n") >= 0:
                        break
                else:
                    break
        except Exception as err:
            print(f"NC RPC error: {err}")
        return NCMessage.decode_response(received_data)

    def get(self, id):
        return self.rpc(NCMessage.encode_request("GET", id))

    def put(self, content):
        return self.rpc(NCMessage.encode_request("PUT", content))

    def delete(self, id):
        return self.rpc(NCMessage.encode_request("DELETE", id))

    def hello(self, message):
        return self.rpc(NCMessage.encode_request("TRACE", message))

    def close(self):
        self.socket.close()


def client_connect(host, port):
    nc = NC(host, port)
    ret = nc.hello("xxxx")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-s", "--server", help="Run Server", action="store_true")
    parser.add_argument("-c", "--client", help="Run Client", action="store_true")
    parser.add_argument(
        "-a", "--address", type=str, default="localhost", help="server address"
    )
    parser.add_argument("-p", "--port", type=int, default=9999, help="service port")

    # parser.add_argument("--input", type=str, default="input.mp4", help="input file")
    # parser.add_argument(
    #     "--refimg", type=str, default="reference.png", help="reference image"
    # )
    # parser.add_argument("--output", type=str, default="output", help="output folder")
    args = parser.parse_args()
    print(args)

    if args.server:
        start_server(args.address, args.port)
    else:
        client_connect(args.address, args.port)
