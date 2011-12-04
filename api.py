import rest.base as base
import json
import time
import os
import mimetypes
import urlparse

PROTOCOL = 'https'
API_HOST = 'open.ge.tt'
BLOB_HOST = 'blobs.ge.tt'
VERSION = 1

RESOURCE_NAMES = {
	'user' : 'users',
	'share' : 'shares',
	'file' : 'files',
	'blob' : 'blobs'
}

def api_url(what, id = None, action = None):
	id = ('%s/' % id) if id else ''
	return '/%s/%s/%s%s' % (VERSION, RESOURCE_NAMES[what], id, action or '')

def api_routes(what):
	return base.ResourceRoutes(api_url(what), headers = { 'User-Agent' : 'gett-pett' })

class Base(base.Resource):
	serialization = parsing = 'json'
	host = API_HOST
	protocol = PROTOCOL

class Token(base.Properties):
	accesstoken = base.property()
	refreshtoken = base.property()
	expires = base.property(type = int)

	def __str__(self):
		return self.accesstoken

	@expires.set
	def expires(self, expires):
		self.write_attribute('expires', time.time() + expires)

	def expired(self):
		return self.expires <= time.time()

def token(user_or_token):
	token = user_or_token.token if hasattr(user_or_token, 'token') else user_or_token
	return { 'accesstoken' : token }

class Gett(object):
	client = base.RestClient(API_HOST, PROTOCOL)

	# Accepts a dict containing secrettoken, email and password or
	# a refreshtoken string
	def __init__(self, credentials_or_refreshtoken):
		self._auth = credentials_or_refreshtoken
		if isinstance(credentials_or_refreshtoken, str):
			self._auth = { 'refreshtoken' : credentials_or_refreshtoken }

		self._token = None
		self._user = None

	@property
	def token(self):
		if self._token is None or self._token.expired():
			self.login()

		return self._token

	def login(self):
		body = None
		if self._token:
			body = { 'refreshtoken' : self._token.refreshtoken }
		else:
			body = self._auth
			
		resp = self.client.request('POST', api_url('user', action = 'login'), {}, json.dumps(body), { 'User-Agent' : 'gett-pett' })
		resp = json.loads(resp)

		self._user = User(resp['user'])
		self._user.gett_client = self

		self._token = Token(resp)

		return self._token

	def user(self):
		if self._user is None:
			self.login()

		return self._user

def sharename(share_or_sharename):
	return share_or_sharename.sharename if isinstance(share_or_sharename, Share) else share_or_sharename

class User(Base):
	routes = api_routes('user')

	class Storage(base.Properties):
		used = base.property(type = int)
		limit = base.property(type = int)
		extra = base.property(type = int)

		def limit_exceeded(self):
			return self.left() <= 0

		def left(self):
			return self.limit - self.used

	userid = base.property(id = True)
	fullname = base.property()
	email = base.property()
	storage = base.property(type = Storage)

	gett_client = base.accessor()

	@routes('read')
	def get(toke):
		return ('GET', 'me', token(toke))

	@property
	def token(self):
		return self.gett_client.token

	#@storage.set
	#def storage(self, value):
	#	self.write_attribute('storage', User.Storage(value))

	def get_storage(self):
		user = self.get(gett_client.token)
		self.storage = user.storage

		return self.storage

	def share(self, sharename):
		share = Share.find(self, sharename)
		share.user = self

		return share

	def shares(self):
		shares = Share.all(self)
		for share in shares: share.user = self

		return shares

	def create_share(self, attrs = {}):
		share = Share.create(self, attrs)
		share.user = self

		return share

	def update_share(self, share_or_sharename, attrs = {}):
		share = Share.update(self, sharename(share_or_sharename), attrs)
		share.user = self

		return share

	def destroy_share(self, share_or_sharename):
		Share.destroy(self, sharename(share_or_sharename))

