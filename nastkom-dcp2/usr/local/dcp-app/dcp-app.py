import shutil
from flask import Flask, request, render_template, redirect, url_for, session, g, flash, jsonify, make_response #, send_from_directory
from functools import wraps

#from app import app
from app.forms import ServerWifiForm, AccessPointForm

import subprocess
import json
import datetime

app = Flask(__name__)

SCRIPTS_DIR = "/usr/local/scripts/"

#user = 'dcp'

# config for Flask modules ( Flask-WTF, for example )
#app.config.from_object('config')

# config
app.secret_key = 'secret'

# login required decorator
def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			return redirect(url_for('login'))
	return wrap

@app.route('/')
@login_required
def index():
	return redirect(url_for('settings'))

@app.route('/apply')
@login_required
def apply():
	try:
		with open('/usr/share/dcp-conf/dcp.conf', 'r') as json_conf:
			conf = json.load(json_conf)
	except Exception:
		print("dcp.conf file Error")
		shutil.copyfile("/usr/share/dcp-conf/dcp.conf.def", "/usr/share/dcp-conf/dcp.conf")
		exit()

	if "aps" not in conf:
		shutil.copyfile("/usr/share/dcp-conf/dcp.conf.def", "/usr/share/dcp-conf/dcp.conf")
		exit()

	aps = conf['aps']
	""" Rewrite wpa_supplicant.conf with actual data """
	wpa_cli = subprocess.run(['wpa_cli','-i','wlan0','remove_network', 'all'],capture_output=True)
	flash(str(wpa_cli.returncode))
	if wpa_cli.stdout == b'OK\n':
		for idx,  ap in enumerate(aps):
			wpa_cli = subprocess.run(['wpa_cli','-iwlan0','add_network'], capture_output=True)
			print(wpa_cli)
			wpa_cli = subprocess.run(['wpa_cli','-iwlan0','set_network', str(idx), 'ssid', '"'+ ap['ssid']+'"'], capture_output=True)
			print(wpa_cli)
			wpa_cli = subprocess.run(['wpa_cli','-iwlan0','set_network', str(idx), 'psk', '"'+ ap['password']+'"'], capture_output=True)
			print(wpa_cli)
			wpa_cli = subprocess.run(['wpa_cli','-iwlan0','set_network', str(idx), 'priority', '10'], capture_output=True)
			print(wpa_cli)
			wpa_cli = subprocess.run(['wpa_cli','-iwlan0','set_network', str(idx), 'id_str', '"client"'], capture_output=True)
			print(wpa_cli)

		wpa_cli = subprocess.run(['wpa_cli','-iwlan0','save_config'], capture_output=True)
		wpa_cli = subprocess.run(['wpa_cli','-iwlan0','reconfigure'], capture_output=True)

		if wpa_cli.stdout == b'OK\n':
			flash("APS reconfigured ")
			print("wpa_cli out ", wpa_cli.stdout)
	else:
		flash("APS error ")

#	""" Rewrite hostapd.conf with actual data """
#	with open('/usr/share/dcp-conf/hostapd.conf', 'r') as f:
#		d = dict(line.strip().split('=') for line in f)
#
#	if conf['ssid'] != d['ssid'] or conf['wpa_passphrase'] != d['wpa_passphrase']:
#		d['ssid'] = conf['ssid']
#		d['wpa_passphrase'] = conf['wpa_passphrase']
#		with open('/usr/share/dcp-conf/hostapd.conf', 'w') as f:
#			for k,v  in d.items():
#				f.write('%s=%s\n' % (k,v))
#	else:
#		# TODO make '$ touch /home/'+user+'/dcp-conf/hostapd.conf' maybe  inotifywait works with it and hostapd restarts
#		flash("Settings are the same")

	return redirect(url_for('settings'))

def getUptime():
	secs = "error"
	with open ('/proc/uptime' , 'r') as f:
		uptime = f.readline()
		secs = int(float(uptime.split()[0]))
		days = int(secs / 86400)
		secs = secs - days*86400
		hours = int(secs/3600)
		secs = secs - hours*3600
		minutes = int(secs/60)
		secs = secs - minutes*60
	return '{} Days  {} hours {} minutes {}  seconds'.format(days,hours,minutes,secs) 

