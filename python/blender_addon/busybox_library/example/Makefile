#
#/************************************************************************************
#***
#***	Copyright 2012 Dell Du(dellrunning@gmail.com), All Rights Reserved.
#***
#***	File Author: Dell, Tue Nov  6 10:42:09 CST 2012
#***
#************************************************************************************/
#

TARGET := test_tasks

SOURCE := main.c

INCS	:= -I../libtasks/include

	#  -I$(BUILD_DIR)/include
LIBS	:= -static -L../libtasks -ltasks -L../hiredis -lhiredis -lanl -L../cJSON -lcjson -lcrypto
	#-L$(BUILD_DIR)/lib -lstd...

CFLAGS := -O2 -fPIC
LDFLAGS := -fPIC

#****************************************************************************
# Makefile code common to all platforms
#****************************************************************************
CFLAGS   := ${CFLAGS} ${DEFINES}
CXXFLAGS := ${CXXFLAGS} ${DEFINES}

OBJECT := $(addsuffix .o,$(basename ${SOURCE}))

all: ${TARGET}
# install

#****************************************************************************
# Compile block
#****************************************************************************
${TARGET}: ${OBJECT}
	${CC} ${LDFLAGS} -o ${TARGET} ${OBJECT} ${LIBS}

install:
	${STRIP} ${TARGET}
	install -m 755 ${TARGET} ${INSTALL_DIR}/bin

#****************************************************************************
# common rules
#****************************************************************************
%.o : %.cpp
	${CXX} ${CXXFLAGS} ${INCS} -c $< -o $@

%.o : %.c
	${CC} ${CFLAGS} ${INCS} -c $< -o $@

#****************************************************************************
# Depend block
#****************************************************************************
depend:

clean:
	rm -f core ${OBJECT} ${TARGET}
