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

import os
import argparse
import pdb
import time
from nc import nc_id, NCClient, NCServer
from app import VideoCommand

import re
import subprocess as sp
import numpy as np

# Good reference
# https://github.com/Zulko/moviepy.git


class VideoReader(object):
    """Use ffmpeg process video"""

    def __init__(self, filename):
        self.filename = filename
        self.n_frames = 0
        self.height = 256
        self.width = 256
        self.fps = 24.000
        self.probe()

    def probe(self):
        """
        ffmpeg -i tennis.mp4 -f null -
        """
        self.n_frames = 0
        cmd = ["ffmpeg", "-i", self.filename, "-f", "null", "-"]
        try:
            proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
            out, err = proc.communicate()
            if proc.returncode != 0:
                return
            err = err.decode(encoding="utf-8")
        except (OSError, ValueError):
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

    def forward(self, start_frame=0, stop_frame=-1, callback=None):
        # [start_frame, stop_frame)

        if self.n_frames < 1:
            return 0

        if start_frame < 0:
            start_frame = 0

        if stop_frame < 0:
            stop_frame = self.n_frames
        stop_frame = min(stop_frame, self.n_frames)

        if start_frame >= stop_frame:
            return 0

        if callback is None:
            callback = self.print_frame

        if start_frame > 0:
            start_time = int(start_frame / self.n_frames)
        else:
            start_time = 0
        start_pos = int(self.fps * start_time + 0.0001)

        # rgba format
        # ffmpeg -i %s -f image2pipe -vcodec rawvideo -pix_fmt rgba - 2>/dev/null
        buffer_size = self.height * self.width * 4
        cmd = [
            "ffmpeg",
            # start time
            "-ss",
            "%.06f" % start_time,
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
        except (OSError, ValueError):
            print(f"read {self.filename} frame error.")
            return 0

        frame_count = 0
        while start_pos < stop_frame:
            buffer = proc.stdout.read(buffer_size)
            start_pos = start_pos + 1  # ==> current frame no is start_pos -1

            if len(buffer) != buffer_size:
                print("frame read error: data length != buffer_size")
                continue

            # skip frames ?
            if (start_pos - 1) < start_frame:
                continue

            frame_data = np.frombuffer(buffer, np.uint8).reshape(
                [self.height, self.width, 4]
            )
            callback(start_pos - 1, frame_data)
            frame_count = frame_count + 1

        proc.terminate()
        proc.stdout.close()
        proc.stderr.close()
        proc.wait()

        return frame_count

    def print_frame(self, no, data):
        print(f"frame: {no} -- {data.shape}")

    def __call__(self, start_frame=0, stop_frame=-1, callback=None):
        return self.forward(start_frame, stop_frame, callback)

    def __repr__(self):
        return f"{self.filename}: n_frames={self.n_frames}, wxh={self.width}x{self.height}, fps={self.fps:.3f}"


def test_video_reader():
    video = VideoReader("/tmp/tennis.mp4")
    print(video)
    video.forward()
    # video()
    pdb.set_trace()


class VideoClient(NCClient):
    """Video client SDK"""

    def clean(self, input_file, noise_level, output_file):
        self.put(VideoCommand.clean(input_file, noise_level, output_file))

    def color(self, input_file, color_picture, output_file):
        self.put(VideoCommand.color(input_file, color_picture, output_file))

    def light(self, input_file, output_file):
        self.put(VideoCommand.light(input_file, output_file))

    def smooth(self, input_file, output_file):
        return self.put(VideoCommand.smooth(input_file, output_file))

    def smask(self, input_file, nframe, x1, x2, y1, y2, output_file):
        return self.put(VideoCommand.smask(input_file, nframe, x1, x2, y1, y2, output_file))

    def pmask(self, input_file, output_file):
        return self.put(VideoCommand.pmask(input_file, output_file))

    def patch(self, input_file, output_file):
        return self.put(VideoCommand.patch(input_file, output_file))

    def zoom(self, input_file, output_file):
        return self.put(VideoCommand.zoom(input_file, output_file))

    def slow(self, input_file, slow_times, output_file):
        return self.put(VideoCommand.slow(input_file, slow_times, output_file))

    def face(self, input_file, face_picture, output_file):
        return self.put(VideoCommand.face(input_file, face_picture, output_file))

    def pose(self, input_file, pose_picture, output_file):
        return self.put(VideoCommand.pose(input_file, pose_picture, output_file))


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
    s.server.shutdown()


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
