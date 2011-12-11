import time
import urllib
import urllib2
import urlparse
import json
import mimetypes
import os
import httplib
import types
import datetime

import rest

# TODO
# investigate /sharename/fileid/upload hangs
# make setup.py
# update README.md
# better error handling?

def _api_url(*url):
	if len(url) == 1:
		url = url[0]

	if isinstance(url, tuple) or isinstance(url, list):
		ids = url[1:]
		url = url[0] % ids

	return 'https://open.ge.tt/1/%s' % url

def _request(url, token = None):
	url = _api_url(url)

	query = {}
	if token:
		if hasattr(token, 'token'):
			token = token.token

		query['accesstoken'] = token

	url = url + '?' + urllib.urlencode(query)

	req = urllib2.Request(url)
	req.add_header('User-Aget', 'pett-gett')

	print url

	return req

def _response(req):
	try:
		resp = urllib2.urlopen(req)
	except urllib2.HTTPError as err:
		print 'error', err.read() #, err.info(), err.code
		raise

	headers = resp.info()

	if headers['Content-Type'] == 'application/json':
		return json.loads(resp.read())

	return resp

def _get(url, token = None):
	req = _request(url, token)
	return _response(req)

def _post(url, token = None, body = None):
	req = _request(url, token)

	if isinstance(body, dict):
		body = json.dumps(body)

	if not body is None:
		req.add_header('Content-Type', 'application/json')

	req.add_data(body or '')

	return _response(req)

class Token(rest.Properties):
	accesstoken = rest.property()
	refreshtoken = rest.property()
	expires = rest.property()

	def __str__(self):
		return self.accesstoken

	@expires.set
	def expires(self, expires):
		self.write_attribute('expires', time.time() + expires)

	def expired(self):
		return self.expires <= time.time()

class User(rest.Properties):
	class Storage(rest.Properties):
		used = rest.property()
		limit = rest.property()
		extra = rest.property()

		@classmethod
		def get(cls, user):
			user = _get(('users/me'), user)
			return cls(user['storage'])

		def limit_exceeded(self):
			return self.left() <= 0

		def left(self):
			return self.limit - self.used

	userid = rest.property(id = True)
	fullname = rest.property()
	email = rest.property()
	storage = rest.property()

	@classmethod
	def login(cls, credentials_or_refreshtoken):
		auth = credentials_or_refreshtoken

		if isinstance(credentials_or_refreshtoken, str):
			auth = { 'refreshtoken' : credentials_or_refreshtoken }
		elif isinstance(credentials_or_refreshtoken, Token):
			auth = { 'refreshtoken' : credentials_or_refreshtoken.refreshtoken }

		attrs = _post('users/login', body = auth)
		user = cls(attrs['user'])
		user.token = Token(attrs)

		return user

	@classmethod
	def login_token(cls, credentials_or_refreshtoken):
		user = cls.login(credentials_or_refreshtoken)
		return user.token

	@storage.set
	def storage(self, value):
		if isinstance(value, dict):
			value = User.Storage(value)

		self.write_attribute('storage', value)

	@property
	def token(self):
		if self._token.expired():
			self.refresh_token()

		return self._token

	@token.setter
	def token(self, token):
		self._token = token

	def refresh_token(self):
		self._token = self.login_token(self._token)
		return self._token

	def get_storage(self):
		self.storage = User.Storage.get(self)
		return self.storage

	def shares(self):
		shares = Share.all(self)
		
		for share in shares:
			share.user = self

		return shares

	def share(self, sharename):
		share = Share.find(sharename)
		share.user = self

		return share

	def create_share(self, attrs = {}):
		share = Share.create(self, attrs)
		share.user = self

		return share

	def update_share(self, sharename, attrs = {}):
		share = Share.update(self, sharename, attrs)
		share.user = self

		return share

	def destroy_share(self, sharename):
		Share.destroy(self, sharename)

def _created(self, value):
	self.write_attribute('created', datetime.datetime.fromtimestamp(value))

def _update_share(self, attrs = {}):
	share = self.__class__.update(self.user, self.sharename, attrs)
	self.attributes = share.attributes

	return self

def _destroy_share(self):
	self.__class__.destroy(self.user, self.sharename)