def getDate():
	return datetime.datetime.now()

def get_ap_state():
#	apmode = 0
#	ret = "STA"
#
#	try:
#		with open('/tmp/apmode', 'r') as f:
#			apmode = int(f.readline())
#	except Exception:
#		ret =  "Unknown"
#
	proc = subprocess.run([SCRIPTS_DIR+'is_running', 'hostapd'])
	if proc.returncode == 0:
		ret = "AP"
		clients = subprocess.run(['iw dev wlan0 station dump | grep signal | wc -l'], shell=True, capture_output = True)
		if clients.returncode == 0:
			ret = f'AP[CLIENTS:{clients.stdout.decode("utf-8")}]'
	else:
		ret =  "STA"
		conn_state = subprocess.run(["wpa_cli -iwlan0 -p/var/run/wpa_supplicant status | grep wpa_state | awk -F[=] '{print $2}'"], shell=True, capture_output = True) 
		if conn_state.returncode == 0:
			if conn_state.stdout == b'COMPLETED\n':
				ret = "STA[CONNECTED]"
			else:
				ret = "STA[DISCONNECTED]"
	return ret

def getSocTemp():
	try:
		with open ('/sys/class/hwmon/hwmon0/temp1_input', 'r') as f:
			soctemp = f.readline()
	except Exception:
		scotemp = 'no data'
	return soctemp

def getLatLon():
	latlon = []
	try:
		with open('/tmp/gps.latlon','r') as f:
			latlon = f.readlines()
	except Exception:
		latlon = ["No fix", "No fix"]

	if len(latlon) != 2:
		latlon = ["No fix", "No fix"]

	return latlon

def getserial():
	# Extract serial from cpuinfo file
	cpuserial = "0000000000000000"
	try:
		f = open('/proc/cpuinfo','r')
		for line in f:
			if line[0:6]=='Serial':
				cpuserial = line[10:26]
		f.close()
	except Exception:
		#cpuserial = "ERROR000000000"
		cpuserial = "0000000000000000"
	return cpuserial

def getWWAN():
	ret = subprocess.run([SCRIPTS_DIR +'checknet.sh', 'wwan0'])
	if ret.returncode == 0:
		return "Internet OK"
	else:
		return "Internet FAIL"

def getVersion():
	#dpkg -s nastkom-dcp | grep -i version
	version = "error"
	#dpkg = subprocess.run(['dpkg', '-s', 'nastkom-dcp'], capture_output=True)
	#if dpkg.returncode == 0:
	#	grep = subprocess.run(['grep', '-i', 'version'], input=dpkg.stdout, capture_output=True, text=True)
	#	if grep.returncode == 0:
	#		version =  grep.stdout
	ret = subprocess.run(['dpkg -s nastkom-dcp2 | grep -i version'], shell=True, text=True, capture_output=True)
	if ret.returncode ==0:
		version = ret.stdout
	return version

@app.route('/info', methods=['POST','GET'])
@login_required
def info():
	version = getVersion()
	serial = getserial()
	latlon = getLatLon()
	soctemp = getSocTemp()
	uptime = getUptime()
	date = getDate()
	apmode = get_ap_state()
	wwan = getWWAN()
	return render_template('info.html', serial=serial, latlon=latlon, version=version, soctemp=soctemp, date=date, uptime=uptime, apmode=apmode, wwan=wwan)


@app.route('/settings', methods=['POST','GET'])
@login_required
def settings():
	try:
		with open('/usr/share/dcp-conf/dcp.conf', 'r') as json_conf:
			conf = json.load(json_conf)
	except Exception:
#		print ("Set default settings")
		shutil.copyfile("/usr/share/dcp-conf/dcp.conf.def", "/usr/share/dcp-conf/dcp.conf")
		exit()

#	if 'ssid' not in conf or 'wpa_passphrase' not in conf or 'server_ip' not in conf or 'server_port' not in conf or 'apn' not in conf:
#		shutil.copyfile("/usr/share/dcp-conf/dcp.conf.def", "/usr/share/dcp-conf/dcp.conf")
#		exit()

