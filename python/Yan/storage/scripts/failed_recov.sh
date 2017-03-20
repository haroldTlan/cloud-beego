#!/bin/bash

#2015.10 Mark
#Recovery failed raids

echo 'use speediodb; select * from disks;' | mysql -uroot -ppasswd | awk '{print $6"  "$1"  "$7"  "$8"   "$9}' | tail -n +2 | cut -d . -f 3 | sort -n
echo 'use speediodb; select * from raids;' | mysql -uroot -ppasswd | awk '{print"###---" $6"---"$1"---###  "$10"  "$11"  "$12}' | tail -n +2 
touch /home/zonion/boot

