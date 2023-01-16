#! /bin/bash

sfdisk /dev/mmcblk2 < /usr/local/scripts/mmcblk2.sfdisk

# tfa
echo 0 > /sys/block/mmcblk2boot0/force_ro
dd if=/dev/zero of=/dev/mmcblk2boot0 bs=1M count=1
dd if=/dev/mmcblk1p1 of=/dev/mmcblk2boot0 bs=128K
echo 1 > /sys/block/mmcblk2boot0/force_ro

echo 0 > /sys/block/mmcblk2boot1/force_ro
dd if=/dev/zero of=/dev/mmcblk2boot1 bs=1M count=1
dd if=/dev/mmcblk1p1 of=/dev/mmcblk2boot1 bs=128K
echo 1 > /sys/block/mmcblk2boot1/force_ro
# u-boot
dd if=/dev/zero of=/dev/mmcblk2p1 bs=1M
dd if=/dev/mmcblk1p3 of=/dev/mmcblk2p1 bs=1M
# /boot FS
dd if=/dev/mmcblk1p4 of=/dev/mmcblk2p2 bs=1M
# /vendor FS
dd if=/dev/mmcblk1p5 of=/dev/mmcblk2p3 bs=1M
# /
dd if=/dev/mmcblk1p6 of=/dev/mmcblk2p4 bs=1M
# /usr/local FS
dd if=/dev/mmcblk1p7 of=/dev/mmcblk2p5 bs=1M


/usr/local/scripts/./fixboot.sh
