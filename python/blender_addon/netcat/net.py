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

import queue
import json
import socket
import select
from enum import Enum

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

class StatusCode(Enum):
    OK = 200
    BadRequest = 400
    NotFound = 404
    ServerError = 500

def decode_message(message):
    '''Decode JSON string to dict object'''
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
        'method': 'pub',
        'context': 'progress',
    }
    d['topic'] = topic
    d['context'] = f'progress:{percent}'
    d['length'] = len(d['context'])
    d['status'] = StatusCode.OK
    return json.dumps(d)

def progress_message_percent(message):
    d = decode_message(message)
    if d is None or d['method'] != 'pub' or (not d['context'].startswith('progress:')):
        return -1.0
    return float(d['context'][:len('progress:')])

def encode_badrequest_message(message):
    d = {}
    d['method'] = 'pub'
    d['topic'] = 'BadRequest'
    d['context'] = message
    d['length'] = len(message)
    d['status'] = StatusCode.BadRequest
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
    '''
    Create queue if not exist
    '''
    root_node = f"netcat_{send_or_recv}_queue"

    if root not in dns :
        dns[root_node] = {topic : queue.Queue()}
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

class NetcatServer:
    '''
        Simple netcat server
    '''
    def __init__(self, port=9090):
		server_address = ('localhost', port)

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(server_address)
        self.server.listen(200)

        self.input_set = [self.server]
        self.output_set = []
        self.except_set = []
        self.message_buffer = {}

        print(f'Server listen on {server_address} ... listen socket {self.server} ')

    def on_accept(self):
        clientsock, clientaddr = self.server.accept()
        print(s.getpeername(), " coming here...")

        clientsock.setblocking(0)
        self.input_set.append(clientsock)
        self.message_buffer[clientsock] = ''

    def on_receive(self, s):
        data = s.recv(1024)
        print("Received message: ", data)

        if data and data != '':
            # client connecting ...
            self.message_buffer += data
            if s not in self.output_set:
                self.output_set.append(s)
        else:
            # client disconnect ...
	        print(s.getpeername(), "disconnected...")
            if s in self.output_set:
                self.output_set.remove(s)
            self.input_set.remove(s)
            del self.message_buffer[s]
            s.close()

    def on_send(self, s):
          # client request something ? if yes, give message
          d = decode_message(self.message_buffer)
          if d is None:
              #send back bad request message
              response_message = encode_badrequest_message(self.message_buffer[s].replace('\"', '').replace('\'', ''))
              s.sendall(response_message)
          else:
              # save message to netcat_recv_queue ?
              if d['method'] == 'pub':
                  save_recv_message(d['topic'], d['context'])
                  # sendback public OK
                  d['status'] = StatusCode.OK
                  s.sendall(json.dumps(d))
              else:
                  # got clinet sub message, we should find message from queue and send back
                  response_message = load_send_message(d['topic'])
                  if len(response_message) == 0:
                      d['status'] = StatusCode.NotFound
                  else:
                      d['context'] = response_message
                      d['status'] = StatusCode.OK
                  s.sendall(json.dumps(d))

          self.message_buffer[s] = ''

    def on_close(self, s):
        print(s.getpeername(), "disconnected")
          if s in self.input_set:
              self.input_set.remove(s)
          if s in self.output_set:
              self.output_set.remove(s)
          if s in self.except_set:
              self.except_set.remove(s)
          s.close()
          del self.message_buffer[s]


    def for_loop(self):
        while True:
            input_ready, output_ready, except_ready = select.select(self.input_set, self.output_set, self.except_set)
            for s in input_ready:
                if s == self.server:
                    # new clinet coming ...
                    self.on_accept()
                else:
                    # old client, read and save message
                    self.on_receive(s)

            for s in output_ready:
                self.on_send(s)

            for s in except_set:
                # have nothing to do except close socket ...
                self.on_close(s)

        # close all sockets, notice self.server include self.input_set
        for s in self.input_set:
            self.on_close(s)
        for s in self.output_set:
            self.on_close(s)
        for s in self.except_set:
            self.on_close(s)
        del self.message_buffer

if __name__ == "__main__":
    s = NetcatServer(9999)
    s.for_loop()
