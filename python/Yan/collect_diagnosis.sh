#!/bin/bash
ZSTOR_PATH=/home/zonion
DIAGNOSIS_PATH=/home/zonion/diagnosis
rm -rf $DIAGNOSIS_PATH
mkdir $DIAGNOSIS_PATH
mysqldump -uspeedio -ppasswd speediodb > $DIAGNOSIS_PATH/speediodb.sql
bash /home/zonion/speedio/scripts/check_info.sh > /home/zonion/recent_info
logsize=`du -sm /var/log | awk '{print $1}'`
sda5size=`df -m | awk '{print $4}' | head -2 | tail -1`
size=`expr $sda5size / 2`
if [ $size -gt $logsize ];then
    cp /var/log/core* $DIAGNOSIS_PATH
    cp /var/log/syslog* $DIAGNOSIS_PATH
    cp /var/log/kern* $DIAGNOSIS_PATH
    cp /var/log/messages* $DIAGNOSIS_PATH
else
    bash /home/zonion/speedio/scripts/dfck.sh 0
    mv /var/logfile/* $DIAGNOSIS_PATH
fi
    cp /var/log/boot.log $DIAGNOSIS_PATH
    cp /var/log/authlog.worningip $DIAGNOSIS_PATH
    cp /home/zonion/recent_info $DIAGNOSIS_PATH
    cp /root/hardware_info $DIAGNOSIS_PATH
    cp /var/log/speedio.* $DIAGNOSIS_PATH
    cp $ZSTOR_PATH/license/key $DIAGNOSIS_PATH
    cd $ZSTOR_PATH
    d=`date +%Y-%m-%d_%H-%M`
    n=`cat /root/hardware_info | grep 010100 | tail -1`
    tar -czvf diagnosis.tar.gz diagnosis
    rm -rf $DIAGNOSIS_PATH


