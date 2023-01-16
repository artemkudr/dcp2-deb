#! /bin/bash

#if [ $# -ne 1 ];
#    then echo "illegal number of parameters"
#    exit -2
#fi

#case "$(curl -s --max-time 5 -I http://google.com | sed 's/^[^ ]*  *\([0-9]\).*/\1/; 1q')" in
#  [23]) echo "HTTP connectivity is up";;
#  5) echo "The web proxy won't let us through";;
#  *) echo "The network is down or very slow";;
#esac

output=$(qmicli -d /dev/cdc-wdm0  --wds-get-packet-service-status  | awk -F[:] '{print $2}')

if [ "${output}" = " 'connected'" ]; then
	echo "WDS CONNECTED"

#	ping -c1 -I "$1" 8.8.8.8
	ping -c1 -I wwan0 8.8.8.8

	if [ "$?" != 0 ]; then
#        	ping -c1 -I "$1" 8.8.8.8
        	ping -c1 -I wwan0 8.8.8.8
        	if [ "$?" != 0 ]; then
                	echo "PING FAILED"
			echo '0' > /tmp/wds_status
                	exit -1
        	fi
	fi
	echo '1' > /tmp/wds_status
	exit 0
fi
echo "WDS NOT CONNECTED"
echo '0' > /tmp/wds_status
exit -1
