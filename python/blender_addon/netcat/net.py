"""Blender Addon Netcat"""
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

import queue
import json
import socketserver
import select
# import pdb
import logging



logging.basicConfig(level=logging.NOTSET)
netcat_logger = logging.getLogger('netcat')

# dns = bpy.app.driver_namespace
dns = {}

# message schema
# {
#     "method": "pub | sub"
#     "topic": "video_clean | video_color | video_smask | ..."
#     "context": "This is message context",
#     "length" : "message length",
#     "status": 200
# }

StatusCode_OK = 200
StatusCode_BadRequest = 400
StatusCode_NotFound = 404
StatusCode_ServerInternalError = 500


def decode_message(message):
    """Decode JSON string to dict object"""
    try:
        d = json.loads(message)
    except:
        return None
    if ("method" not in d) or (d["method"] not in ("pub", "sub")):
        return None
    if ("topic" not in d) or (not isinstance(d["topic"], str)):
        return None
    if ("context" not in d) or (not isinstance(d["context"], str)):
        return None
    if ("length" not in d) or (not isinstance(d["length"], int)):
        return None
    if ("status" not in d) or (not isinstance(d["status"], int)):
        return None
    if len(d["context"]) != d["length"]:
        return None
    return d


def encode_progress_message(topic, percent):
    d = {
        "method": "pub",
        "context": "progress",
    }
    d["topic"] = topic
    d["context"] = f"progress:{percent}"
    d["length"] = len(d["context"])
    d["status"] = StatusCode_OK
    return json.dumps(d)


def progress_message_percent(message):
    d = decode_message(message)
    if d is None or d["method"] != "pub" or (not d["context"].startswith("progress:")):
        return -1.0
    return float(d["context"][: len("progress:")])


def encode_badrequest_message(message):
    d = {}
    d["method"] = "pub"
    d["topic"] = "BadRequest"
    d["context"] = message
    d["length"] = len(message)
    d["status"] = StatusCode_BadRequest

    return json.dumps(d)


def empty_message(topic):
    d = {}
    d["method"] = "response"
    d["topic"] = topic
    d["context"] = "no message"
    d["length"] = len(d["context"])
    d["status"] = 200
    return json.dumps(d)


def get_queue_helper(send_or_recv, topic):
    """
    Create queue if not exist
    """
    root_node = f"netcat_{send_or_recv}_queue"

    if root_node not in dns:
        dns[root_node] = {topic: queue.Queue()}
    elif topic not in dns[root_node]:
        dns[root_node][topic] = queue.Queue()
    return dns[root_node][topic]


def get_send_queue(topic):
    return get_queue_helper("send", topic)


def get_recv_queue(topic):
    return get_queue_helper("recv", topic)


def clear_send_queue():
    dns = bpy.app.driver_namespace
    try:
        dns["netcat_send_queue"] = None
    except:
        pass


def clear_recv_queue():
    dns = bpy.app.driver_namespace
    try:
        dns["netcat_recv_queue"] = None
    except:
        pass


def save_send_message(topic, message):
    # no save empty message
    if topic is None or message is None or len(message) == 0:
        return
    q = get_send_queue(topic)
    try:
        q.put(message, timeout=1)
    except:
        pass


def save_recv_message(topic, message):
    # no save empty message
    if topic is None or message is None or len(message) == 0:
        return
    q = get_recv_queue(topic)
    try:
        q.put(message, timeout=1)
    except:
        pass


def load_send_message(topic):
    q = get_send_queue(topic)
    if q.empty():
        return ""
    try:
        return q.get(timeout=1)
    except:
        return ""


def load_recv_message(topic):
    q = get_recv_queue(topic)
    if q.empty():
        return ""
    try:
        return q.get(timeout=1)
    except:
        return ""




# class NetcatServer:
#     """
#     Simple netcat server
#     """

#     def __init__(self, port=9090):
#         server_address = ("localhost", port)

#         self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.server.bind(server_address)
#         self.server.listen(200)

#         self.input_set = [self.server]
#         self.output_set = []
#         self.except_set = []
#         self.message_buffer = {}

#         netcat_logger.info(f"Netcat server listen on {server_address} ... ")

#     def on_accept(self):
#         clientsock, clientaddr = self.server.accept()
#         netcat_logger.debug(f"{clientaddr} coming ... ")

