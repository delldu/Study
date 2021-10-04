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

import argparse
import os
import pdb  # For debug
from timeit import default_timer as timer
import logging
from string import Template

import numpy as np
import onnx
import onnxruntime


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

def function_spend_time(func):
    def wrapper(*args, **kwargs):
        start = timer()
        func_return = func(*args, **kwargs)
        end = timer()
        spend = int((end - start) * 1000)
        logging.info(f"{func.__name__}() spend {spend} ms")

        return func_return

    return wrapper


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
    onnx.checker.check_model(model)
    s = get_onnx_info(model)
    print(s)

def onnx_shape(onnx_filename, shape, output_onnx_filename):
    """
    input.height=224 ==> {"input.height": 244, }
    """
    onnx_model = onnx.load(onnx_filename)
    onnx.checker.check_model(onnx_model)

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
    if len(output_onnx_filename) > 0:
        onnx.save(onnx_model, output_onnx_filename)
    else:
        print(get_onnx_info(onnx_model))

def onnx_run(onnx_filename, input_data_file=None, print_time=True, number=1, repeat=1, output_data_file=None):
    onnx_model = onnx.load(onnx_filename)
    onnx.checker.check_model(onnx_model)

    def is_dynamic():
        for t in onnx_model.graph.input:
            name, etype, dims, dynamic = value_info_parse(t)
            if dynamic:
                return True
        return False

    def format_times(times):
        mean_ts = np.mean(times) * 1000
        std_ts = np.std(times) * 1000
        max_ts = np.max(times) * 1000
        min_ts = np.min(times) * 1000

        header = "Execution time summary:\n{0:^10} {1:^10} {2:^10} {3:^10}".format(
            "mean (ms)", "max (ms)", "min (ms)", "std (ms)"
        )
        stats = "{0:^10.2f} {1:^10.2f} {2:^10.2f} {3:^10.2f}".format(
            mean_ts, max_ts, min_ts, std_ts
        )
        return "%s\n%s\n" % (header, stats)

    def make_inputs_data():
        try:
            user_input_data = np.load(input_data_file) if input_data_file else {}
        except IOError as ex:
            raise Exception("Error loading inputs file: %s" % ex)
        # pdb.set_trace()

        input_data = {}
        shape = get_onnx_shape(onnx_model)
        for k, v in shape.items():
            if k in user_input_data:
                print(f"Loading {k} from user input data")
            else:
                print(f"Create {k} from random data")
                input_data[k] = np.random.random_sample(size=v).astype("float32")

        return input_data

    def save_outputs_data(outputs):
        # pdb.set_trace()
        if output_data_file:
            np.savez(output_data_file, data=outputs)
        # pass
        # np.savez(numpy_file, data=numpy_data)


    session_options = onnxruntime.SessionOptions()
    # session_options.log_severity_level = 0

    # Set graph optimization level
    session_options.graph_optimization_level = (
        onnxruntime.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
    )
    # onnxruntime support dynamic shape, loading onnx_filename is OK ...
    ort_engine = onnxruntime.InferenceSession(onnx_filename, session_options)

    inputs = make_inputs_data()
    outputs = ort_engine.run(None, inputs)

    times = []
    for r in range(repeat):
        start_time = timer()
        for n in range(number):
            ort_engine.run(None, inputs)
        stop_time = timer()
        times.append((stop_time - start_time)/number)
    if (print_time):
        print(format_times(times))

    if output_data_file:
        save_outputs_data(output_data_file)

    return outputs


if __name__ == "__main__":
    """Onnx executor ...
        tvme test.onnx --list
        tvme test.onnx --size <shape> --output new_test.onnx
        tvme test.onnx --run --inputs i.npz --print-time --number n --repeat n -outputs o.npz
    """
    parser = argparse.ArgumentParser(
        description="build onnx model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("FILE", type=str, help="input file")
    parser.add_argument("-l", "--list", help="list onnx", action="store_true")
    parser.add_argument("-s", "--shape", help="shape onnx", action="store_true")
    parser.add_argument("-r", "--run", help="run model with onnxruntime", action="store_true")

    shape_group = parser.add_argument_group("shape options")
    shape_group.add_argument("--size", type=str, default="", 
        help="setup input dynamic shape, e.g. input.height=224,input.width=224")
    shape_group.add_argument("-o", "--output", type=str, default="", help="output model file (.onnx)")

    run_group = parser.add_argument_group("run options")
    run_group.add_argument("--inputs", type=str, help="input data file (.npz)")
    run_group.add_argument("--print-time", action="store_true", help="print the execution time(s)")
    run_group.add_argument("--repeat", metavar="N", type=int, default=1, help="run the model n times.")
    run_group.add_argument("--number", metavar="N", type=int, default=3, help="repeat the run n times.")
    run_group.add_argument("--outputs", type=str, help="output data file (.npz)")
            
    args = parser.parse_args()

    if not os.path.exists(args.FILE):
        print("file {} not exist.".format(args.FILE))
        os._exit(0)

    if args.list:
        onnx_list(args.FILE)

    if len(args.size) > 0:
        onnx_shape(args.FILE, args.size, args.output)

    if args.run:
        onnx_run(args.FILE, args.inputs, args.print_time, args.number, args.repeat, args.outputs)
