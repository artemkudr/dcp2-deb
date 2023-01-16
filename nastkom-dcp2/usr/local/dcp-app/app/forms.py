from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Length, Regexp, IPAddress, NumberRange

class ServerWifiForm(FlaskForm):
	ssid = StringField('SSID', validators=[DataRequired(), Length(min=4, max=16, message="4-16 characters available"), Regexp("^[A-Za-z0-9_-]{4,16}$", message="'A-Z' 'a-z' '0-9' '_' '-' available")], render_kw={'autofocus':True})
	password = StringField('Password', validators=[DataRequired(), Length(min=4, max=16, message="8-16 characters available"), Regexp("^[A-Za-z0-9@$!%*#?&]{8,16}$", message="'A-Z' 'a-z' '0-9' !@#$%^&* available")])


#	device_type_1 = StringField('Device Type 1', validators=[DataRequired()], render_kw={'readonly':1})
#	server_port_1 = IntegerField('Server Port 1', validators=[DataRequired()], render_kw={'size':5})
#	server_ip_1 = StringField('Server IP 1', validators=[DataRequired(), IPAddress(message='must be IP string')])
	
#	device_type_2 = StringField('Device Type 2', validators=[DataRequired()], render_kw={'readonly':1})
#	server_port_2 = IntegerField('Server Port 2', validators=[DataRequired()], render_kw={'size':5})
#	server_ip_2 = StringField('Server IP 2', validators=[DataRequired(), IPAddress(message='must be IP string')])

#	device_type_3 = StringField('Device Type 3', validators=[DataRequired()], render_kw={'readonly':1})
#	server_port_3 = IntegerField('Server Port 3', validators=[DataRequired()], render_kw={'size':5})
#	server_ip_3 = StringField('Server IP 3', validators=[DataRequired(), IPAddress(message='must be IP string')])

#	protocol_id_1 = IntegerField('Protocol Id 1', validators=[DataRequired()], render_kw={'size':2})
#	protocol_id_2 = IntegerField('Protocol Id 2', validators=[DataRequired()], render_kw={'size':2})
#	protocol_id_3 = IntegerField('Protocol Id 3', validators=[DataRequired()], render_kw={'size':2})

#	local_ip = StringField('Local IP', validators=[DataRequired(), IPAddress(message='must be IP string')], render_kw={'readonly':1} )
#	local_port = IntegerField('Local Port', validators=[DataRequired(),  NumberRange(min=81, max=60999, message="availale range is 81-60999")], render_kw={'size':5, 'readonly':1})
	server_ip = StringField('Server IP', validators=[DataRequired(), IPAddress(message='must be IP string')])
#	server_port = IntegerField('Server Port', validators=[DataRequired()], render_kw={'size':5})

	apn = StringField('APN')
	apn_user = StringField('User')
	apn_pass = StringField('Password')

	sleep_mode = BooleanField('Enable Sleep mode without ext power')

	autoUpdate = BooleanField('Check for updates every 6 hours', default="False")

class AccessPointForm(FlaskForm):
	# lat ^(\+|-)?(?:90(?:(?:\.0{1,6})?)|(?:[0-9]|[1-8][0-9])(?:(?:\.[0-9]{1,6})?))$
	# lon ^(\+|-)?(?:180(?:(?:\.0{1,6})?)|(?:[0-9]|[1-9][0-9]|1[0-7][0-9])(?:(?:\.[0-9]{1,6})?))$
	id = HiddenField('id')
	name = StringField('Name', validators=[DataRequired(), Length(min=3, max=16), Regexp("^[A-Za-z0-9]{3,16}$")], render_kw={'placeholder':'Name'})
	lat = StringField('Lat', validators=[DataRequired(), Regexp("^(\+|-)?(?:90(?:(?:\.0{1,6})?)|(?:[0-9]|[1-8][0-9])(?:(?:\.[0-9]{1,9})?))$")], render_kw={'autofocus':True, 'placeholder':'Latitude'})
	lon = StringField('Lon', validators=[DataRequired(), Regexp("^(\+|-)?(?:180(?:(?:\.0{1,6})?)|(?:[0-9]|[1-9][0-9]|1[0-7][0-9])(?:(?:\.[0-9]{1,9})?))$")], render_kw={'placeholder':'Longitude'})
#	ssid = StringField('SSID', validators=[DataRequired(), Length(min=4, max=16), Regexp("^[A-Za-z0-9_-]{4,16}$")], render_kw={'placeholder':'SSID'})
#	password = StringField('Password', validators=[DataRequired(), Length(min=8, max=16), Regexp("^[A-Za-z0-9@$!%*#?&]{8,16}$")], render_kw={'placeholder':'Password'})
	radius = IntegerField('Radius', validators=[DataRequired(), NumberRange(min=1, max=100, message="Radius range is 1-100")], render_kw={'size':3,'placeholder':'Radius(km)'})


