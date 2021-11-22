/************************************************************************************
***
***	Copyright 2021 Dell(18588220928g@163.com), All Rights Reserved.
***
***	File Author: Dell, 2021-11-22 18:23:02
***
************************************************************************************/

#include "tasks.h"
#include "hiredis.h"
#include "cJSON.h"

#include <stdio.h>
#include <stdlib.h>
#include <syslog.h>				// syslog, RFC3164 ?
#include <string.h>
#include <openssl/md5.h>
#include <sys/types.h>
#include <unistd.h>

#define CheckPoint(fmt, arg...) \
  printf("# CheckPoint: %d(%s): " fmt "\n", (int)__LINE__, __FILE__, ##arg)
#if 0
#define syslog_info(fmt, arg...)                \
  do {                                          \
    syslog(LOG_INFO, "Info: " fmt "\n", ##arg); \
  } while (0)
#define syslog_debug(fmt, arg...)                                          \
  do {                                                                     \
    syslog(LOG_DEBUG, "Debug: %d(%s): " fmt "\n", (int)__LINE__, __FILE__, \
           ##arg);                                                         \
  } while (0)
#define syslog_error(fmt, arg...)                                        \
  do {                                                                   \
    syslog(LOG_ERR, "Error: %d(%s): " fmt "\n", (int)__LINE__, __FILE__, \
           ##arg);                                                       \
  } while (0)
#else
#define syslog_info(fmt, arg...)               \
  do {                                         \
    fprintf(stderr, "Info: " fmt "\n", ##arg); \
  } while (0)
#define syslog_debug(fmt, arg...)                                        \
  do {                                                                   \
    fprintf(stderr, "Debug: %d(%s): " fmt "\n", (int)__LINE__, __FILE__, \
            ##arg);                                                      \
  } while (0)
#define syslog_error(fmt, arg...)                                        \
  do {                                                                   \
    fprintf(stderr, "Error: %d(%s): " fmt "\n", (int)__LINE__, __FILE__, \
            ##arg);                                                      \
  } while (0)
#endif

#define check_tasks(tasks)                     \
  do {                                         \
    if (!tasks_valid(tasks)) return RET_ERROR; \
  } while (0)

#define CHECK_TASKS(tasks)                \
  do {                                    \
    if (!tasks_valid(tasks)) return NULL; \
  } while (0)


char *tasks_version()
{
	return TASKS_VERSION;
}

// # gcc md5.c -o md5 -lssl

TIME time_now()
{
	TIME ms;
	struct timeval t;

	gettimeofday(&t, NULL);
	ms = t.tv_sec * 1000 + t.tv_usec / 1000;

	return ms;
}


redisContext *redis_open()
{
	redisContext *c = redisConnect("127.0.0.1", 6379);
	if (c == NULL || c->err) {
		if (c) {
			syslog_error("Error: %s", c->errstr);
			redisFree(c);
		} else {
			syslog_error("Allocate redis context");
		}
		return NULL;
	}

	return c;
}

void redis_close(redisContext * c)
{
	redisFree(c);
}

void redis_free_replay(redisReply * reply)
{
	if (reply)
		freeReplyObject(reply);
}

// type:
// REDIS_REPLY_STATUS -- SET key value
// REDIS_REPLY_STRING -- GET key
// REDIS_REPLY_ARRAY -- LRANGE list 0 -1

// reply = redisCommand(c,"LRANGE mylist 0 -1");
// if (reply->type == REDIS_REPLY_ARRAY) {
//     for (j = 0; j < reply->elements; j++) {
//         printf("%u) %s\n", j, reply->element[j]->str);
//     }
// }
// freeReplyObject(reply);

redisReply *redis_command(redisContext * c, char *cmd, int type)
{
	redisReply *reply = redisCommand(c, cmd);
	if (reply == NULL || c->err) {
		syslog_error("reply is NULL or server error (error: %s)", c->errstr);
		return NULL;
	}
	if (reply->type != type) {
		if (reply->type == REDIS_REPLY_ERROR)
			syslog_error("Redis Error: %s\n", reply->str);

		syslog_error("'%s' expected reply type %d but got %d", cmd, type, reply->type);
		redis_free_replay(reply);
		return NULL;
	}

	return reply;
}

redisReply *tasks_command(TASKS * tasks, char *cmd, int type)
{
	return redis_command((redisContext *) tasks->redis, cmd, type);
}

char *dump_task_value(TASK *task)
{
	char *string = NULL;
	cJSON *root = cJSON_CreateObject();

    if (cJSON_AddStringToObject(root, "id", task->id) == NULL)
        goto end;
    if (cJSON_AddStringToObject(root, "content", task->content) == NULL)
        goto end;
    if (cJSON_AddNumberToObject(root, "create", task->create) == NULL)
        goto end;

    string = cJSON_Print(root);
    if (string == NULL)
        syslog_error("JSON Print.");
end:
	syslog_error("Dump task value.");
    cJSON_Delete(root);

    return string;	
}

char *dump_task_state(float progress)
{
	char *string = NULL;
	cJSON *root = cJSON_CreateObject();

    if (cJSON_AddNumberToObject(root, "progress", progress) == NULL)
        goto end;
    if (cJSON_AddNumberToObject(root, "update", time_now()) == NULL)
        goto end;
    if (cJSON_AddNumberToObject(root, "pid", getpid()) == NULL)
        goto end;

    string = cJSON_Print(root);
    if (string == NULL)
        syslog_error("JSON Print.");
end:
	syslog_error("Dump task state.");
    cJSON_Delete(root);

    return string;	
}


int load_task_value(char *string, TASK *task)
{
    int status = 0;
    TASKID id;
    const cJSON *idnode = NULL;
    const cJSON *content = NULL;
    const cJSON *create = NULL;

    cJSON *root = cJSON_Parse(string);
    if (root == NULL)
    {
        const char *error_ptr = cJSON_GetErrorPtr();
        if (error_ptr != NULL)
            syslog_error("JSON Parse: %s", error_ptr);
        goto end;
    }

    idnode = cJSON_GetObjectItemCaseSensitive(root, "id");
    if (cJSON_IsString(idnode) && (idnode->valuestring != NULL)) {
    	// save task id
    	memcpy(task->id, idnode->valuestring, sizeof(TASKID));
    } else {
    	syslog_error("JSON string without task id? it is impossiable.");
    	goto end;
    }

    content = cJSON_GetObjectItemCaseSensitive(root, "content");
    if (cJSON_IsString(content) && (content->valuestring != NULL)) {
    	// save task content
    	memcpy(task->content, content->valuestring, strlen(content->valuestring));
    } else {
    	syslog_error("JSON string without content? it is impossiable.");
    	goto end;
    }
    create = cJSON_GetObjectItemCaseSensitive(root, "create");
    if (! cJSON_IsNumber(create)) {
    	syslog_error("JSON string without create time? it is impossiable.");
        goto end;
    } else {
    	task->create = (TIME)create->valuedouble;
    }

    // Does content match id ?
    get_task_id(task->content, id);
    status = (strcmp(task->id, id) == 0);

end:
    cJSON_Delete(root);

    return (status == 1)?RET_OK : RET_ERROR;
}

int load_task_state(char *string, TASK *task)
{
    int status = 0;
    const cJSON *progress = NULL;
    const cJSON *update = NULL;
    const cJSON *pid = NULL;

    cJSON *root = cJSON_Parse(string);
    if (root == NULL)
    {
        const char *error_ptr = cJSON_GetErrorPtr();
        if (error_ptr != NULL)
            syslog_error("JSON Parse: %s", error_ptr);
        goto end;
    }

	status = 1; // JSON status OK
    progress = cJSON_GetObjectItemCaseSensitive(root, "progress");
    if (cJSON_IsNumber(progress)) {
    	task->progress = (float)progress->valuedouble;
    } else {
    	// set default progress
    	task->progress = 0.0;
    }
    update = cJSON_GetObjectItemCaseSensitive(root, "update");
    if (cJSON_IsNumber(update)) {
    	task->update = (TIME)update->valuedouble;
    } else {
    	// set default time
    	task->update = time_now();
    }
    pid = cJSON_GetObjectItemCaseSensitive(root, "pid");
    if (cJSON_IsNumber(pid)) {
    	task->pid = (int)pid->valuedouble;
    } else {
    	task->pid = 0;
    }
end:
    cJSON_Delete(root);

    return (status == 1)?RET_OK : RET_ERROR;
}


int tasks_valid(TASKS * tasks)
{
	int ret = tasks && tasks->name && tasks->redis;
	if (!ret) {
		syslog_error("tasks is not valid.");
	}
	return ret;
}

int get_task_id(char *content, TASKID id)
{
	int i;
	unsigned char digest[16];

	MD5_CTX context;
	MD5_Init(&context);
	MD5_Update(&context, content, strlen(content));
	MD5_Final(digest, &context);

	for (i = 0; i < 16; ++i)
		sprintf(&id[i * 2], "%02x", (unsigned int) digest[i]);

	return RET_OK;
}

TASKS *tasks_create(char *name, int reset)
{
	TASKS *tasks;
	char cmd[1024];
	redisReply *reply;

	if (strcmp(name, "state") == 0) {
		syslog_error("tasks name could not be set as state.");
		return NULL;
	}

	tasks = (TASKS *) calloc((size_t) 1, sizeof(TASKS));

	if (tasks == NULL) {
		syslog_error("Allocate memory.");
		return NULL;
	}
	tasks->name = strdup(name);
	if (tasks->name == NULL) {
		syslog_error("Allocate memory for tasks name.");
		free(tasks);
		return NULL;
	}
	tasks->redis = (void *) redis_open();

	if (tasks->redis && reset) {
		// DEL video.tasks video.queue
		snprintf(cmd, sizeof(cmd), "DEL %s.tasks %s.queue", name, name);
		reply = tasks_command(tasks, cmd, REDIS_REPLY_STATUS);	// REDIS_REPLY_INTEGER ?
		if (reply)
			redis_free_replay(reply);
	}

	return tasks;
}


int get_task_value(TASKS * tasks, TASKID id, TASK * task)
{
	int ret = RET_ERROR;
	char cmd[1024];
	redisReply *reply;

	check_tasks(tasks);

	// cmd like: GET video.id
	snprintf(cmd, sizeof(cmd), "GET %s.%s", tasks->name, id);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply) {
		// JSON decode ...
		ret = load_task_value(reply->str, task);
		redis_free_replay(reply);
	}
	return ret;
}

float get_task_state(TASKS * tasks, TASKID id)
{
	TASK task;
	int ret = RET_ERROR;
	char cmd[1024];
	redisReply *reply;

	if (!tasks_valid(tasks))
		return 0.0;

	snprintf(cmd, sizeof(cmd), "GET state.%s", id);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply) {
		ret = load_task_state(reply->str, &task);
		redis_free_replay(reply);
	}

	return (ret == RET_OK)? task.progress : 0.0;
}

int set_task_state(TASKS * tasks, TASKID id, float progress)
{
	char *jstr;
	char cmd[1024];
	redisReply *reply;

	check_tasks(tasks);

	jstr = dump_task_state(progress);
	if (jstr == NULL) {
		syslog_error("Dump task state string.");
		return RET_ERROR;
	}
	snprintf(cmd, sizeof(cmd), "SET state.%s %s", id, jstr);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STATUS);
	if (reply) {
		redis_free_replay(reply);
		return RET_OK;
	}
	free(jstr);

	return RET_ERROR;
}

int get_index_task(TASKS * tasks, int index, TASK * task)
{
    // self.re.lindex(self.queue, index)
	int ret = RET_ERROR;
	char cmd[1024];
	redisReply *reply;

	check_tasks(tasks);

	snprintf(cmd, sizeof(cmd), "LINDEX %s.queue %d", tasks->name, index);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply) {
		ret = get_task_value(tasks, reply->str, task);
		redis_free_replay(reply);
	}

	return ret;
}

int get_first_task(TASKS * tasks, TASK * task)
{
	return get_index_task(tasks, 0, task);
}

int get_last_task(TASKS * tasks, TASK * task)
{
	return get_index_task(tasks, -1, task);
}

int get_queue_task(TASKS * tasks, char *pattern, TASK * task)
{
	int ret = RET_ERROR;
	TASKID id;
	char cmd[1024];
	redisReply *reply;

	check_tasks(tasks);

	// xxxx8888
	if (pattern != NULL && strlen(pattern) > 0) {

	} else {
		// First task
		snprintf(cmd, sizeof(cmd), "LPOP %s.queue", tasks->name);
		reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
		if (reply) {
			memcpy(id, reply->str, sizeof(TASKID));
			ret = RET_OK; // Get ID OK
			redis_free_replay(reply);
		}
	}

	if (ret == RET_OK)
		ret = get_task_value(tasks, id, task);

	return ret;
}

int set_queue_task(TASKS * tasks, char *content)
{
	TASKID id;
	TASK task;
	char cmd[1024];
	redisReply *reply;
	char *string;

	check_tasks(tasks);

	get_task_id(content, id);
	memset(&task, 0, sizeof(TASK));
	memcpy(task.id, id, sizeof(TASKID));
	memcpy(task.content, content, strlen(content));

	// set default
	task.create = time_now();

	string = dump_task_value(&task);
	if (string == NULL) {
		syslog_error("JSON dumps.");
		return RET_ERROR;
	}

    // # force delete id from video.queue/tasks
    // pipe.lrem(self.tasks, 0, id)
    // pipe.lrem(self.queue, 0, id)
	snprintf(cmd, sizeof(cmd), "LREM %s.tasks 0 %s", tasks->name, id);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply)
		redis_free_replay(reply);

	snprintf(cmd, sizeof(cmd), "LREM %s.queue 0 %s", tasks->name, id);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply)
		redis_free_replay(reply);

    // # push id to tail of queue/tasks
    // pipe.rpush(self.tasks, id)
    // pipe.rpush(self.queue, id)
	snprintf(cmd, sizeof(cmd), "RPUSH %s.tasks %s", tasks->name, id);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply)
		redis_free_replay(reply);

	snprintf(cmd, sizeof(cmd), "RPUSH %s.queue %s", tasks->name, id);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply)
		redis_free_replay(reply);

    // # set id/content/create
    // pipe.set(f"{self.name}.{id}", json.dumps(task))
	snprintf(cmd, sizeof(cmd), "SET %s.%s %s", tasks->name, id, string);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply)
		redis_free_replay(reply);

	free(string);

	return RET_OK;
}

