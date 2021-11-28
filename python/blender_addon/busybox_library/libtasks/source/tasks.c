/************************************************************************************
***
***	Copyright 2021 Dell(18588220928@163.com), All Rights Reserved.
***
***	File Author: Dell, 2021-11-22 18:23:02
***
************************************************************************************/

#include "tasks.h"
#include "hiredis.h"
#include "cJSON.h"

#include <stdlib.h>
#include <openssl/md5.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <sys/inotify.h>

#define PIDSET_MAX_NO 1024

typedef struct {
	int count;
	pid_t pids[PIDSET_MAX_NO];
} PIDSET;

static PIDSET __global_pid_set;
PIDSET *pid_set()
{
	return &__global_pid_set;
}

// Redis Tasks API

// internal implement:
//     video.tasks -- rpush list for all video task ['color.00001', 'clean.00002', ... ]
//     video.queue -- rpush list for queue, ['color.00001', 'clean.00002'] for queue

//     video.color.00001.value -- json string: 'id', 'content', 'create' with valid check.
//     video.color.00001.state -- json string: 'progress', 'update', 'pid', 'status'

//     video.clean.00002.value -- json string: 'id', 'content', 'create' with valid check.
//     video.clean.00002.state -- json string: 'progress', 'update', 'pid', 'status'


char *taskset_version()
{
	return TASKSET_VERSION;
}

TIME time_now()
{
	TIME ms;
	struct timeval t;

	gettimeofday(&t, NULL);
	ms = t.tv_sec * 1000 + t.tv_usec / 1000;

	return ms;
}

int file_exists(char *filename)
{
	struct stat s;
	if (!filename) {
		syslog_error("file name is null");
		return 0;
	}
	if (stat(filename, &s) != 0 || !S_ISREG(s.st_mode)) {
		syslog_error("file '%s' not exists.", filename);
		return 0;
	}
	return 1;
}

redisContext *redis_connect()
{
	redisContext *c = redisConnect("127.0.0.1", 6379);
	if (c == NULL || c->err) {
		if (c) {
			syslog_error("Redis connect: %s", c->errstr);
			redisFree(c);
		} else {
			syslog_error("Allocate memory for redis connect context");
		}
		return NULL;
	}
	return c;
}

int taskset_valid(TASKSET * tasks)
{
	if (tasks == NULL || tasks->name == NULL) {
		syslog_error("Task set is NULL");
		return 0;
	}
	// re-connect chance ?
	if (tasks->redis == NULL)
		tasks->redis = (void *) redis_connect();

	if (tasks->redis == NULL)
		syslog_error("Redis re-connect");

	return (tasks->redis == NULL) ? 0 : 1;
}

#define check_taskset(tasks) do { if (! taskset_valid(tasks)) return RET_ERROR; } while (0)

int check_reply(TASKSET * tasks, redisReply * reply)
{
	int need_reset = 0;

	redisContext *c = (redisContext *) tasks->redis;
	if (reply == NULL || c->err) {
		syslog_error("Redis reply is NULL or %s", c->errstr);
		need_reset = 1;
	} else if (reply->type == REDIS_REPLY_ERROR) {
		syslog_error("Redis reply %s", reply->str);
		need_reset = 1;
	}
	if (need_reset && c != NULL) {
		redisFree(c);
		tasks->redis = NULL;	// setup for re-connect if we check_taskset
	}

	return (need_reset) ? RET_ERROR : RET_OK;
}

// check reply and type
int check_reply_type(TASKSET * tasks, redisReply * reply, int type)
{
	int ret = check_reply(tasks, reply);
	return (ret == RET_OK && reply->type == type) ? RET_OK : RET_ERROR;
}

#define free_reply(reply) do { if (reply) freeReplyObject(reply); } while(0)

#define taskset_get_command(tasks, fmt, args...) redisCommand((redisContext *)tasks->redis, fmt, ##args)

#define taskset_set_command(tasks, reply, ret, fmt, args...) do { \
	ret = RET_ERROR; \
	if (taskset_valid(tasks)) { \
		reply = redisCommand((redisContext *)tasks->redis, fmt, ##args); \
		ret = check_reply(tasks, reply); \
		free_reply(reply);\
	} \
} while(0)

#define taskset_del_command(tasks, reply, fmt, args...) do { \
	if (taskset_valid(tasks)) { \
		reply = redisCommand((redisContext *)tasks->redis, fmt, ##args); \
		check_reply(tasks, reply); \
		free_reply(reply);\
	} \
} while(0)

