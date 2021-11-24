#/************************************************************************************
#***
#***	Copyright 2021 Dell(18588220928g@163.com), All Rights Reserved.
#***
#***	File Author: Dell, 2021-11-22 17:57:41
#***
#************************************************************************************/
#

XSUBDIRS :=  \
	hiredis \
	libtasks


BSUBDIRS :=

all: premake
	@for d in $(XSUBDIRS)  ; do \
		if [ -d $$d ] ; then \
			$(MAKE) -C $$d || exit 1; \
		fi \
	done	

install:
	@for d in $(XSUBDIRS)  ; do \
		if [ -d $$d ] ; then \
			$(MAKE) -C $$d install || exit 1; \
		fi \
	done	

clean:
	@for d in $(XSUBDIRS) ; do \
		if [ -d $$d ] ; then \
			$(MAKE) -C $$d clean || exit 1; \
		fi \
	done	

premake:
	@for d in $(BSUBDIRS)  ; do \
		if [ -d $$d ] ; then \
			echo "Pre-make $$d .................................................."; \
			cd $$d && ./build_makefile && cd ..  ; \
		fi \
	done	
