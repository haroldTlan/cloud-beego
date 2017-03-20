#!/bin/bash

# 2015.4.21 v1.0 Mark
# 2015.5.21 v1.1 Mark

# check linux info

check_linux_info()
{
    local info=$1
    local Info=''
    if cat /etc/issue | grep -q -E -i "ubuntu|debian|onion";then
        Info='apt'
    elif cat /etc/issue | grep -q -E -i "centos|red hat|redhat";then
        Info='yum'
    elif cat /proc/version | grep -q -E -i "ubuntu|debian";then
        Info='apt'
    elif cat /proc/version | grep -q -E -i "centos|red hat|redhat";then
        Info='yum'
    else
        echo "unkonw"
    fi
 
    if [ "$info" == "$Info" ];then
        return 0
    else
        return 1
    fi   
}

# check iscsi service
check_iscsi_service()
{
    if check_linux_info apt;then
        if dpkg -l | grep -q open-iscsi;then
            cd /etc/init.d
            ./open-iscsi restart
        else
            echo "open-iscsi not found, maybe install failed, please check your network or apt-get source."
            exit 1
        fi
    elif check_linux_info yum;then
        if rpm -qa | grep -q iscsi-initiator;then
            chkconfig --add iscsi 
            chkconfig --level 2 on
            chkconfig --level 3 on
            chkconfig --level 4 on
            chkconfig --level 5 on
            cd /etc/init.d
            ./iscsi restart
            ./iscsid restart
        else
            echo "iscsi-initiator not found, maybe install failed, please check your network or yum source."
            exit 1
        fi
    fi  
}

# check storage ip
get_storage_ip()
{
    while true
    do
    echo -e "Please input the ip address of storage from GUI:\c"
    read ip
        #if ping $ip -c 1 > /dev/null 2>&1;then
        if curl -s http://$ip:8080/api/systeminfo > /dev/null 2>&1;then
            echo $ip > /etc/iscsi/zbxip
            return 0
        else
            echo "wrong ip address"
            get_storage_ip
            return 1
        fi
    done
}

get_iscsi_wwn()
{
    ip=`cat /etc/iscsi/zbxip`
    wwn=$(echo 'initiator list' | ssh admin@$ip | grep WWN | awk '{print $4}')
    echo $wwn > /etc/iscsi/zbxiscsi
    cd /etc/iscsi/
    sed 's/^/InitiatorName=/' /etc/iscsi/zbxiscsi > /etc/iscsi/zbxiscsi_I
    #echo 'ls' | targetcli |  grep '\.net\.zbx\.target' | awk '{print $3}' > /etc/iscsi/zbxiscsi_T
}


start_iscsi_service()
{
    check_iscsi_service
    get_storage_ip
    ip=`cat /etc/iscsi/zbxip`
    get_iscsi_wwn
    WWN_I=`cat /etc/iscsi/zbxiscsi_I`
    cd /etc/iscsi/
    cp /etc/iscsi/zbxiscsi_I /etc/iscsi/initiatorname.iscsi
    iscsiadm -m discovery -t sendtargets -p $ip:3260
    iscsiadm -m discovery -t sendtargets -p $ip:3260 > /etc/iscsi/zbxiscsi_T
    WWN_T=`cat /etc/iscsi/zbxiscsi_T | awk '{print $2}'`
    iscsiadm -m node -T $WWN_T -p $ip:3260 -l
}

# check & install linux iscsi initiator
case $1 in 
start)
    iscsiadm -m host | grep tcp > /dev/null
    if [ $? -eq 0 ];then
        cd /etc/init.d
        ./open-iscsi status
        exit 0
    else
        if check_linux_info apt;then
            if dpkg -l | grep -q "open-iscsi";then
                start_iscsi_service
            else
                echo "open-iscsi not found, going to install it..."
                sleep 1
                apt-get -y install open-iscsi > /dev/null
                start_iscsi_service
            fi
        elif check_linux_info yum;then
            if  rpm -qa | grep -q "iscsi-initiator";then
                start_iscsi_service
            else
                echo "iscsi_initiator not found, going to install it..."
                sleep 1
                yum -y install iscsi_initiator  > /dev/null
                start_iscsi_service
            fi
        fi
    fi
    ;;

check)
    cd /etc/init.d
    ./open-iscsi status
    ;;

stop)
    get_storage_ip
    ip=$`cat /etc/iscsi/zbxip`
    get_iscsi_wwn
    WWN_T=`cat /etc/iscsi/zbxiscsi_T | awk '{print $2}'`
    iscsiadm -m node -T $WWN_T -p $ip:3260 -u
    ;;
*)
    echo "* Usage: ./iscsi.sh {start|stop|check|}"
    exit 0
esac
