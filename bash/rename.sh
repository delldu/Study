#/************************************************************************************
#***
#***	Copyright 2022 Dell(18588220928@163.com), All Rights Reserved.
#***
#***	File Author: Dell, 2022年 05月 30日 星期一 14:13:11 CST
#***
#************************************************************************************/
#
#! /bin/sh


usage()
{
	echo "Usage: $0 dir_name"

	exit 1
}


[ "$1" == "" ] && usage


dir_name=$1
file_list=`ls ${dir_name}/*.png 2>/dev/null | sort`

count=1
for s_filename in $file_list ;
do
	d_filename=`printf '%s/%04d.png' $dir_name $count`
	echo $s_filename "--->" $d_filename
	#mv $s_filename $d_filename

	count=`expr $count + 1`
done

