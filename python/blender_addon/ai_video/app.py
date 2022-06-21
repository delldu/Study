"""AI Power"""
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

import re


def function_parse(s):
    """
    example:
        f_name, f_args = function_parse("clean(input_file=xxxx, output_file=yyyy)")
        # f_name, f_args -- clean', {'input_file': 'xxxx', 'output_file': 'yyyy'}
    """
    f_name = ""
    f_args = {}
    pattern = r"(\w[\w\d_]*)\((.*)\)$"
    match = re.match(pattern, s)
    if match:
        f_name = match.group(1)
        args = [e.strip() for e in match.group(2).split(",")]
        for e in args:
            kv = e.split("=")
            if len(kv) == 2:
                f_args[kv[0].strip()] = kv[1].strip()
            else:
                f_args[kv[0].strip()] = ""
    return f_name, f_args


class VideoCommand(object):
    """
    Video Application SDK
    """

    @classmethod
    def clean(cls, input_file, noise_level, output_file):
        f_command = (
            f"clean(input_file={input_file}, noise_level={noise_level}, output_file={output_file})"
        )
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def color(cls, input_file, color_picture, output_file):
        f_command = (
            f"color(input_file={input_file}, color_picture={color_picture}, output_file={output_file})"
        )
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def light(cls, input_file, output_file):
        f_command = f"light(input_file={input_file}, output_file={output_file})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def smooth(cls, input_file, output_file):
        f_command = f"smooth(input_file={input_file}, output_file={output_file})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def smask(cls, input_file, nframe, x1, x2, y1, y2, output_file):
        f_command = f"smask(input_file={input_file}, nframe={nframe}, x1={x1}, x2={x2}, y1={y1}, y2={y2}, output_file={output_file})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def pmask(cls, input_file, output_file):
        f_command = f"pmask(input_file={input_file}, output_file={output_file})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def patch(cls, input_file, output_file):
        f_command = f"patch(input_file={input_file}, output_file={output_file})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def zoom(cls, input_file, output_file):
        f_command = f"zoom(input_file={input_file}, output_file={output_file})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def slow(cls, input_file, slow_times, output_file):
        f_command = f"slow(input_file={input_file}, slow_times={slow_times}, output_file={output_file})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def face(cls, input_file, face_picture, output_file):
        f_command = (
            f"face(input_file={input_file}, face_picture={face_picture}, output_file={output_file})"
        )
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def pose(cls, input_file, pose_picture, output_file):
        f_command = (
            f"pose(input_file={input_file}, pose_picture={pose_picture}, output_file={output_file})"
        )
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command


class VideoStrips(object):
    """Todo List: data[s.name] = id"""

    def __init__(self):
        self.data = {}

    def put(self, name, id):
        self.data[name] = id
        print("Video Todo List:", self.data)

    def get(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        try:
            del self.data[name]
        except KeyError:
            pass

    def size(self):
        return len(self.data)

    def names(self):
        return [e for e in self.data.keys()]
