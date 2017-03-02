#!/bin/bash

#space
echo "sda5 Space"
df -h | head -2 | tail -1 

#disk_location
echo ------------------------------------------------------
echo "Disk Info"
python /home/zonion/speedio/show_location.pyc | grep -v { | sort -k3nr
num=`python /home/zonion/speedio/show_location.pyc | grep -v { | wc -l`
echo "Disk Num"
echo $num

#raid_info
echo ------------------------------------------------------
echo "RAID Status"
mdadm -D /dev/md* | grep "State :"

#lun_info
echo ------------------------------------------------------
echo "Volume Info"
pvs

#speedio.log_info
echo ------------------------------------------------------
echo "ZBX Info"
cat -n /var/log/speedio.log | grep Traceback | tail -5

#syslog_info
echo ------------------------------------------------------
echo "syslog info: Disk Error Info"
echo -e \# 
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
python /home/zonion/speedio/show_location.pyc | grep -v { | sort -k3nr > /tmp/diskinfo
cat /tmp/diskinfo | while read line
do
    sd=`echo $line | awk '{print $2}'`
    read_error=`cat /var/log/syslog | grep -A 1 "\[$sd\]" | grep 'Unrecovered read'| wc -l`
    #start=`cat -n /var/log/syslog | grep -E 'end_request|medium' | grep $sd |head -1 | awk '{print $1}'`
    #end=`cat -n /var/log/syslog | grep -E 'end_request|medium' | grep $sd |tail -1 | awk '{print $1}'`
    #case "$start" in
    #    "")
    #        link_error=0
    #        ;;
    #    **)
    #        range=$(($end-$start))
    #        link_error=`cat -n /var/log/syslog | grep -A $range $start | grep 'mpt2sas0: log' |wc -l`
    #        ;;
    #esac
    medium_error=`cat /var/log/syslog | grep 'medium' | grep $sd | wc -l`
    IO_error=`cat /var/log/syslog | grep 'end_request: I/O' | grep $sd | wc -l`
    plug_time=`cat /var/log/syslog | grep 'Attached SCSI disk' | grep $sd | wc -l`
    printf "|%-20s|%-15s|%-25s|%-15s|%-15s\n" "Disk" "I/O Error" "Unrecovered_Read_Error" "Medium_Error" "Plug_Time"
    printf "|%-20s|%-15s|%-25s|%-15s|%-15s\n" "$line" "$IO_error" "$read_error" "$medium_error"  "$plug_time"
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
done
link_log_sum=`cat /var/log/syslog | grep 'mpt2sas0: log_info' | wc -l`
link_retry_sum=`cat /var/log/syslog | grep 'retries' | grep mpt2sas0 | wc -l`
link_timeout_sum=`cat /var/log/syslog | grep 'timeout' | grep mpt2sas0 | wc -l`


cat /var/log/syslog | grep 'mpt2sas0: log_info' | awk -F "[()]" '{print $2}'>>/tmp/code
sort /tmp/code | uniq -c >>/tmp/code_sort_time
sort /tmp/code | uniq -c | sort -k1nr>>/tmp/code_sort_num
cat /tmp/code_sort_time | while read line
do
        code=`echo $line | awk '{print $2}'`
        code_times=`echo $line | awk '{print $1}'`
        error=`python lsi_decode_loginfo.py $code | grep Code`
        printf "|%-20s|%-15s\n" "error_code" "error_times"
        printf "|%-20s|%-15s\n" "$code" "$code_times"
        printf "|%-25s\n" "error_reason"
        echo  "$error"
        echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
done
rm /tmp/code
rm /tmp/code_sort_time
rm /tmp/code_sort_num


echo "Link_Log_Sum: $link_log_sum"
echo "Link_Retry_Sum: $link_retry_sum"
echo "Link_Timeout_Sum: $link_timeout_sum"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

echo "syslog info: Memory Error"
echo -e \#
cat -n /var/log/syslog | grep -E "segfault|can't fork"

echo "syslog info: Reboot Info"
re=`cat /var/log/syslog |  grep 'imklog' | wc -l`
md=`cat /var/log/syslog |  grep 'raid:md0: raid level' | wc -l`
sd=`cat /var/log/syslog |  grep 'Attached SCSI disk' | wc -l`
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
printf "|%-20s|%-15s|%-25s\n" "Reboot Time" "RAID Scan Time" "Disk Scan Time"
printf "|%-20s|%-15s|%-25s\n" "$re" "$md" "$sd"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

echo "syslog info: iSCSI Error"
echo -e \#
cat -n /var/log/syslog | grep "iSCSI Login timeout" | head -1

#corefile_info
echo ------------------------------------------------------
echo "Core Info"
if [ -e /var/log/core* ];then
    ls -al /var/log/core*
else
    echo -e \#
fi

#mcelog_info
echo ------------------------------------------------------
echo "MCElog Info"
dpkg -l | grep mcelog > /dev/null
if [ $? -eq 0 ];then
    :
else
    dpkg -i mcelog.deb
fi
mcelog
cat /var/log/mcelog | grep Location
cat /var/log/mcelog | grep Transaction
echo ------------------------------------------------------
