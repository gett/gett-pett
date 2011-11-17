#
# 	User
#		Shares
#			Files
#

import httplib
import json
import time
"""
class Property(object):
	def __init__(self, opts = {}):
		self.__dict__.update(opts)

	def get(self, f):
		self.read = f
		return self

	def set(self, f):
		self.write = f
		return self

	def __get__(self, instance, owner):
		print(owner)
		if(self.read):
			return self.read(instance)
		else:
			return instance.read_attribute(self.name)

	def __set__(self, instance, value):
		if(self.write):
			self.write(instance, value)
		else:
			instance.write_attribute(self.name, value)

def property(type = None, required = True, key = None, write = None, read = None):
	return Property({ 'type' : type, 'required' : required, 'key' : key, 'write' : write, 'read' : read })


class Attribute(object):
	def __init__(self, name, prop):
		self.name = name
		self.prop = prop

	def __get__(self, instance, owner):
		if(self.prop.read):
			return self.prop.read(instance)
		else:
			return instance.read_attribute(self.name)

	def __set__(self, instance, value):
		if(self.prop.write):
			self.prop.write(instance, value)
		else:
			instance.write_attribute(self.name, value)


class Resource(object):
	@classmethod
	def properties(cls):
		if not hasattr(cls, '_properties'):
			cls._properties = [(name, p) for name, p in cls.__dict__.items() if isinstance(p, Property)]

			for name, p in cls._properties:
				p.name = name
		
		return cls._properties

	@classmethod
	def has_property(cls, name):
		return not cls.get_property(name) is None

	@classmethod
	def get_property(cls, name):
		return dict(cls.properties()).get(name, None)

	def __init__(self, attrs = {}):
		props = dict([(name, None) for name, p in self.properties()])
		props.update(attrs)
		self._properties = props

		#for name, prop in self.properties():
		#	setattr(self, name, Attribute(name, prop))

		#self.attributes = props

	def __getitem__(self, name):
		return self.read_attribute(name)

	def __setitem__(self, name, value):
		self.write_attribute(name, value)

	def valid(self):
		props = dict(self.properties())
		for name, value in self.attributes.items():
			prop = props[name]

			if prop.required:
				if not hasattr(self, name) or getattr(self, name) is None:
					return False
			
			if prop.type:
				if hasattr(self, name) and not isinstance(value, prop.type):
					return False

		return True

	def read_attribute(self, name):
		return self._properties[name]

	def write_attribute(self, name, value):
		self._properties[name] = value

	@__builtins__.property
	def attributes(self):
		#return dict([(name, value) for name, value in self._properties.items() if not value is None])

		attrs = []
		for name, p in self.properties():
			if hasattr(self, name):
				attrs.append((name, getattr(self, name)))

		return dict(attrs)
 
	@attributes.setter
	def attributes(self, attrs):
		if not isinstance(attrs, dict):
			return

		#attrs = dict([(name, value) for name, value in attrs.items() if self.has_property(name)])
		#self._properties.update(attrs)

		props = [n for n, p in self.properties()]		
		for name, value in attrs.items():
			if name in props:			
				setattr(self, name, value)
"""	

HOST = '192.168.2.171:20000'

class HttpClient(object):
	def __init__(self):
		self._encoder = json.JSONEncoder()
		self._decoder = json.JSONDecoder()

	def authenticated_json_request(self, method, token, url = '/', body = ''):
		url = '%s?accesstoken=%s' % (url, token.accesstoken)
		return self.json_request(method, url, body)

	def json_request(self, method, url = '/', body = ''):
		if isinstance(body, dict):
			body = self._encoder.encode(body)

		resp = self.request(method, url, body)
		return self._decoder.decode(resp)

	def request(self, method, url = '/', body = ''):
		http_connection = httplib.HTTPConnection(HOST)
		http_connection.request(method, url, body)

		resp = http_connection.getresponse()
		if resp.status not in range(200, 300):
			raise IOError('Unexpected status code received %s %s' % (resp.status, resp.reason))

		return resp.read()

class JsonResource(object):
	def __init__(self, http, baseurl):
		self._http = http
		self._baseurl = baseurl

	def all(self):
		return self._http.json_request('GET', self._url())

	def get(self, id):
		return self.json_request('GET', self._url(id))

	def create(self, body):
		return self.json_request('POST', self._url(), body)

	def update(self, id, body):
		return self.json_request('PUT', self._url(id), body)

	def destroy(self, id):
		return self.json_request('DELETE', self._url(id))

	def _url(self, id = ''):
		return self._baseurl + ('/%s' % id)

