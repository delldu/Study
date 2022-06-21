"""NC Server, Client SDK"""
# coding=utf-8
#
# /************************************************************************************
# ***
# ***    Copyright Dell 2020, All Rights Reserved.
# ***
# ***    File Author: Dell, 2021年 11月 12日 星期五 03:00:26 CST
# ***
# ************************************************************************************/
#
# https://docs.python.org/3/library/socketserver.html?highlight=tcpserver#socketserver.TCPServer

import os

import time
import json
import hashlib
import signal
import socket
import queue
import socketserver
import threading
import multiprocessing


def nc_id(value):
    """
    nc_id like 'e80b5017098950fc58aad83c8c14978e'
    """
    return hashlib.md5(value.encode(encoding="utf-8")).hexdigest()


class NCTasks(object):
    """
    NCTasks for server
    id, content, created, progress, updated, pid
    """

    def __init__(self):
        self.taskd = {}
        self.taskq = queue.Queue()

    def __repr__(self):
        """Format Color Tasks"""
        outfmt = "{:32} {:84} {:8} {:8} {:8} {:8}"
        output = []
        output.append(
            outfmt.format("task id", "content", "create", "progress", "update", "pid")
        )
        output.append(
            outfmt.format("-" * 32, "-" * 84, "-" * 8, "-" * 8, "-" * 8, "-" * 8)
        )
        # output.append("-" * 128)
        for k, v in self.taskd.items():
            i = v["content"]
            # c = time.ctime(v['created'])
            # c = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v["created"]))
            c = time.strftime("%H:%M:%S", time.localtime(v["created"]))
            p = v["progress"]
            u = time.strftime("%H:%M:%S", time.localtime(v["updated"]))
            pid = v["pid"]
            output.append(outfmt.format(k, i, c, f"{p:6.2f} %", u, pid))
        return "\n".join(output)

    def get(self, key):
        return self.taskd.get(key, None)

    def update_progress(self, id, progress, pid):
        d = self.taskd.get(id, None)
        if d is not None:
            d["progress"] = max(0, min(progress, 100))
            d["updated"] = time.time()
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
                "created": time.time(),
                "updated": time.time(),
                "pid": 0,
            }

        key = nc_id(value)
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
        except KeyError:
            pass

        qlist = []
        while not self.taskq.empty():
            qlist.append(self.taskq.get())

        try:
            qlist.remove(key)
            del self.taskd[key]
        except KeyError:
            pass

        for e in qlist:
            self.taskq.put(e)

        return True

    def queue_size(self):
        return self.taskq.qsize()


class NCMessage(object):
    Status_OK = 200
    Status_BadRequest = 400
    Status_NotFound = 404
    Status_Error = 500

    REQUEST_METHOD = ("GET", "PUT", "DELETE", "TRACE")
    RESPONSE_STATUS = (
        Status_OK,
        Status_BadRequest,
        Status_NotFound,
        Status_Error,
    )

    @classmethod
    def decode_request(cls, message):
        """Decode JSON string to dict object"""
        try:
            d = json.loads(message)
            if d["method"] not in NCMessage.REQUEST_METHOD:
                return None
            if not isinstance(d["content"], str):
                return None
            if not isinstance(d["length"], int):
                return None
            if len(d["content"]) != d["length"]:
                return None
        except Exception:
            return None
        return d

    @classmethod
    def decode_response(cls, message):
        """Decode JSON string to dict object"""
        try:
            d = json.loads(message)
            if d["status"] not in NCMessage.RESPONSE_STATUS:
                return None
            if not isinstance(d["content"], str):
                return None
            if not isinstance(d["length"], int):
                return None
            if len(d["content"]) != d["length"]:
                return None
        except Exception:
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
        """GET request: content -- id/Response: content progress"""
        id = dmsg["content"]
        t = self.server.tasks.get(id)
        if t is None:
            return NCMessage.encode_response(NCMessage.Status_NotFound, f"get {id}")
        # get progress status ?
        return NCMessage.encode_response(NCMessage.Status_OK, str(t["progress"]))

    def handle_put_message(self, dmsg):
        """PUT request: content -- msg/Response: content == put msg"""
        msg = dmsg["content"]
        self.server.tasks.queue_put(msg)
        return NCMessage.encode_response(NCMessage.Status_OK, f"put {msg}")

    def handle_delete_message(self, dmsg):
        """DELETE content -- id"""
        status = NCMessage.Status_OK
        id = dmsg["content"]
        if not self.server.tasks.queue_del(id):
            status = NCMessage.Status_NotFound
        return NCMessage.encode_response(status, f"delete {id}")

    def handle_message(self, request_message):
        """Only echo message if request is not empy else server.tasks will send back for debug"""
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
                NCMessage.Status_BadRequest, request_message.replace('"', "'")
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
                    NCMessage.Status_OK, dmsg["content"]
                )
        # '\n' is readline style for client
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
        except (ConnectionResetError, Exception):
            """Write error or client disconnected ..."""
            pass
        # read nothing, so close client connection ...
        self.finish()
        return False

    def handle(self):
        """current client read loop ..."""
        while self.handle_request():
            pass


