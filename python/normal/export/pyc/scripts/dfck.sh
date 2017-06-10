#!/bin/bash

#2015.3 Mark
#2015.8.27 V1.1 Mark

d=`date +%Y-%m-%d`

space_check()
{
    df=`df -h |grep sda5| awk '{print $5}' | cut -d % -f 1`
    return $df
}

space_create()
{
    if mount | grep -q logspace;then
        :
    else
        rm -rf /logspace
        mkdir /logspace
        mount -t tmpfs none /logspace -o size=30m
    fi
}

change_rcstep()
{
    if [ -e /etc/rc.local.ori ];then
        :
    else
        cp /etc/rc.local /etc/rc.local.ori
    fi
    space_check
    if  [ $df -eq 100 ];then
        if [[ -e /home/zonion/license/key && -e /home/zonion/license/key.sig ]];then
            echo "$d The usage of /dev/sda5 is still $df%, please check it manually" >> /var/log/syslog
            cp /etc/rc.local.ori /etc/rc.local
        else
            echo "$d The space is too full to get license" >> /var/log/syslog
            mount -o remount rw /
            sed -i '/rc.step/'d /etc/rc.local
        fi
    else
        echo "$d The corefile and log has been packed to /var/logfile/,the usage of sda5 is $df% now" >> /var/log/syslog
    fi
}

space_clean()
{
    space_check
    echo "$d The usage of /dev/sda5 is $df%" >> /var/log/syslog
    # arg '0' means force clean
    if [ $df -gt 85 ] || [ $1 -eq 0 ];then
        space_create
        cd /logspace
        echo "Packing the corefile..."
        ls /var/log/core-* | cut -d - -f 2 > /tmp/comm
        sort /tmp/comm | uniq > /tmp/comm_uniq
        cat /tmp/comm_uniq | while read line
        do
            tar zcvfP core$d-$line.tar.gz `find /var/log -name core-$line*`
        done 
        rm -f  /var/log/core-*
        echo "Packing the bigggest three logfile and key log..."
        ls -l /var/log/ -h -S | head -4 | grep -v total | awk '{print $9}' >> /tmp/biglog
        ls -l /var/log/ -h -S | awk '{print $9}' | grep -E 'syslog|speedio' >> /tmp/biglog
        cat /tmp/biglog | sort | uniq | while read line
        do
            tar zcvfP log$d-$line.tar.gz /var/log/$line
            echo > /var/log/$line
        done
        if [ -d /var/logfile ];then
            : 
        else
            mkdir /var/logfile
        fi
        mv /logspace/* /var/logfile/
        sleep 10
        cd /root/
        umount /logspace
        rm -rf /logspace
        sleep 10
        change_rcstep
    else
        :
    fi
}
input=$1
# arg '0' means force clean
space_clean ${input:-1}