#         clientsock.setblocking(0)
#         self.input_set.append(clientsock)
#         self.message_buffer[clientsock] = ""

#     def on_receive(self, s):
#         data = s.recv(1024)
#         netcat_logger.debug("{s} received message: {data}")

#         if data and data != "":
#             # s is readable, so connecting on ...
#             self.message_buffer[s] += data.decode(encoding="utf-8")
#             if s not in self.output_set:
#                 self.output_set.append(s)
#         else:
#             # client disconnect ...
#             natcat_logger.debug(f"{s.getpeername()} disconnected...")
#             if s in self.output_set:
#                 self.output_set.remove(s)
#             self.input_set.remove(s)
#             del self.message_buffer[s]
#             s.close()

#     def on_send(self, s):
#         # client request something ? if yes, give message to send
#         if len(self.message_buffer[s]) == 0:
#             return

#         d = decode_message(self.message_buffer[s])
#         if d is None:
#             # send back bad request message
#             response_message = encode_badrequest_message(
#                 self.message_buffer[s].replace('"', "").replace("'", "")
#             )
#             s.send(response_message.encode(encoding="utf-8"))
#         else:
#             # save message to netcat_recv_queue ?
#             if d["method"] == "pub":
#                 save_recv_message(d["topic"], d["context"])
#                 # sendback public OK
#                 d["status"] = StatusCode_OK
#                 s.send(json.dumps(d).encode(encoding="utf-8"))
#             else:
#                 # got clinet sub message, we should find message from queue and send back
#                 response_message = load_send_message(d["topic"])
#                 if len(response_message) == 0:
#                     d["context"] = "Not Found"
#                     d["status"] = StatusCode_NotFound
#                 else:
#                     d["context"] = response_message
#                     d["status"] = StatusCode_OK
#                 d["length"] = len(d["context"])
#                 s.send(json.dumps(d).encode(encoding="utf-8"))

#         self.message_buffer[s] = ""

#     def on_close(self, s):
#         netcat_logger.debug(f"{s.getpeername()} disconnected.")

#         if s in self.input_set:
#             self.input_set.remove(s)
#         if s in self.output_set:
#             self.output_set.remove(s)
#         if s in self.except_set:
#             self.except_set.remove(s)
#         s.close()
#         del self.message_buffer[s]

#     def for_loop(self):
#         while True:
#             input_ready, output_ready, except_ready = select.select(
#                 self.input_set, self.output_set, self.except_set
#             )
#             for s in input_ready:
#                 if s == self.server:
#                     # new clinet coming ...
#                     self.on_accept()
#                 else:
#                     # old client, read and save message
#                     self.on_receive(s)

#             for s in output_ready:
#                 self.on_send(s)

#             for s in except_ready:
#                 # nothing to do except 'close socket' ...
#                 self.on_close(s)

#         # close all sockets, notice self.server include self.input_set
#         for s in self.input_set:
#             self.on_close(s)
#         for s in self.output_set:
#             self.on_close(s)
#         for s in self.except_set:
#             self.on_close(s)
#         del self.message_buffer


class NetcatTCPHandler(socketserver.StreamRequestHandler):
    '''
        Netcat handler
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
                    # self.data is 'bytes' class, include '\n'
                    netcat_logger.debug(f"{self.client_address[0]} wrote: {self.data}")
                    self.handle_message(self.data)

                else:
                    break
            except Exception as e:
                print(f"{self.client_address} disconnected.")
                break


if __name__ == "__main__":
    '''
    Good Case 
        {"method":"pub", "topic":"video_clean","context":"progress:50.05", "length": 14, "status":200}
        {"method":"sub", "topic":"video_clean","context":"", "length": 0, "status":200}

    Bad Case
        Hello
        {"method":"xxx", "topic":"video_clean","context":"", "length": 0, "status":200}
        {"method":"xxx", "topic":"video_clean","context":"", "length": 0, "status":200
    '''

    # Create the server, binding to localhost on port 9999

    # s = NetcatServer(9999)
    # s.for_loop()

    # server = SocketServer.ThreadingTCPServer(addr,Servers,bind_and_activate = False)


    HOST, PORT = "localhost", 9999
    server = socketserver.ThreadingTCPServer((HOST, PORT), NetcatTCPHandler, bind_and_activate = False)
    server.allow_reuse_address = True
    server.server_bind()
    server.server_activate()
    server.serve_forever()
