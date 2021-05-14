"""Onnx Model Tools."""# coding=utf-8
#
# /************************************************************************************
# ***
# ***    Copyright Dell 2021, All Rights Reserved.
# ***
# ***    File Author: Dell, 2021年 03月 23日 星期二 12:42:57 CST
# ***
# ************************************************************************************/
#

import numpy as np

import argparse
import pdb  # For debug
import time
import os
import onnx
import tvm
from tvm import relay

if __name__ == '__main__':
    """TVM Onnx tools ..."""

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', type=str, default="test.onnx", help="input onnx file")
    parser.add_argument('-e', '--export', help="export tvm model", action='store_true')
    parser.add_argument('-v', '--verify', help="verify tvm model", action='store_true')
    parser.add_argument('-g', '--gpu', help="use gpu", action='store_true')
    parser.add_argument('-o', '--output', type=str, default="output", help="output folder")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print("ONNX model file {} not exist.".format(args.input))
        os._exit(0)

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # /************************************************************************************
    # ***
    # ***    MS: Define Global Names
    # ***
    # ************************************************************************************/
    if args.gpu:
        target = tvm.target.Target("cuda", host='llvm')
        device = tvm.gpu(0)
    else:
        target = tvm.target.Target("llvm", host='llvm')
        device = tvm.cpu(0)
    input_shape = (1, 3, 1024, 1024)


    def tvm_export():
        """Export onnx model."""

        print("Building model on {} ...".format(target))

        onnx_model = onnx.load(args.input)
        onnx_json_path = "{}/{}.json".format(args.output, os.path.basename(args.input))
        onnx_so_path = "{}/{}.so".format(args.output, os.path.basename(args.input))
        onnx_params_path = "{}/{}.params".format(args.output, os.path.basename(args.input))

        # Parsing onnx model
        sym, params = relay.frontend.from_onnx(onnx_model, {'input': input_shape})

        # Create TVM model
        with relay.build_config(opt_level=2):
            graph, lib, params = relay.build_module.build(sym, target, params=params)

        # Output TVM model
        with open(onnx_json_path, 'w') as fo:
            fo.write(graph)
        lib.export_library(onnx_so_path)
        with open(onnx_params_path, 'wb') as fo:
            fo.write(relay.save_param_dict(params))


    def tvm_verify():
        """Verify onnx model."""

        print("Running model on {} ...".format(device))

        onnx_json_path = "{}/{}.json".format(args.output, os.path.basename(args.input))
        onnx_so_path = "{}/{}.so".format(args.output, os.path.basename(args.input))
        onnx_params_path = "{}/{}.params".format(args.output, os.path.basename(args.input))

        # Load module
        loaded_json = open(onnx_json_path).read()
        loaded_solib = tvm.runtime.load_module(onnx_so_path)
        loaded_params = bytearray(open(onnx_params_path, "rb").read())

        module =  tvm.contrib.graph_executor.create(loaded_json, loaded_solib, device)
        module.load_params(loaded_params)

        # Predict
        # /************************************************************************************
        # ***
        # ***    MS: Define Input Data
        # ***
        # ************************************************************************************/        
        input = tvm.nd.array((np.random.uniform(size=input_shape).astype("float32")), device)

        module.set_input("input", input)

        start_time = time.time()
        for i in range(10):
            print("Running {}/10 ... ".format(i + 1, 10))
            module.run()
        end_time = time.time()

        output = module.get_output(0)

        print(output)

        print("Prediction spend {:.3f} seconds/10 times .".format(end_time - start_time))

    if args.export:
        tvm_export()

    if args.verify:
        tvm_verify()
