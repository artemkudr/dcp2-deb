#! /usr/bin/python3

import sys, json, math, subprocess

SCRIPTS_DIR = '/usr/local/scripts/'
#SCRIPTS_DIR = '/vendor/wifi/'


#def get_ap_state():
#	""" systemctl returncode=0 if active and returncode=3 if inactive states of service"""
#	hostapd = subprocess.run(['systemctl', 'is-active', 'hostapd'], capture_output=True)
#	if hostapd.returncode == 0 or  hostapd.returncode == 3:
#		if hostapd.stdout == b'active\n':
#			print("AP mode active")
#			return True
#		else:
#			print("AP mode inactive")
#			return False
#	else:
#		print("systemctl (hostapd) reguest failed")
#		return None

def get_ap_state():
	apmode = 0

	try:
		with open('/tmp/apmode', 'r') as f:
			apmode = int(f.readline())
	except Exception:
		print("apmode status error")

	if apmode == 1:
		print("AP mode active")
		return 1
	else:
		print("AP mode inactive")
		return 0



""" START SCRIPT """

ap_state = get_ap_state()

if ap_state == 1:
	net_status = subprocess.run([SCRIPTS_DIR+'checknet.sh', 'wwan0'], capture_output = True)
	if net_status.returncode == 0:
		print('Internet Online on WWAN0')
	else:
		print('No Internet on WWAN0')
