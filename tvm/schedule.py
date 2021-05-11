'''
TVM Schedule Primitives
'''
# from __future__ import absolute_import, print_function

import fire
import tvm
import tvm.te as te

import pdb

m = te.var('m')
n = te.var('n')

A = te.placeholder((m, n), name='A')
B = te.placeholder((m, n), name='B')
C = te.compute((m, n), lambda i, j: A[i, j] + B[i, j], name='C')
D = te.compute((m, n), lambda i, j: A[i, j] * B[i, j], name='D')


def schedule_split():
    sche = te.create_schedule([C.op, D.op])

    print("Calculate C:")
    co, ci = sche[C].split(C.op.axis[0], factor=32)
    print(tvm.lower(sche, [A, B, C], simple_mode=True))
    fadd = tvm.build(sche, [A, B, C], 'c', target_host='c', name="cpu_fadd")

    print("Calculate D:")
    do, di = sche[D].split(D.op.axis[1], nparts=32)
    print(tvm.lower(sche, [A, B, D], simple_mode=True))


def schedule_tile():
    sche = te.create_schedule([C.op, D.op])

    mo, no, mi, ni = sche[C].tile(C.op.axis[0], C.op.axis[1], x_factor=10, y_factor=5)
    # fused = sche[C].fuse(mi, ni)
    sche[C].reorder(mi, no, mo, ni)
    print(tvm.lower(sche, [A, B, C], simple_mode=True))


def schedule_bind():
    sche = te.create_schedule([C.op, D.op])

    print("Calculate C:")
    mo, mi = sche[C].split(C.op.axis[0], factor=64)
    sche[C].bind(mo, te.thread_axis("blockIdx.x"))
    sche[C].bind(mi, te.thread_axis("threadIdx.x"))
    print(tvm.lower(sche, [A, B, C], simple_mode=True))
    fadd = tvm.build(sche, [A, B, C], target_host='c', target='cuda', name='cuda_fadd')

    # print("Calculate D:")
    # print(tvm.lower(sche, [A, B, D], simple_mode=True))


def schedule_compute():
    sche = te.create_schedule([C.op, D.op])

    print("Calculate C:")
    # sche[C].compute_at(sche[C], C.op.axis[0])
    # sche[C].compute_inline()
    # sche[C].compute_root()
    print(tvm.lower(sche, [A, B, C, D], simple_mode=True))



def build():
    tgt_host = "llvm"
    tgt = "llvm"

    sche = te.create_schedule([C.op])
    print(tvm.lower(sche, [A, B, C], simple_mode=True))

    fadd = tvm.build(sche, [A, B, C], tgt, target_host=tgt_host, name="add")

    pdb.set_trace()

    ######################################################################
    # Save Compiled Module
    # --------------------
    from tvm.contrib import cc
    from tvm.contrib import utils

    fadd.save("deploy.o")
    cc.create_shared("deploy.so", ["deploy.o"])

if __name__ == '__main__':
    fire.Fire()
