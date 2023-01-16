#! /usr/bin/python3
import sys
import selectors
import io
import struct
import binascii
import logging
import os
import shutil

from logging.handlers import RotatingFileHandler
from datetime import datetime

#MAX_LOG_BYTES = 2048
MAX_LOG_BYTES = 8000000

SRC_DIR ="/usr/local/data/Receiving/"
DST_DIR ="/usr/local/data/ToTransmit/"
ARCH_DIR = "/media/sd/archive/"

class Message:
	def __init__(self, selector, sock, addr, port, logger):
		self.selector = selector
		self.sock = sock
		self.addr = addr
		self._recv_buffer = b""
		self._send_buffer = b""
		self.request = None
		self.response_created = False
		self.parcel_num = 0
		self.package_len = 0
		self.content_type = 0
		self.logger = None
		self.imei = ""
		self.handler =  None
		self.port = port
		self.start_time = datetime.utcnow()
		self.main_logger = logger
		self.device_type = None
		self.fullPath = None
		self.fName = None

	def _set_selector_events_mask(self, mode):
		"""Set selector to listen for events : mode is 'r', 'w' or 'rw'."""
		if mode == "r":
			events = selectors.EVENT_READ
		elif mode == "w":
			events = selectors.EVENT_WRITE
		elif mode == "rw":
			events = selectors.EVENT_READ | selectors.EVENT_WRITE
		else:
			raise ValueError(f"Invalid events mask mode {repr(mode)}.")
		self.selector.modify(self.sock, events, data = self)


	def _read(self):
		try:
			data = self.sock.recv(4096)
		except BlockingIOError:
			# Resource temporarily unawailable (errno EWOULDBLOCK)
			pass
		except TimeoutError:
			raise RuntimeError("Peer ", self.addr, " closed")
		else:
			if data:
				self._recv_buffer += data
			else:
				self.main_logger.info("Peer closed")
				raise RuntimeError("Peer ", self.addr, " closed")

	def _write(self):
		if self._send_buffer:
			self.main_logger.info("sending %s to %s", repr(self._send_buffer), self.addr)
			try:
				sent = self.sock.send(self._send_buffer)
			except BlockingIOError:
				pass
			else:
				self._init_recv_process()
				self._set_selector_events_mask("r")

	def _init_recv_process(self):
		self.package_len = 0
		self.parcel_num = 0
		self.content_type = 0

	def process_events(self, mask):
		if mask & selectors.EVENT_READ:
			self.read();
		if mask & selectors.EVENT_WRITE:
			self.write();

#	def answer_crc_calc(self, data, len):
#		crc = 0
#		while len:
#			crc=crc+data
#


	def copy_file_to_archive(self, src_dir, file_name, dst_dir):
		utc = datetime.utcnow()
		base_name = os.path.join(dst_dir, file_name )
		try:
			shutil.make_archive(base_name, 'zip', src_dir, file_name)
		except:
			pass


	def process_header(self, device_type):
		self.main_logger.info("header received")
		utc = datetime.utcnow()
		timestamp = int(utc.timestamp())
#		utc_time = int(datetime.utcnow().timestamp())
		self.imei = str(struct.unpack('<Q',self._recv_buffer[2:10])[0])

		self.device_type = device_type
		self.logger = logging.getLogger(self.imei)
		self.logger.setLevel(logging.INFO)

		self.main_logger.info("imei: %s", self.imei)
		self.fName = self.imei + utc.strftime(".%y%m%d_%H%M%S")
		self.fullPath = SRC_DIR + device_type + '/' + self.fName
		open(self.fullPath, 'a').close()
		self.handler = RotatingFileHandler(self.fullPath, maxBytes = MAX_LOG_BYTES, backupCount=1) 
		self.logger.addHandler(self.handler)

		self._recv_buffer = self._recv_buffer[10:]
		answer = bytearray()
		answer.extend(b'\x7B')
		answer.extend(b'\x00') # or 04 it time presence
		answer.extend(b'\x00')

		# send time in aswer
#		answer.extend(int(timestamp).to_bytes(4,'little'))
#		answer.insert(3,(sum(answer[3:6])//256).to_bytes(1,"little")[0])

		answer.extend(b'\x7D')
		self._send_buffer += answer
		# Set selector to listen for write events, we're done reading.
		self._set_selector_events_mask("w")

	def process_package(self):
		self.main_logger.info("package received")
		if self.package_len == 0 and len(self._recv_buffer) >= 2:
			self.parcel_num = self._recv_buffer[1]
			self.package_len = 2
		if len(self._recv_buffer) > self.package_len:
			self.content_type = self._recv_buffer[self.package_len]
			self.main_logger.info("content_type %i", self.content_type)
			if self.content_type == 0x5D:
				# standart self.main_logger.info
				# over logging mechanism
				self.logger.info("data:" + self._recv_buffer[:self.package_len+1].hex())
				self._recv_buffer = self._recv_buffer[self.package_len+1:]

				answer = bytearray()
				answer.extend(b'\x7B')
				answer.extend(b'\x00')
				answer.extend(int(self.parcel_num).to_bytes(1,"little"))
				answer.extend(b'\x7D')
				self._send_buffer = answer
				self._set_selector_events_mask("w")
			elif self.content_type == 0x01 or self.content_type == 0x06 or self.content_type == 0x03 or self.content_type == 0x04 :
				if len(self._recv_buffer) > (self.package_len+2):
					self.package_len += struct.unpack('<H',self._recv_buffer[self.package_len+1 : self.package_len+3])[0] + 8
#					self.main_logger.info("package_len %i", self.package_len)
					if len(self._recv_buffer) > self.package_len:
						self.process_package()
			else:
				self.close()

	def read(self):
		self._read()

		if len(self._recv_buffer) >= 10:
			if self._recv_buffer[0] == 0xFF:
				for device in self.port['devices']:
					if (self._recv_buffer[1] == device['header']):
						self.process_header(device['type'])
						return
				self.main_logger.info("id not in _ids %i", self._recv_buffer[1] )
				self.close()
			elif self._recv_buffer[0] == 0x5B:
				self.process_package()
			else:
				self.main_logger.info("read: %s", self._recv_buffer[:10].hex())
				self.close()

	def write(self):
		self._write()

	def close(self):
		self.main_logger.info("closing connection to %s", self.addr)
		try:
			self.selector.unregister(self.sock)
		except Exception as e:
			self.main_logger.info("error: selector.unregister() exception for %s", f"{self.addr}:{repr(e)}")
		try:
			self.sock.close()

			handlers = self.logger.handlers[:]
			for handler in handlers:
				handler.close()
				self.logger.removeHandler(handler)

		except OSError as e:
			self.main_logger.info("error: socket.close() exception for %s", f"{self.addr}: {repr(e)}")
		finally:
			# Delete reference to socket object for garbage collection"
			self.sock = None
			if len(self.imei):
				utc = datetime.utcnow()
				#src = os.path.join(SRC_DIR + self.device_type, self.fName)
				self.copy_file_to_archive(os.path.join(SRC_DIR, self.device_type), self.fName, os.path.join(ARCH_DIR, self.device_type))
				dst = os.path.join(DST_DIR, self.device_type)
				shutil.move(self.fullPath, dst)