int del_queue_task(TASKS * tasks, TASKID id)
{
	char cmd[1024];
	redisReply *reply;

	check_tasks(tasks);

    // pipe.lrem(self.tasks, 0, id)
	snprintf(cmd, sizeof(cmd), "LREM %s.tasks 0 %s", tasks->name, id);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply)
		redis_free_replay(reply);

    // pipe.lrem(self.queue, 0, id)
	snprintf(cmd, sizeof(cmd), "LREM %s.queue 0 %s", tasks->name, id);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply)
		redis_free_replay(reply);

    // pipe.delete(f"{self.name}.{id}")
	snprintf(cmd, sizeof(cmd), "DEL %s.%s", tasks->name, id);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply)
		redis_free_replay(reply);

    // pipe.delete(f"state.{id}")
	snprintf(cmd, sizeof(cmd), "DEL state.%s", id);
	reply = tasks_command(tasks, cmd, REDIS_REPLY_STRING);
	if (reply)
		redis_free_replay(reply);

	return RET_OK;
}

void tasks_destroy(TASKS * tasks)
{
	if (tasks) {
		if (tasks->name)
			free(tasks->name);
		if (tasks->redis)
			redis_close((redisContext *) tasks->redis);
		free(tasks);
	}
}

int demo_image_service()
{
	while (1) {
		// open window ?
	}

	return RET_OK;
}

int demo_video_service()
{
	TASK t;
	int pids = 0;
	TASKS *video = tasks_create("video", 1);	// reset

	while (video) {
		// open window ?
		if (pids < 2) {
			// could create new process for tasks
			if (get_queue_task(video, "", &t) == RET_OK) {
				// we got task, create process
				;
			} else {
				// NO task, clear_resource
				;
				// clear_resource()
			}

		} else {
			// no resourece
			;
			// clear_resource() ...
		}
	}
	tasks_destroy(video);

	return RET_OK;
}
