#!/bin/bash
#systemctl stop wifimode.service # it stops all the processes, that has been run by wifimode.service
systemctl stop gpsget.service
#apt-get update && apt-get install nastkom-dcp2 | grep "is already the newest version" && echo "FAIL" || reboot now
apt-get update && apt-get install nastkom-dcp2 > /tmp/autoupd.log
if [ "$?" -ne 0 ]
   then
      exit 2
   else
      cat /tmp/autoupd.log | grep "is already the newest version" && exit 1  || exit 0
fi
