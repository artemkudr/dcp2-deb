#!/usr/bin/env sh

SSID=
PASSWD=
WLAN=wlan0
WPA_FILE=/etc/wpa_supplicant.conf
DRIVER_NAME=nl80211

usage()
{
	echo "Usage: ./ifup_wifi_sta [-ssid wifi_sta_name] [-passwd wifi_sta_passwd] [-driver nl80211 or wext]"
}

clean_stage()
{
	killall udhcpc
	killall wpa_supplicant
	killall hostapd
	killall udhcpd
	sleep 1
}

enable_wifi()
{
	T_HCI="phy0"
	RFKILL_SYS_PATH="/sys/class/rfkill/"
	dir=`ls ${RFKILL_SYS_PATH}`
	for i in ${dir}
	do
		if [ ${T_HCI} == `cat ${RFKILL_SYS_PATH}${i}/name` ];then
			echo 0 > ${RFKILL_SYS_PATH}${i}/state
			echo "find ${T_HCI} enable it"
			sleep 1
			echo 1 > ${RFKILL_SYS_PATH}${i}/state
		fi
	done
}

parse_input_info()
{
	while [ $# -gt 0 ];do
		case $1 in -ssid)
			SSID="$2"
		shift
		;;
		-passwd)
		PASSWD="$2"
		if [ ${#PASSWD} -lt 8 ];then
			echo "passwd should be 8...64"
			exit
		fi
		shift
		;;
		-driver)
		DRIVER_NAME="$2"
		shift
		;;
		-h)
		usage
		exit
		;;
		esac
		shift $(( $# > 0? 1:0))
	done
	echo "SSID:${SSID} PASSWD:${PASSWD} DRIVER:${DRIVER_NAME}"
}

connect_wifi(){
if [ -n "${SSID}" ];then
	head -n 4 ${WPA_FILE} > ${WPA_FILE}.tmp
	echo "ctrl_interface=/var/run/wpa_supplicant" > ${WPA_FILE}.tmp
	wpa_passphrase ${SSID} ${PASSWD} >> ${WPA_FILE}.tmp
	mv ${WPA_FILE} ${WPA_FILE}.bak
	mv ${WPA_FILE}.tmp ${WPA_FILE}
fi
wpa_supplicant -B -i ${WLAN} -c ${WPA_FILE} -D ${DRIVER_NAME} >/dev/null 2>&1
}

obtain_dns(){
# run dhcpc always
	udhcpc -i ${WLAN} &
}

parse_input_info $@
clean_stage
enable_wifi
connect_wifi
obtain_dns
