#!/bin/bash

process=csdn_proc.py
count=`ps -ef | grep -w $process | grep -v grep | wc -l`
if [ $count -gt 0 ]
then
    ps -ef | grep -w $process | grep -v grep | awk '{print $2}' | xargs kill -9
fi

sleep 1
nohup python3 $process & >/dev/null 2>&1
exit 