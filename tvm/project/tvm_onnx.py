"""Onnx Model Tools."""  # coding=utf-8
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
import onnxruntime


def value_info_parse(t):
    """parsing tensor value information"""
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


def file_name_parse(filename):
    """return file base and ext"""
    return os.path.splitext(os.path.basename(filename))


def get_onnx_info(model):
    template = Template(
        """
        Model Information:
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
        """
    )

    domain = model.domain
    if len(domain) < 1:
        domain = "ai.onnx"

    opset = [e.version for e in model.opset_import]
    input_list = []
    for t in model.graph.input:
        name, _, dims, _ = value_info_parse(t)
        input_list.append(f"        {name}: {dims}")
    output_list = []
    for t in model.graph.output:
        name, _, dims, _ = value_info_parse(t)
        output_list.append(f"        {name}: {dims}")

    s = template.substitute(
        domain=domain,
        producer_name=model.producer_name,
        producer_version=model.producer_version,
        model_version=model.model_version,
        ir_version=model.ir_version,
        opset=opset,
        graph_name=model.graph.name,
        input_list="\n".join(input_list),
        output_list="\n".join(output_list),
    )
    # remove first 8 space from template
    s = s.replace(" " * 8, "").strip()
    return s


def get_onnx_shape(model):
    """Just input shape"""
    shape = {}
    for t in model.graph.input:
        name, etype, dims, dynamic = value_info_parse(t)
        shape[name] = dims
    return shape


def onnx_list(onnx_filename):
    model = onnx.load(onnx_filename)
    onnx.checker.check_model(onnx_model)
    s = get_onnx_info(model)
    print(s)