#	if 'device_type_1' not in conf or 'protocol_id_1' not in conf or 'server_ip_1' not in conf or 'server_port_1' not in conf:
#		conf['device_type_1'] = "A4"
#		conf['protocol_id_1'] = 22
#		conf['server_ip_1'] = "77.242.3.226"
#		conf['server_port_1'] = 85
#
#	if 'device_type_2' not in conf or 'protocol_id_2' not in conf or 'server_ip_2' not in conf or 'server_port_2' not in conf:
#		conf['device_type_2'] = "A5"
#		conf['protocol_id_2'] = 23
#		conf['server_ip_2'] = "77.242.3.226"
#		conf['server_port_2'] = 87
#
#	if 'device_type_3' not in conf or 'protocol_id_3' not in conf or 'server_ip_3' not in conf or 'server_port_3' not in conf:
#		conf['device_type_3'] = "UTPM"
#		conf['protocol_id_3'] = 25
#		conf['server_ip_3'] = "77.242.3.226"
#		conf['server_port_3'] = 87

	if 'server_ip' not in conf:
		conf['server_ip'] = "77.242.3.226"


	if 'autoUpdate' not in conf:
		autoUpdateRecord = {"autoUpdate":"false"}
		conf.update(autoUpdateRecord)
	
	if 'sleep_mode' not in conf:
		sleepModeRecord = {"sleep_mode":"false"}
		conf.update(sleepModeRecord)

	form = ServerWifiForm()
	ports = conf['ports']

	if request.method == 'GET':
		form.ssid.data = conf['ssid']
		form.password.data = conf['wpa_passphrase']
		#form.local_ip.data = conf['local_ip']
		#form.local_port.data = conf['local_port']

		form.server_ip.data = conf['server_ip']
		
#		form.device_type_1.data = conf['device_type_1']
#		form.server_ip_1.data = conf['server_ip_1']
#		form.server_port_1.data = conf['server_port_1']
#		form.protocol_id_1.data = conf['protocol_id_1']
#
#		form.device_type_2.data = conf['device_type_2']
#		form.server_ip_2.data = conf['server_ip_2']
#		form.server_port_2.data = conf['server_port_2']
#		form.protocol_id_2.data = conf['protocol_id_2']
#
#		form.device_type_3.data = conf['device_type_3']
#		form.server_ip_3.data = conf['server_ip_3']
#		form.server_port_3.data = conf['server_port_3']
#		form.protocol_id_3.data = conf['protocol_id_3']
#
		form.apn.data = conf['apn']
		form.apn_user.data = conf['apn_user']
		form.apn_pass.data = conf['apn_pass']
		
		form.autoUpdate.data = (conf['autoUpdate'] == "True")
		form.sleep_mode.data = (conf['sleep_mode'] == "True")

		return render_template('settings.html', form=form, ports = ports)
	else:
		if form.validate_on_submit():
			conf['ssid']=form.ssid.data
			conf['wpa_passphrase']=form.password.data

			#conf['local_ip']=form.local_ip.data
			#conf['local_port']=form.local_port.data

			
			
#			conf['device_type_1']=form.device_type_1.data
#			conf['device_type_2']=form.device_type_2.data
#			conf['device_type_3']=form.device_type_3.data
#
#			conf['server_ip_1']=form.server_ip_1.data
#			conf['server_port_1']=form.server_port_1.data
#			
#			conf['server_ip_2']=form.server_ip_2.data
#			conf['server_port_2']=form.server_port_2.data
#
#			conf['server_ip_3']=form.server_ip_3.data
#			conf['server_port_3']=form.server_port_3.data
#
#			conf['protocol_id_1'] = form.protocol_id_1.data
#			conf['protocol_id_2'] = form.protocol_id_2.data
#			conf['protocol_id_3'] = form.protocol_id_3.data
#
			conf['server_ip'] = form.server_ip.data
			
			conf['apn']=form.apn.data
			conf['apn_user']=form.apn_user.data
			conf['apn_pass']= form.apn_pass.data
			
			if (request.form.getlist('autoUpdate')):
				conf['autoUpdate']= "True"
			else:
				conf['autoUpdate']= "False"

			if (request.form.getlist('sleep_mode')):
				conf['sleep_mode']= "True"
			else:
				conf['sleep_mode']= "False"

			with open('/usr/share/dcp-conf/dcp.conf', 'w') as json_conf:
				json.dump(conf, json_conf, indent=2)
			flash("Settings saved in this session, but not applied yet!")
		return render_template('settings.html', form=form, ports = ports)


