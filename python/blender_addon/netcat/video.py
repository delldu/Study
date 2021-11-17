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
import os
import argparse
import pdb
import time

from nc import nc_id, function_parse, NCClient, NCServer


class VideoClient(NCClient):
    """Video client SDK"""

    def clean(self, infile, noise_level, outfile):
        f_message = (
            f"clean(infile={infile}, noise_level={noise_level}, outfile={outfile})"
        )
        f_name, f_args = function_parse(f_message)
        assert f_name != "", f"{f_message} is not valid function."
        return self.put(f_message)

    def color(self, infile, color_picture, outfile):
        f_message = (
            f"color(infile={infile}, color_picture={color_picture}, outfile={outfile})"
        )
        f_name, f_args = function_parse(f_message)
        assert f_name != "", f"{f_message} is not valid function."
        return self.put(f_message)

    def light(self, infile, outfile):
        f_message = f"light(infile={infile}, outfile={outfile})"
        f_name, f_args = function_parse(f_message)
        assert f_name != "", f"{f_message} is not valid function."
        return self.put(f_message)

    def smooth(self, infile, outfile):
        f_message = f"smooth(infile={infile}, outfile={outfile})"
        f_name, f_args = function_parse(f_message)
        assert f_name != "", f"{f_message} is not valid function."
        return self.put(f_message)

    def smask(self, infile, nframe, r, c, h, w, outfile):
        f_message = f"smask(infile={infile}, nframe={nframe}, r={r}, c={c}, h={h}, w={w}, outfile={outfile})"
        f_name, f_args = function_parse(f_message)
        assert f_name != "", f"{f_message} is not valid function."
        return self.put(f_message)

    def pmask(self, infile, outfile):
        f_message = f"pmask(infile={infile}, outfile={outfile})"
        f_name, f_args = function_parse(f_message)
        assert f_name != "", f"{f_message} is not valid function."
        return self.put(f_message)

    def patch(self, infile, outfile):
        f_message = f"patch(infile={infile}, outfile={outfile})"
        f_name, f_args = function_parse(f_message)
        assert f_name != "", f"{f_message} is not valid function."
        return self.put(f_message)

    def zoom(self, infile, zoom_x, outfile):
        f_message = f"zoom(infile={infile}, zoom_x={zoom_x}, outfile={outfile})"
        f_name, f_args = function_parse(f_message)
        assert f_name != "", f"{f_message} is not valid function."
        return self.put(f_message)

    def slow(self, infile, slow_x, outfile):
        f_message = f"slow(infile={infile}, slow_x={slow_x}, outfile={outfile})"
        f_name, f_args = function_parse(f_message)
        assert f_name != "", f"{f_message} is not valid function."
        return self.put(f_message)

    def face(self, infile, face_picture, outfile):
        f_message = (
            f"face(infile={infile}, face_picture={face_picture}, outfile={outfile})"
        )
        f_name, f_args = function_parse(f_message)
        assert f_name != "", f"{f_message} is not valid function."
        return self.put(f_message)

    def body(self, infile, body_picture, outfile):
        f_message = (
            f"body(infile={infile}, body_picture={body_picture}, outfile={outfile})"
        )
        f_name, f_args = function_parse(f_message)
        assert f_name != "", f"{f_message} is not valid function."
        return self.put(f_message)


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

    nc.zoom("input.mp4", 4, "output.mp4")
    nc.slow("input.mp4", 3, "output.mp4")

    nc.face("input.mp4", "face.png", "output.mp4")
    nc.body("input.mp4", "body.png", "output.mp4")

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
