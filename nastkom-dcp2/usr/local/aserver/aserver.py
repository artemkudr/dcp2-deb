#!/usr/bin/python3
import sys
import shutil
import socket
import selectors
import types
import traceback
import libserver
import json
import time
import os
from threading import Thread
from datetime import datetime
from collections import namedtuple
import logging
from logging.handlers import RotatingFileHandler

LOG_MAX_SIZE = 16384

def set_keepalive_linux(sock, after_idle_sec=60, interval_sec=60, max_fails=10):
	"""Set TCP keepalive on an open socket.
	It activates after after_idle_sec of idleness,
	then sends a keepalive ping once every interval_sec,
	and closes the connection after max_fails failed ping ()
	"""
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
	sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
	sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
	sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)

def errorExit():
#	shutil.copyfile("/usr/share/dcp-conf/dcp.conf.def", "/usr/share/dcp-conf/dcp.conf")
	time.sleep(5)
	exit()

def copy_file_to_archive(src_dir, file_name, dst_dir):
	utc = datetime.utcnow()
	base_name = os.path.join(dst_dir, file_name + utc.strftime(".%y%m%d_%H%M%S") )
	try:
		shutil.make_archive(base_name, 'zip', src_dir, file_name)
	except:
		pass

def proc( ip, port, logger):
	logger.info('aserver for %s:%i', ip, port['port'])
	sel = selectors.DefaultSelector()
	lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Avoid bind() exception: OSError: [Errno 48] Address already in use
	lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	lsock.bind((ip, port['port']))
	lsock.listen()

	# TCP Keepalive Options
	set_keepalive_linux(lsock, after_idle_sec = 5, interval_sec = 3, max_fails = 3)

	logger.info('aserver listening on %s:%i', (ip, port['port']))
	lsock.setblocking(False)
	sel.register(lsock, selectors.EVENT_READ, data = None)


	def accept_wrapper(sock):
		conn, addr = sock.accept()
		logger.info('aserver accepted connection from %s', addr)
		conn.setblocking(False)
		message = libserver.Message(sel, conn, addr, port, logger)
		sel.register(conn, selectors.EVENT_READ, data = message)

	while True:
		events = sel.select(timeout = 0)
		for key, mask in events:
			if key.data is None:
				accept_wrapper(key.fileobj)
			else:
				message = key.data
				try:
					message.process_events(mask)
				except Exception:
					#logger.info('aserver main: error: exception for', f'{message.addr}\n{traceback.format_exc()}')
					message.close()

if __name__ == "__main__":
	port = int(sys.argv[1])
	conf_file = "/usr/share/dcp-conf/dcp.conf"
	SRC_DIR="/usr/local/data/Receiving/"
	DST_DIR="/usr/local/data/ToTransmit/"
	ARCH_DIR="/media/sd/archive/"
	utc = datetime.utcnow()

	logger = logging.getLogger(__name__)
	handler = RotatingFileHandler("/var/log/aserver_" + str(port), maxBytes = LOG_MAX_SIZE, backupCount=1)
	logger.setLevel(logging.CRITICAL)
	formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s", "%Y-%m-%d %H:%M:%S")
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	try:
		with open(conf_file, "r") as json_file:
			conf = json.load(json_file)
			if 'local_ip' not in conf :
				logger.info ("settings %i not set", )
			else:
				for p in conf['ports']:
					if p['port'] == port:
						for d in p['devices']:
							files = os.listdir(SRC_DIR + d['type'])
							for f in files:
								copy_file_to_archive( os.path.join(SRC_DIR, d['type']), f,  os.path.join(ARCH_DIR, d['type']))
								shutil.move( os.path.join(SRC_DIR, d['type'], f),  os.path.join(DST_DIR, d['type'], f))
						proc( conf['local_ip'], p, logger )
	except Exception as e:
		logger.info(e)
		errorExit()

	logger.info("Must not be excecuted")