@app.route('/staticaps', methods=['GET'])
@app.route('/staticaps/<int:id>', methods=['GET','POST','DELETE', 'PUT'])
@login_required
def staticaps(id=None):
	try:
		with open('/usr/share/dcp-conf/dcp.conf', 'r') as json_conf:
			conf = json.load(json_conf)
	except Exception:
		shutil.copyfile("/usr/share/dcp-conf/dcp.conf.def", "/usr/share/dcp-conf/dcp.conf")
		exit()

	if 'aps' not in conf:
		shutil.copyfile("/usr/share/dcp-conf/dcp.conf.def", "/usr/share/dcp-conf/dcp.conf")
		exit()

	aps=conf['aps']

	form = AccessPointForm()

	if request.method == 'DELETE':
		if  id <= len(aps):
			aps.pop(id)
			with open('/usr/share/dcp-conf/dcp.conf','w') as json_conf:
				json.dump(conf, json_conf, indent=2)
			resp = {'success' : 'Ok'}
		return jsonify(resp)

	if request.method == 'POST' or request.method == 'PUT':
		if form.validate_on_submit():
			ap = {"name":form.name.data,
					"lat":form.lat.data,
					"lon":form.lon.data,
#					"ssid":form.ssid.data,
#					"password":form.password.data,
					"radius":form.radius.data}

			if request.method == 'POST':
				aps.append(ap)
			else : #PUT
				#if id < len(aps):
				aps[id] = ap

#			if id == 0 or  len(aps) == 0 :
#				aps.append(ap)
#			elif id < len(aps):
#				aps[id] = ap

			with open('/usr/share/dcp-conf/dcp.conf','w') as json_conf:
				json.dump(conf, json_conf, indent=2)

			resp = {'success' : 'Ok'}
		else:
			resp = {'errors': ['error validation',]}
		return  jsonify(resp)
	elif id != None and id < len(aps):
		return jsonify(aps[id])

	return render_template('staticaps.html', aps=aps, form=form)


@app.route('/login', methods=['POST','GET'])
def login():
	error = None
	if request.method == 'POST':
		if request.form['username'] != 'admin' or request.form['password'] != 'admin':
			error = 'Invalid username/password'
		else:
			session['logged_in'] = True
#			with open('/usr/share/dcp-conf/hostapd.conf', 'r') as f:
#				hostapd = dict(line.strip().split('=') for line in f)
#				with open('/usr/share/dcp-conf/dcp.conf','r') as json_conf:
#					conf = json.load(json_conf)
#					conf['ssid'] = hostapd['ssid']
#					conf['wpa_passphrase'] = hostapd['wpa_passphrase']
#				with open('/usr/share/dcp-conf/dcp.conf','w') as json_conf:
#					json.dump(conf, json_conf, indent=2)
			return redirect(url_for('settings'))

	return render_template('login.html', error=error)

@app.route('/update')
@login_required
def update():
	ret = subprocess.run([SCRIPTS_DIR +'autoupd.sh'])
	if ret.returncode == 0:
		flash("Update process ret = Device will be restarted")
	elif ret.returncode == 1 :
		flash("Update process ret = Firmware already updated")
	else :
		flash("Update process ret = Error")
		
#	return redirect(request.url)
	return redirect(url_for('settings'))

@app.route('/logout')
@login_required
def logout():
	session.pop('logged_in', None)
	flash('You are logged out.')
	return redirect(url_for('login'))

@app.route('/reboot',methods=['POST'])
@login_required
def reboot():
	subprocess.Popen(['reboot','now'])
	return redirect(url_for('login'))

if __name__ == "__name__":
	app.run(host="0.0.0.0")
