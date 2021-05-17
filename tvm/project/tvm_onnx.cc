/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

/*!
 * \brief Example code on load and run TVM module.s
 * \file cpp_deploy.cc
 */
#include <dlpack/dlpack.h>
#include <tvm/runtime/module.h>
#include <tvm/runtime/packed_func.h>
#include <tvm/runtime/registry.h>
#include <cstdio>
#include <fstream> 

#include <stdio.h>
#include <unistd.h>
#include <getopt.h>
#include <stdlib.h>
#include <syslog.h>
#include <nimage/image.h>
#include <nimage/nnmsg.h>

// For mkdir
#include <sys/types.h>
#include <sys/stat.h>

#include <cuda.h>
#include <cuda_runtime.h>


#define IMAGE_SERVICE_URL "tcp://127.0.0.1:9001"
#define IMAGE_SERVICE_CODE 0x90010000 

// typedef int (*CustomSevice)(int socket, int service_code, TENSOR *input_tensor);
typedef int (*CustomSevice)(int, int, TENSOR *);

// Simple RuntimeEngine for prediction

// xxxx8888 RuntimeEngine

struct RuntimeEngine {
	int use_gpu;

	int x_n, x_dims[4];
	int y_n, y_dims[4];
	DLTensor *x, *y;

	tvm::runtime::PackedFunc get_input;
	tvm::runtime::PackedFunc set_input;
	tvm::runtime::PackedFunc run;
	tvm::runtime::PackedFunc get_output;
};

RuntimeEngine *create_engine(char *so_file_name, char *json_file_name, char *params_file_name, int use_gpu)
{
	RuntimeEngine *engine = NULL;

	// load in the library
	DLDevice device {kDLCPU, 0};
	if (use_gpu)
		device.device_type = kDLGPU;

	CheckPoint();

	tvm::runtime::Module mod_so = tvm::runtime::Module::LoadFromFile(so_file_name);

	CheckPoint();

	std::ifstream json_in(json_file_name, std::ios::in);
	if(json_in.fail()) {
		throw std::runtime_error("could not open json file");
	}
	std::string mod_json((std::istreambuf_iterator<char>(json_in)), std::istreambuf_iterator<char>());
	json_in.close();

	// parameters in binary
	TVMByteArray mod_params;
	std::ifstream params_in(params_file_name, std::ios::binary);
	if(params_in.fail()) {
		throw std::runtime_error("could not open params file");
	}
	std::string mod_params_data((std::istreambuf_iterator<char>(params_in)), std::istreambuf_iterator<char>());
	params_in.close();
	mod_params.data = mod_params_data.c_str();
	mod_params.size = mod_params_data.length();

	// create the graph executor module, tvm.graph_executor.create, tvm.graph_runtime.create
	tvm::runtime::Module gmod = (* tvm::runtime::Registry::Get("tvm.graph_executor.create"))
	        (mod_json, mod_so, (int)device.device_type, device.device_id); // device.device_type must be casted to int !!!

	// // load patameters
	tvm::runtime::PackedFunc load_params = gmod.GetFunction("load_params");
	load_params(mod_params);

	engine = new RuntimeEngine();

	if (engine) {
		engine->use_gpu = use_gpu;
		engine->get_input = gmod.GetFunction("get_input");
		engine->set_input = gmod.GetFunction("set_input");
		engine->get_output = gmod.GetFunction("get_output");
		engine->run = gmod.GetFunction("run");
	} else {
		throw std::runtime_error("create engine");
	}

	int i, ndim, len;
	char buf[256];
	engine->x = engine->get_input(0);
	engine->y = engine->get_output(0);
	engine->x_n = 1;

	ndim = ARRAY_SIZE(engine->x_dims);
	for (len = 0, i = 0; i < engine->x->ndim; i++) {
		// save input shapes to x_dims[0, 4)
		engine->x_n *= engine->x->shape[i];
		if (i < ndim)
			engine->x_dims[i] = (int)engine->x->shape[i];
		else {
			engine->x_dims[ndim - 1] *= (int)engine->x->shape[i];
		}

		// format output
		len += snprintf(buf + len, sizeof(buf) - 1 - len, "%d", (int)engine->x->shape[i]);
		if (i < engine->x->ndim - 1)
			len += snprintf(buf + len, sizeof(buf) - 1 - len, "x");
	}
	// Fill x_dims with 1 for others ...
	for (; i < 4; i++)
		engine->x_dims[i] = 1;
	syslog_info("Model input: %s", buf);

	engine->y_n = 1;
	ndim = ARRAY_SIZE(engine->y_dims);
	for (len = 0, i = 0; i < engine->y->ndim; i++) {
		// save input shapes to y_dims[0, 4)
		engine->y_n *= engine->y->shape[i];
		if (i < ndim) {
			engine->y_dims[i] = (int)engine->y->shape[i];
		}
		else {
			engine->y_dims[ndim - 1] *= (int)engine->y->shape[i];
		}
		// format output
		len += snprintf(buf + len, sizeof(buf) - 1 - len, "%d", (int)engine->y->shape[i]);
		if (i < engine->y->ndim - 1)
			len += snprintf(buf + len, sizeof(buf) - 1 - len, "x");
	}
	// Fill y_dims with 1 for others ...
	for (; i < 4; i++)
		engine->y_dims[i] = 1;

	syslog_info("Model output: %s", buf);

	return engine;
}

