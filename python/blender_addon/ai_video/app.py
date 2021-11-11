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
        f_name, f_args = function_parse("clean(infile=xxxx, outfile=yyyy)")
        # f_name, f_args -- clean', {'infile': 'xxxx', 'outfile': 'yyyy'}
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
    '''
    Video Application SDK
    '''

    @classmethod
    def clean(cls, infile, noise_level, outfile):
        f_command = (
            f"clean(infile={infile}, noise_level={noise_level}, outfile={outfile})"
        )
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def color(cls, infile, color_picture, outfile):
        f_command = (
            f"color(infile={infile}, color_picture={color_picture}, outfile={outfile})"
        )
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def light(cls, infile, outfile):
        f_command = f"light(infile={infile}, outfile={outfile})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def smooth(cls, infile, outfile):
        f_command = f"smooth(infile={infile}, outfile={outfile})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def smask(cls, infile, nframe, x1, x2, y1, y2, outfile):
        f_command = f"smask(infile={infile}, nframe={nframe}, x1={x1}, x2={x2}, y1={y1}, y2={y2}, outfile={outfile})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def pmask(cls, infile, outfile):
        f_command = f"pmask(infile={infile}, outfile={outfile})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def patch(cls, infile, outfile):
        f_command = f"patch(infile={infile}, outfile={outfile})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def zoom(cls, infile, outfile):
        f_command = f"zoom(infile={infile}, outfile={outfile})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def slow(cls, infile, slow_x, outfile):
        f_command = f"slow(infile={infile}, slow_x={slow_x}, outfile={outfile})"
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def face(cls, infile, face_picture, outfile):
        f_command = (
            f"face(infile={infile}, face_picture={face_picture}, outfile={outfile})"
        )
        f_name, f_args = function_parse(f_command)
        assert f_name != "", f"{f_command} is not valid function."
        return f_command

    @classmethod
    def pose(cls, infile, pose_picture, outfile):
        f_command = (
            f"pose(infile={infile}, pose_picture={pose_picture}, outfile={outfile})"
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
        print("video Todo List:", self.data)

    def get(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        try:
            del self.data[name]
        except:
            pass

    def size(self):
        return len(self.data)

    def names(self):
        return [e for e in self.data.keys()]


