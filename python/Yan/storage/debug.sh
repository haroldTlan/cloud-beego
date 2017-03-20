dmsetup remove /dev/mapper/rqr-sdb*
delpart /dev/sdb 1
delpart /dev/sdb 2
delpart /dev/sdb 3
delpart /dev/sdb 4

dmsetup remove /dev/mapper/rqr-sdc*
delpart /dev/sdc 1
delpart /dev/sdc 2
delpart /dev/sdc 3
delpart /dev/sdc 4

dmsetup remove /dev/mapper/rqr-sde*
delpart /dev/sde 1
delpart /dev/sde 2
delpart /dev/sde 3
delpart /dev/sde 4

dmsetup remove /dev/mapper/rqr-sdg*
delpart /dev/sdg 1
delpart /dev/sdg 2
delpart /dev/sdg 3
delpart /dev/sdg 4
