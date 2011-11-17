import http
import urllib

class ResourceRoutes(object):
	def __init__(self, baseurl, query = {}, headers = {}):
		pass

	def all(self, f):
		pass

	def get(self, f):
		pass

_actions = ['all', 'find', 'create', 'update', 'destroy']
for name in _actions:
	def decorator(self, f):
		def func(cls, *args):
			pass

		return func
	
	setattr(ResourceRoutes, name, decorator)

class RestClient(object):
	def __init__(self, host, default_query = {}, default_headers = {}):
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

	def request(self, method, url = '/', query = {}, body = '', headers = {}):
		http_connection = httplib.HTTPConnection(self._host)
		http_connection.request(method, url + '?' + urllib.urlencode(self._query(query)), body, self._headers(headers))

		resp = http_connection.getresponse()
		if resp.status not in range(200, 300):
			raise IOError('Unexpected status code received %s %s' % (resp.status, resp.reason))

		return resp.read()

	def _query(self, query):
		res = {}
		res.update(self._default_query)
		res.update(query)

		return res

	def _headers(self, headers):
		res = {}
		res.update(self._default_headers)
		res.update(headers)

		return res

if __name__ == '__main__':
	class H(object):
		h = 1

	class F(H):
		h = 2

		@classmethod
		def t(cls):
			print cls.h

	F.t()
