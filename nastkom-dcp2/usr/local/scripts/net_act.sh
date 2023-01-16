#! /bin/bash

exec 2>/dev/null

rx_packets=( $(</sys/class/net/wlan0/statistics/rx_packets) )
rx_packets_new=$rx_packets

while :
do
	let "dif = rx_packets_new - rx_packets"
	if [ $dif -gt 0  ]; then
        	echo 0 > /sys/class/gpio/gpio6/value
	        sleep 0.05
        	echo 1 > /sys/class/gpio/gpio6/value
		sleep 0.05
	else
		sleep 0.5
		link=$( iw wlan0 link | wc -l )
    conn=$( hostapd_cli all_sta | wc -l )
    if ( [ $conn -le 1 ] && [ $link -le 1 ] ); then
			echo 0 > /sys/class/gpio/gpio6/value
    fi
	fi
	rx_packets=$rx_packets_new
	rx_packets_new=( $(</sys/class/net/wlan0/statistics/rx_packets) )
done
