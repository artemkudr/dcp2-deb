#! /bin/bash
DIR="/sys/class/gpio/gpio139"
PREV=1
[ ! -d $DIR ] && echo 139 > /sys/class/gpio/export && echo in > "${DIR}/direction"
while [ 1 ]
do
	#cat "${DIR}/value"
	if [ $(<"${DIR}/value") = "1" ]; 
		then PREV=1
		else if [ $PREV = 0 ];
			then echo mem > /sys/power/state
			else PREV=0
		fi
	fi
	sleep 3
done
