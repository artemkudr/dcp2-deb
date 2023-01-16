#!/usr/bin/env python3
import sys
import shutil
import os
import socket
import selectors
import types
import traceback
import json
import time
import libclient
import logging
from logging.handlers import RotatingFileHandler

LOG_MAX_SIZE = 16384
LOG_PATH = "/var/log/aclient_"

from collections import namedtuple

def getserial():
	# Extract serial from cpuinfo file
	cpuserial = "0000000000000000"
	try:
		f = open('/proc/cpuinfo','r')
		for line in f:
			if line[0:6]=='Serial':
				cpuserial = line[10:26]
		f.close()
	except:
		#cpuserial = "ERROR000000000"
		cpuserial = "0000000000000000"
	return cpuserial

def check_internet(host, port):
	try:
		s= socket.create_connection((host, port), 2)
		s.close()
		return True
	except:
		pass
	return False

def start_connections(host, port, header, src,  files, serial, logger):
	conn_id = 0
	addr = (host, port)
	for file in files:
		conn_id = conn_id + 1
		logger.info("starting connection %i to %s with %s", conn_id,  addr,  file)
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setblocking(False)
		""" # see cat /proc/sys/net/ipv4/tcp_syn_retries
		# value 5 means approx 120 seconds to raise exception for sock.connect
		# can use socket.settimeout() to reduce timeout of connection
		#               sock.settimeout(10)
		# but it cause another blocking mode  than setblocking()

		# scok.connect_ex return a value instead of raising exception
		# (but in case 'host not found' it can still raise exception)

		# the socket in nonblocking mode, so tre result of connection you will get
		# after select inidcates socket as writable. Use getsockopt to read the SO_ERROR
		# option at level SOL_SOCKET to determine whether connect() completed succesfully
		# (SO_ERROR is zero) or not (SO_ERROR is one of usual codes)
		# error codes listed int /usr/include/asm-generric/errno.h"""
		sock.connect_ex(addr)
		events = selectors.EVENT_READ | selectors.EVENT_WRITE
		message = libclient.Message(sel, sock, addr, src, file, serial, header, logger)
		sel.register(sock, events, data=message)

def create_directory(folder):
	try:
		os.mkdir(folder)
		logger.info("Directory %s created", folder)
	except:
		logger.info("Directory %s creation error", folder)
		pass


def proc(type, ip, port, header, logger):
	src_folder = "ToTransmit"
	dst_folder = "archive"

	""" create working directories on local disk eMMC"""
	src = os.path.join('/usr/local/data/', src_folder, type)
	create_directory(src)

	""" create working directories on external drive SD"""
	sd_dst = os.path.join('/media/sd/', dst_folder, type)
	create_directory(sd_dst)

	while True:
		dfiles =  os.listdir(src)
		files = []
		for file in dfiles:
			size = os.path.getsize(os.path.join(src, file))
			if size != 0:
				files.append(file)
		logger.info("ip:port =  %s:%i", ip, port)
		if check_internet(ip, port) == True:
			if len(files):
				logger.info("There are %i files to send", len(files))
				files = files[:10]
				start_connections(ip, port, header, src, files, serial, logger)

				while True:
					events = sel.select(timeout=1)
					for key, mask in events:
						message = key.data
						try:
							message.process_events(mask)
						except Exception:
							message.close()
					# Check for a socket being monitored to continue.
					if not sel.get_map():
						break
			else:
				logger.info("No files to send")
				time.sleep(30)
		else:
			logger.info("No internet connection")
			time.sleep(30)

if __name__ == "__main__":
	device_type = str(sys.argv[1])

	sel = selectors.DefaultSelector()

	serial_str = getserial()
	serial = int(serial_str,16).to_bytes(8, 'little')

	conf_file = "/usr/share/dcp-conf/dcp.conf"

	logger = logging.getLogger(device_type)

	handler = RotatingFileHandler(LOG_PATH+device_type, maxBytes = LOG_MAX_SIZE, backupCount=1)

	#change CRITICAL to INFO for debug
	logger.setLevel(logging.CRITICAL)

	formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s", "%Y-%m-%d %H:%M:%S")
	handler.setFormatter(formatter)


	logger.addHandler(handler)

	logger.info('Started')

	try:
		with open(conf_file, "r") as json_file:
			conf = json.load(json_file)

		#do not use defaults
		#if 'server_ip' not in conf:
			#conf['server_ip'] = '188.19.14.190'
			#with open(conf_file, "w") as json_file:
			#	json.dump(conf, json_file, indent=4)


		for port in conf['ports']:
			for device in port['devices']:
				if device['type'] == device_type:
					proc(device_type, conf['server_ip'], port['port'], device['header'], logger)
	except Exception as e:
		print(e)
		logger.info("dcp.conf file Error")
