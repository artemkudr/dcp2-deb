#!/usr/bin/env sh
# File: /usr/bin/ifup_wifi_ap.sh
WWAN=wwan0
WLAN=wlan0
SSID=NASTKOM
PASSWD=Nastkom1
WLAN_IP=192.168.10.1
DHCP_FILE=/etc/udhcpd.conf
HOSTAPD_FILE=/tmp/hostapd.conf

usage(){
	echo "Usage: ./ifup_wifi_ap [-ssid wifi_ap_name] [-passwd wifi_ap_passwd] [-ip ip-address]"
}

parse_input_info(){
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
		-ip)
		WLAN_IP="$2"
		shift
		;;
		-h)
		usage
		exit
		;;
	esac
	shift $(( $# > 0? 1:0))
	done
	echo "SSID:${SSID} PASSWD:${PASSWD} IP:${WLAN_IP}"
}

hostapd_conf(){
# hotapd configuration
cat > /tmp/hostapd.conf << EOF
interface=wlan0
driver=nl80211
# mode Wi-Fi (a = IEEE 802.11a, b = IEEE 802.11b, g = IEEE 802.11g)
hw_mode=g
ssid=$SSID
channel=7
wmm_enabled=0
macaddr_acl=0
# Wi-Fi closed, need an authentication
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSWD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF
}

clean_stage(){
	killall udhcpc
	killall wpa_supplicant
	killall hostapd
	killall udhcpd
	sleep 1
}

enable_wifi(){
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

enable_ap_mode(){
	ifconfig ${WLAN} up ${WLAN_IP}

	sleep 1
	udhcpd ${DHCP_FILE}
	hostapd -B ${HOSTAPD_FILE}
}

parse_input_info $@
clean_stage
enable_wifi
hostapd_conf
enable_ap_mode