char *dump_task_value(TASK * task)
{
	char *string = NULL;
	cJSON *root = cJSON_CreateObject();

	if (cJSON_AddStringToObject(root, "id", task->id) == NULL) {
		syslog_error("cJSON_AddStringToObject for task id");
		goto end;
	}
	if (cJSON_AddStringToObject(root, "content", task->content) == NULL) {
		syslog_error("cJSON_AddStringToObject for task content");
		goto end;
	}
	if (cJSON_AddNumberToObject(root, "create", task->create) == NULL) {
		syslog_error("cJSON_AddNumberToObject for task create time");
		goto end;
	}

	string = cJSON_PrintUnformatted(root);
	if (string == NULL) {
		syslog_error("cJSON_PrintUnformatted for task value");
	}
  end:
	cJSON_Delete(root);

	return string;
}

char *dump_task_state(float progress)
{
	char *string = NULL;
	cJSON *root = cJSON_CreateObject();

	if (cJSON_AddNumberToObject(root, "progress", progress) == NULL) {
		syslog_error("cJSON_AddNumberToObject for task progress");
		goto end;
	}
	if (cJSON_AddNumberToObject(root, "update", time_now()) == NULL) {
		syslog_error("cJSON_AddNumberToObject for task update");
		goto end;
	}
	if (cJSON_AddNumberToObject(root, "pid", getpid()) == NULL) {
		syslog_error("cJSON_AddNumberToObject for task pid");
		goto end;
	}

	string = cJSON_PrintUnformatted(root);
	if (string == NULL) {
		syslog_error("cJSON_PrintUnformatted for task state");
	}
  end:
	cJSON_Delete(root);

	return string;
}

int load_task_value(char *string, TASK * task)
{
	TASKID id;
	int status = 0;
	const cJSON *idnode = NULL;
	const cJSON *content = NULL;
	const cJSON *create = NULL;

	cJSON *root = cJSON_Parse(string);
	if (root == NULL) {
		const char *error_ptr = cJSON_GetErrorPtr();
		if (error_ptr != NULL)
			syslog_error("JSON parse %s for '%s'", error_ptr, string);
		goto end;
	}

	memset(task, 0, sizeof(TASK));	// must init
	idnode = cJSON_GetObjectItemCaseSensitive(root, "id");
	if (cJSON_IsString(idnode) && (idnode->valuestring != NULL)) {
		memcpy(task->id, idnode->valuestring, sizeof(TASKID));
	} else {
		syslog_error("JSON string without task id");
		goto end;
	}

	content = cJSON_GetObjectItemCaseSensitive(root, "content");
	if (cJSON_IsString(content) && (content->valuestring != NULL)) {
		size_t len = MIN(strlen(content->valuestring), TASK_CONTENT_MAX_LEN - 1);
		memcpy(task->content, content->valuestring, len);
	} else {
		syslog_error("JSON string without content");
		goto end;
	}
	create = cJSON_GetObjectItemCaseSensitive(root, "create");
	if (!cJSON_IsNumber(create)) {
		syslog_error("JSON string without create time");
		goto end;
	} else {
		task->create = (TIME) create->valuedouble;
	}

	// content match id ?
	get_task_id(task->content, id);
	status = (strcmp(task->id, id) == 0);

  end:
	cJSON_Delete(root);

	return (status == 1) ? RET_OK : RET_ERROR;
}