TENSOR *engine_forward(RuntimeEngine *engine, TENSOR *input)
{
	int n;
	float *p;
	TENSOR *output;

	CHECK_TENSOR(input);
	n = input->batch * input->chan * input->height * input->width;
	if (n != engine->x_n) {
		syslog_error("Input tensor size %d does not match engine input size %d", n, engine->x_n);
		return NULL;
	}
	output = tensor_create(engine->y_dims[0], engine->y_dims[1], engine->y_dims[2], engine->y_dims[3]);
	CHECK_TENSOR(output);

	p = static_cast<float*>(engine->x->data);
	if (engine->use_gpu) {
		cudaMemcpy(p, input->data, engine->x_n * sizeof(float), cudaMemcpyHostToDevice);
	} else {
		memcpy(p, input->data, engine->x_n * sizeof(float));
	}

	engine->run();

	p = static_cast<float*>(engine->y->data);
	if (engine->use_gpu) {
		cudaMemcpy(output->data, p, engine->y_n * sizeof(float), cudaMemcpyDeviceToHost);
	} else {
		memcpy(output->data, p, engine->y_n * sizeof(float));
	}

	return output;
}

void destroy_engine(RuntimeEngine *engine)
{
	if (engine)
		delete engine;
	engine = NULL;
}

TENSOR *tensor_rpc(int socket, TENSOR * input, int reqcode)
{
	int rescode = -1;
	TENSOR *output = NULL;

	CHECK_TENSOR(input);

	if (tensor_send(socket, reqcode, input) == RET_OK) {
		output = tensor_recv(socket, &rescode);
	}
	if (rescode != reqcode) {
		// Bad service response
		syslog_error("Remote running service.");
		tensor_destroy(output);
		return NULL;
	}
	return output;
}

// zoom 4x
TENSOR *do_service(RuntimeEngine *engine, int msgcode, TENSOR *input)
{
	TENSOR *output;

	(void) msgcode;	// avoid compiler complaint
	CHECK_TENSOR(input);

	if (input->height == engine->x_dims[2] && input->width == engine->x_dims[3]) {
		output = engine_forward(engine, input);
		return output;
	}

	TENSOR *forward_input = tensor_zoom(input, engine->x_dims[2], engine->x_dims[3]);
	CHECK_TENSOR(forward_input);
	TENSOR *forward_output = engine_forward(engine, forward_input);
	CHECK_TENSOR(forward_output);

	output = tensor_zoom(forward_output, 4 * input->height, 4 * input->width);

	tensor_destroy(forward_output);
	tensor_destroy(forward_input);

	return output;
}

