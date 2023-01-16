#! /usr/bin/python3

import sys, json, math, subprocess, time, shlex, socket, logging
from logging.handlers import RotatingFileHandler

SCRIPTS_DIR = '/usr/local/scripts/'

DEFAULT_TIMEOUT = 30
FAST_TIMEOUT = 5
TIMEOUT = DEFAULT_TIMEOUT
STA_TIMEOUT = 60
MODEM_TIMEOUT = 60

LOG_MAX_SIZE = 8192

modem_not_connected = 0
sta_not_connected = 0
ap_true_times = 0
max_ap_true_times = 3

apn = "internet"
apn_user = ""
apn_pass = ""

server_ip = ""

def distance(lat1, lon1, lat2, lon2):
	R = 6373.0	#radius of the Earth
	# coordinates must be converted to radians
	# for the calculations to be correct
	lat1 = math.radians(float(lat1))
	lon1 = math.radians(float(lon1))
	lat2 = math.radians(float(lat2))
	lon2 = math.radians(float(lon2))
	# change in coordinates
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	# Haversine formula
	a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
	distance = R * c
	return distance

def get_ap_state():
	apmode = subprocess.run([SCRIPTS_DIR+'is_running', 'hostapd'])
	if apmode.returncode == 0:
		logger.info("AP mode active")
		return 1
	else:
		logger.info("AP mode inactive")
		return 0

def is_sta_connected():
	conn_state = subprocess.run(["wpa_cli -iwlan0 -p/var/run/wpa_supplicant status | grep wpa_state | awk -F[=] '{print $2}'"], shell=True, capture_output = True)
	if conn_state.returncode == 0:
		if conn_state.stdout == b'COMPLETED\n':
			return True
		else:
			return False
def sta_start():
	wlan0_recovery()
	logger.info("sta_start", ssid, password)

	wifi_sta = subprocess.run([SCRIPTS_DIR + 'wifi/ifup_wifi_sta.sh', '-driver', 'nl80211', '-ssid', ssid, '-passwd', password], shell=False)
	if wifi_sta.returncode == 0:
		logger.info("STA mode started OK")
		sta_not_connected = 0
	else:
		logger.info("STA mode start Failed")

# TODO hardcoded profile path
def modem_start():
	global apn
	global apn_user
	global apn_pass
	global modem_not_connected

	with open('/tmp/profile', 'w') as profile:
		profile.write('PROXY=yes\n')
		profile.write(f'APN={apn}\n')
		if len(apn_user)>0 and len(apn_pass)>0:
			profile.write(f'APN_USER={apn_user}\n')
			profile.write(f'APN_PASS={apn_pass}\n')

	qmi = subprocess.run(['qmi-network --profile /tmp/profile /dev/cdc-wdm0 start'], shell=True)

#	MANUAL START UDHCPC
	try:
		udhcpc = subprocess.run(['udhcpc', '-i', 'wwan0'], timeout=10) # -q -f -n
	except subprocess.TimeoutExpired:
		logger.info("WWAN0: udhcpc timeout")
		pass
	else:
		modem_not_connected = 0

# 	AUTOMATIC DHCP OVER SYSTEMD_NETWORKD-NETWORKD
#	modem_not_connected = 0

def modem_stop():
	qmi = subprocess.run(['qmi-network', '/dev/cdc-wdm0', 'stop'])
	udhcpc = subprocess.run(['killall', 'udhcpc'])
	ip = subprocess.run(['ip', 'addr', 'flush', 'dev', 'wwan0'])

def wlan0_recovery():
	logger.info('wlan0_recovery')
	subprocess.run(['echo -n "48004000.sdmmc" > /sys/bus/amba/drivers/mmci-pl18x/48004000.sdmmc/driver/unbind'], shell = True)
	time.sleep(1)
	subprocess.run(['echo -n "48004000.sdmmc" > /sys/bus/amba/drivers/mmci-pl18x/bind'], shell = True)
	time.sleep(3)

def check_internet(host, port):
	try:
		s = socket.create_connection((host, port), 2)
		s.close()
		return True
	except:
		pass
	return False


