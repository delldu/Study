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
import logging

logger = logging.getLogger("compile_engine")
autotvm_logger = logging.getLogger("autotvm")
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)


if __name__ == '__main__':
    """TVM Onnx tools ..."""

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('input', type=str, help="input onnx file (eg: test.onnx)")
    parser.add_argument('-e', '--export', help="export tvm model", action='store_true')
    parser.add_argument('-v', '--verify', help="verify tvm model", action='store_true')
    parser.add_argument('-g', '--gpu', help="use gpu", action='store_true')
    parser.add_argument('-o', '--output', type=str, default="models", help="output folder")

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
    else:
        target = tvm.target.Target("llvm", host='llvm')
    device = tvm.device(str(target), 0)        
    input_shape = [1, 3, 512, 512]
    # input_shape = (1, 3, tvm.relay.Any(), tvm.relay.Any())

    def tvm_export():
        """Export onnx model."""

        print("Building model on {} ...".format(target))

        onnx_model = onnx.load(args.input)
        if (args.gpu):
            onnx_json_path = "{}/cuda_{}.json".format(args.output, os.path.basename(args.input))
            onnx_so_path = "{}/cuda_{}.so".format(args.output, os.path.basename(args.input))
            onnx_params_path = "{}/cuda_{}.params".format(args.output, os.path.basename(args.input))
        else:
            onnx_json_path = "{}/cpu_{}.json".format(args.output, os.path.basename(args.input))
            onnx_so_path = "{}/cpu_{}.so".format(args.output, os.path.basename(args.input))
            onnx_params_path = "{}/cpu_{}.params".format(args.output, os.path.basename(args.input))

        # Parsing onnx model
        # sym, params = relay.frontend.from_onnx(onnx_model, {'input': input_shape}, freeze_params=False)
        sym, params = relay.frontend.from_onnx(onnx_model, freeze_params=False)
        sym = relay.transform.DynamicToStatic()(sym)
        print(sym)

        # Create TVM model
        with relay.build_config(opt_level=3):
            graph, lib, params = relay.build_module.build(sym, target, params=params)

        # https://discuss.tvm.apache.org/t/relay-frontend-can-relay-take-none-include-shape/5772/2
        # executable = tvm.relay.backend.vm.compile(mod, target, params=params)

        # xxxx8888
        # opt_level = 3
        # with tvm.transform.PassContext(opt_level=opt_level):
        # executable = tvm.relay.backend.vm.compile(mod, target, params=params)
        # code, lib = executable.save()
        # Examples
        # --------------------------------------------
        #     import numpy as np
        #     import tvm
        #     from tvm import te
        #     from tvm import relay
        #     # define a simple network.
        #     x = relay.var('x', shape=(10, 10))
        #     f = relay.Function([x], x + x)
        #     mod = tvm.IRModule({"main": f})
        #     # create a Relay VM.
        #     dev = tvm.cpu()
        #     target = "llvm"
        #     executable = relay.vm.compile(mod, target)
        #     code, lib = executable.save()

        #     # save and load the code and lib file.
        #     tmp = tvm.contrib.utils.tempdir()
        #     path_lib = tmp.relpath("lib.so")
        #     lib.export_library(path_lib)

        #     with open(tmp.relpath("code.ro"), "wb") as fo:
        #         fo.write(code)

        #     loaded_lib = tvm.runtime.load_module(path_lib)
        #     loaded_code = bytearray(open(tmp.relpath("code.ro"), "rb").read())

        #     # deserialize.
        #     des_exec = tvm.runtime.vm.Executable.load_exec(loaded_code, loaded_lib)
        #     # execute the deserialized executable.

        #     x_data = np.random.rand(10, 10).astype('float32')
        #     des_vm = tvm.runtime.vm.VirtualMachine(des_exec, dev)
        #     res = des_vm.run(x_data)
        #     print(res.numpy())




        # Output TVM model
        with open(onnx_json_path, 'w') as fo:
            fo.write(graph)
        lib.export_library(onnx_so_path)
        with open(onnx_params_path, 'wb') as fo:
            fo.write(relay.save_param_dict(params))


    def tvm_verify():
        """Verify onnx model."""

        print("Running model on {} ...".format(device))

        if (args.gpu):
            onnx_json_path = "{}/cuda_{}.json".format(args.output, os.path.basename(args.input))
            onnx_so_path = "{}/cuda_{}.so".format(args.output, os.path.basename(args.input))
            onnx_params_path = "{}/cuda_{}.params".format(args.output, os.path.basename(args.input))
        else:
            onnx_json_path = "{}/cpu_{}.json".format(args.output, os.path.basename(args.input))
            onnx_so_path = "{}/cpu_{}.so".format(args.output, os.path.basename(args.input))
            onnx_params_path = "{}/cpu_{}.params".format(args.output, os.path.basename(args.input))

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
        module.run()
        output = module.get_output(0)
        print(output)


        print("Evaluating ...")
        ftimer = module.module.time_evaluator("run", device, number=1, repeat=5)
        prof_res = np.array(ftimer().results) * 1000  # multiply 1000 for converting to millisecond
        print(
            "%-20s %-19s (%s)" % (onnx_so_path, "%.2f ms" % np.mean(prof_res), "%.2f ms" % np.std(prof_res))
        )



    if args.export:
        tvm_export()

    if args.verify:
        tvm_verify()
