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

#define IMAGE_SERVICE_URL "tcp://127.0.0.1:9001"
#define IMAGE_SERVICE_CODE 0x90010000 

// typedef int (*CustomSevice)(int socket, int service_code, TENSOR *input_tensor);
typedef int (*CustomSevice)(int, int, TENSOR *);

// Simple RuntimeEngine for prediction
struct RuntimeEngine {
	int use_gpu;
	tvm::runtime::PackedFunc set_input;
	tvm::runtime::PackedFunc run;
	tvm::runtime::PackedFunc get_output;
};

void destroy_engine(RuntimeEngine *engine)
{
	if (engine)
		delete engine;
	engine = NULL;
}

RuntimeEngine *create_engine(char *so_file_name, char *json_file_name, char *params_file_name, int use_gpu)
{
	RuntimeEngine *engine = NULL;

	// load in the library
	DLDevice dev {kDLCPU, 0};
	tvm::runtime::Module mod_so = tvm::runtime::Module::LoadFromFile(so_file_name);

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

	// create the graph executor module
	tvm::runtime::Module gmod = (* tvm::runtime::Registry::Get("tvm.graph_runtime.create"))
	        (mod_json, mod_so, (int)dev.device_type, dev.device_id); // dev.device_type must be casted to int !!!

	// // load patameters
	tvm::runtime::PackedFunc load_params = gmod.GetFunction("load_params");
	load_params(mod_params);

	engine = new RuntimeEngine();

	if (engine) {
		engine->use_gpu = use_gpu;
		engine->set_input = gmod.GetFunction("set_input");
		engine->get_output = gmod.GetFunction("get_output");
		engine->run = gmod.GetFunction("run");
	}

	return engine;
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

TENSOR *do_service(RuntimeEngine *engine, int msgcode, TENSOR *input)
{
	int n;
	int dtype_code = kDLFloat;
	int dtype_bits = 32;
	int dtype_lanes = 1;
	DLTensor *x, *y;
	int64_t input_dims[4], output_dims[4];
	float *p;
	DLDevice dev {kDLCPU, 0};
	TENSOR *output;

	CHECK_TENSOR(input);

	// set input data
	input_dims[0] = input->batch;
	input_dims[1] = input->chan;
	input_dims[2] = input->height;
	input_dims[3] = input->width;
	n = input->batch * input->chan * input->height * input->width;
	TVMArrayAlloc(input_dims, 4, dtype_code, dtype_bits, dtype_lanes, dev.device_type, dev.device_id, &x);
	p = static_cast<float*>(x->data);
	memcpy(p, input->data, n * sizeof(float));

	// allocate output space ... ?
	output_dims[0] = input->batch;
	output_dims[1] = input->chan;
	output_dims[2] = input->height;
	output_dims[3] = input->width;
	n = input->batch * input->chan * input->height * input->width;
	TVMArrayAlloc(output_dims, 4, dtype_code, dtype_bits, dtype_lanes, dev.device_type, dev.device_id, &y);

	engine->set_input("x", x);
	engine->run();
	engine->get_output(0, y);

	p = static_cast<float*>(y->data);
	output = tensor_create(output_dims[0], output_dims[1], output_dims[2], output_dims[3]);
	CHECK_TENSOR(output);
	memcpy(output->data, p, n * sizeof(float));

	TVMArrayFree(x);
	TVMArrayFree(y);

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
      // SaveTensorAsImage(recv_tensor, input_file);
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
		return server(endpoint, "our_model", use_gpu);
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