class Token(object):
	def __init__(self, attrs):
		self._accesstoken = attrs['accesstoken']
		self._refreshtoken = attrs['refreshtoken']
		self._expires = time.time() + attrs['expires']

	@property
	def accesstoken(self):
		return self._accesstoken

	@property
	def refreshtoken(self):
		return self._refreshtoken

	def expired(self):
		return self._expires <= time.time()

	def url(self, url):
		return url + '?accesstoken=' + self._accesstoken

class User(object):
	BASEURL = '/u/'

	# Accepts a dict containing secrettoken, email and password or
	# a refreshtoken string
	def __init__(self, credentials_or_refreshtoken):
		self._auth = credentials_or_refreshtoken
		if isinstance(credentials_or_refreshtoken, str):
			self._auth = { 'refreshtoken' : credentials_or_refreshtoken }

		self._http = HttpClient()
		#self._shares = 

		self._userid = None
		self._token = None

	@property
	def userid(self):
		return self._userid

	@property
	def token(self):
		if self._token is None or self._token.expired():
			self.authenticate()

		return self._token

	def authenticate(self):
		body = None
		if self._token:
			body = { 'refreshtoken' : self._token.refreshtoken }
		else:
			body = self._auth
			
		resp = self._http.json_request('POST', self.__class__.BASEURL + 'authenticate', body)

		self._userid = resp['userid']
		self._token = Token(resp)

		return self._token

	def shares(self):
		resp = self._http.authenticated_json_request('GET', self.token, Share.BASEURL)
		return [Share(r, self) for r in resp]

	def create_share(self, title = None):
		body = { 'title' : title } if title else ''
		resp = self._http.authenticated_json_request('POST', self.token, Share.BASEURL, body)

		share = Share(resp, self)
		return share

def attributes(obj, attrs, *names):
	# Oh noes...
	klass = obj.__class__
	for name in names:
		setattr(obj, '_' + name, attrs.get(name, None))
		setattr(klass, name, property(lambda self: getattr(self, '_' + name)))

	klass.attributes = lambda self: dict([(name, getattr(self, '_' + name)) for name in names])

class Share(object):
	BASEURL = '/s/'

	def __init__(self, attrs, user):
		attributes(self, attrs, 'sharename', 'readystate', 'created', 'updated', 'live', 'title')
		
		self._user = user

		self._files = []
		for file in attrs['files']:
			self._files.append(File(file, self, self._user))

	def __str__(self):
		return str(self.attributes())

	def __repr__(self):
		return str(self)

	@property
	def user(self):
		return self._user

	def files(self):
		return self._files

	def create_file(self, filepath):
		pass

	def update(self, attrs):
		pass

	def destroy(self):
		pass

class File(object):
	def __init__(self, attrs, share, filepath = None):
		attributes(self, attrs, 'created', 'updated', 'downloads', 'fileid', 'filename', 'downloadurl', 'readystate', 'size')

		self._share = share
		self._filepath = filepath

	def share(self):
		return self._share

	def filepath(self):
		return self._filepath

	def read(self):
		pass

	def write(self):
		pass

	def destroy(self):
		pass

if __name__ == '__main__':
	#http = HttpClient('')
	#print http.json_request('POST', '/u/authenticate', { 'secrettoken' : 'verysecret', 'email' : 'm@ge.tt', 'password' : 'qweqwe' })

	class H(Resource):
		f = property(type = str, required = True, key = 'f_g')
		g = property(type = int)

		#@f.get
		#def f(self):
		#	return self.f

		@f.get
		def f(self):
			return self.read_attribute('f') + ' you'

	h = H({ 'f' : 'hello', 'g' : 2 })
	print(h.attributes)
	h.f = 5

	#user = User({ 'secrettoken' : 'verysecret', 'email' : 'm@ge.tt', 'password' : 'qweqwe' })
	#print(user.shares())
	#print(user.create_share('My new awesome share'))

	#print user.token

	#class H():
	#	def __init__(self):
	#		attributes(self, { 'hello' : False, 'g' : 4 }, 'hello')

	#print(H().hello)
	#print(H().g)