class Share(rest.Properties):
	def __new__(cls, *args, **kwargs):
		instance = super(Share, cls).__new__(cls, *args, **kwargs)

		instance.update = types.MethodType(_update_share, instance, cls)
		instance.destroy = types.MethodType(_destroy_share, instance, cls)

		return instance

	sharename = rest.property(id = True)
	title = rest.property()
	readystate = rest.property()
	created = rest.property(write = _created)
	live = rest.property()
	files = rest.property()

	@classmethod
	def all(cls, token):
		shares = _get('shares', token = token)
		return [cls(s) for s in shares]

	@classmethod
	def find(cls, sharename):
		share = _get(('shares/%s', sharename))
		return cls(share)

	@classmethod
	def create(cls, token, attrs = {}):
		share = _post('shares/create', token, attrs)
		return cls(share)

	@classmethod
	def update(cls, token, sharename, attrs = {}):
		share = _post(('shares/%s/update', sharename), token, attrs)
		return cls(share)

	@classmethod
	def destroy(cls, token, sharename):
		_post(('shares/%s/destroy', sharename), token)

	@files.set
	def files(self, value):
		value = value or []
		self.write_attribute('files', [File(f) for f in value])

	@property
	def user(self):
		return self._user

	@user.setter
	def user(self, user):
		self._user = user

	def file(self, fileid):
		file = File.find(self.sharename, fileid)
		file.share = self

		return file

	def create_file(self, attrs = {}):
		file = File.create(self.user, self.sharename, attrs)
		file.share = self

		return file

	def destroy_file(self, fileid):
		File.destroy(self.user, self.sharename, fileid)

	def blob_file(self, fileid):
		file = self.file(fileid)
		return file.blob()

	def write_file(self, fileid, file):
		file = self.file(fileid)
		file.write(file)

	def upload_file(self, filepath):
		return File.upload_file(self.user, self.sharename, filepath)

def _destroy_file(self):
	share = self.share
	self.__class__.destroy(share.user, share.sharename, self.fileid)

class File(rest.Properties):
	def __new__(cls, *args, **kwargs):
		instance = super(File, cls).__new__(cls, *args, **kwargs)
		instance.destroy = types.MethodType(_destroy_file, instance, cls)

		return instance

	class Upload(rest.Properties):
		puturl = rest.property()
		posturl = rest.property()

		@classmethod
		def get(cls, token, sharename, fileid):
			upload = _get(('files/%s/%s/upload', sharename, fileid), token)
			return cls(upload)

		def putpath(self):
			url = urlparse.urlparse(self.puturl)
			return url.path + '?' + url.query

		def postpath(self):
			url = urlparse.urlparse(self.posturl)
			return url.path + '?' + url.query

	fileid = rest.property(id = True)
	filename = rest.property()
	sharename = rest.property()
	downloadurl = rest.property()
	readystate = rest.property()
	size = rest.property()
	downloads = rest.property()
	created = rest.property(write = _created)
	upload = rest.property()

	@classmethod
	def find(cls, sharename, fileid):
		file = _get(('files/%s/%s', sharename, fileid))
		return cls(file)

	@classmethod
	def create(cls, token, sharename, attrs = {}):
		file = _post(('files/%s/create', sharename), token, attrs)
		return cls(file)

	@classmethod
	def destroy(cls, token, sharename, fileid):
		_post(('files/%s/%s/destroy', sharename, fileid), token)

	@classmethod
	def upload_file(cls, token, sharename, filepath):
		with open(filepath, 'rb') as f:
			mime, enc = mimetypes.guess_type(filepath)
			file = cls.create(token, sharename, { 'filename' : os.path.basename(filepath) })

			file.write(f, mime)

			return file

	@upload.set
	def upload(self, value):
		if value:
			if isinstance(value, dict):
				value = File.Upload(value)

			self.write_attribute('upload', value)

	@upload.get
	def upload(self):
		upload = self.read_attribute('upload')

		if upload is None:
			share = self.share
			upload = File.Upload.get(share.user, share.sharename, self.fileid)

			self.upload = upload

		return upload

	@property
	def share(self):
		return self._share

	@share.setter
	def share(self, share):
		self.sharename = share.sharename
		self._share = share

	def write(self, file, mimetype = None):
		headers =  { 'User-Agent' : 'gett-pett' }

		if mimetype:
			headers['Content-Type'] = mimetype

		conn = httplib.HTTPConnection('blobs.ge.tt')
		conn.request('PUT', self.upload.putpath(), file, headers)

		resp = conn.getresponse()

		if resp.status not in range(200, 300):
			raise urllib2.HTTPError(self.upload.puturl, resp.status, resp.reason, dict(resp.getheaders()), resp)
			#raise urllib2.URLError('Unexpected status code received %s %s' % (resp.status, resp.reason))

		self.readystate = 'uploaded'

	def blob(self):
		if self.readystate in ['uploading', 'uploaded'] or (self.readystate == 'remote' and self.share.live):
			return _get(('files/%s/%s/blob', self.share.sharename, self.fileid))
		else:
			raise StandardError("Wrong state, can't read file")

	def thumb(self):
		if self.readystate == 'uploaded':
			return _get(('files/%s/%s/blob/thumb', self.share.sharename, self.fileid))
		else:
			raise StandardError("Wrong state, can't retreive image thumb")

	def scale(self, width, height):
		if self.readystate == 'uploaded':
			return _get(('files/%s/%s/blob/scale?size=%sx%s', self.share.sharename, self.fileid, width, height))
		else:
			raise StandardError("Wrong state, can't retreive scaled image")
	