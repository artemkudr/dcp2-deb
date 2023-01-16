#! /usr/bin/python3

import os, ctypes, subprocess

from time import sleep
from serial import Serial

# types definitions 

c_uint8 = ctypes.c_uint8

class Flags_bits(ctypes.LittleEndianStructure):
	_fields_ = [
		("all_done", c_uint8, 1),
		("gps_fix", c_uint8, 1),
		("wds_status", c_uint8, 1),
		("nas_status", c_uint8, 1),
		("ap_mode", c_uint8, 1),
		("sta_mode", c_uint8, 1),
		("mode1", c_uint8, 1),
		("mode2", c_uint8, 1),
	]

class Flags(ctypes.Union):
	_fields_ = [("b", Flags_bits),
	("asbyte", c_uint8)]

# Globals

SCRIPTS_DIR = '/usr/local/scripts/'

flags = Flags()
flags.asbyte = 0x00
sec = 0
port = "/dev/ttySTM2"

# Functions

def check_wds_status():
	wds_status = 0
	try:
		with open('/tmp/wds_status') as f:
			wds_status = int(f.readline())
	except Exception:
		#print("exception")
		return 0
	#print(wds_status)
	return wds_status

def sum_file_sizes(src):
	dfiles =  os.listdir(src)
	files = []
	size = 0
	for file in dfiles:
		if os.path.isdir(os.path.join(src,file)):
			size += sum_file_sizes(os.path.join(src, file))
		else:	
			size += os.path.getsize(os.path.join(src, file))
	return size

def check_all_done(sec):
#       all_done = 0
#       try:
#               with open('/tmp/all_done_status') as f:
#                       all_done = int(f.readline())
#       except Exception:
#               #print("exception")
#               return 0
#       #print(all_done)
#       return all_done

	src = "/usr/local/dcp-tx/"
	size = sum_file_sizes(src)
	if (size):
		print("NOT All done")
		return 0
	else:
		print('all_done')
		return 1

def check_nas_status():
	return 0

def get_ap_state():
        apmode = subprocess.run([SCRIPTS_DIR+'is_running', 'hostapd'])
        if apmode.returncode == 0:
                print("AP mode active")
                return 1
        else:
                print("AP mode inactive")
                return 0

def check_gpsfix():
	try:
		with open('/tmp/gps.latlon', 'r') as gps:
			position = dict(line.strip().split(':') for line in gps)
	except Exception: #IOError #FileNotFoundError
		print("gps.latlon error")
		return 0
	else:
		if len(position) == 2:
			return 1
		else:
			return 0
		
if __name__ == "__main__":
	
	print ("Connecting port")
	ser = Serial(port, baudrate = 9600, timeout = 1)
	#ser.write(b'AT+QGPS=1\r\n')
	while(1):
		flags.b.gps_fix = check_gpsfix()
		
		flags.b.wds_status = check_wds_status()
		if flags.b.wds_status == 1 :
			flags.b.nas_status = 1
		else:
			flags.b.nas_status = check_nas_status()
		
		if get_ap_state():
			flags.b.ap_mode = 1
			flags.b.sta_mode = 0
		else:
			flags.b.ap_mode = 0
			flags.b.sta_mode = 1

		if sec % 5 == 0:
			flags.b.all_done = check_all_done(sec)
			if flags.b.gps_fix:
				print('GPS FIX OK')
			else:
				print('GPS FIX FAIL')
			if flags.b.wds_status:
				print('WDS OK')
			else:
				print('WDS FAIL')
			if flags.b.ap_mode:
				print('AP MODE')
			else:
				print('STA MODE')

		out = flags.asbyte.to_bytes(1, byteorder='little')
		#print(flags.asbyte)
		ser.write(out)
		#print(ser.read())
		sleep(1)
		sec = sec + 1
	ser.close()
