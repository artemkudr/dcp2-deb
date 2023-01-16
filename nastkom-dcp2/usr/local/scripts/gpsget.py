#! /usr/bin/python3
import io, subprocess
from datetime import datetime
from time import sleep
from serial import Serial

portwrite = "/dev/ttyUSB2"
port = "/dev/ttyUSB1"

def parseGPS(data):
#	lat = 1
#	lon = 1
	print ("raw:", data) #prints raw data
#	if data[0:6] == "$GPRMC":
	if data.startswith("$GPRMC"):
		sdata = data.split(",")
		if sdata[2] == 'V':
			with open("/tmp/gps.latlon","w") as f:
				f.write(" ")
			print ("no satellite data available")
	
			with open("/sys/class/leds/gps_fix/brightness", "w") as led:
				led.write("0")
			return
		print ("-----Parsing GPRMC-----")
		time = sdata[1][0:2] + ":" + sdata[1][2:4] + ":" + sdata[1][4:6]
		hour = int(sdata[1][0:2])
		minute = int(sdata[1][2:4])
		#time = sdata[1][0:2] + ":" + sdata[1][2:4] + ":" + sdata[1][4:6]
		lat = decode(sdata[3]) #latitude
		dirLat = sdata[4]      #latitude direction N/S
		lon = decode(sdata[5]) #longitute
		dirLon = sdata[6]      #longitude direction E/W
		speed = sdata[7]       #Speed in knots
		trCourse = sdata[8]    #True course
		day = sdata[9][0:2]  
		month =  sdata[9][2:4]
		Year =  sdata[9][4:6]          #date
		
		variation = sdata[10]  #Magnetic variation
		variationEW = sdata[11]#Magnetic variation E/W indicator
		positionMode = sdata[12]#N-no fix A-Autonomous D-differential
		#navStatusChecksum = sdata[13]
		#nc = navStatusChecksum.split("*")
		#navigationStatus = nc[0] #only for NMEA v4.10
		#checksum = nc[1]      #checksum
		#print ("time : %s, latitude : %s(%s), longitude : %s(%s), speed : %s, True Course : %s, Date : %s, Checksum : %s "%    (time,lat,dirLat,lon,dirLon,speed,trCourse,date,checksum))

		dt = datetime.utcnow()
		
		if dt.year != int(Year)+2000 or dt.month != int(month) or dt.day != int(day) or dt.hour != hour or dt.minute != minute: 
			date_and_time = Year + month + day + " " + time
			try:
				print("sync...", dt, date_and_time)
				settime = subprocess.run(['date', '+%Y%m%d%T', '-s', date_and_time], shell=False)		
			except :
				pass	
			
		with open("/tmp/gps.latlon","w") as f:
			f.write("lat:"+str(lat)+"\nlon:"+str(lon))
		with open("/sys/class/leds/gps_fix/brightness", "w") as led:
			led.write("1")
#	else:
#		print ("Printed data is",data[0:6])

def decode(coord):
	#Converts DDDMM.MMMMM -> DD deg MM.MMMMM min
	x = coord.split(".")
	head = x[0]
	tail = x[1]
	deg = head[0:-2]
	min = head[-2:]
	min=min+'.'+tail
	return int(deg) + float(min)/60
	#return deg + " deg " + min + "." + tail + " min"
	
tick = 0
print ("Connecting port")
serw = Serial(portwrite, baudrate = 115200, timeout = 1)
serw.write(b'AT+QGPS=1\r\n')
serw.close()
sleep(1)

print ("Receiving GPS data")
ser = Serial(port, baudrate = 115200, timeout = 0.5)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
while True:
	data = sio.readline()
	parseGPS(data )
	tick = tick + 1
