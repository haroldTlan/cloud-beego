function set_sysfs
{
	echo $2 > $1
	echo $1:`cat $1`
}

sync
echo 3 > /proc/sys/vm/drop_caches
set_sysfs /sys/block/$1/make-it-fail $2
set_sysfs /sys/kernel/debug/fail_make_request/probability 100
set_sysfs /sys/kernel/debug/fail_make_request/times $3