class NCServer(socketserver.ThreadingTCPServer):
    # allow_reuse_address come from ThreadingTCPServer
    allow_reuse_address = True

    def __init__(
        self,
        server_address,
        max_children=2,
    ):
        super().__init__(server_address, NCHandler)
        self.max_children = max_children
        self.active_children = set()
        self.max_children = max_children
        self.progress_queue = multiprocessing.Queue()
        self.tasks = NCTasks()

        signal.signal(signal.SIGCHLD, self.clean_battlefield)

    def clean_battlefield(self, signum, frame):
        """signam, frame is for signal.signal(), no meaning here"""
        # Clean zombie process
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
            if pid > 1:
                self.active_children.discard(pid)
        except ChildProcessError:
            # have not any children, we're done
            self.active_children.clear()
        except (OSError, Exception):
            pass

        # clear progress queue
        while not self.progress_queue.empty():
            m = self.progress_queue.get()
            self.tasks.update_progress(m["id"], m["progress"], m["pid"])

    def handle_service(self, q, content):
        """xxx For real service, should be overridden"""
        id = nc_id(content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.2)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)

    def working_forever(self):
        while True:
            # idle or busy ?
            if (
                self.tasks.queue_size() == 0
                or len(self.active_children) >= self.max_children
            ):
                self.clean_battlefield(0, 0)
                continue
            # there are tasks and also running resource, create process ...
            id = self.tasks.queue_get()
            t = self.tasks.get(id)
            pargs = (self.progress_queue, t["content"])
            p = multiprocessing.Process(
                target=self.handle_service, args=pargs, daemon=True
            )
            p.start()
            self.active_children.add(p.pid)

    def serve_forever(self):
        threading.Thread(target=self.working_forever, args=(), daemon=True).start()
        return super().serve_forever()


class NCJobs(object):
    """
    NCJobs for client and local
    id, content, created, progress, updated
    """

    def __init__(self):
        self.jobs = {}
        self.adds = set()
        self.dels = set()

    def __repr__(self):
        """Format Color Tasks"""
        outfmt = "{:32} {:84} {:8} {:8} {:8}"
        output = []
        output.append(
            outfmt.format("task id", "content", "create", "progress", "update")
        )
        output.append(outfmt.format("-" * 32, "-" * 84, "-" * 8, "-" * 8, "-" * 8))
        for k, v in self.jobs.items():
            i = v["content"]
            c = time.strftime("%H:%M:%S", time.localtime(v["created"]))
            p = v["progress"]
            u = time.strftime("%H:%M:%S", time.localtime(v["updated"]))
            output.append(outfmt.format(k, i, c, f"{p:6.2f} %", u))
        return "\n".join(output)

    def update_progress(self, id, progress):
        d = self.jobs.get(id, None)
        if d:
            d["progress"] = max(0, min(progress, 100))
            d["updated"] = time.time()
            self.jobs[id] = d

    def get(self, key):
        return self.jobs.get(key, None)

    def keys(self):
        return self.jobs.keys()

    def put(self, value):
        def new_task():
            return {
                "content": value,
                "progress": 0,
                "created": time.time(),
                "updated": time.time(),
            }

        key = nc_id(value)
        self.adds.add(key)
        self.jobs[key] = new_task()

    def delete(self, key):
        if key not in self.jobs:
            return False
        # self.dels used for remote sync, so add here
        self.dels.add(key)
        del self.jobs[key]
        return True

    def adds_list(self):
        return [e for e in self.adds]

    def adds_delete(self, key):
        self.adds.remove(key)

    def dels_list(self):
        return [e for e in self.dels]

    def dels_delete(self, key):
        self.dels.remove(key)


class NCClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.alive = False
        self.jobs = NCJobs()

        self.timer = None
        self.start_timer()

    def connect(self):
        if not self.alive:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                self.socket.settimeout(2)
                self.alive = True
            except (OSError, socket.gaierror) as err:
                self.alive = False
                print(f"Connect {self.host}:{self.port} error: {str(err)}")
        else:
            self.hello("Hello, NC Server !")

    def sync_task(self):
        """Sync jobs status with remote"""

        def rpc_get(id):
            d = self.rpc(NCMessage.encode_request("GET", id))
            try:
                progress = -1
                if d and d["status"] == NCMessage.Status_OK:
                    progress = int(d["content"])
                return progress
            except Exception:
                return -1

        def rpc_put(content):
            d = self.rpc(NCMessage.encode_request("PUT", content))
            try:
                return d and d["status"] == NCMessage.Status_OK
            except Exception:
                return False

        def rpc_delete(id):
            d = self.rpc(NCMessage.encode_request("DELETE", id))
            try:
                return d and d["status"] in (
                    NCMessage.Status_OK,
                    NCMessage.Status_NotFound,
                )
            except Exception:
                return False

        if not self.alive:
            # print("Remote service shutdown ...")
            return

        # print("Syncing tasks with remote ...")
        # 1) Put task to remote
        alist = self.jobs.adds_list()
        for id in alist:
            v = self.jobs.get(id)
            try:
                if v and rpc_put(v["content"]):
                    # put task to remote OK, so delete it from adds
                    self.jobs.adds_delete(id)
            except Exception:
                pass

        # 2) Delete task from remote
        dlist = self.jobs.dels_list()
        for id in dlist:
            if rpc_delete(id):
                # nofify remote 'delete id' OK, delete dels
                self.jobs.dels_delete(id)

        # 3) Update progress
        for id in self.jobs.keys():
            d = rpc_get(id)
            if d > 0:
                self.jobs.update_progress(id, d)

    def start_timer(self):
        # Do period jobs
        self.connect()
        self.sync_task()
        self.timer = threading.Timer(3, self.start_timer)
        self.timer.start()

    def is_alive(self):
        return self.alive

    def rpc(self, message):
        """Request and Response Model"""
        received_data = ""
        try:
            self.socket.sendall(bytes(message + "\n", "utf-8"))
            while True:
                data = self.socket.recv(1024)
                if data and len(data) > 0:
                    received_data += data.decode(encoding="utf-8")
                    self.alive = True
                    if data.find(b"\n") >= 0:
                        break
                else:
                    # socket read 0 bytes ?
                    break
        except Exception as err:
            print(f"Client RPC error: {err}")
            self.alive = False
            return None

        return NCMessage.decode_response(received_data)

    def keys(self):
        return self.jobs.keys()

    def get(self, id):
        try:
            v = self.jobs.get(id)
            if v:
                return v["progress"]
        except Exception:
            pass
        return 0

    def put(self, content):
        self.jobs.put(content)

    def delete(self, id):
        self.jobs.delete(id)

    def hello(self, message):
        return self.rpc(NCMessage.encode_request("TRACE", message))

    def close(self):
        if self.timer:
            self.timer.cancel()

        if self.alive:
            self.socket.close()
        self.alive = False
