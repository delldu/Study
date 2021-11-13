"""Video Server."""
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

# THIS FILE IS ONLY FOR TEST !!!


import argparse
import pdb
import time

from nc import nc_id, NCClient, NCServer
from app import VideoCommand
import subprocess as sp
import numpy as np

class VideoReader(object):
    """Use ffmpeg process video"""

    def __init__(self, filename):
        self.filename = filename
        self.n_frames = 0
        self.height = 256
        self.width = 256
        self.fps = 24
        self.probe()

    def probe(self):
        """
        ffmpeg -i tennis.mp4 -f null -
        """
        import re

        self.n_frames = 0
        cmd = ["ffmpeg", "-i", self.filename, "-f", "null", "-"]
        try:
            proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
            out, err = proc.communicate()
            if proc.returncode != 0:
                return
            err = err.decode(encoding="utf-8")
        except:
            print(f"{cmd} error: {err}")
            return

        video_match = r"Stream.*Video.*,\s*(\d+)x(\d+).*,\s*(\d+)\s*fps"
        frame_match = r"frame=\s*(\d+) fps=.*speed"

        g = re.findall(video_match, err)
        if g:
            # g[0] is input stream and g[1] is output stream
            self.width = int(g[0][0])
            self.height = int(g[0][1])
            self.fps = float(g[0][2])
            g = re.findall(frame_match, err)
            if g:
                self.n_frames = int(g[0])

    def forward(self, callback=None):
        if self.n_frames < 1:
            return 0
        if callback is None:
            callback = self.print_frame

        # rgba format
        buffer_size = self.height * self.width * 4
        cmd = [
            "ffmpeg",
            # input
            "-i",
            self.filename,
            # convert
            "-f",
            "image2pipe",
            "-pix_fmt",
            "rgba",
            "-vcodec",
            "rawvideo",
            # output
            "-",
        ]
        try:
            proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, bufsize=buffer_size)
        except:
            print(f"read {self.filename} frame error.")
            return 0
        for frame_no in range(self.n_frames):
            buffer = proc.stdout.read(buffer_size)
            if len(buffer) != buffer_size:
                print(f"frame buffer != buffer_size ?")
                continue
            frame_data = np.frombuffer(buffer, np.uint8).reshape(
                [self.height, self.width, 4]
            )
            callback(frame_no, frame_data)
        proc.terminate()

        return frame_no + 1

    def print_frame(self, no, data):
        print(f"frame: {no} -- {data.shape}")

    def __call__(self, callback=None):
        return self.forward(callback)

    def __repr__(self):
        return f"{self.filename}: n_frames={self.n_frames}, wxh={self.width}x{self.height}, fps={self.fps:.3f}"


def test_video_reader():
    video = VideoReader("/tmp/tennis.mp4")
    print(video)
    video.forward()
    # video()


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

    # test_video_reader()
    if args.server:
        start_server(args.address, args.port)
    else:
        client_connect(args.address, args.port)

