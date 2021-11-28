/************************************************************************************
***
*** Copyright 2021 Dell(18588220928@163.com), All Rights Reserved.
***
*** File Author: Dell, 2021-11-22 18:23:02
***
************************************************************************************/

#include "tasks.h"

int video_clean(TASKSET * video, char *key, int argc, char *argv[])
{
	int i;

	char *input_file = fargs_search("input_file", argc, argv);
	char *sigma = fargs_search("sigma", argc, argv);
	char *output_file = fargs_search("output_file", argc, argv);

	if (! file_exists(input_file))
		return RET_ERROR;

	if (sigma == NULL || output_file == NULL) {
		syslog_error("video clean task miss parameters.");
		set_task_state(video, key, -100.0);
		return RET_ERROR;
	}

	// load clean model
	for (i = 0; i < 100; i++) {
		set_task_state(video, key, (float) (i + 1));
		if (i % 10 == 0)
			sleep(1);
	}

	return RET_OK;
}

int video_color(TASKSET * video, char *key, int argc, char *argv[])
{
	int i;

	char *input_file = fargs_search("input_file", argc, argv);
	char *color_picture = fargs_search("color_picture", argc, argv);
	char *output_file = fargs_search("output_file", argc, argv);

	if (! file_exists(input_file))
		return RET_ERROR;

	if (color_picture == NULL || output_file == NULL) {
		syslog_error("video color task miss parameters.");
		set_task_state(video, key, -100.0);
		return RET_ERROR;
	}
	// load color model
	for (i = 0; i < 100; i++) {
		set_task_state(video, key, (float) (i + 1));
		if (i % 10 == 0)
			sleep(1);
	}

	return RET_OK;
}

int video_slow(TASKSET * video, char *key, int argc, char *argv[])
{
	int i;

	char *input_file = fargs_search("input_file", argc, argv);
	char *slow_x = fargs_search("slow_x", argc, argv);
	char *output_file = fargs_search("output_file", argc, argv);

	if (! file_exists(input_file))
		return RET_ERROR;

	if (slow_x == NULL || output_file == NULL) {
		syslog_error("video slow task miss parameters.");
		set_task_state(video, key, -100.0);
		return RET_ERROR;
	}
	// load slow model
	for (i = 0; i < 100; i++) {
		set_task_state(video, key, (float) (i + 1));
		if (i % 10 == 0)
			sleep(1);
	}

	return RET_OK;
}

int video_skip(TASKSET * video, char *key, int argc, char *argv[])
{
	// avoid compiler compaint
	(void) argc;
	(void) argv;

	set_task_state(video, key, -100.0);
	return RET_ERROR;
}


int video_handler(char *name)
{
	TASK task;
	TASKSET *video;
	int ret, f_argc;
	char *f_name, *f_argv[32], f_buffer[TASK_CONTENT_MAX_LEN], key[256];

	ret = RET_ERROR;

	// subprocess need re-connect to redis server
	video = create_taskset(name);
	if (!video)
		return RET_ERROR;

	if (get_queue_task(video, NULL, &task) == RET_OK) {
		get_task_key(task.content, key, sizeof(key));

		// save task content to buffer for parsing
		snprintf(f_buffer, sizeof(f_buffer), "%s", task.content);
		f_name = f_buffer;
		f_argc = fargs_parse(f_buffer, ARRAY_SIZE(f_argv), f_argv);

		if (strcmp(f_name, "clean") == 0) {
			ret = video_clean(video, key, f_argc, f_argv);
		} else if (strcmp(f_name, "color") == 0) {
			ret = video_color(video, key, f_argc, f_argv);
		} else if (strcmp(f_name, "slow") == 0) {
			ret = video_slow(video, key, f_argc, f_argv);
		} else {
			syslog_error("video '%s' NOT implemented", f_name);
			ret = video_skip(video, key, f_argc, f_argv);
		}
	}
	destroy_taskset(video);

	return ret;
}

void video_client()
{
	int i;
	char command[1024];

	TASKSET *video = create_taskset("video");
	if (!video)
		return;

	// loop for test redis server start/stop
	for (i = 1; i < 10; i++) {
		snprintf(command, sizeof(command), "clean(input_file=i_%d.mp4,sigma=30,output_file=o_%d.mp4)", i, i);
		set_queue_task(video, command);

		snprintf(command, sizeof(command), "color(input_file=i_%d.mp4,color_picture=color.png,output_file=o_%d.mp4)", i, i);
		set_queue_task(video, command);

		snprintf(command, sizeof(command), "slow(input_file=i_%d.mp4,slow_x=3,output_file=o_%d.mp4)", i, i);
		set_queue_task(video, command);

		snprintf(command, sizeof(command), "zoom(input_file=i_%d.mp4,output_file=o_%d.mp4)", i, i);
		set_queue_task(video, command);
	}

	destroy_taskset(video);
}


void video_server()
{
	taskset_service("video", 4, video_handler);
}
