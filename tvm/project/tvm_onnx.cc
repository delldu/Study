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

#include <stdio.h>
#include <unistd.h>
#include <getopt.h>
#include <stdlib.h>
#include <syslog.h>
#include <nimage/image.h>
#include <nimage/nnmsg.h>

#define IMAGE_SERVICE_URL "tcp://127.0.0.1:9001"
#define IMAGE_SERVICE_CODE 0x90010000 

typedef tvm::runtime::Module TVM_Module;
typedef tvm::runtime::NDArray TVM_Tensor;

int server(char *endpoint, int use_gpu)
{
	std::vector < int64_t > input_shape;
	std::vector < int64_t > output_shape;

	// load in the library
	DLDevice dev {
	kDLCPU, 0};
	TVM_Module mod_factory = TVM_Module::LoadFromFile("lib/test_relay_add.so");

	// create the graph executor module
	TVM_Module gmod = mod_factory.GetFunction("default") (dev);
	tvm::runtime::PackedFunc set_input = gmod.GetFunction("set_input");
	tvm::runtime::PackedFunc get_output = gmod.GetFunction("get_output");
	tvm::runtime::PackedFunc run = gmod.GetFunction("run");


	// Use the C++ API
	input_shape.clear();
	output_shape.clear();


	TVM_Tensor x = TVM_Tensor::Empty({ 2, 2 }, DLDataType { kDLFloat, 32, 1 }, dev);
	TVM_Tensor y = TVM_Tensor::Empty({ 2, 2 }, DLDataType { kDLFloat, 32, 1 }, dev);

	for (int i = 0; i < 2; ++i) {
		for (int j = 0; j < 2; ++j) {
			static_cast < float *>(x->data)[i * 2 + j] = i * 2 + j;
		}
	}
	// set the right input
	set_input("x", x);
	// run the code
	run();
	// get the output
	get_output(0, y);

	for (int i = 0; i < 2; ++i) {
		for (int j = 0; j < 2; ++j) {
			ICHECK_EQ(static_cast < float *>(y->data)[i * 2 + j], i * 2 + j + 1);
		}
	}

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

    // eg: server limited: only accept 4 times tensor !!!
    // xxxx8888 recv_tensor = ResizeOnnxRPC(socket, send_tensor, IMAGE_SERVICE_CODE, 4);
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
		return server(endpoint, use_gpu);
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
