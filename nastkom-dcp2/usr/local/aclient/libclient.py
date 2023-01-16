import os
import sys
import selectors
import io
import json
import struct
from datetime import datetime
from shutil import make_archive

import logging

#MIN_BYTES_TO_SEND = 16383
MIN_BYTES_TO_SEND = 768
#MIN_BYTES_TO_SEND = 512

MIN_PACKAGE_LEN = 12

class Message:
	def __init__(self, selector, sock, addr, src, file_name, serial, header, logger):
		self.selector = selector
		self.sock = sock
		self.addr = addr
		self.src = src
		self.file_name = file_name
		self._recv_buffer = b""
		self._send_buffer = b""
		self.request = None
		self.response_received = False
		self.poll_time = None
		self.poll_now = False
		self.hfile = None
		self.serial = serial
		self.header = header | 0x80
		self.logger = logger

	def _set_selector_events_mask(self, mode):
		"""Set selector to listen for events : mode is 'r', 'w' or 'rw'."""
		if mode == "r":
			events = selectors.EVENT_READ
		elif mode == "w":
			events = selectors.EVENT_WRITE
		elif mode == "rw":
			events = selectors.EVENT_READ | selectors.EVENT_WRITE
		else :
			raise ValueError(f"Invalid events mask mode {repr(mode)}.")
		self.selector.modify(self.sock, events, data = self)


	def _read(self):
		try:
			data = self.sock.recv(4096)
		except BlockingIOError:
			# Resource temporarily unawailable (errno EWOULDBLOCK)
			pass
		else :
			if data:
				self._recv_buffer += data
			else :
				raise RuntimeError("Peer ", self.addr, " closed")

	def _write(self):
		if self._send_buffer:
			self.logger.info("sending %s to %s", repr(self._send_buffer[:16]),  self.addr)
			try:
				sent = self.sock.send(self._send_buffer)
			except BlockingIOError:
				pass
			else :
				self._set_selector_events_mask("r")
		elif self.hfile == None:
			self.logger.info("Read header of %s", self.file_name)
			self.hfile = open(os.path.join(self.src, self.file_name), 'r')
			answer = bytearray()
			answer.extend(b'\xFF')
			answer.extend(self.header.to_bytes(1, 'big'))
			c_name = self.file_name.split('.')
			answer.extend(int(c_name[0]).to_bytes(8,'little'))
			answer.extend(self.serial)
			self._send_buffer = answer
			self.logger.info(answer)
			self._set_selector_events_mask("w")


	def process_line(self):
		line = self.hfile.readline()
		if line!='':
			linekv = line.split(':')
			if len(linekv) == 2:
				if linekv[0] == "data":
					try:
						package_ba = bytearray.fromhex(linekv[1])
					except Exception :
						return -1

					if ( package_ba[0] ==  0x5B  and package_ba[-1] == 0x5D ):
						package_len = len(package_ba)
						self.logger.info("package_len = %i", package_len)
						if package_len < MIN_PACKAGE_LEN:
							return -1
						package_len_calc = 2
						while package_len_calc < package_len-1 :
							self.logger.info("packet_type = %i",  package_ba[package_len_calc])
							if  package_ba[package_len_calc] != 0x01 and  package_ba[package_len_calc] != 0x03 and package_ba[package_len_calc] != 0x04:
								self.logger.info("packet_type_error")
								return -1
							package_len_calc += struct.unpack('<H', package_ba[package_len_calc+1:package_len_calc+3])[0]+ 8
							self.logger.info("package_len_calc = %i", package_len_calc)
						if package_len_calc != package_len-1:
							self.logger.info("len error")
							return -1

						if len(self._send_buffer) > 0 :
							self._send_buffer[-1:-1] = package_ba[2:]
							del(self._send_buffer[-1])
						else :
							self._send_buffer = package_ba

						if (len(self._send_buffer) > MIN_BYTES_TO_SEND ) :
							self._set_selector_events_mask("w")
							return 0
					else :
						self.logger.info("data line pre/postfix error")
				else :
					self.logger.info("data line has no 'data' mark")
			else :
				self.logger.info("data line has no semicolon")
			return -1
		else :
			self.logger.info("EOF %s", self.file_name)
			# TODO
			# if something in buffer -> comlete it and send
			#...
			if len(self._send_buffer):
				self._set_selector_events_mask("w")
				return 0

			self.close()
			os.remove(os.path.join(self.src, self.file_name))
			return 0

	def process_events(self, mask):
		if mask & selectors.EVENT_READ:
			self.read();
		if mask & selectors.EVENT_WRITE:
			self.write();

	def read(self):
		self._read()
		if len(self._recv_buffer) > 2:
			if self._recv_buffer[0] == 0x7B and self._recv_buffer[1] == 0x04:
				if len(self._recv_buffer) == 9:
					self.logger.info("Header Ack received")
					#self.logger.info(self._recv_buffer)
					self._recv_buffer = self._recv_buffer[9:]
					del(self._send_buffer[:])
					while True:
						if self.process_line()==0:
							break
			elif self._recv_buffer[0] == 0x7B and self._recv_buffer[1] == 0x00:
				if len(self._recv_buffer) == 4:
					self.logger.info("Data Ack received")
					self.logger.info(self._recv_buffer)
					self._recv_buffer = self._recv_buffer[4:]
					del(self._send_buffer[:])
					while True:
						if self.process_line() == 0:
							break
				else :
					self.logger.info("errorrrrr")

	def write(self):
		self._write()

	def close(self):
		self.logger.info("closing connection to %s", self.addr)
		try:
			self.selector.unregister(self.sock)
		except Exception as e:
			print(f"error: selector.unregister() exception for ", f"{self.addr}:{repr(e)}")
		try:
			self.sock.close()
		except OSError as e:
			print(f"error: socket.close() exception for ", f"{self.addr}: {repr(e)}")
		try:
			self.hfile.close()
		except Exception as e:
#			print("error: self.hfile.close() exception")
			pass

		finally:
			# Delete reference to socket object for garbage collection"
			self.sock = None
