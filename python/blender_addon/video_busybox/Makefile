#/************************************************************************************
#***
#***	File Author: Dell, 2021年 11月 22日 星期一 14:33:18 CST
#***
#************************************************************************************/

# Configurations
APPLETS := $(shell ./makebox --source)

TARGET := video_busybox

SOURCE := main.c
SOURCE += $(APPLETS)

INCS	:=  

LIBS	:=  

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
${TARGET}: applets.h ${OBJECT}
	${CC} -o ${TARGET} ${LDFLAGS} ${OBJECT} ${LIBS}

applets.h: busybox.config
	./makebox --table > applets.h

install:
	#${STRIP} ${TARGET}
	install -m 755 ${TARGET} ${INSTALL_DIR}/bin
	./makebox --links ${INSTALL_DIR}/bin

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
	rm -f core ${OBJECT}
	rm -f core ${TARGET}
	rm -f applets.h