int load_task_state(char *string, TASK * task)
{
	int status = 0;
	const cJSON *progress = NULL;
	const cJSON *update = NULL;
	const cJSON *pid = NULL;

	cJSON *root = cJSON_Parse(string);
	if (root == NULL) {
		const char *error_ptr = cJSON_GetErrorPtr();
		if (error_ptr != NULL)
			syslog_error("JSON parse %s", error_ptr);
		goto end;
	}

	status = 1;					// JSON status OK
	progress = cJSON_GetObjectItemCaseSensitive(root, "progress");
	if (cJSON_IsNumber(progress)) {
		task->progress = (float) progress->valuedouble;
	} else {
		// set default progress
		task->progress = 0.0;
	}
	update = cJSON_GetObjectItemCaseSensitive(root, "update");
	if (cJSON_IsNumber(update)) {
		task->update = (TIME) update->valuedouble;
	} else {
		// set default time
		task->update = time_now();
	}
	pid = cJSON_GetObjectItemCaseSensitive(root, "pid");
	if (cJSON_IsNumber(pid)) {
		task->pid = (int) pid->valuedouble;
	} else {
		task->pid = 0;
	}
  end:
	cJSON_Delete(root);

	return (status == 1) ? RET_OK : RET_ERROR;
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

int get_task_key(char *content, char *key_buff, size_t key_size)
{
	TASKID id;
	int len;
	char prefix[1024], *p;

	snprintf(prefix, sizeof(prefix), "%s", content);
	if ((p = strchr(prefix, '(')) == NULL) {
		syslog_error("task content '%s' miss (", content);
		return RET_ERROR;
	}
	*p = '\0';
	len = strlen(prefix);
	if (len + 1 + sizeof(TASKID) > key_size) {
		syslog_error("key_size (%ld) too small (< %ld) from get_task_key()", key_size, len + 1 + sizeof(TASKID));
		return RET_ERROR;
	}

	get_task_id(content, id);
	snprintf(key_buff, key_size, "%s.%s", prefix, id);

	return RET_OK;
}

TASKSET *create_taskset(char *name)
{
	TASKSET *tasks;

	tasks = (TASKSET *) calloc((size_t) 1, sizeof(TASKSET));
	if (tasks == NULL) {
		syslog_error("Allocate memory for task set '%s'", name);
		return NULL;
	}
	tasks->name = strdup(name);
	if (tasks->name == NULL) {
		syslog_error("Allocate memory for task set name of '%s'", name);
		free(tasks);

		return NULL;
	}

	tasks->redis = (void *) redis_connect();
	return tasks;
}

int get_task_value(TASKSET * tasks, char *key, TASK * task)
{
	int ret;
	redisReply *reply;

	// GET video.color.id.value
	check_taskset(tasks);
	reply = taskset_get_command(tasks, "GET %s.%s.value", tasks->name, key);
	ret = check_reply_type(tasks, reply, REDIS_REPLY_STRING);
	if (ret == RET_OK) {
		ret = load_task_value(reply->str, task);
	}
	free_reply(reply);

	return ret;
}

float get_task_state(TASKSET * tasks, char *key)
{
	int ret;
	TASK task;
	redisReply *reply;

	if (!taskset_valid(tasks))
		return 0.0;

	// GET video.color.id.state
	reply = taskset_get_command(tasks, "GET %s.%s.state", tasks->name, key);
	ret = check_reply_type(tasks, reply, REDIS_REPLY_STRING);
	if (ret == RET_OK)
		ret = load_task_state(reply->str, &task);
	free_reply(reply);

	return (ret == RET_OK) ? task.progress : 0.0;
}

int set_task_state(TASKSET * tasks, char *key, float progress)
{
	int ret;
	char *jstr;
	redisReply *reply;

	if ((jstr = dump_task_state(progress)) == NULL)
		return RET_ERROR;

	// SET video.color.id.state 
	taskset_set_command(tasks, reply, ret, "SET %s.%s.state %s", tasks->name, key, jstr);

	free(jstr);

	return ret;
}

// timeout is ms
int wait_task_done(TASKSET * tasks, char *key, int timeout, TASK_DONE_CALLBACK callback)
{
	TASK task;
	int ret, f_argc;
	char *f_argv[32], f_buffer[TASK_CONTENT_MAX_LEN];
	char *output_file;

	fd_set rfds;
	struct timeval tv;
	int fd, wd, nready;

	if (callback == NULL) {
		syslog_error("Please set call back in wait_task_done()");
		return RET_ERROR;
	}

	if ((ret = get_task_value(tasks, key, &task)) != RET_ERROR) {
		syslog_error("Task '%s.%s' not exist.", tasks->name, key);
		return RET_ERROR;
	}

	snprintf(f_buffer, sizeof(f_buffer), "%s", task.content);
	f_argc = fargs_parse(f_buffer, ARRAY_SIZE(f_argv), f_argv);
	output_file = fargs_search("output_file", f_argc, f_argv);
	if (!output_file) {
		syslog_error("Task miss output file parameters.");
		return RET_ERROR;
	}
	// monitor output file
	ret = RET_ERROR;

	fd = inotify_init();
	if (fd < 0) {
		syslog_error("inotify_init");
		return RET_ERROR;
	}
	wd = inotify_add_watch(fd, output_file, IN_CLOSE_WRITE);
	if (wd >= 0) {
		FD_ZERO(&rfds);
		FD_SET(fd, &rfds);
		tv.tv_sec = timeout / 1000;
		tv.tv_usec = (timeout % 1000) * 1000;
		nready = select(fd + 1, &rfds, NULL, NULL, &tv);
		if (nready == -1) {
			syslog_error("select");
		} else if (nready == 0) {
			;					// timeout;
		} else {
			// now output file is created
			ret = RET_OK;
			callback(key, output_file);
		}
		inotify_rm_watch(fd, wd);
	}
	close(fd);

	return ret;
}

int get_queue_len(TASKSET * tasks)
{
	int ret;
	redisReply *reply;

	check_taskset(tasks);
	reply = taskset_get_command(tasks, "LLEN %s.queue", tasks->name);
	ret = check_reply_type(tasks, reply, REDIS_REPLY_INTEGER);
	ret = (ret == RET_OK) ? reply->integer : 0;
	free_reply(reply);

	return ret;
}

int get_first_qkey(TASKSET * tasks, char *key_buff, size_t key_size)
{
	int ret;
	redisReply *reply;

	check_taskset(tasks);
	reply = taskset_get_command(tasks, "LINDEX %s.queue 0", tasks->name);
	ret = check_reply_type(tasks, reply, REDIS_REPLY_STRING);
	if (ret == RET_OK)
		ret = snprintf(key_buff, key_size, "%s", reply->str) > 0 ? RET_OK : RET_ERROR;
	free_reply(reply);

	return ret;
}

int get_queue_task(TASKSET * tasks, char *pattern, TASK * task)
{
	int ret = RET_ERROR;
	char key[256];
	redisReply *reply;

	check_taskset(tasks);

	if (pattern != NULL && strlen(pattern) > 0) {
		int j, match_len;
		char match[256];

		// color will match 'color.id'
		snprintf(match, sizeof(match), "%s.", pattern);
		match_len = strlen(match);

		reply = taskset_get_command(tasks, "LRANGE %s.queue 0 -1", tasks->name);
		ret = check_reply_type(tasks, reply, REDIS_REPLY_ARRAY);
		if (ret == RET_OK) {
			ret = RET_ERROR;	// must init, not found
			for (j = 0; j < (int) reply->elements; j++) {
				if (strncmp(reply->element[j]->str, match, match_len) != 0)
					continue;
				snprintf(key, sizeof(key), "%s", reply->element[j]->str);
				// force delete id from queue
				taskset_del_command(tasks, reply, "LREM %s.queue 0 %s", tasks->name, key);
				ret = RET_OK;	// found
				break;
			}
		}
	} else {
		// First task
		reply = taskset_get_command(tasks, "LPOP %s.queue", tasks->name);
		ret = check_reply_type(tasks, reply, REDIS_REPLY_STRING);
		if (ret == RET_OK)
			snprintf(key, sizeof(key), "%s", reply->str);
		free_reply(reply);
	}

	if (ret == RET_OK)
		ret = get_task_value(tasks, key, task);

	return ret;
}

int set_queue_task(TASKSET * tasks, char *content)
{
	TASK task;
	int ret;
	char key[256], *string, *id;
	redisReply *reply;

	if (get_task_key(content, key, sizeof(key)) != RET_OK)
		return RET_ERROR;

	id = strchr(key, '.');
	if (id == NULL) {
		syslog_error("It is impossible, please check program logic !!!");
		return RET_ERROR;
	}
	id++;						// skip '.'

	memset(&task, 0, sizeof(TASK));	// must init
	memcpy(task.id, id, sizeof(TASKID));
	memcpy(task.content, content, strlen(content));
	// set default
	task.create = time_now();
	if ((string = dump_task_value(&task)) == NULL)
		return RET_ERROR;

	// set task value
	taskset_set_command(tasks, reply, ret, "SET %s.%s.value %s", tasks->name, key, string);

	free(string);

	if (ret == RET_OK) {
		// # force delete id from video.queue/tasks
		taskset_del_command(tasks, reply, "LREM %s.tasks 0 %s", tasks->name, key);
		taskset_del_command(tasks, reply, "LREM %s.queue 0 %s", tasks->name, key);

		// # push id to tail of queue/tasks
		taskset_del_command(tasks, reply, "RPUSH %s.tasks %s", tasks->name, key);
		taskset_del_command(tasks, reply, "RPUSH %s.queue %s", tasks->name, key);
	}

	return ret;
}

int delete_task(TASKSET * tasks, char *key)
{
	redisReply *reply;

	// LREM video.queue 0 key
	taskset_del_command(tasks, reply, "LREM %s.queue 0 %s", tasks->name, key);

	// LREM video.tasks 0 key
	taskset_del_command(tasks, reply, "LREM %s.tasks 0 %s", tasks->name, key);

	// DEL video.color.id.value
	taskset_del_command(tasks, reply, "DEL %s.%s.value", tasks->name, key);

	// DEL video.color.id.state
	taskset_del_command(tasks, reply, "DEL %s.%s.state", tasks->name, key);

	return RET_OK;
}

int taskset_clear(TASKSET * tasks)
{
	int j, ret;
	redisReply *reply;

	check_taskset(tasks);
	reply = taskset_get_command(tasks, "LRANGE %s.queue 0 -1", tasks->name);
	ret = check_reply_type(tasks, reply, REDIS_REPLY_ARRAY);
	if (ret == RET_OK) {
		for (j = 0; j < (int) reply->elements; j++)
			delete_task(tasks, reply->element[j]->str);
	}

	check_taskset(tasks);
	reply = taskset_get_command(tasks, "LRANGE %s.tasks 0 -1", tasks->name);
	ret = check_reply_type(tasks, reply, REDIS_REPLY_ARRAY);
	if (ret == RET_OK) {
		for (j = 0; j < (int) reply->elements; j++)
			delete_task(tasks, reply->element[j]->str);
	}

	return ret;
}

void destroy_taskset(TASKSET * tasks)
{
	if (tasks) {
		if (tasks->name)
			free(tasks->name);
		if (tasks->redis)
			redisFree((redisContext *) tasks->redis);
		free(tasks);
	}
}

void pidset_clear()
{
	pid_set()->count = 0;
}

int pidset_count()
{
	return pid_set()->count;
}

int search_pid(pid_t pid)
{
	int i;
	PIDSET *set = pid_set();
	for (i = 0; i < set->count; i++) {
		if (set->pids[i] == pid)
			return i;
	}
	return -1;
}

int register_pid(pid_t pid)
{
	int index;
	PIDSET *set = pid_set();

	index = search_pid(pid);
	if (index >= 0)
		return RET_OK;			// pid exists

	if (set->count < PIDSET_MAX_NO) {
		set->pids[set->count] = pid;
		set->count++;
		return RET_OK;
	}
	// pid set full
	return RET_ERROR;
}

void unregister_pid(pid_t pid)
{
	int index;
	PIDSET *set = pid_set();

	if ((index = search_pid(pid)) >= 0) {
		set->pids[index] = set->pids[set->count - 1];
		set->count--;
	}
}

void taskset_service(char *tasks_name, int max_workers, TASKSET_HANDLER handle)
{
	pid_t pid;
	TASKSET *taskset = create_taskset(tasks_name);

	if (!taskset)
		return;

	pidset_clear();
	if (max_workers < 1)
		max_workers = 1;		// at least 1

	syslog_info("Running '%s' service with %d workers ...", tasks_name, max_workers);
	while (1) {
		// is there any idle slot in pools and queue task ?
		if (pidset_count() < max_workers && get_queue_len(taskset) > 0) {
			// create process
			pid = fork();
			if (pid == -1) {
				syslog_error("system fork");
				continue;
			}

			if (pid == 0) {
				exit(handle(tasks_name));
			} else {
				register_pid(pid);
			}
		} else {
			// idle time, clean zombie
			pid = waitpid(-1, NULL, WNOHANG);
			if (pid > 1)
				unregister_pid(pid);
			else
				sleep(1);
		}
	}
	destroy_taskset(taskset);
}

int get_token(char *buf, char deli, int maxcnt, char *targv[])
{
	int n = 0;
	int squote = 0;
	int dquote = 0;

	if (!buf)
		return 0;

	targv[n] = buf;
	while (*buf && (n + 1) < maxcnt) {
		if ((squote % 2) == 0 && (dquote % 2) == 0 && deli == *buf) {
			*buf = '\0';
			++buf;
			while (*buf == deli)
				++buf;
			targv[++n] = buf;
			squote = dquote = 0;	// new start !!!
		}
		squote += (*buf == '\'') ? 1 : 0;
		dquote += (*buf == '\"') ? 1 : 0;
		++buf;
	}
	return (n + 1);
}

int fargs_parse(char *command, int maxargc, char *argv[])
{
	char *bs, *be;

	bs = strchr(command, '(');
	be = strrchr(command, ')');
	if (bs == NULL || be == NULL || bs > be) {
		syslog_error("command does not match function pattern.");
		return -1;
	}
	*bs++ = '\0';				// remove '(' and move to next char
	*be = '\0';					// remove ')'
	return get_token(bs, ',', maxargc, argv);
}

char *fargs_search(char *name, int argc, char *argv[])
{
	int i;
	char *es;

	for (i = 0; i < argc; i++) {
		es = strchr(argv[i], '=');
		if (es && strncmp(argv[i], name, (int) (es - argv[i])) == 0)
			return es + 1;		// skip =
	}
	return NULL;
}
