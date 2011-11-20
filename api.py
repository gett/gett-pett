import rest.base as base
import json
import time
import os

HOST = 'open.ge.tt'
VERSION = 1

class Base(base.Resource):
	serialization = parsing = 'json'
	version = VERSION
	host = HOST

	@classmethod
	def gett_url(cls, url):
		if not url.startswith('/'):
			url = '/' + url

		return '/%s%s/' % (cls.version, url)

	@classmethod
	def gett_routes(cls, url):
		return base.ResourceRoutes(cls.gett_url(url), headers = { 'User-Agent' : 'gett-pett' })

class Token(object):
	def __init__(self, attrs):
		self._accesstoken = attrs['accesstoken']
		self._refreshtoken = attrs['refreshtoken']
		self._expires = time.time() + attrs['expires']

	def __str__(self):
		return self._accesstoken

	@property
	def accesstoken(self):
		return self._accesstoken

	@property
	def refreshtoken(self):
		return self._refreshtoken

	@property
	def attributes(self):
		return dict([(name, getattr(self, '_%s' % name)) for name in ['accesstoken', 'refreshtoken', 'expires']])

	def expired(self):
		return self._expires <= time.time()

def token(user_or_token):
	token = user_or_token.token if hasattr(user_or_token, 'token') else user_or_token
	return { 'accesstoken' : token }

class Gett(object):
	client = base.RestClient(HOST)

	# Accepts a dict containing secrettoken, email and password or
	# a refreshtoken string
	def __init__(self, credentials_or_refreshtoken):
		self._auth = credentials_or_refreshtoken
		if isinstance(credentials_or_refreshtoken, str):
			self._auth = { 'refreshtoken' : credentials_or_refreshtoken }

		self._token = None
		self._userid = None

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
			
		resp = self.client.request('POST', '/%s/u/authenticate' % VERSION, {}, json.dumps(body))
		resp = json.loads(resp)

		self._userid = resp['userid']
		self._token = Token(resp)

		return self._token

	def user(self):
		user = User()
		#user = User.get(self.token)
		user.gett_client = self

		return user

def sharename(share_or_sharename):
	return share_or_sharename.sharename if isinstance(share_or_sharename, Share) else share_or_sharename

class User(Base):
	routes = Base.gett_routes('u')

	userid = base.property(id = True)
	fullname = base.property(required = True)
	email = base.property(required = True)
	storage = base.property(required = True, type = int)

	gett_client = base.accessor(type = Gett)

	@routes('read')
	def get(toke):
		return ('GET', None, token(toke))

	@property
	def token(self):
		return self.gett_client.token

	def share(self, sharename):
		share = Share.find(self, sharename)
		share.user = self

		return share

	def shares(self):
		shares = Share.all(self)
		for share in shares: share.user = self

		return shares

	def create_share(self, attrs = {}):
		return Share.create(self, attrs)

	def update_share(self, share_or_sharename, attrs = {}):
		return Share.update(self, sharename(share_or_sharename), attrs)

	def destroy_share(self, share_or_sharename):
		Share.destroy(self, sharename(share_or_sharename))

class Share(Base):
	routes = Base.gett_routes('s')

	sharename = base.property(id = True)
	title = base.property()
	readystate = base.property(required = True)
	created = base.property(required = True, type = int)
	updated = base.property(required = True, type = int)
	live = base.property(required = True, type = bool)
	files = base.property(required = True, type = list)

	user = base.accessor(type = User)

	@routes('read')
	def all(user):
		return ('GET', None, token(user))

	@routes('read')
	def find(user, sharename):
		return ('GET', '%s' % sharename, token(user))

	@routes('read', 'write')
	def create(user, attrs = {}):
		return ('POST', None, token(user), attrs)

	@routes('read', 'write')
	def update(user, sharename, attrs = {}):
		return ('GET', '%s' % sharename, token(user), attrs)

	@routes
	def destroy(user, sharename):
		return ('DELETE', '%s' % sharename, token(user))

	@files.set
	def files(self, files):
		files = files or []
		self.write_attribute('files', [File(attr) for attr in files])

	def file(self, fileid):
		return File.find(self.user, self.sharename, fileid)

	def create_file(self, attrs = {}):
		return File.create(self.user, self.sharename, attrs)

	def destroy_file(self, file_or_fileid):
		fileid = file_or_fileid.fileid if isinstance(file_or_fileid, File) else file_or_fileid
		File.destroy(self.user, self.sharename, fileid)

	#def update(self, attrs = {}):
	#	return self.__class__.update(self.user, self.sharename, attrs)

	#def destroy(self):
	#	self.__class__.destroy(self.user, self.sharename)

class File(Base):
	routes = Base.gett_routes('f')

	fileid = base.property(id = True)
	filename = base.property(required = True)
	downloadurl = base.property(required = True)
	readystate = base.property(required = True)
	size = base.property(required = True, type = int)
	downloads = base.property(required = True)
	created = base.property(required = True, type = int)
	updated = base.property(required = True, type = int)

	share = base.accessor(type = Share)
	#filepath = base.accessor()

	@routes('read')
	def all(user, sharename):
		return ('GET', '%s' % s, token(user))

	@routes('read')
	def find(user, sharename, fileid):
		return ('GET', '%s/%s' % (sharename, fileid), token(user))

	@routes('read', 'write')
	def create(user, sharename, attrs = {}):
		return ('POST', '%s' % sharename, token(user), attrs)

	@routes
	def destroy(user, sharename, fileid):
		return ('DELETE', '%s/%s' % (sharename, fileid), token(user))

	def read(self, file):
		pass

	def write(self, file):
		pass

	#def destroy(self):
	#	pass

#if __name__ == '__main__':
	#access = 'a.test.uAdqxG7tSsP6qxLzVBXhUhJXcHGBSbL6Gck2m-fc.1321821220.7cdace3b62785c20d70fae861f3c7777984e1651'

gett = Gett({ 'apikey' : 'tfztwb6f0xaoo5hfrfi0ac57kokzkt9', 'email' : 'dettebrugestiltest@hotmail.com', 'password' : 'qweqwe' })
	#print gett.token
	#print gett.userid
	#print gett.user()

#	print gett.user().shares()

	#print User.client()

	#print User.get('a.test.a7KfN4mGtTydx.1321800365.0e133992e039b6874e700ae70b0a02267710f519')
	#print Share.all(access)

	#class H(object):
	#	def __init__(self):
	#		self.h = 1

	#	@property
	#	def g():
	#		pass

	#H().g = 6

	#print Share.create(access, { 'title' : 'cute' })

	#print Share.find('a.test.a7KfN4mGtTydx.1321800365.0e133992e039b6874e700ae70b0a02267710f519', '8peRL5A')
