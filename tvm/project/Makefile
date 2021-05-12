#/************************************************************************************
#***
#***	Copyright 2020 Dell(18588220928g@163.com), All Rights Reserved.
#***
#***	File Author: Dell, 2020-11-22 02:26:07
#***
#************************************************************************************/
#
INSTALL_DIR := /usr/local/
TVM_ROOT := $(shell cd ../..; pwd)
DMLC_CORE := ${TVM_ROOT}/3rdparty/dmlc-core

TARGET := tvm_onnx

SOURCE :=  \
	tvm_onnx.cc tvm_runtime.cc

INCS	:= $(shell ./tvmtool --cflags)

LIBS	:= \
		$(shell ./tvmtool --libs) \

DEFINES := -std=c++14 -O2 -fPIC -DDMLC_USE_LOGGING_LIBRARY=\<tvm/runtime/logging.h\>


CXXFLAGS := -O2 -fPIC -Wall -Wextra

LDFLAGS := -fPIC

#****************************************************************************
# Makefile code common to all platforms
#****************************************************************************
CXXFLAGS := ${CXXFLAGS} ${DEFINES}

OBJECT := $(addsuffix .o,$(basename ${SOURCE}))

#****************************************************************************
# Compile block
#****************************************************************************
all: ${TARGET}

${TARGET}: ${OBJECT}
	${CXX} ${LDFLAGS} -o ${TARGET} ${OBJECT} ${LIBS}

install:
	install -m 755 ${TARGET} ${INSTALL_DIR}/bin

#****************************************************************************
# common rules
#****************************************************************************
%.o : %.cc
	${CXX} ${CXXFLAGS} ${INCS} -c $< -o $@

#****************************************************************************
# Depend block
#****************************************************************************
depend:

clean:
	rm -f core ${OBJECT} ${TARGET}
