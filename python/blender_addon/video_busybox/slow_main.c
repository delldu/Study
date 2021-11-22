
/************************************************************************************
***
***	Copyright 2021-2022 Dell Du(dellrunning@gmail.com), All Rights Reserved.
***
***	File Author: Dell, 2021年 11月 22日 星期一 14:33:18 CST
***
************************************************************************************/



#include <stdio.h>
#include <unistd.h>
#include <getopt.h>
#include <stdlib.h>

void slow_help(char *cmd)
{
	printf("Usage: %s [option]\n", cmd);
	printf("    -h, --help                   Display this help.\n");

	exit(1);
}

int slow_main(int argc, char **argv)
{
	int optc;
	int option_index = 0;

	struct option long_opts[] = {
		{ "help", 0, 0, 'h'},
		{ 0, 0, 0, 0}

	};

	if (argc <= 1)
		slow_help(argv[0]);
	
	while ((optc = getopt_long(argc, argv, "h", long_opts, &option_index)) != EOF) {
		switch (optc) {
		case 'h':	// help
		default:
			slow_help(argv[0]);
			break;
	    	}
	}

	// MS -- Modify Section ?

	return 0;
}
