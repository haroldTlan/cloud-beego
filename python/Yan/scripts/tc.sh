#!/bin/bash
#configure for $DEV
DEV=eth0

#Set The IP POOL
IP_POOL_CUS=()
IP_POOL_CUS[0]=192.168.2.1-253\|4000kbit
#################################################################




BW_TOTAL=1000mbit

stop_tc(){
	tc qdisc del dev $DEV root > /dev/null 2>&1
}

add_rule(){
	if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ];then
		echo "add_rule() run Error"
		exit
	fi
	ID=$1
	SPEED=$2
	IP=$3
	tc class add dev $DEV parent 1:1 classid 1:$ID htb rate $SPEED ceil $SPEED
	tc qdisc add dev $DEV parent 1:$ID handle ${ID}: sfq perturb 10
	tc filter add dev $DEV protocol ip parent 1: prio 8 u32 match ip dst $IP flowid 1:$ID
}

start_tc(){
	tc qdisc del dev $DEV root > /dev/null 2>&1
	tc qdisc add dev $DEV root handle 1: htb default 40
	tc class add dev $DEV parent 1: classid 1:1 htb rate $BW_TOTAL
	tc class add dev $DEV parent 1:1 classid 1:10 htb rate 1mbit ceil 1mbit
	tc class add dev $DEV parent 1:1 classid 1:40 htb rate 5mbit ceil 5mbit
	tc qdisc add dev $DEV parent 1:10 handle 10: sfq perturb 10
	tc qdisc add dev $DEV parent 1:40 handle 40: sfq perturb 10
	for ((i=0;i<${#IP_POOL_CUS[@]};i++));do
		IP=$(echo ${IP_POOL_CUS[$i]}|awk -F"|" '{print $1}')
		IP1=$(echo $IP|awk -F"." '{print $1"."$2"."$3}')
		IP2=$(echo $IP|awk -F"." '{print substr($NF,0,index($NF,"-")-1)}')
		IP3=$(echo $IP|awk -F"." '{print substr($NF,index($NF,"-")+1)}')
		SPEED=$(echo ${IP_POOL_CUS[$i]}|awk -F"|" '{print $2}')
		#echo IP:$IP,IP1:$IP1,IP2:$IP2,IP3:$IP3
		for ((j=IP2;j<=IP3;j++));do
			ID_BASE=$[i+1]
			ID=$[ID_BASE * 1000 + j]
			#echo j:$j,ID:$ID
			add_rule $ID $SPEED ${IP1}.$j
		done
		#add_rule $ID $SPEED $IP
	done
	#tc filter add dev $DEV protocol ip parent 1: prio 10 u32 match ip dst 192.168.1.0/24 flowid 1:10
	#icmp
	tc filter add dev $DEV protocol ip parent 1: prio 10 u32 match ip protocol 1 0xff
}

status_tc(){
	tc -s qdisc show dev $DEV
	echo ""
	tc class show dev $DEV
	echo ""
	tc -s class show dev $DEV
	echo ""
	tc filter ls dev $DEV parent ffff:
}

case $1 in
  restart | start)
    start_tc
	echo -e "bwctl start [ \033[1;32m"Success!"\033[0m ]"
	;;
  stop)
    stop_tc
	echo "bwctl stop [ \033[1;32m"Success!"\033[0m ]"
	;;
  status)
    status_tc
	;;
  *)
   echo  Usage:' bwctl.sh start | stop | restart |status'
esac
