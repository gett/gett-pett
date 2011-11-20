import httplib
import urllib
import inspect

class Request(object):
	PARTS = ['method', 'url', 'query', 'body', 'headers']

	def __init__(self, method = 'GET', url = '/', query = {}, body = '', headers = {}):
		self.method = method
		self.url = url
		self.query = query
		self.body = body
		self.headers = headers

	def __iter__(self):
		for name in Request.PARTS:
			yield self[name]

	def __getitem__(self, name):
		return getattr(self, name)

	def __setitem__(self, name, value):
		if not name in Request.PARTS:
			raise StandardError('Unknown part ' + name)

		setattr(self, name, value)

"""
	@property
	def method(self):
		return self._method

	@property
	def url(self):
		return self._url

	@property
	def query(self):
		return self._query

	@property
	def body(self):
		return self._body

	@property
	def headers(self):
		return self._headers
"""

"""
for name in Request.PARTS:
	def get(self):
		return self[name]

	setattr(Request, name, property(get))
"""
class Route(object):
	def __init__(self, *rw):
		self.read = 'read' in rw
		self.read_raw = 'read_raw' in rw
		self.write = 'write' in rw

	def __call__(self, f):
		def route(cls, *args, **kwargs):
			route = f(*args, **kwargs)

			#if not hasattr(cls, 'client'):
			#	if not hasattr(cls, 'host'):
			#		raise StandardError('Class variable "host" needs to be declared')
			
			#	cls.client = RestClient(cls.host)

			#return cls.routes.parse_route(route)
			request = cls.routes.parse_route(route)
			if self.write and not isinstance(request.body, str):
				#if hasattr(request.body, 'serialize'):
				#	request.body = request.body.serialize()
				#else:
				#	request.body = str(request.body)
				body = request.body
				if isinstance(body, dict):
					body = cls(body).serialize()

				request.body = body

			response = cls.client().request(*request)
			if self.read:
				return cls.parse(response)
			elif self.read_raw:
				return response
			else:
				return None

		return classmethod(route)

class ResourceRoutes(object):
	PARTS = Request.PARTS #['method', 'url', 'query', 'body', 'headers']
	METHODS = ['GET', 'POST', 'PUT', 'DELETE']

	def __init__(self, baseurl = '/', query = {}, headers = {}):
		if not baseurl.endswith('/'):
			baseurl = baseurl + '/'

		if not baseurl.startswith('/'):
			baseurl = '/' + baseurl

		self._baseurl = baseurl
		self._query = query
		self._headers = headers

		self._routes = {}

	def __call__(self, *rw):
		if len(rw) == 1 and hasattr(rw[0], '__call__'):
			route = Route()
			return route.__call__(rw[0])
		else:
			return Route(*rw)

	def parse_route(self, route):
		normalized = []

		if route is None:
			return
		elif isinstance(route, dict):
			route_list = []

			for part in ResourceRoutes.PARTS:
				route_list.append(route.get(part, None))

			route = route_list
		elif isinstance(route, str):
			route = [route]

		if isinstance(route, tuple) or isinstance(route, list):
			length = len(route)
			for i, part in enumerate(ResourceRoutes.PARTS):
				item = route[i] if i < length else None

				if part == 'method':
					item = item or 'GET'
					item = item.upper()
					if not item in ResourceRoutes.METHODS:
						raise StandardError('Unkown method type ' + item)
				elif part == 'url':
					item = item or self._baseurl
					if not item.startswith('http://') and not item.startswith('/'):
						item = self._baseurl + item
				elif part == 'query':
					item = item or {}
					item.update(self._query)
				elif part == 'body':
					item = item or ''
				elif part == 'headers':
					item = item or {}
					item.update(self._headers)

				normalized.append(item)
		else:
			raise StandardError('Unsupported argument type %s' % route)

		return Request(*normalized)

