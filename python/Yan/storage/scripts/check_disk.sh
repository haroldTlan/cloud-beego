#!/bin/bash
rm /root/disk_info*.txt
d=`date +%Y-%m-%d`
num=`python /home/zonion/speedio/show_location.pyc | grep -v { | wc -l`
echo "Date:$d"  >> /root/disk_info-$num-$d.txt
echo "Total Disk Number: $num" >> /root/disk_info-$num-$d.txt

for i in {b..y}
do
    fdisk -l /dev/sd$i | grep GB | grep Disk  2>&1 >> /root/disk_info-$num-$d.txt  
    hdparm -I /dev/sd$i | grep Number >> /root/disk_info-$num-$d.txt
done
echo 'disk query_zero_progress' | python /home/zonion/speedio/speedcli.pyc >> /root/disk_info-$num-$d.txt
