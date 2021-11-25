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
#include <unistd.h>
#include <sys/wait.h>

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

redisContext *redis_connect()
{
	redisContext *c = redisConnect("127.0.0.1", 6379);
	if (c == NULL || c->err) {
		if (c) {
			syslog_error("Redis connect: %s", c->errstr);
			redisFree(c);
		} else {
			syslog_error("Allocate memory");
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
		if (error_ptr != NULL) {
			syslog_error("JSON parse %s", error_ptr);
			syslog_debug("JSON: %s", string);
		}
		goto end;
	}

	memset(task, 0, sizeof(TASK));	// must
	idnode = cJSON_GetObjectItemCaseSensitive(root, "id");
	if (cJSON_IsString(idnode) && (idnode->valuestring != NULL)) {
		// save task id
		memcpy(task->id, idnode->valuestring, sizeof(TASKID));
	} else {
		syslog_error("JSON string without task id");
		goto end;
	}

	content = cJSON_GetObjectItemCaseSensitive(root, "content");
	if (cJSON_IsString(content) && (content->valuestring != NULL)) {
		// save task content
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
	int i, len;
	char prefix[64], *p;

	p = strstr(content, "(");
	if (p == NULL) {
		syslog_error("Content '%s' missing (", content);
		return RET_ERROR;
	}
	len = (int) (p - content);
	if (len > (int) sizeof(prefix) - 1) {
		syslog_error("Content prefix too long (> %ld)", sizeof(prefix) - 1);
		return RET_ERROR;
	}
	if (len + 1 + sizeof(TASKID) > key_size) {
		syslog_error("key_size (%ld) too small (< %ld)", key_size, len + 1 + sizeof(TASKID));
		return RET_ERROR;
	}
	// save prefix
	for (i = 0; i < len; i++)
		prefix[i] = content[i];
	prefix[i] = '\0';

	get_task_id(content, id);
	snprintf(key_buff, key_size, "%s.%s", prefix, id);

	return RET_OK;
}


TASKSET *create_taskset(char *name)
{
	TASKSET *tasks;

	tasks = (TASKSET *) calloc((size_t) 1, sizeof(TASKSET));
	if (tasks == NULL) {
		syslog_error("Allocate memory for task set");
		return NULL;
	}
	tasks->name = strdup(name);
	if (tasks->name == NULL) {
		syslog_error("Allocate memory for task set name");
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

int get_index_task(TASKSET * tasks, int index, TASK * task)
{
	int ret;
	redisReply *reply;

	check_taskset(tasks);
	reply = taskset_get_command(tasks, "LINDEX %s.queue %d", tasks->name, index);
	ret = check_reply_type(tasks, reply, REDIS_REPLY_STRING);
	if (ret == RET_OK)
		ret = get_task_value(tasks, reply->str, task);
	free_reply(reply);

	return ret;
}

int get_first_task(TASKSET * tasks, TASK * task)
{
	return get_index_task(tasks, 0, task);
}

int get_last_task(TASKSET * tasks, TASK * task)
{
	return get_index_task(tasks, -1, task);
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
			for (j = 0; j < (int) reply->elements; j++) {
				if (strncmp(reply->element[j]->str, match, match_len) != 0)
					continue;

				// save key
				snprintf(key, sizeof(key), "%s", reply->element[j]->str);
				// force delete id from queue
				taskset_del_command(tasks, reply, "LREM %s.queue 0 %s", tasks->name, key);
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
	TASKID id;
	TASK task;
	int ret;
	char key[256];
	char *string;
	redisReply *reply;

	if (get_task_key(content, key, sizeof(key)) != RET_OK)
		return RET_ERROR;

	get_task_id(content, id);

	memset(&task, 0, sizeof(TASK));
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

int del_queue_task(TASKSET * tasks, char *key)
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

void pidset_dump(char *title)
{
	int i;
	PIDSET *set = pid_set();
	printf("%s pids count = %d: ", title, pidset_count());
	for (i = 0; i < set->count; i++) {
		printf("%d -- %d, ", i, set->pids[i]);
	}
	printf("\n");
}

int pidset_find(pid_t pid)
{
	int i;
	PIDSET *set = pid_set();
	for (i = 0; i < set->count; i++) {
		if (set->pids[i] == pid)
			return i;
	}
	return -1;
}

int pidset_add(pid_t pid)
{
	int index;
	PIDSET *set = pid_set();

	if (pid < 2)
		return RET_ERROR;		// pid should be > 1

	index = pidset_find(pid);
	if (index >= 0)
		return RET_OK;			// exists

	if (set->count < PIDSET_MAX_NO) {
		set->pids[set->count] = pid;
		set->count++;
		return RET_OK;
	}
	// set full

	return RET_ERROR;
}

void pidset_remove(pid_t pid)
{
	int index;
	PIDSET *set = pid_set();

	index = pidset_find(pid);
	if (index >= 0) {
		set->pids[index] = set->pids[set->count - 1];
		set->count--;
	}
}

void pidset_clean()
{
	pid_t pid;

	pid = waitpid(-1, NULL, WNOHANG);
	if (pid > 1)
		pidset_remove(pid);
}

void taskset_service(char *taskset_name, int max_workers, TASKSET_HANDLER handle)
{
	pid_t pid;
	TASK task;
	TASKSET *taskset = create_taskset(taskset_name);

	pidset_clear();
	while (taskset) {
		// is there empty slot in process pools ?
		// is there task avaible ?
		if (pidset_count() < max_workers && get_first_task(taskset, &task) == RET_OK) {
			// create process
			pid = fork();
			if (pid == -1) {
				syslog_error("fork");
				continue;
			}

			if (pid == 0) {
				exit(handle(taskset_name));
			}
			else {
				pidset_add(pid);
			}
		} else {
			// idle time, clean resource
			pidset_clean();
			sleep(1);
		}
	}
	destroy_taskset(taskset);
}


int get_token(char *buf, char deli, int maxcnt, char *tv[])
{
	int squote = 0;
	int dquote = 0;
	int n = 0;

	if (!buf)
		return 0;
	tv[n] = buf;
	while (*buf && (n + 1) < maxcnt) {
		if ((squote % 2) == 0 && (dquote % 2) == 0 && deli == *buf) {
			*buf = '\0';
			++buf;
			while (*buf == deli)
				++buf;
			tv[++n] = buf;
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
	int n;
	char *bs, *be;

	bs = strchr(command, '(');
	be = strrchr(command, ')');

	if (bs == NULL || be == NULL || bs > be) {
		syslog_error("command does not match function pattern.");
		return -1;
	}
	*bs++ = '\0';				// remove ( and move to next position
	*be = '\0';					// remove )
	n = get_token(bs, ',', maxargc, argv);

	return n;
}

char *fargs_search(char *name, int fargc, char *fargv[])
{
	char *bs;
	int i, len;

	for (i = 0; i < fargc; i++) {
		bs = strchr(fargv[i], '=');
		if (bs == NULL)
			continue;
		len = (int) (bs - fargv[i]);
		if (strncmp(fargv[i], name, len) == 0)
			return bs + 1;		// skip =
	}
	return NULL;
}

int video_clean(TASKSET *video, char *key, int argc, char *argv[])
{
	int i;

	char *infile = fargs_search("infile", argc, argv);
	char *sigma = fargs_search("sigma", argc, argv);
	char *outfile = fargs_search("outfile", argc, argv);

	if (infile == NULL || sigma == NULL || outfile == NULL) {
		syslog_error("video_clean missing parameters.");
		return RET_ERROR;
	}

	// load clean model
	for (i = 0; i < 100; i+=10) {
		set_task_state(video, key, (float)(i + 1));
		sleep(1);
	}

	return RET_OK;
}

int video_color(TASKSET *video, char *key, int argc, char *argv[])
{
	int i;

	char *infile = fargs_search("infile", argc, argv);
	char *color_picture = fargs_search("color_picture", argc, argv);
	char *outfile = fargs_search("outfile", argc, argv);

	if (infile == NULL || color_picture == NULL || outfile == NULL) {
		syslog_error("video_color missing parameters.");
		return RET_ERROR;
	}

	// load color model
	for (i = 0; i < 100; i+=10) {
		set_task_state(video, key, (float)(i + 1));
		sleep(1);
	}

	return RET_OK;
}

int video_slow(TASKSET *video, char *key, int argc, char *argv[])
{
	int i;

	char *infile = fargs_search("infile", argc, argv);
	char *slow_x = fargs_search("slow_x", argc, argv);
	char *outfile = fargs_search("outfile", argc, argv);

	if (infile == NULL || slow_x == NULL || outfile == NULL) {
		syslog_error("video_slow missing parameters.");
		return RET_ERROR;
	}

	// load slow model
	for (i = 0; i < 100; i+=10) {
		set_task_state(video, key, (float)(i + 1));
		sleep(1);
	}

	return RET_OK;
}


int video_handler(char *name)
{
	TASK task;
	TASKSET *video;
	int ret, f_argc;
	char *f_name, *f_argv[256], f_buffer[1024], key[256];

	ret = RET_ERROR;
	video = create_taskset(name);
	if (video && get_queue_task(video, NULL, &task) == RET_OK) {
		get_task_key(task.content, key, sizeof(key));

		// save task content to buffer for parsing
		snprintf(f_buffer, sizeof(f_buffer), "%s", task.content);
		f_name = f_buffer;
		f_argc = fargs_parse(f_buffer, ARRAY_SIZE(f_argv), f_argv);

		CheckPoint("Running video task ... pid = %d", getpid());

		if (strcmp(f_name, "clean") == 0) {
			ret = video_clean(video, key, f_argc, f_argv);
		} else if (strcmp(f_name, "color") == 0) {
			ret = video_color(video, key, f_argc, f_argv);
		} else if (strcmp(f_name, "slow") == 0) {
			ret = video_slow(video, key, f_argc, f_argv);
		} else {
			syslog_error("NOT implemented video model %s", f_name);
		}
	}
	destroy_taskset(video);

	return ret;
}

int image_clean(TASKSET *image, char *key, int argc, char *argv[])
{
	int i;

	char *infile = fargs_search("infile", argc, argv);
	char *sigma = fargs_search("sigma", argc, argv);
	char *outfile = fargs_search("outfile", argc, argv);

	if (infile == NULL || sigma == NULL || outfile == NULL) {
		syslog_error("image_clean missing parameters.");
		return RET_ERROR;
	}

	// load clean model
	for (i = 0; i < 5; i++) {
		set_task_state(image, key, (float)(i + 1)*20.0);
		sleep(1);
	}

	return RET_OK;
}

int image_color(TASKSET *image, char *key, int argc, char *argv[])
{
	int i;

	char *infile = fargs_search("infile", argc, argv);
	char *color_picture = fargs_search("color_picture", argc, argv);
	char *outfile = fargs_search("outfile", argc, argv);

	if (infile == NULL || color_picture == NULL || outfile == NULL) {
		syslog_error("image_color missing parameters.");
		return RET_ERROR;
	}

	// load color model
	for (i = 0; i < 5; i++) {
		set_task_state(image, key, (float)(i + 1)*20.0);
		sleep(1);
	}

	return RET_OK;
}

int image_zoom(TASKSET *image, char *key, int argc, char *argv[])
{
	int i;

	char *infile = fargs_search("infile", argc, argv);
	char *outfile = fargs_search("outfile", argc, argv);

	if (infile == NULL || outfile == NULL) {
		syslog_error("image_zoom missing parameters.");
		return RET_ERROR;
	}

	// load zoom model
	for (i = 0; i < 5; i++) {
		set_task_state(image, key, (float)(i + 1)*20.0);
		sleep(1);
	}

	return RET_OK;
}

int image_handler(char *name)
{
	TASK task;
	TASKSET *image;
	int ret, f_argc;
	char *f_name, *f_argv[256], f_buffer[1024], key[256], pattern[256];

	int total_running_times = 0;
	int continue_idle_times = 0;

	ret = RET_ERROR;
	pattern[0] = '\0';	// Set any at first
	image = create_taskset(name);

	while (image) {
		if (get_queue_task(image, pattern, &task) == RET_OK) {
			total_running_times++;
			continue_idle_times = 0;	// stop count

			get_task_key(task.content, key, sizeof(key));

			// save task content to buffer for parsing
			snprintf(f_buffer, sizeof(f_buffer), "%s", task.content);
			f_name = f_buffer;
			f_argc = fargs_parse(f_buffer, ARRAY_SIZE(f_argv), f_argv);

			// save pattern for next loop
			snprintf(pattern, sizeof(pattern), "%s", f_name);

			CheckPoint("Running image task ...");
			if (strcmp(f_name, "clean") == 0) {
				ret = image_clean(image, key, f_argc, f_argv);
			} else if (strcmp(f_name, "color") == 0) {
				ret = image_color(image, key, f_argc, f_argv);
			} else if (strcmp(f_name, "zoom") == 0) {
				ret = image_zoom(image, key, f_argc, f_argv);
			} else {
				syslog_error("NOT implemented image model %s", f_name);
			}
		} else {
			// no task avaible
			continue_idle_times++;
			sleep(1);
		}

		// schedule strategy
		if (total_running_times >= 100 || continue_idle_times >= 5)
			break;
	}
	destroy_taskset(image);

	return ret;
}


void demo_video_client()
{
	char *clean_task = "clean(infile=a.mp4,sigma=30,outfile=b.mp4)";
	char *color_task = "color(infile=a.mp4,color_picture=color.png,sigma=30,outfile=b.mp4)";
	char *slow_task = "slow(infile=c.mp4,slow_x=3,outfile=d.mp4)";

	TASKSET *video = create_taskset("video");
	if (! video) {
		syslog_error("create video task set");
		return;
	}

	set_queue_task(video, clean_task);
	set_queue_task(video, color_task);
	set_queue_task(video, slow_task);

	destroy_taskset(video);
}


void demo_video_server()
{
	taskset_service("video", 2, video_handler);
}


void demo_image_client()
{
	char *clean_task = "clean(infile=a.mp4,sigma=30,outfile=b.mp4)";
	char *color_task = "color(infile=a.mp4,color_picture=color.png,sigma=30,outfile=b.mp4)";
	char *zoom_task = "zoom(infile=c.mp4,outfile=d.mp4)";

	TASKSET *image = create_taskset("image");
	if (! image) {
		syslog_error("create image task set");
		return;
	}

	// loop for test redis server start/stop
	set_queue_task(image, clean_task);
	set_queue_task(image, color_task);
	set_queue_task(image, zoom_task);

	destroy_taskset(image);
}


void demo_image_server()
{
	taskset_service("image", 2, image_handler);
}
