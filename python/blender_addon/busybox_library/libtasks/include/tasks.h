/************************************************************************************
***
***	Copyright 2021 Dell(18588220928g@163.com), All Rights Reserved.
***
***	File Author: Dell, 2021-11-22 18:22:25
***
************************************************************************************/

#ifndef _TASKSET_H
#define _TASKSET_H

#if defined(__cplusplus)
extern "C" {
#endif

#include <sys/types.h>

#define RET_OK 0
#define RET_ERROR (-1)

#define TASKSET_VERSION "1.0.0"
#define TASK_CONTENT_MAX_LEN 1024

#define MIN(a, b) ((a) > (b) ? (b) : (a))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define ARRAY_SIZE(x) (int)(sizeof(x) / sizeof(x[0]))

	typedef int64_t TIME;

	typedef char TASKID[33];	// md5 hexdigest of content

	typedef struct {
		TASKID id;
		TIME create;
		char content[TASK_CONTENT_MAX_LEN];
		float progress;
		TIME update;
		int pid;
	} TASK;

	typedef struct {
		char *name;
		void *redis;			// data is stored on redis server
	} TASKSET;

	// typedef int (*TASKSET_HANDLER)(char *taskset_name);
	typedef int (*TASKSET_HANDLER) (char *);

	char *taskset_version();
	int get_task_id(char *content, TASKID id);	// thread safety
	int get_task_key(char *content, char *key_buff, size_t key_size);

	TASKSET *create_taskset(char *name);

	void taskset_service(char *taskset_name, int max_workers, TASKSET_HANDLER handle);

// The following not touch queue
	int get_task_value(TASKSET * tasks, char *key, TASK * task);
	float get_task_state(TASKSET * tasks, char *key);
	int set_task_state(TASKSET * tasks, char *key, float progress);

// The following touch queue
	int get_first_task(TASKSET * tasks, TASK * task);
	int get_queue_task(TASKSET * tasks, char *pattern, TASK * task);
	int set_queue_task(TASKSET * tasks, char *content);
	int del_queue_task(TASKSET * tasks, char *key);
	int get_queue_len(TASKSET * tasks);

	void destroy_taskset(TASKSET * tasks);

	void demo_video_client();
	void demo_video_server();

	void demo_image_client();
	void demo_image_server();

#if defined(__cplusplus)
}
#endif
#endif							// _TASKSET_H
