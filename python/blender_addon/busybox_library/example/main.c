
/************************************************************************************
***
***	Copyright 2012 Dell Du(dellrunning@gmail.com), All Rights Reserved.
***
***	File Author: Dell, Tue Nov  6 10:41:46 CST 2012
***
************************************************************************************/


#include <stdio.h>
#include <unistd.h>
#include <getopt.h>
#include <stdlib.h>

void demo_video_client();
void demo_video_server();

void help(char *cmd)
{
	printf("Usage: %s [option]\n", cmd);
	printf("    -h, --help                   Display this help.\n");
	printf("    -c, --client                 Run client.\n");
	printf("    -s, --server                 Run server.\n");

	exit(1);
}

int main(int argc, char **argv)
{
	int optc;
	int option_index = 0;

	struct option long_opts[] = {
		{ "help", 0, 0, 'h'},
		{ "client", 0, 0, 'c'},
		{ "server", 0, 0, 's'},
		{ 0, 0, 0, 0}

	};

	if (argc <= 1)
		help(argv[0]);
	
	while ((optc = getopt_long(argc, argv, "h c s", long_opts, &option_index)) != EOF) {
		switch (optc) {
		case 'c':	// client
			demo_video_client();
			break;
		case 's':	// server
			demo_video_server();
			break;
		case 'h':	// help
		default:
			help(argv[0]);
			break;
	    }
	}

	// MS -- Modify Section ?

	return 0;
}
