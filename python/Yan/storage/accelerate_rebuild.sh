#!/bin/bash

echo $((8192*4)) > /sys/block/$1/md/sync_speed_max
echo $((8192*4)) > /sys/block/$1/md/sync_speed_min
