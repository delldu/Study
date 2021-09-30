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
import tarfile 
from tvm import relay
from string import Template

def value_info(t):
    ''' parsing tensor value information'''
    # make_tensor_value_info(name,elem_type,shape,doc_string="",shape_denotation=None) --> ValueInfoProto

    dynamic = False
    name = t.name
    etype = t.type.tensor_type.elem_type
    shape = t.type.tensor_type.shape
    dims = []
    for e in shape.dim:
        if e.dim_value > 0:
            dims.append(e.dim_value)
        else:
            dims.append(e.dim_param)
            dynamic = True
    return name, etype, dims, dynamic


def file_name(filename):
    '''return file base and ext '''
    return os.path.splitext(os.path.basename(filename))

def model_tar(onnx_file, output):
    # with open(f"{}/readme.txt", "w") as f:
    #     f.write(f"{onnx_file}")

    file_list = ["readme.txt", "model.so", "model.json", "model.params"]
    for file in file_list:
        fullpath = f"{output}/{file}"
        assert os.path.exists(fullpath), f"file {fullpath} not exist."

    base, _ = file_name(onnx_file)
    tar_filename = f"{output}/{base}.tar" 

    t = tarfile.open(tar_filename, "w:gz")
    for file in file_list:
        fullpath = f"{output}/{file}"
        t.add(fullpath)
    t.close() 


def onnx_list(onnx_file):
    list_template = Template("""
        Model Summary:
            Domain: ${domain}
            Producer: ${producer_name} ${producer_version}
            Model Version: ${model_version}
            IR Version: ${ir_version}
            Model Opset: ${opset}
            Graph name: ${graph_name}
        Inputs:
            ${input_list}
        Outputs:
            ${output_list}
        """)


    model = onnx.load(onnx_file)
    domain = model.domain
    if (len(domain) < 1):
        domain = "ai.onnx"

    opset = [e.version for e in model.opset_import]
    input_list = []
    for t in model.graph.input:
        name, _, dims, _ = value_info(t)
        input_list.append(f"        {name}: {dims}")
    output_list = []
    for t in model.graph.output:
        name, _, dims, _ = value_info(t)
        output_list.append(f"        {name}: {dims}")

    s = list_template.substitute(
        domain=domain,
        producer_name=model.producer_name,
        producer_version = model.producer_version,
        model_version=model.model_version,
        ir_version=model.ir_version,
        opset=opset,
        graph_name=model.graph.name,
        input_list="\n".join(input_list),
        output_list="\n".join(output_list)
    )
    # remove first 8 space
    s = s.replace(" " * 8, "").strip()
    print(s)

def onnx_edit(onnx_file, output, shape):
    base, _ = file_name(onnx_file)
    output_filename = f"{output}/{base}.onnx"
    assert onnx_file != output_filename, "Warning: I/O file name is same"

    # Convert input.height=224, ... to {"input.height": 244, }
    shape_dict = {}
    for e in shape.split(','):
        k, v = e.split('=')
        assert v is not None and v.isdigit(), "Warning: invalid shape."
        shape_dict[k.strip()] = int(v)
    assert shape_dict is not None, "Warning: shape is empty."

    def update_dims(tensor):
        shape = tensor.type.tensor_type.shape
        for e in shape.dim:
            if e.dim_value > 0:
                continue
            key = tensor.name + "." + e.dim_param
            if key in shape_dict.keys():
                e.dim_value = shape_dict[key]
            else:
                print(f"Warning: missing {key} shape")

    model = onnx.load(onnx_file)
    for tensor in model.graph.input:
        update_dims(tensor)
    # for tensor in model.graph.output:
    #     update_dims(tensor)

    onnx.checker.check_model(model)
    onnx.save(model, output_filename)
    print(f"Save new model to {output_filename}.")


def build_onnx(onnx_file, device, output):
    if device.lower() in ["cuda", "gpu"]:
        target = tvm.target.Target("cuda", host='llvm')
    else:
        target = tvm.target.Target("llvm", host='llvm')
    device = tvm.device(str(target), 0)    