def set_ap_state(state):
	global modem_not_connected
	global sta_not_connected
	global TIMEOUT
	global ap_true_times
	global first_run

	if state:
		logger.info("Set AP mode")
	else :
		logger.info("Set STA mode")

	cur_state = get_ap_state()

	if (cur_state == state): # and first_run == False:
		if state == True:
			# Check internet on WWAN0
			is_inet_ok = subprocess.run([SCRIPTS_DIR +'checknet.sh', 'wwan0'])
			if is_inet_ok.returncode != 0:
				logger.info('WWAN0 offline')
				modem_not_connected += TIMEOUT
				if modem_not_connected >= MODEM_TIMEOUT:
					logger.info("WWAN0 not connected timeout occured")
					modem_stop()
					time.sleep(3)
					modem_start()
		else :
			# Restart STA if not connected
			if is_sta_connected() == 0 or check_internet(server_ip, 87) == False :
				sta_not_connected += TIMEOUT
				if sta_not_connected >= STA_TIMEOUT :
					logger.info("STA not connected timeout occured")
					sta_start()
			else :
				logger.info("STA status CONNECTED")
				sta_not_connected = 0
	elif state == True:
		if ap_true_times < max_ap_true_times:
			ap_true_times += 1
			TIMEOUT = FAST_TIMEOUT
			return

		with open("/sys/class/leds/wifi_ap/brightness", "w") as f:
			f.write("0")
		with open("/sys/class/leds/wifi_sta/brightness", "w") as f:
			f.write("1")

		TIMEOUT = DEFAULT_TIMEOUT

		# Enable Modem Network
		modem_stop()
		time.sleep(3)
		modem_start()

		# Enable AP mode (DHCP enables automatically)
		wifi_ap = subprocess.run([SCRIPTS_DIR + 'wifi/ifup_wifi_ap.sh', '-ssid', ssid, '-passwd', password, '-ip', local_ip])

		if wifi_ap.returncode == 0:
			logger.info("Switched AP On Success")
		else:
			logger.info("Switch AP On Failed")
			wlan0_recovery()
		first_run = False
	else :
		if ap_true_times > 0:
			ap_true_times -= 1
			TIMEOUT = FAST_TIMEOUT
			return

		with open("/sys/class/leds/wifi_ap/brightness", "w") as f:
			f.write("1")
		with open("/sys/class/leds/wifi_sta/brightness", "w") as f:
			f.write("0")

		TIMEOUT = DEFAULT_TIMEOUT

		# Disable Modem Network
		modem_stop()

		# Start WiFi in STA mode
		sta_start()
		first_run = False

""" START SCRIPT """
ap_true_times=0
first_run = True

logger = logging.getLogger("wifimode")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("/var/log/wifimode.log", maxBytes = LOG_MAX_SIZE, backupCount=1)
formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)

logger.addHandler(handler)

while(1):

	try:
		with open('/usr/share/dcp-conf/dcp.conf', 'r') as json_conf:
			conf = json.load(json_conf)
	except Exception:
		logger.info("dcp.conf error")
		set_ap_state(False)

	aps = conf['aps']
	ssid = str(conf['ssid'])
	password = str(conf['wpa_passphrase'])
	logger.info(ssid, password)
	local_ip = '192.168.10.1'

	server_ip = conf['server_ip']

	for port in conf['ports']:
		iptables = subprocess.run(['/usr/sbin/iptables -t nat -C PREROUTING -p tcp --dport ' + str(port['port']) + ' -j DNAT --to-destination ' + local_ip + ':' + str(port['port'])], shell=True)
		if iptables.returncode != 0:
			iptables = subprocess.run(['iptables -t nat -A PREROUTING -p tcp --dport ' + str(port['port']) + '  -j DNAT --to-destination ' + local_ip + ':' + str(port['port'])], shell=True)

	apn = str(conf['apn'])
	apn_user = str(conf['apn_user'])
	apn_pass = str(conf['apn_pass'])

	if len(aps)>0:
		try:
			with open('/tmp/gps.latlon', 'r') as gps:
				position = dict(line.strip().split(':') for line in gps)
		except Exception: #IOError #FileNotFoundError
			logger.info("gps.latlon error")
			set_ap_state(False)
		else:
			if len(position) == 2:
				logger.info("Current position is: %s", position)

				""" client_mode = True if we are inside geozone of stationary WiFi point so we must switch AP state to off  """
				client_mode = False
				for  idx, ap in enumerate(aps):
					if 'radius' not in ap:
						ap['radius']=1
					logger.info(f"AP#{idx}:\n\tLat:{ap['lat']}\n\tLon:{ap['lon']}")
					if distance(position['lat'], position['lon'], ap['lat'], ap['lon']) < ap['radius']:
						client_mode = True
						break

				if client_mode == True:
					logger.info("In geozone of static AP")
					set_ap_state(False)
				else:
					logger.info("Not in geozone")
					set_ap_state(True)

			else:
				logger.info("No GPS fix")
				set_ap_state(False)

	else:
		# no static aps configured, so we cant run in STA mode correct, but we cant run AP mode at all, so turn AP off
		logger.info("There are no static aps configured")
		set_ap_state(False)

	time.sleep(TIMEOUT)


