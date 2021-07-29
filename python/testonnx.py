"""Test onnx export."""  # coding=utf-8
#
# /************************************************************************************
# ***
# ***    Copyright Dell 2021, All Rights Reserved.
# ***
# ***    File Author: Dell, 2021年 07月 17日
# ***
# ************************************************************************************/
#
import torch
import ons
import argparse
import os
import pdb  # For debug
import time

import numpy as np
import onnx
import onnxruntime
import torch
from torch import nn
import torch.nn.functional as F
import torchvision.transforms as transforms
from torch.autograd import Function
from PIL import Image

import math
import torch


def to_numpy(tensor):
    return (
        tensor.detach().cpu().numpy()
        if tensor.requires_grad
        else tensor.cpu().numpy()
    )

def onnx_load(onnx_file):
    session_options = onnxruntime.SessionOptions()
    # session_options.log_severity_level = 0

    # Set graph optimization level
    session_options.graph_optimization_level = (
        onnxruntime.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
    )

    onnx_model = onnxruntime.InferenceSession(onnx_file, session_options)
    # onnx_model.set_providers(['CUDAExecutionProvider'])
    print(
        "Onnx Model Engine: ",
        onnx_model.get_providers(),
        "Device: ",
        onnxruntime.get_device(),
    )

    return onnx_model


def onnx_forward(onnx_model, input):
    def to_numpy(tensor):
        return (
            tensor.detach().cpu().numpy()
            if tensor.requires_grad
            else tensor.cpu().numpy()
        )

    onnxruntime_inputs = {onnx_model.get_inputs()[0].name: to_numpy(input)}
    onnxruntime_outputs = onnx_model.run(None, onnxruntime_inputs)
    return torch.from_numpy(onnxruntime_outputs[0])


class TestModel(nn.Module):
    # def __init__(self):
    #     super(TestModel, self).__init__()

    def forward(self, input):
        B, C, H, W = input.shape
        return input.view(B*C, H, W)


if __name__ == "__main__":
    """Onnx tools ..."""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-o", "--output", type=str, default="output", help="output folder"
    )

    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    model = TestModel()
    model.eval()

    onnx_file_name = "/tmp/test.onnx"

    dummy_input = torch.randn(1, 3, 256, 256)

    #
    # /************************************************************************************
    # ***
    # ***    MS: Define Global Names
    # ***
    # ************************************************************************************/
    #
    def export_onnx():
        """Export onnx model."""

        # 1. Create and load model.

        # 2. Model export
        print("Exporting onnx model to {}...".format(onnx_file_name))

        input_names = ["input"]
        output_names = ["output"]
        dynamic_axes = {
            "input": {0: "batch", 1:"channel", 2: "height", 3: "width"},
        }

        torch.onnx.export(
            model,
            dummy_input,
            onnx_file_name,
            input_names=input_names,
            output_names=output_names,
            verbose=True,
            opset_version=11,
            keep_initializers_as_inputs=False,
            export_params=True,
            dynamic_axes=dynamic_axes
        )

        # 3. Optimize model
        print("Checking model ...")
        onnx_model = onnx.load(onnx_file_name)
        onnx.checker.check_model(onnx_model)
        # https://github.com/onnx/optimizer

        # 4. Visual model
        # python -c "import netron; netron.start('/tmp/test.onnx')"


    def verify_onnx():
        """Verify onnx model."""

        # dummy_input = torch.randn(10, 3, 512, 256)
        dummy_input = torch.randn(5, 2, 512, 256)

        onnxruntime_engine = onnx_load(onnx_file_name)

        with torch.no_grad():
            torch_output = model(dummy_input)

        onnxruntime_inputs = {
            onnxruntime_engine.get_inputs()[0].name: to_numpy(dummy_input),
        }
        onnxruntime_outputs = onnxruntime_engine.run(None, onnxruntime_inputs)

        np.testing.assert_allclose(
            to_numpy(torch_output), onnxruntime_outputs[0], rtol=1e-03, atol=1e-03
        )
        print(torch_output.shape)
        print(onnxruntime_outputs[0].shape)

        print(
            "Onnx model {} has been tested with ONNXRuntime, result sounds good !".format(
                onnx_file_name
            )
        )

    export_onnx()
    verify_onnx()
