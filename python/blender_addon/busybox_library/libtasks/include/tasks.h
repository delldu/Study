/************************************************************************************
***
***	Copyright 2021 Dell(18588220928g@163.com), All Rights Reserved.
***
***	File Author: Dell, 2021-11-22 18:22:25
***
************************************************************************************/

#ifndef _TASKS_H
#define _TASKS_H

#if defined(__cplusplus)
extern "C" {
#endif

#include <sys/types.h>

#define RET_OK 0
#define RET_ERROR (-1)

#define TASKS_VERSION "1.0.0"
#define MAX_TASK_CONTENT_LEN 1024


	typedef int64_t TIME;

	typedef char TASKID[33];	// md5 hexdigest of content

	typedef struct {
		TASKID id;
		TIME create;
		char content[MAX_TASK_CONTENT_LEN];
		float progress;
		TIME update;
		int pid;
	} TASK;

	typedef struct {
		char *name;
		void *redis;			// data is stored on redis server
	} TASKS;

    char *tasks_version();
	int get_task_id(char *content, TASKID id); // thread safety

	TASKS *tasks_create(char *name, int reset);

// The following not touch queue
	int get_task_value(TASKS * tasks, TASKID id, TASK * task);
	float get_task_state(TASKS * tasks, TASKID id);
	int set_task_state(TASKS * tasks, TASKID id, float progress);
	int get_first_task(TASKS * tasks, TASK * task);
	int get_last_task(TASKS * tasks, TASK * task);

// The following impact queue
	int get_queue_task(TASKS * tasks, char *pattern, TASK * task);
	int set_queue_task(TASKS * tasks, char *content);
	int del_queue_task(TASKS * tasks, TASKID id);

	void tasks_destroy(TASKS * tasks);

	int demo_image_service();
	int demo_video_service();

#if defined(__cplusplus)
}
#endif
#endif							// _TASKS_H