"""
class Route(object):
	def __init__(self, f):
		self._route = f

	def route(self, *args, **kwargs):
		return self._cls.routes.parse_route(self._route(*args, **kwargs))

	def __get__(self, instance, owner):
		self._cls = owner
		return self

	def __call__(self, *args, **kwargs):
		cls = self._cls
		route = self._route(*args, **kwargs)
		print route
			
		if not hasattr(cls, 'client'):
			if not hasattr(cls, 'host'):
				raise StandardError('Class variable host needs to be declared')
			
			cls.client = RestClient(cls.host)

		#return cls.routes.parse_route(route)
		resp = cls.client.request(*cls.routes.parse_route(route))
"""

"""
_actions = ['all', 'find', 'destroy']

for name in _actions:
	def decorator(self, f):
		#def func(cls, *args, **kwargs):
			#route = f(*args, **kwargs)
			#print route
			
			#if not hasattr(cls, 'client'):
			#	if not hasattr(cls, 'host'):
			#		raise StandardError('Class variable host needs to be declared')

			#	cls.client = RestClient(cls.host)

			#return cls.routes.parse_route(route)
			#return cls.client.request(*cls.routes.parse_route(route))

		#return classmethod(func)
		#return classmethod(Route(f))
		return Route(f)
	
	setattr(ResourceRoutes, name, decorator)
"""
class RestClient(object):
	def __init__(self, host):
		self._host = host

		#self._encoder = json.JSONEncoder()
		#self._decoder = json.JSONDecoder()

	#def authenticated_json_request(self, method, token, url = '/', body = ''):
	#	url = '%s?accesstoken=%s' % (url, token.accesstoken)
	#	return self.json_request(method, url, body)

	#def json_request(self, method, url = '/', body = ''):
	#	if isinstance(body, dict):
	#		body = self._encoder.encode(body)

	#	resp = self.request(method, url, body)
	#	return self._decoder.decode(resp)

	@property
	def host(self):
		return self._host

	def request(self, method = 'GET', url = '/', query = {}, body = '', headers = {}):
		#print(method, url, query, body, headers)
		http_connection = httplib.HTTPConnection(self._host)
		http_connection.request(method, url + '?' + urllib.urlencode(query), body, headers)

		resp = http_connection.getresponse()
		if resp.status not in range(200, 300):
			raise IOError('Unexpected status code received %s %s' % (resp.status, resp.reason))

		return resp.read()

class Base(object):
	# subclass needs to define 'host' as a class variable
	
	@classmethod
	def client(cls):
		if not hasattr(cls, '_rest_client'):
			cls._rest_client = RestClient(cls.host)

		return cls._rest_client

class RestRoutes(Base):
	routes = ResourceRoutes()

	@routes('read')
	def all():
		return ('GET')

	@routes('read')
	def find(id):
		return ('GET', '%s' % id)

	@routes('write', 'read')
	def create(attrs):
		return ('POST', None, None, attrs)

	@routes('write')
	def update(id, attrs):
		return ('PUT', '%s' % id, None, attrs)

	@routes
	def destroy(id):
		return ('DELETE', '%s' % id)

	def create(self, attrs = {}):
		self.attributes = attrs
		return self.__class__.create(self.attributes)

	def update(self, attrs = {}):
		self.attributes = attrs
		return self.__class__.update(self.attributes)

	def destroy(self):
		return self.__class__.destroy(self.id)

if __name__ == '__main__':
	class H(Base):
		host = 'open.ge.tt'
		routes = ResourceRoutes('/1/u')

	#print H.all()

	class Foo():
		@classmethod
		@property
		def client(cls):
			print(cls)

	print Foo.client
	Foo.client()

	#	for name in ['foo', 'bar']:
	#		eval('def ' + name + '(a,b): print(a,b)')

	#r = ResourceRoutes('/y/', { 'token' : '123134' })
	#print r.parse_route(['POST', 'g/t', { 'g' : '3' }, None, { 'what' : '3' }])
	
	#H.foo(1,2)

	#class F(H):
	#	h = 2

	#	@classmethod
	#	def t(cls):
	#		print cls.h

	#F.t()

	#class F():
	#	routes = ResourceRoutes()

	#	@routes.all
	#	def all(user, share):
	#		return ('GET', '/%s/%s' % (user, share))

	#print F.all
	#print F.all(4, 4)

	#f = F()
	#f.all(user, share) # returns all files