int server(char *endpoint, char *model_name, int use_gpu)
{
	int socket, count, msgcode;
	TENSOR *input_tensor, *output_tensor;
	char so_file_name[256], json_file_name[256], params_file_name[256];
	RuntimeEngine *engine = NULL;

	if ((socket = server_open(endpoint)) < 0)
		return RET_ERROR;

	snprintf(so_file_name, sizeof(so_file_name) - 1, "%s.so", model_name);
	snprintf(json_file_name, sizeof(json_file_name) - 1, "%s.json", model_name);
	snprintf(params_file_name, sizeof(params_file_name) - 1, "%s.params", model_name);

	engine = create_engine(so_file_name, json_file_name, params_file_name, use_gpu);

	if (engine == NULL) {
		syslog_error("Create Engine.");
		server_close(socket);
		return RET_ERROR;
	}

	count = 0;
	for (;;) {
		if (!socket_readable(socket, 1000))	// timeout 1 s
			continue;

		input_tensor = service_request(socket, &msgcode);
		if (!tensor_valid(input_tensor))
			continue;

		syslog_info("Service %d times", count);

		// Real service ...
		time_reset();
		output_tensor = do_service(engine, msgcode, input_tensor);
		time_spend((char *) "Service");

		service_response(socket, msgcode, output_tensor);

		tensor_destroy(output_tensor);
		tensor_destroy(input_tensor);

		count++;
	}
	destroy_engine(engine);

	syslog(LOG_INFO, "Service shutdown.\n");
	server_close(socket);

	return RET_OK;
}

void save_tensor_as_image(TENSOR * tensor, char *filename)
{
	char output_filename[256], *p;
	IMAGE *image = image_from_tensor(tensor, 0);

	if (image_valid(image)) {
		mkdir("output", S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);

		p = strrchr(filename, '/');
		p = (!p) ? filename : p + 1;
		snprintf(output_filename, sizeof(output_filename) - 1, "output/%s", p);
		image_save(image, output_filename);
		image_destroy(image);
	}
}

int image_post(int socket, char *input_file)
{
  IMAGE *send_image;
  TENSOR *send_tensor, *recv_tensor;

  printf("Image posting %s ...\n", input_file);

  send_image = image_load(input_file); check_image(send_image);

  if (image_valid(send_image)) {
    send_tensor = tensor_from_image(send_image, 0);
    check_tensor(send_tensor);

    recv_tensor = tensor_rpc(socket, send_tensor, IMAGE_SERVICE_CODE);
    if (tensor_valid(recv_tensor)) {
      save_tensor_as_image(recv_tensor, input_file);
      tensor_destroy(recv_tensor);
    }

    tensor_destroy(send_tensor);
    image_destroy(send_image);
  }

  return RET_OK;
}


void help(char *cmd)
{
	printf("Usage: %s [option] <image files>\n", cmd);
	printf("    h, --help                   Display this help.\n");
	printf("    e, --endpoint               Set endpoint.\n");
	printf("    s, --server <0 | 1>         Start server (use gpu).\n");

	exit(1);
}

int main(int argc, char **argv)
{
	int i, optc;
	int use_gpu = 0;
	int running_server = 0;
	int socket;

	int option_index = 0;
	char *endpoint = (char *) IMAGE_SERVICE_URL;

	struct option long_opts[] = {
		{"help", 0, 0, 'h'},
		{"endpoint", 1, 0, 'e'},
		{"server", 1, 0, 's'},
		{0, 0, 0, 0}
	};

	if (argc <= 1)
		help(argv[0]);

	while ((optc = getopt_long(argc, argv, "h e: s:", long_opts, &option_index)) != EOF) {
		switch (optc) {
		case 'e':
			endpoint = optarg;
			break;
		case 's':
			running_server = 1;
			use_gpu = atoi(optarg);
			break;
		case 'h':				// help
		default:
			help(argv[0]);
			break;
		}
	}

	if (running_server) {
		// if (IsRunning(endpoint))
		// 	exit(-1);
		return server(endpoint, "output/image_zooms.onnx", use_gpu);
	} else if (argc > 1) {
		if ((socket = client_open(endpoint)) < 0)
			return RET_ERROR;

		for (i = optind; i < argc; i++)
			image_post(socket, argv[i]);

		client_close(socket);
		return RET_OK;
	}

	help(argv[0]);

	return RET_ERROR;
}
