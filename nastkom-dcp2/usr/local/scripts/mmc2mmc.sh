#! /bin/bash

# u-boot
dd if=/dev/zero of=/dev/mmcblk2p1 bs=1M
dd if=/dev/mmcblk1p1 of=/dev/mmcblk2p1 bs=1M
# /boot FS
dd if=/dev/mmcblk1p2 of=/dev/mmcblk2p2 bs=1M
# /vendor FS
dd if=/dev/mmcblk1p3 of=/dev/mmcblk2p3 bs=1M
# /
dd if=/dev/mmcblk1p4 of=/dev/mmcblk2p4 bs=1M
# /usr/local FS
dd if=/dev/mmcblk1p5 of=/dev/mmcblk2p5 bs=1M
