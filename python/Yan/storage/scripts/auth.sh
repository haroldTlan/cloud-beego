#!/bin/bash
#2015.7 Mark

AUTHLOG=/var/log/auth.log
if [ -f $AUTHLOG ];then
    echo "use log file: $AUTHLOG"
else
    echo there is no AUTHLOG.
    exit 1
fi

rm -f /var/log/authlog.*

LOG=/var/log/authlog.log
IP=/var/log/authlog.ip
WORNING_IP=/var/log/authlog.worningip
FAIL_IP=/var/log/authlog.failip

cat $AUTHLOG | grep 'Failed password'  | grep -v invalid >> $LOG
cat $AUTHLOG | grep 'Failed password' | grep -v invalid | grep -v times  | awk '{print $9"-"$11}' | sort | uniq -c > $IP 

cat $IP | while read line
do
    ip=`echo $line | awk '{print $2}' |cut -d - -f 2`
    User=`echo $line | awk '{print $2}' |cut -d - -f 1`
    Count=`echo $line | awk '{print $1}'`
    Get=`cat $AUTHLOG | grep $ip | grep "$User from" | grep 'Accepted password' | wc -l`
    Host=`host $ip | awk '{print $5}'`
    Times=`cat $LOG | grep $ip | grep "$User from" | head -1 | awk '{print $1"-"$2"-"$3}'`
    Timee=`cat $LOG | grep $ip | grep "$User from" | tail -1 | awk '{print $1"-"$2"-"$3}'`
    Time=$Times---$Timee
    s=$(date -d `cat $LOG | grep $ip | grep "$User from" | head -1 | awk '{print $3}'` +%s)
    e=$(date -d `cat $LOG | grep $ip | grep "$User from" | tail -1 | awk '{print $3}'` +%s)
    time=$(($e-$s))
    #if [ ${time#-} -gt 10 ] && [ $Get -eq 0 ];then
        printf "|%-8s|%-17s|%-12s|%-15s|%-35s|%-s\n" "User" "IP_Address" "Fail_times" "Success_times" "Time_Range" "Host" >> $WORNING_IP
        printf "|%-8s|%-17s|%-12s|%-15s|%-35s|%-s\n" "$User" "$ip" "$Count" "$Get" "$Time" "$Host" >> $WORNING_IP
        echo "----------------------------------------------------------------------------------------------------" >> $WORNING_IP
        if [ $Get -eq 0 ];then
            echo "The dangerous ip is:$ip, the user is:$User. It is not allowed to login by ssh now" >> /var/log/syslog
            [ -z "`cat /etc/hosts.deny | grep $ip`" ] && echo "sshd: $ip" >> /etc/hosts.deny&&service ssh restart|| cd .
            
            sleep 2
        fi
    #fi
done
echo "The worning ip info: /var/log/authlog.worningip" >> /var/log/syslog
cat $WORNING_IP





