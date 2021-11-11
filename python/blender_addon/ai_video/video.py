"""Video Server."""
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

# THIS FILE IS ONLY FOR TEST !!!


import argparse
import pdb
import time

from nc import nc_id, NCClient, NCServer
from app import VideoCommand


class VideoClient(NCClient):
    """Video client SDK"""

    def clean(self, infile, noise_level, outfile):
        self.put(VideoCommand.clean(infile, noise_level, outfile))

    def color(self, infile, color_picture, outfile):
        self.put(VideoCommand.color(infile, color_picture, outfile))

    def light(self, infile, outfile):
        self.put(VideoCommand.light(infile, outfile))

    def smooth(self, infile, outfile):
        return self.put(VideoCommand.smooth(infile, outfile))

    def smask(self, infile, nframe, x1, x2, y1, y2, outfile):
        return self.put(VideoCommand.smask(infile, nframe, x1, x2, y1, y2, outfile))

    def pmask(self, infile, outfile):
        return self.put(VideoCommand.pmask(infile, outfile))

    def patch(self, infile, outfile):
        return self.put(VideoCommand.patch(infile, outfile))

    def zoom(self, infile, outfile):
        return self.put(VideoCommand.zoom(infile, outfile))

    def slow(self, infile, slow_x, outfile):
        return self.put(VideoCommand.slow(infile, slow_x, outfile))

    def face(self, infile, face_picture, outfile):
        return self.put(VideoCommand.face(infile, face_picture, outfile))

    def pose(self, infile, pose_picture, outfile):
        return self.put(VideoCommand.pose(infile, pose_picture, outfile))


class VideoServer(NCServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


class VideoCleanServer(VideoServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


class VideoColorServer(VideoServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


class VideoLightServer(VideoServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


class VideoStableServer(VideoServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


class VideoSMaskServer(VideoServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


class VideoPMaskServer(VideoServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


class VideoPatchServer(VideoServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


class VideoZoomxServer(VideoServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


class VideoSlowxServer(VideoServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


class VideoFaceServer(VideoServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


class VideoPoseServer(VideoServer):
    def handle_service(self, q, f_content):
        """For real service, should be overridden"""
        id = nc_id(f_content)
        pid = os.getpid()
        for i in range(100):
            time.sleep(0.1)
            m = {"id": id, "progress": i + 1, "pid": pid}
            q.put(m)


def start_server(HOST="localhost", PORT=9999):
    s = NCServer((HOST, PORT))
    s.max_children = 3
    s.serve_forever()
    server.shutdown()


def client_connect(host, port):
    nc = VideoClient(host, port)
    ret = nc.hello("xxxx")
    print(ret)

    nc.clean("input.mp4", 30, "output.mp4")
    nc.color("input.mp4", "color.png", "output.mp4")
    nc.light("input.mp4", "output.mp4")
    nc.smooth("input.mp4", "output.mp4")

    nc.smask("input.mp4", 50, 11, 12, 13, 14, "output.mp4")
    nc.pmask("input.mp4", "output.mp4")
    nc.patch("input.mp4", "output.mp4")

    nc.zoom("input.mp4", "output.mp4")
    nc.slow("input.mp4", 3, "output.mp4")

    nc.face("input.mp4", "face.png", "output.mp4")
    nc.pose("input.mp4", "pose.png", "output.mp4")

    pdb.set_trace()

    nc.close()


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
    args = parser.parse_args()

    if args.server:
        start_server(args.address, args.port)
    else:
        client_connect(args.address, args.port)
