#/************************************************************************************
#***
#***	Copyright 2021 Dell(18588220928@163.com), All Rights Reserved.
#***
#***	File Author: Dell, 2021-11-22 18:25:28
#***
#************************************************************************************/
#

LIB_NAME := libtasks

INCS	:= -Iinclude -I../hiredis
	# -I$(BUILD_DIR)/include
SOURCE :=  \
	source/tasks.c \
	source/cJSON.c \
	source/image.c \
	source/video.c

DEFINES := -DDEBUG
CFLAGS := -O2 -fPIC -Wall -Wextra
LDFLAGS := -fPIC

#****************************************************************************
# Makefile code common to all platforms
#****************************************************************************
CFLAGS   := ${CFLAGS} ${DEFINES}
CXXFLAGS := ${CXXFLAGS} ${DEFINES}
OBJECTS := $(addsuffix .o,$(basename ${SOURCE}))

#****************************************************************************
# Compile block
#****************************************************************************
all: staticlib
# sharelib
# staticlib

sharelib: $(OBJECTS)
	$(LD) $(LDFLAGS) -shared -soname $(LIB_NAME).so -o $(LIB_NAME).so $(OBJECTS)
	# cp $(LIB_NAME).so ${INSTALL_DIR}/lib
	# mv $(LIB_NAME).so ../lib


staticlib:$(OBJECTS)
	$(AR) $(ARFLAGS) $(LIB_NAME).a $(OBJECTS)
	# cp $(LIB_NAME).a ${INSTALL_DIR}/lib
	# mv $(LIB_NAME).a ../lib


#****************************************************************************
# Depend block
#****************************************************************************
depend:

#****************************************************************************
# common rules
#****************************************************************************
%.o : %.cpp
	${CXX} ${CXXFLAGS} ${INCS} -c $< -o $@

%.o : %.c
	${CC} ${CFLAGS} ${INCS} -c $< -o $@


clean:
	rm -rf *.a *.so *.o $(OBJECTS)

