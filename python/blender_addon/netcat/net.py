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
# import pdb

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

# class SetQueue(Queue.Queue):
#     def _init(self, maxsize):
#         self.queue = set()
#     def _put(self, item):
#         self.queue.add(item)
#     def _get(self):
#         return self.queue.pop()


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
                print("please start service here ? ...")

                self.data = self.rfile.readline()
                if self.data and len(self.data) > 0:
                    # self.data is bytes, should be at least including '\n'
                    self.handle_message(self.data)
                else:
                    break
            except ConnectionResetError as e:
                # print(f"{self.client_address} disconnected.")
                break

class NetcatServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


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
    HOST, PORT = "localhost", 9999
    server = NetcatServer((HOST, PORT), NetcatTCPHandler)
    server.serve_forever()
    server.shutdown()
