#!/bin/bash
if [ -e /home/zonion/speedio/scripts/$1 ];
    then
        cat /etc/crontab | grep $1 > /dev/null 2>&1
        if [ $? -eq 0 ];then
            echo "$1 crontab exist"
        else
            echo "25 6    * * *   root    bash /home/zonion/speedio/scripts/$1 > /dev/null 2>&1" >> /etc/crontab
            echo "$1 crontab config success"
        fi
    else  
        echo "There is no $1d "
fi

