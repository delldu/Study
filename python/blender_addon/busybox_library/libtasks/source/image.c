/************************************************************************************
***
*** Copyright 2021 Dell(18588220928@163.com), All Rights Reserved.
***
*** File Author: Dell, 2021-11-22 18:23:02
***
************************************************************************************/
#include "tasks.h"

int image_handle_break(int total_running_times, int continue_idle_times)
{
	// image schedule strategy
	return (total_running_times >= 100 || continue_idle_times >= 5);
}

int image_clean(TASKSET * image)
{
	TASK task;
	int i, ret, f_argc;
	char *f_name, *f_argv[32], f_buffer[TASK_CONTENT_MAX_LEN], key[256];
	int total_running_times = 0;
	int continue_idle_times = 0;

	char *infile, *sigma, *outfile;

	// load clean model

	ret = RET_OK;

	while (1) {
		if (get_queue_task(image, "clean", &task) == RET_OK) {
			total_running_times++;
			continue_idle_times = 0;	// stop count           

			get_task_key(task.content, key, sizeof(key));

			// save task content to buffer for parsing
			snprintf(f_buffer, sizeof(f_buffer), "%s", task.content);
			f_name = f_buffer;
			f_argc = fargs_parse(f_buffer, ARRAY_SIZE(f_argv), f_argv);

			if (strcmp(f_name, "clean") != 0) {
				syslog_error("Task '%s' is not 'clean'", f_name);
				ret = RET_ERROR;
				continue;
			}

			infile = fargs_search("infile", f_argc, f_argv);
			sigma = fargs_search("sigma", f_argc, f_argv);
			outfile = fargs_search("outfile", f_argc, f_argv);

			if (infile == NULL || sigma == NULL || outfile == NULL) {
				syslog_error("image clean task miss parameters.");
                set_task_state(image, key, -100.0);

				ret = RET_ERROR;
				continue;
			}
			// fake image clean
			for (i = 0; i < 5; i++) {
				set_task_state(image, key, (float) (i + 1) * 20.0);
				sleep(1);
			}
            set_task_state(image, key, 100.0);
		} else {
			continue_idle_times++;
			sleep(1);
		}

		if (image_handle_break(total_running_times, continue_idle_times))
			break;
	}

	return ret;
}

int image_skip(TASKSET * image, char *skip_name)
{
	TASK task;
	char key[256];

	while (get_queue_task(image, skip_name, &task) == RET_OK) {
		syslog_info("skip '%s' task %s", skip_name, task.content);

		if (get_task_key(task.content, key, sizeof(key)) == RET_OK)
			set_task_state(image, key, -100.0);	
	}
	return RET_OK;
}


int image_handler(char *name)
{
	TASKSET *image;
	int ret = RET_ERROR;
	char key[256], *p;

	// sub process, need re-connect to redis server
	image = create_taskset(name);
	if (!image)
		return RET_ERROR;

	if (get_first_qkey(image, key, sizeof(key)) == RET_OK) {
		p = strrchr(key, '.');	// hexdigest not include '.'
		if (p)
			*p = '\0';			// key ==> f_name

		if (strcmp(key, "clean") == 0) {
			ret = image_clean(image);
		} else {
			// skip this kind of tasks
			syslog_error("image '%s' NOT implemented", key);
			ret = image_skip(image, key);
		}
	}
	destroy_taskset(image);

	return ret;
}

void image_client()
{
	int i;
	char command[1024];

	TASKSET *image = create_taskset("image");
	if (!image)
		return;

	// loop for test redis server start/stop
	for (i = 1; i < 10; i++) {
		snprintf(command, sizeof(command), "clean(infile=i_%d.mp4,sigma=30,outfile=o_%d.mp4)", i, i);
		set_queue_task(image, command);

		snprintf(command, sizeof(command), "color(infile=i_%d.mp4,color_picture=color.png,outfile=o_%d.mp4)", i, i);
		set_queue_task(image, command);

		snprintf(command, sizeof(command), "zoom(infile=i_%d.mp4,outfile=o_%d.mp4)", i, i);
		set_queue_task(image, command);
	}

	destroy_taskset(image);
}


void image_server()
{
	taskset_service("image", 3, image_handler);
}
