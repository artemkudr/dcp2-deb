#! /bin/bash

echo "fix boot records for extlinux conf"
mount /dev/mmcblk2p2 /media/sd/

echo "MENU BACKGROUND /splash.bmp" > /media/sd/mmc0_extlinux/extlinux.conf
echo "TIMEOUT 20" >> /media/sd/mmc0_extlinux/extlinux.conf
echo "LABEL stm32mp157c-ya157c-v2" >> /media/sd/mmc0_extlinux/extlinux.conf
echo "        KERNEL /uImage" >> /media/sd/mmc0_extlinux/extlinux.conf
echo "        FDTDIR /" >> /media/sd/mmc0_extlinux/extlinux.conf
echo "        INITRD /uInitrd" >> /media/sd/mmc0_extlinux/extlinux.conf
echo "        APPEND root=PARTUUID=35219908-c613-4b08-9322-3391ff571e19 rootwait rw console=ttySTM0,115200" >> /media/sd/mmc0_extlinux/extlinux.conf


echo "menu title Select the boot mode" > /media/sd/mmc0_extlinux/stm32mp157c-ya157c-v2_extlinux.conf
echo "MENU BACKGROUND /splash.bmp" >> /media/sd/mmc0_extlinux/stm32mp157c-ya157c-v2_extlinux.conf
echo "TIMEOUT 20" >> /media/sd/mmc0_extlinux/stm32mp157c-ya157c-v2_extlinux.conf
echo "DEFAULT stm32mp157c-ya157c-v2" >> /media/sd/mmc0_extlinux/stm32mp157c-ya157c-v2_extlinux.conf
echo "LABEL stm32mp157c-ya157c-v2" >> /media/sd/mmc0_extlinux/stm32mp157c-ya157c-v2_extlinux.conf
echo "        KERNEL /uImage" >> /media/sd/mmc0_extlinux/stm32mp157c-ya157c-v2_extlinux.conf
echo "        FDTDIR /" >> /media/sd/mmc0_extlinux/stm32mp157c-ya157c-v2_extlinux.conf
echo "        INITRD /uInitrd" >> /media/sd/mmc0_extlinux/stm32mp157c-ya157c-v2_extlinux.conf
echo "        APPEND root=PARTUUID=35219908-c613-4b08-9322-3391ff571e19 rootwait rw console=ttySTM0,115200" >> /media/sd/mmc0_extlinux/stm32mp157c-ya157c-v2_extlinux.conf

umount /dev/mmcblk2p2
