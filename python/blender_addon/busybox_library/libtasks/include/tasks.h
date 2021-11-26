/************************************************************************************
***
***	Copyright 2021 Dell(18588220928@163.com), All Rights Reserved.
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
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <syslog.h>				// syslog, RFC3164 ?

#define RET_OK 0
#define RET_ERROR (-1)

#define TASKSET_VERSION "1.0.0"
#define TASK_CONTENT_MAX_LEN 1024

#define MIN(a, b) ((a) > (b) ? (b) : (a))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define ARRAY_SIZE(x) (int)(sizeof(x) / sizeof(x[0]))

#define CheckPoint(fmt, arg...) \
  printf("# CheckPoint: %d(%s): " fmt "\n", (int)__LINE__, __FILE__, ##arg)

#if 0
#define syslog_info(fmt, arg...)                \
	  do {                                          \
	    syslog(LOG_INFO | LOG_PERROR, "Info: " fmt "\n", ##arg); \
	  } while (0)

#define syslog_debug(fmt, arg...)                                          \
	  do {                                                                     \
	    syslog(LOG_DEBUG | LOG_PERROR, "Debug: %d(%s): " fmt "\n", (int)__LINE__, __FILE__, \
	           ##arg);                                                         \
	  } while (0)

#define syslog_error(fmt, arg...)                                        \
	  do {                                                                   \
	    syslog(LOG_ERR | LOG_PERROR, "Error: %d(%s): " fmt "\n", (int)__LINE__, __FILE__, \
	           ##arg);                                                       \
	  } while (0)
#else
#define syslog_info(fmt, arg...)                \
	  do {                                          \
	    fprintf(stderr, "Info: " fmt "\n", ##arg); \
	  } while (0)

#define syslog_debug(fmt, arg...)                                          \
	  do {                                                                     \
	    fprintf(stderr, "Debug: %d(%s): " fmt "\n", (int)__LINE__, __FILE__, \
	           ##arg);                                                         \
	  } while (0)

#define syslog_error(fmt, arg...)                                        \
	  do {                                                                   \
	    fprintf(stderr, "Error: %d(%s): " fmt "\n", (int)__LINE__, __FILE__, \
	           ##arg);                                                       \
	  } while (0)
#endif

	typedef int64_t TIME;

	typedef char TASKID[33];	// md5 hex digest of content

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

	// typedef int (*TASKSET_HANDLER)(char *tasks_name);
	typedef int (*TASKSET_HANDLER) (char *);

	char *taskset_version();
	int get_task_id(char *content, TASKID id);	// thread safety
	int get_task_key(char *content, char *key_buff, size_t key_size);

	TASKSET *create_taskset(char *name);

	void taskset_service(char *tasks_name, int max_workers, TASKSET_HANDLER handle);

	int get_task_value(TASKSET * tasks, char *key, TASK * task);
	float get_task_state(TASKSET * tasks, char *key);
	int set_task_state(TASKSET * tasks, char *key, float progress);

	// The following touch queue
	int get_first_qkey(TASKSET * tasks, char *key_buff, size_t key_size);
	int get_queue_len(TASKSET * tasks);
	int get_queue_task(TASKSET * tasks, char *pattern, TASK * task);
	int set_queue_task(TASKSET * tasks, char *content);

	int delete_task(TASKSET * tasks, char *key);
	// delete all tasks
	int taskset_clear(TASKSET * tasks);

	void destroy_taskset(TASKSET * tasks);

	// Helper
	int fargs_parse(char *command, int maxargc, char *argv[]);
	char *fargs_search(char *name, int argc, char *argv[]);

	// image demo
	void video_client();
	void video_server();

	// image demo
	void image_client();
	void image_server();

#if defined(__cplusplus)
}
#endif
#endif							// _TASKSET_H
