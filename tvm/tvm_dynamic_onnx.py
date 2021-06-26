
import numpy as np
import tvm
import tvm.testing
import tvm.topi.testing
from tvm import relay
from tvm.contrib import graph_executor

import onnx
from onnx import TensorProto, helper, mapping, numpy_helper
import pdb

def get_input_data_shape_dict(graph_def, input_data):
    if isinstance(input_data, list):
        input_names = {}
        shape_dict = {}
        for i, _ in enumerate(input_data):
            input_names[i] = graph_def.graph.input[i].name
            shape_dict[input_names[i]] = input_data[i].shape
    else:
        input_names = graph_def.graph.input[0].name
        shape_dict = {input_names: input_data.shape}

    return input_names, shape_dict


def get_tvm_output_with_vm(
    graph_def, input_data, target, device, opset=None, freeze_params=False, convert_to_static=False
):
    """Generic function to execute and get tvm output with vm executor"""
    if not isinstance(input_data, list):
        input_data = [input_data]
    _, shape_dict = get_input_data_shape_dict(graph_def, input_data)

    mod, params = relay.frontend.from_onnx(
        graph_def, shape_dict, opset=opset, freeze_params=freeze_params
    )

    if convert_to_static:
        mod = relay.transform.DynamicToStatic()(mod)

    ex = relay.create_executor("vm", mod=mod, device=device, target=target)
    result = ex.evaluate()(*input_data, **params)
    if isinstance(result, tvm.runtime.NDArray):
        return result.numpy()
    return [r.numpy() for r in result]



def verify_simple_dynamic_model(a_shape, b_shape, target, dev):
    def verify_model(ex, a_shape, b_shape):
        a_array = np.random.uniform(size=a_shape).astype("float32")
        b_array = np.random.uniform(size=b_shape).astype("float32")
        # matmul
        out_np = np.matmul(a_array, b_array)
        # relu
        out_np[out_np < 0] = 0

        tvm_out = ex.evaluate()(a_array, b_array).numpy()
        tvm.testing.assert_allclose(out_np, tvm_out, rtol=1e-5, atol=1e-5)

    mul_node = helper.make_node("MatMul", ["a", "b"], ["out"])
    relu_node = helper.make_node("Relu", ["out"], ["relu"])

    a_array = np.random.uniform(size=a_shape).astype("float32")
    b_array = np.random.uniform(size=b_shape).astype("float32")
    # matmul
    out_np = np.matmul(a_array, b_array)

    graph = helper.make_graph(
        [mul_node, relu_node],
        "matmul_test",
        inputs=[
            helper.make_tensor_value_info("a", TensorProto.FLOAT, list(a_shape)),
            helper.make_tensor_value_info("b", TensorProto.FLOAT, list(b_shape)),
        ],
        outputs=[helper.make_tensor_value_info("relu", TensorProto.FLOAT, list(out_np.shape))],
    )

    model = helper.make_model(graph, producer_name="matmul_test")

    a_anys = [relay.Any()] * len(a_shape)
    b_anys = [relay.Any()] * len(b_shape)

    mod, params = relay.frontend.from_onnx(model, {"a": a_anys, "b": b_anys})
    # https://discuss.tvm.apache.org/t/relay-frontend-can-relay-take-none-include-shape/5772/2


    # # xxxx8888
    # # opt_level = 3
    # # with tvm.transform.PassContext(opt_level=opt_level):
    # executable = tvm.relay.backend.vm.compile(mod, target, params=params)
    # # code, lib = executable.save()
    # # Examples
    # # --------------------------------------------
    # #     import numpy as np
    # #     import tvm
    # #     from tvm import te
    # #     from tvm import relay
    # #     # define a simple network.
    # #     x = relay.var('x', shape=(10, 10))
    # #     f = relay.Function([x], x + x)
    # #     mod = tvm.IRModule({"main": f})
    # #     # create a Relay VM.
    # #     dev = tvm.cpu()
    # #     target = "llvm"
    # #     executable = relay.vm.compile(mod, target)
    # #     code, lib = executable.save()

    # #     # save and load the code and lib file.
    # #     tmp = tvm.contrib.utils.tempdir()
    # #     path_lib = tmp.relpath("lib.so")
    # #     lib.export_library(path_lib)

    # #     with open(tmp.relpath("code.ro"), "wb") as fo:
    # #         fo.write(code)

    # #     loaded_lib = tvm.runtime.load_module(path_lib)
    # #     loaded_code = bytearray(open(tmp.relpath("code.ro"), "rb").read())

    # #     # deserialize.
    # #     des_exec = tvm.runtime.vm.Executable.load_exec(loaded_code, loaded_lib)
    # #     # execute the deserialized executable.

    # #     x_data = np.random.rand(10, 10).astype('float32')
    # #     des_vm = tvm.runtime.vm.VirtualMachine(des_exec, dev)
    # #     res = des_vm.run(x_data)
    # #     print(res.numpy())
    # # pdb.set_trace()


    # ex = relay.create_executor("vm", mod=mod, device=dev, target=target)
    verify_model(ex, a_shape, b_shape)
    verify_model(ex, [a * 2 for a in a_shape], [b * 2 for b in b_shape])
    verify_model(ex, [a * 3 for a in a_shape], [b * 3 for b in b_shape])

    pdb.set_trace()

# TODO(mbrookhart, electriclilies): Add CUDA as a target once batch matmul is fixed
@tvm.testing.parametrize_targets("llvm")
def test_batch_matmul_dynamic_model(target, dev):
    verify_simple_dynamic_model((2, 3, 4, 3), (2, 3, 3, 4), target, dev)
    verify_simple_dynamic_model((2, 4, 3), (3, 4), target, dev)
    verify_simple_dynamic_model((2, 3, 4, 3), (3, 4), target, dev)


if __name__ == "__main__":
    target = "llvm"
    device = tvm.cpu(0)
    test_batch_matmul_dynamic_model(target, device)