class File(Base):
	routes = api_routes('file')
	blobs = base.RestClient(BLOB_HOST)

	class Upload(Base):
		routes = api_routes('file')

		puturl = base.property()
		posturl = base.property()

		@routes('read')
		def get(self, user, sharename, fileid):
			return ('GET', '%s/%s' % (sharename, fileid), token(user))

		def putpath(self):
			url = urlparse.urlparse(self.puturl)
			return url.path + '?' + url.query

		def postpath(self):
			url = urlparse.urlparse(self.posturl)
			return url.path + '?' + url.query

	fileid = base.property(id = True)
	filename = base.property()
	sharename = base.property()
	downloadurl = base.property()
	#puturl = base.property()
	#posturl = base.property()
	readystate = base.property()
	size = base.property(type = int)
	downloads = base.property()
	created = base.property(type = int)
	updated = base.property(type = int)
	upload = base.property(type = Upload)

	share = base.accessor()

	@routes('read')
	def find(user, sharename, fileid):
		return ('GET', '%s/%s' % (sharename, fileid))

	@routes('read', 'write')
	def create(user, sharename, attrs = {}):
		return ('POST', '%s/create' % sharename, token(user), attrs)

	@routes
	def destroy(user, sharename, fileid):
		return ('POST', '%s/%s/destroy' % (sharename, fileid), token(user))

	@classmethod
	def upload(cls, user, sharename, filepath):
		filename = os.path.basename(filepath)
		f = cls.create(user, sharename, { 'filename' : filename })

		f.write(filepath)

		return f

	@share.set
	def share(self, share):
		self.sharename = share.sharename
		self._share = share

	#@uploadurls.set
	#def uploadurls(self, value):
	#	self.write_attribute('uploadurls', File.Upload(value))

	#def putpath(self):
	#	url = urlparse.urlparse(self.puturl)
	#	return url.path + '?' + url.query

	def read(self, filepath):
		if self.readystate in ['uploading', 'uploaded'] or (self.readystate == 'remote' and self.share.live):
			pass
		else:
			raise StandardError("Wrong state, can't download file")

	def write(self, filepath):
		with open(filepath, 'rb') as f:
			type, enc = mimetypes.guess_type(filepath)
			#type = 'text/plain'
			self.blobs.request('PUT', self.upload.putpath(), {}, f, { 'Content-Type' : (type or 'application/octet-stream') })

	#def destroy(self):
	#	pass

class Share(Base):
	routes = api_routes('share')

	sharename = base.property(id = True)
	title = base.property()
	readystate = base.property()
	created = base.property(type = int)
	updated = base.property(type = int)
	live = base.property(type = bool)
	files = base.property(type = [File])

	user = base.accessor()

	@routes('read')
	def all(user):
		return ('GET', None, token(user))

	@routes('read')
	def find(user, sharename):
		return ('GET', '%s' % sharename)

	@routes('read', 'write')
	def create(user, attrs = {}):
		return ('POST', 'create', token(user), attrs)

	@routes('read', 'write')
	def update(user, sharename, attrs = {}):
		return ('POST', '%s/update' % sharename, token(user), attrs)

	@routes
	def destroy(user, sharename):
		return ('POST', '%s/destroy' % sharename, token(user))

	#@files.set
	#def files(self, files):
	#	files = files or []
	#	self.write_attribute('files', [File(attr) for attr in files])

	def file(self, fileid):
		file = File.find(self.user, self.sharename, fileid)
		file.share = self

		#print file

		return file

	def create_file(self, attrs = {}):
		file = File.create(self.user, self.sharename, attrs)
		file.share = self

		return file

	def upload_file(self, filepath):
		file = File.upload(self.user, self.sharename, filepath)
		file.share = self
		#file.share = self

		return file

	def destroy_file(self, file_or_fileid):
		fileid = file_or_fileid.fileid if isinstance(file_or_fileid, File) else file_or_fileid
		File.destroy(self.user, self.sharename, fileid)

	#def update(self, attrs = {}):
	#	return self.__class__.update(self.user, self.sharename, attrs)

	#def destroy(self):
	#	self.__class__.destroy(self.user, self.sharename)

if __name__ == '__main__':
	#access = 'a.test.uAdqxG7tSsP6qxLzVBXhUhJXcHGBSbL6Gck2m-fc.1321821220.7cdace3b62785c20d70fae861f3c7777984e1651'

	import time

	gett = Gett({ 'apikey' : 'dflhj4hiurtwhljdfshou45hudfsku43hkgdsfhkgrtdfg', 'email' : 'dettebrugestiltest@hotmail.com', 'password' : 'foobar' })
	print gett.user().create_share({ 'title' : 'MY SHARE DO NOT TOUCH %s' % time.time() }).upload_file('README.md')

	#print User.get(gett.token)