if __name__ == '__main__':
    """TVM Onnx tools ..."""

    parser = argparse.ArgumentParser(description="tvm tool for onnx model", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('input', type=str, help="input model file (eg: test.onnx or test.tar)")
    parser.add_argument('-l', '--list', help="list onnx information", action='store_true')

    parser.add_argument('-e', '--edit', help="edit dynamic onnx input shape", action='store_true')
    static_group = parser.add_argument_group('edit options')
    static_group.add_argument('-s', '--shape', type=str, default="input.height=224, input.width=224", help="set I/O shape")

    parser.add_argument('-b', '--build', help="build onnx to tar model", action='store_true')
    build_group = parser.add_argument_group('build options')
    build_group.add_argument('-d', '--device', choices=['cpu', 'gpu'], default="cpu", help="build for device")

    parser.add_argument('-v', '--verify', help="verify model (onnx/tar)", action='store_true')
    parser.add_argument('-o', '--output', type=str, default="output", help="output folder")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print("model file {} not exist.".format(args.input))
        os._exit(0)

    file_base, file_ext = file_name(args.input)
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    if args.list:
        assert file_ext != 'onnx', f"view expect onnx model, but got {file_ext} model."
        onnx_list(args.input)

    if args.edit:
        assert file_ext != 'onnx', f"edit expect onnx model, but got {file_ext} model."
        onnx_edit(args.input, args.output, args.shape)

    if args.build:
        assert file_ext != 'onnx', f"build expect onnx model, but got {file_ext} model."
        build_onnx(args.input, args.device, args.output)

    if args.verify:
        assert file_ext != 'tar', f"verify tvm model, but got {file_ext} model."
        verify_model(agrs.input)





    # # /************************************************************************************
    # # ***
    # # ***    MS: Define Global Names
    # # ***
    # # ************************************************************************************/
    # if args.gpu:
    #     target = tvm.target.Target("cuda", host='llvm')
    # else:
    #     target = tvm.target.Target("llvm", host='llvm')
    # device = tvm.device(str(target), 0)        
    # # input_shape = [1, 3, 512, 512]
    # input_shape = (1, 3, tvm.relay.Any(), tvm.relay.Any())

    # def tvm_export():
    #     """Export onnx model."""

    #     print("Building model on {} ...".format(target))

    #     onnx_model = onnx.load(args.input)
    #     if (args.gpu):
    #         onnx_json_path = "{}/cuda_{}.json".format(args.output, os.path.basename(args.input))
    #         onnx_so_path = "{}/cuda_{}.so".format(args.output, os.path.basename(args.input))
    #         onnx_params_path = "{}/cuda_{}.params".format(args.output, os.path.basename(args.input))
    #     else:
    #         onnx_json_path = "{}/cpu_{}.json".format(args.output, os.path.basename(args.input))
    #         onnx_so_path = "{}/cpu_{}.so".format(args.output, os.path.basename(args.input))
    #         onnx_params_path = "{}/cpu_{}.params".format(args.output, os.path.basename(args.input))

    #     # Parsing onnx model
    #     mod, params = relay.frontend.from_onnx(onnx_model, {'input': input_shape}, freeze_params=False)
    #     # mod, params = relay.frontend.from_onnx(onnx_model, freeze_params=False)
    #     # mod = relay.transform.DynamicToStatic()(mod)
    #     print(mod)

    #     # Create TVM model
    #     # with relay.build_config(opt_level=3):
    #     #     graph, lib, params = relay.build_module.build(mod, target, params=params)

    #     with tvm.transform.PassContext(opt_level=3):
    #         graph, lib, params = relay.build_module.build(mod, target, params=params)


    #     # https://discuss.tvm.apache.org/t/relay-frontend-can-relay-take-none-include-shape/5772/2
    #     # executable = tvm.relay.backend.vm.compile(mod, target, params=params)

    #     # xxxx8888
    #     # opt_level = 3
    #     # with tvm.transform.PassContext(opt_level=opt_level):
    #     # executable = tvm.relay.backend.vm.compile(mod, target, params=params)
    #     # code, lib = executable.save()
    #     # Examples
    #     # --------------------------------------------
    #     #     import numpy as np
    #     #     import tvm
    #     #     from tvm import te
    #     #     from tvm import relay
    #     #     # define a simple network.
    #     #     x = relay.var('x', shape=(10, 10))
    #     #     f = relay.Function([x], x + x)
    #     #     mod = tvm.IRModule({"main": f})
    #     #     # create a Relay VM.
    #     #     dev = tvm.cpu()
    #     #     target = "llvm"
    #     #     executable = relay.vm.compile(mod, target)
    #     #     code, lib = executable.save()

    #     #     # save and load the code and lib file.
    #     #     tmp = tvm.contrib.utils.tempdir()
    #     #     path_lib = tmp.relpath("lib.so")
    #     #     lib.export_library(path_lib)

    #     #     with open(tmp.relpath("code.ro"), "wb") as fo:
    #     #         fo.write(code)

    #     #     loaded_lib = tvm.runtime.load_module(path_lib)
    #     #     loaded_code = bytearray(open(tmp.relpath("code.ro"), "rb").read())

    #     #     # deserialize.
    #     #     des_exec = tvm.runtime.vm.Executable.load_exec(loaded_code, loaded_lib)
    #     #     # execute the deserialized executable.

    #     #     x_data = np.random.rand(10, 10).astype('float32')
    #     #     des_vm = tvm.runtime.vm.VirtualMachine(des_exec, dev)
    #     #     res = des_vm.run(x_data)
    #     #     print(res.numpy())




    #     # Output TVM model
    #     lib.export_library(onnx_so_path)
    #     with open(onnx_json_path, 'w') as fo:
    #         fo.write(graph)
    #     with open(onnx_params_path, 'wb') as fo:
    #         fo.write(relay.save_param_dict(params))


    # def tvm_verify():
    #     """Verify onnx model."""

    #     print("Running model on {} ...".format(device))

    #     if (args.gpu):
    #         onnx_json_path = "{}/cuda_{}.json".format(args.output, os.path.basename(args.input))
    #         onnx_so_path = "{}/cuda_{}.so".format(args.output, os.path.basename(args.input))
    #         onnx_params_path = "{}/cuda_{}.params".format(args.output, os.path.basename(args.input))
    #     else:
    #         onnx_json_path = "{}/cpu_{}.json".format(args.output, os.path.basename(args.input))
    #         onnx_so_path = "{}/cpu_{}.so".format(args.output, os.path.basename(args.input))
    #         onnx_params_path = "{}/cpu_{}.params".format(args.output, os.path.basename(args.input))

    #     # Load module
    #     loaded_json = open(onnx_json_path).read()
    #     loaded_solib = tvm.runtime.load_module(onnx_so_path)
    #     loaded_params = bytearray(open(onnx_params_path, "rb").read())

    #     module =  tvm.contrib.graph_executor.create(loaded_json, loaded_solib, device)
    #     module.load_params(loaded_params)

    #     # Predict
    #     # /************************************************************************************
    #     # ***
    #     # ***    MS: Define Input Data
    #     # ***
    #     # ************************************************************************************/

    #     # input_shape = [1, 3, 256, 256]
    #     input = tvm.nd.array((np.random.uniform(size=input_shape).astype("float32")), device)

    #     module.set_input("input", input)
    #     module.run()
    #     output = module.get_output(0)
    #     print(output)


    #     print("Evaluating ...")
    #     ftimer = module.module.time_evaluator("run", device, number=1, repeat=5)
    #     prof_res = np.array(ftimer().results) * 1000  # multiply 1000 for converting to millisecond
    #     print(
    #         "%-20s %-19s (%s)" % (onnx_so_path, "%.2f ms" % np.mean(prof_res), "%.2f ms" % np.std(prof_res))
    #     )



    # if args.export:
    #     tvm_export()

    # if args.verify:
    #     tvm_verify()