def build_onnx(onnx_filename, device, shape, output):
    onnx_model = onnx.load(onnx_filename)
    onnx.checker.check_model(onnx_model)
    device = device.lower()
    shape = shape.replace(" ", "").strip()  # remove blanks
    base, _ = file_name_parse(onnx_filename)
    tar_filename = f"{output}/{base}.tar"

    def set_shape():
        # Convert input.height=224, ... to {"input.height": 244, }
        shape_dict = {}
        for e in shape.split(","):
            k, v = e.split("=")
            assert (
                v is not None and v.isdigit()
            ), f"shape dim ${v} is not valid from ${k} = ${v}."
            shape_dict[k.strip()] = int(v)

        def update_dim(tensor):
            shape = tensor.type.tensor_type.shape
            for e in shape.dim:
                if e.dim_value > 0:
                    continue
                key = tensor.name + "." + e.dim_param
                if key in shape_dict.keys():
                    e.dim_value = shape_dict[key]
                else:
                    print(f"missing {key} shape")

        for tensor in onnx_model.graph.input:
            update_dim(tensor)

        onnx.checker.check_model(onnx_model)

    def is_dynamic():
        for t in onnx_model.graph.input:
            name, etype, dims, dynamic = value_info_parse(t)
            if dynamic:
                return True
        return False

    def model_build():
        """
        Create model.txt, model.so, model.json, model.params ...
        """
        print(f"Building {onnx_filename} on {device}...")
        target = (
            tvm.target.Target("cuda", host="llvm")
            if device in ["cuda", "gpu"]
            else tvm.target.Target("llvm", host="llvm")
        )
        mod, params = relay.frontend.from_onnx(onnx_model)
        # mod = relay.transform.DynamicToStatic()(mod)
        with tvm.transform.PassContext(opt_level=3):
            graph, lib, params = relay.build_module.build(mod, target, params=params)

        # Output model
        with open(f"{output}/model.txt", "w") as fo:
            fo.write(f"device: {device}\nmodel: {onnx_filename}\nshape: {shape}")
        lib.export_library(f"{output}/model.so")
        with open(f"{output}/model.json", "w") as fo:
            fo.write(graph)
        with open(f"{output}/model.params", "wb") as fo:
            fo.write(relay.save_param_dict(params))

    def model_package():
        file_list = ["model.txt", "model.so", "model.json", "model.params"]
        t = tarfile.open(tar_filename, "w:gz")
        for file in file_list:
            fullpath = f"{output}/{file}"
            t.add(fullpath)
        t.close()
        print(f"{tar_filename} created.")

    def check_modtxt():
        s_device = ""
        s_onnx_filename = ""
        with open(f"{output}/model.txt", "r") as fo:
            lines = fo.readlines()
        for line in lines:
            if line.startswith("device:"):
                s_device = line.replace("device:", "", 1).strip()
            if line.startswith("model:"):
                s_onnx_filename = line.replace("model:", "", 1).strip()
            if line.startswith("shape:"):
                s_shape = line.replace("shape:", "", 1).strip()
        assert s_device == device, "got error device."
        assert s_shape == shape, "got error shape."
        assert s_onnx_filename == onnx_filename, "got error file name."

    def model_load():
        check_modtxt()
        target = tvm.cuda() if device in ["cuda", "gpu"] else tvm.cpu()
        # Load module
        loaded_so = tvm.runtime.load_module(f"{output}/model.so")
        loaded_json = open(f"{output}/model.json").read()
        loaded_params = bytearray(open(f"{output}/model.params", "rb").read())
        gmod = tvm.contrib.graph_executor.create(loaded_json, loaded_so, target)
        gmod.load_params(loaded_params)
        return gmod

    def expect_output(input_data):
        session_options = onnxruntime.SessionOptions()
        # session_options.log_severity_level = 0

        # Set graph optimization level
        session_options.graph_optimization_level = (
            onnxruntime.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
        )
        # onnxruntime support dynamic shape, loading onnx_filename is OK ...
        ort_engine = onnxruntime.InferenceSession(onnx_filename, session_options)
        outputs = ort_engine.run(None, input_data)
        return outputs[0]

    def model_output(gmod, input_data):
        s_device = tvm.cuda() if device in ["cuda", "gpu"] else tvm.cpu()
        for k, v in input_data.items():
            s_data = tvm.nd.array(v, s_device)
            gmod.set_input(k, s_data)
        gmod.run()
        return gmod.get_output(0).numpy()

    def model_verify(gmod):
        # gmod input shape is same as onnx's ?
        # gmod.get_num_inputs() -- 147
        # gmod.get_input(0) -- <tvm.nd.NDArray shape=(1, 3, 244, 244), cpu(0)>

        # gmod output result is same as onnx's ?
        input_data = {}
        shape = get_onnx_shape(onnx_model)
        for k, v in shape.items():
            input_data[k] = np.random.random_sample(size=v).astype("float32")
        expect_value = expect_output(input_data)
        model_value = model_output(gmod, input_data)
        np.testing.assert_allclose(model_value, expect_value, rtol=1e-03, atol=1e-03)
        print("Test model OK !")

    def model_perf(gmod):
        target = tvm.cuda() if device in ["cuda", "gpu"] else tvm.cpu()
        print(f"Test {tar_filename} on {device} ...")
        ftimer = gmod.module.time_evaluator("run", target, number=1, repeat=5)
        tvm_perf = np.array(ftimer().results) * 1000  # multiply 1000 for millisecond
        print(
            "    mean time %.2f ms, std %.2f ms" % (np.mean(tvm_perf), np.std(tvm_perf))
        )

    if len(shape) > 0:
        set_shape()

    if is_dynamic():
        print("model is dynamic, could not be built. please reference:")
        print(get_onnx_info(onnx_model))
        return

    model_build()
    model_package()
    gmod = model_load()
    model_perf(gmod)

    model_verify(gmod)


if __name__ == "__main__":
    """TVM Onnx tools ..."""

    parser = argparse.ArgumentParser(
        description="build onnx model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", type=str, help="input file")
    parser.add_argument("-l", "--list", help="list onnx", action="store_true")
    parser.add_argument("-b", "--build", help="build model", action="store_true")
    build_group = parser.add_argument_group("build options")
    build_group.add_argument(
        "-d", "--device", choices=["cpu", "gpu"], default="cpu", help="target device"
    )
    build_group.add_argument(
        "-s",
        "--shape",
        type=str,
        default="",
        help="set dynamic shape such as input.height=224,input.width=224",
    )
    build_group.add_argument(
        "-o", "--output", type=str, default="output", help="output folder"
    )

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print("model file {} not exist.".format(args.input))
        os._exit(0)

    file_base, file_ext = file_name_parse(args.input)
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    if args.list:
        assert file_ext != "onnx", f"List onnx model, got {file_ext} model."
        onnx_list(args.input)

    if args.build:
        assert file_ext != "onnx", f"Build onnx model, got {file_ext} model."
        build_onnx(args.input, args.device, args.shape, args.output)
