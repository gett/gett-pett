import json
import socket
import ssl
import Queue
import threading
import string
import random

HOST = 'open.ge.tt'
PORT = 443

SESSION = string.ascii_uppercase + string.ascii_lowercase + string.digits

def _generate_session(size = 8):
	return ''.join(random.choice(SESSION) for x in range(size))

class JsonSocket(object):
	def __init__(self, host, port):
		sock = socket.socket();sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock = ssl.wrap_socket(sock)
		sock.connect((host, port))

		self._socket = sock

		self._handshake()

	def _handshake(self):
		self._socket.send('GET / HTTP/1.1\r\nUpgrade: jsonsocket\r\n\r\n')
		resp = self._read('\r\n\r\n')

	def _read(self, terminator):
		buffer = []

		while len(buffer) < 1 or terminator not in buffer[-1]:
			buffer.append(self._socket.recv(1024))

		buffer[-1] = buffer[-1].replace(terminator, '')

		return ''.join(buffer)

	def send(self, msg):
		if not isinstance(json, str):
			msg = json.dumps(msg)

		self._socket.send(msg + '\n')

	def recv(self):
		resp = self._read('\n')

		while resp == 'ping':
			self.send('pong')

		return json.loads(resp)

	def close(self):
		self._socket.close()

class Api(threading.Thread):
	def __init__(self):
		self._socket = None #JsonSocket(HOST, PORT)
		self._session = _generate_session()

		self._run = True

		super(Api, self).__init__()

	def connect(self, token):
		self._socket = JsonSocket(HOST, PORT)

		self._socket.send({
			'type' : 'connect',
			'accesstoken' : str(token.token if hasattr(token, 'token') else token),
			'session' : self._session
		})

		self.start()

	@property
	def session(self):
		return self._session

	def on_download(self, sharename, fileid, filename):
		pass

	def on_storagelimit(self, sharename, fileid, filename):
		pass

	def on_filestat(self, sharename, fileid, filename, size):
		pass

	def on_violatedterms(self, sharename, fileid, filename, reason):
		pass

	def on_error(self, err):
		raise err

	def run(self):
		try:
			while self._run:
				msg = self._socket.recv()
				method = getattr(self, 'on_' + msg['type'])

				del msg['type']
				method(**msg)
		except (socket.error, ValueError) as err:
			self.on_error(err)


	def close(self):
		self._run = False
		self._socket.close()
