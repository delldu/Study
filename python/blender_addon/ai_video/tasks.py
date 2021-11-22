"""Redis Tasks."""
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

import os
import time
import hashlib
import json
import redis
import pdb

# THIS FILE IS ONLY FOR TEST !!!


def task_id(value):
    """
    nc_id like 'e80b5017098950fc58aad83c8c14978e'
    """
    return hashlib.md5(value.encode(encoding="utf-8")).hexdigest()


def print_redis_error(e):
    print("Redis running error:", e)
    print("Redis server start OK ?")
    print("Reference command:")
    print("    sudo service redis-server start/stop/restart/status")


def print_json_error(e):
    print("Json parse error:", e)


class RedisTasks(object):
    """
    Redis Tasks API

    internal implement:
        video.tasks -- rpush list for all sets ['00001', '00002', ... ]
        video.queue -- rpush list for queue, ['00001', '00002'] for queue
        video.00001 -- json string: 'id', 'content', 'create' with valid check.
        state.00001 -- json string: 'progress', 'update', 'pid', 'status'
    """

    def __init__(self, name, reset=False):
        """name like video, image ..."""
        assert name != "state", "state is key word in this class"
        self.name = name

        self.tasks = f"{self.name}.tasks"
        self.queue = f"{self.name}.queue"

        self.re = redis.Redis(host="localhost", port=6379, decode_responses=True)

        # reset is good for server, but not for client
        if reset:
            try:
                pipe = self.re.pipeline()
                pipe.delete(self.tasks)
                pipe.delete(self.queue)
                pipe.execute()
            except redis.RedisError as e:
                print_redis_error(e)

    def __repr__(self):
        """General use for debug."""

        def get_default_state(id):
            try:
                s = self.re.get(f"state.{id}")
            except redis.RedisError as e:
                print_redis_error(e)
                s = "{}"
            try:
                d = json.loads(s)
            except json.decoder.JSONDecodeError:
                # state maybe not exists, ignore is reasonable
                d = {}
            except Exception:
                d = {}

            # set default value
            if "progress" not in d:
                d["progress"] = 0
            if "update" not in d:
                d["update"] = time.time()
            if "pid" not in d:
                d["pid"] = 0
            return d

        outfmt = "{:32} {:64} {:8} {:8} {:8} {:8}"
        output = []
        output.append(
            outfmt.format("task id", "content", "create", "progress", "update", "pid")
        )
        output.append(
            outfmt.format("-" * 32, "-" * 64, "-" * 8, "-" * 8, "-" * 8, "-" * 8)
        )

        # output.append("-" * 128)
        try:
            keys = self.re.lrange(self.tasks, 0, -1)
        except redis.RedisError as e:
            print_redis_error(e)
            keys = []

        for id in keys:
            d = self.get_task_value(id)
            if d is None:
                continue
            content = d.get("content", "")
            create_time = d.get("create", time.time())
            create_time = time.strftime("%H:%M:%S", time.localtime(create_time))

            d = get_default_state(id)
            progress = d.get("progress")
            update_time = d.get("update")
            update_time = time.strftime("%H:%M:%S", time.localtime(update_time))
            pid = d.get("pid")

            output.append(
                outfmt.format(
                    id,
                    content,
                    create_time,
                    f"{progress:6.2f} %",
                    update_time,
                    str(pid),
                )
            )
        return "\n".join(output)

    def get_task_value(self, id):
        try:
            s = self.re.get(f"{self.name}.{id}")
        except redis.RedisError as e:
            print_redis_error(e)
            return None
        try:
            d = json.loads(s)
            return (
                d
                if d.get("id", "") == id and id == task_id(d.get("content", ""))
                else None
            )
        except json.decoder.JSONDecodeError as e:
            print_json_error(e)
        except Exception:
            return None

    def get_task_state(self, id):
        """General this is called by client."""

        try:
            s = self.re.get(f"state.{id}")
        except redis.RedisError as e:
            print_redis_error(e)
            return 0
        try:
            d = json.loads(s)
            return float(d["progress"])
        except json.decoder.JSONDecodeError:
            # state maybe not exists, ignore is reasonable
            return 0
        except Exception:
            return 0

    def set_task_state(self, id, progress):
        """General this is called by server worker."""

        s = json.dumps(
            {"update": time.time(), "progress": progress, "pid": os.getpid()}
        )
        try:
            self.re.set(f"state.{id}", s)
            return True
        except redis.RedisError as e:
            print_redis_error(e)
            return False

    def get_first_task(self):
        """General this is called by server worker."""

        def get_qid():
            try:
                return self.re.lindex(self.queue, 0)
            except redis.RedisError as e:
                print_redis_error(e)
            return None

        id = get_qid()
        return self.get_task_value(id) if id else None


    def get_last_task(self):
        """General this is called by server worker."""
        def get_qid():
            try:
                return self.re.lindex(self.queue, -1)
            except redis.RedisError as e:
                print_redis_error(e)
            return None

        id = get_qid()
        return self.get_task_value(id) if id else None


    def get_queue_task(self, pattern=None):
        """General this is called by server worker."""

        def get_qid():
            try:
                return self.re.lpop(self.queue)
            except redis.RedisError as e:
                print_redis_error(e)
            return None

        def get_pattern_id(pattern):
            try:
                keys = self.re.lrange(self.queue, 0, -1)
                for id in keys:
                    t = self.get_task_value(id)
                    if t and t["content"].startswith(pattern + "("):
                        self.re.lrem(self.queue, 0, id)
                        return id
            except redis.RedisError as e:
                print_redis_error(e)
            return None

        if isinstance(pattern, str) and len(str) > 0:
            id = get_pattern_id(pattern)
        else:
            id = get_qid()
        return self.get_task_value(id) if id else None

    def set_queue_task(self, content):
        """General this is called by client."""

        id = task_id(content)
        task = {"id": id, "content": content, "create": time.time()}
        try:
            pipe = self.re.pipeline()

            # force delete id from video.queue/tasks
            pipe.lrem(self.tasks, 0, id)
            pipe.lrem(self.queue, 0, id)

            # push id to tail of queue/tasks
            pipe.rpush(self.tasks, id)
            pipe.rpush(self.queue, id)

            # set id/content/create
            pipe.set(f"{self.name}.{id}", json.dumps(task))

            pipe.execute()

            return True
        except redis.RedisError as e:
            print_redis_error(e)
            return False

    def del_queue_task(self, id):
        """General this is called by client."""

        try:
            pipe = self.re.pipeline()
            pipe.lrem(self.tasks, 0, id)
            pipe.lrem(self.queue, 0, id)
            pipe.delete(f"{self.name}.{id}")
            pipe.delete(f"state.{id}")
            pipe.execute()
            return True
        except redis.RedisError as e:
            print_redis_error(e)
            return False


if __name__ == "__main__":
    video = RedisTasks("video")
    video.set_queue_task("color(infile=a.mp4, color_picture=color.png, outfile=o.mp4)")
    video.set_queue_task("clean(infile=clean_input.mp4, sigma=30, outfile=clean_output.mp4)")

    # print(video)

    pdb.set_trace()
