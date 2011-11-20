import __builtin__

class Accessor(object):
	ALLOWED = ['type', 'required', 'write', 'read', 'id']

	def __init__(self, opts = {}):
		#allowed = ['type', 'required', 'write', 'read', 'id']
		for name, value in opts.items():
			if name not in self.ALLOWED:
				raise StandardError('Unknown option "%s"' % name)

		defaults = dict([(name, None) for name in self.ALLOWED])
		defaults.update(opts)

		self.__dict__.update(defaults)

	def get(self, f):
		self.read = f
		return self

	def set(self, f):
		self.write = f
		return self

	def valid(self, instance):
		value = instance.read_attribute(self.name)
		if self.required or self.id:
			if value is None: 
				return False

		if self.type:
			if not isinstance(value, self.type):
				return False

		return True

	def __get__(self, instance, owner):
		if self.read:
			return self.read(instance)

		return instance.__dict__.get(self.name, None)

	def __set__(self, instance, value):
		if self.write:
			self.write(instance, value)
		else:
			instance.__dict__[self.name] = value

class Property(Accessor):
	def __get__(self, instance, owner):
		if self.read:
			return self.read(instance)

		return instance.read_attribute(self.name)

	def __set__(self, instance, value):
		if self.write:
			self.write(instance, value)
		else:
			instance.write_attribute(self.name, value)

def property(**opts):
	# TODO add default and readonly
	#allowed = ['type', 'required', 'write', 'read', 'id']
	#for name, value in opts.items():
	#	if name not in allowed:
	#		raise StandardError('Unknown option "%s"' % name)

	#defaults = dict([(name, None) for name in allowed])
	#defaults.update(opts)
	return Property(opts)

def accessor(**opts):
	return Accessor(opts)

#def property(type = None, required = True, key = None, write = None, read = None):
#	return Property({ 'type' : type, 'required' : required, 'key' : key, 'write' : write, 'read' : read })

def _assigned(cls, var, klass):
	var = '_%s' % var
	values = getattr(cls, var, None)

	if not values:
		values = [(name, p) for name, p in cls.__dict__.items() if isinstance(p, klass)]

		for name, p in values:
			p.name = name

		setattr(cls, var, values)
	
	return values

class Base(object):
	@classmethod
	def properties(cls):
		return _assigned(cls, 'properties', Property)
		#if not hasattr(cls, '_properties'):
		#	cls._properties = [(name, p) for name, p in cls.__dict__.items() if isinstance(p, Property)]

		#	for name, p in cls._properties:
		#		p.name = name
		
		#return cls._properties

	@classmethod
	def accessors(cls):
		return _assigned(cls, 'accessors', Accessor)

	@classmethod
	def has_property(cls, name):
		return not cls.get_property(name) is None

	@classmethod
	def get_property(cls, name):
		return dict(cls.properties()).get(name, None)

	@classmethod
	def id_property(cls):
		for name, p in cls.properties():
			if(p.id):
				return (name, p)

		return (None, None)

	def __init__(self, attrs = {}):
		props = dict([(name, None) for name, p in self.properties()])
		self._properties = props.copy()

		props.update(attrs)
		self.attributes = props

		#for name, prop in self.properties():
		#	setattr(self, name, Attribute(name, prop))

		#self.attributes = props

	def __getitem__(self, name):
		return self.read_attribute(name)

	def __setitem__(self, name, value):
		self.write_attribute(name, value)

	def __repr__(self):
		return str(self)

	def __str__(self):
		return str(self.attributes)

	def valid(self):
		return all([p.valid(self) for n, p in self.properties()])

		#props = dict(self.properties())
		#for name, value in self.attributes.items():
		#	prop = props[name]

		#	if prop.required:
		#		if not hasattr(self, name) or getattr(self, name) is None:
		#			return False
			
		#	if prop.type:
		#		if hasattr(self, name) and not isinstance(value, prop.type):
		#			return False

		#return True

	@__builtin__.property
	def id(self):
		name, prop = self.id_property()
		return self.read_attribute(name) if name else None

	def read_attribute(self, name):
		return self._properties[name]

	def write_attribute(self, name, value):
		self._properties[name] = value

	@__builtin__.property
	def attributes(self):
		#return dict([(name, value) for name, value in self._properties.items() if not value is None])

		attrs = []
		for name, p in self.properties():
			value = getattr(self, name)
			if not value is None:
				attrs.append((name, value))

		return dict(attrs)
 
	@attributes.setter
	def attributes(self, attrs):
		if not isinstance(attrs, dict):
			return

		#attrs = dict([(name, value) for name, value in attrs.items() if self.has_property(name)])
		#self._properties.update(attrs)

		props = [n for n, p in self.properties()] + [n for n, a in self.accessors()]
		for name, value in attrs.items():
			if name in props:			
				setattr(self, name, value)

if __name__ == '__main__':
	#http = HttpClient('')
	#print http.json_request('POST', '/u/authenticate', { 'secrettoken' : 'verysecret', 'email' : 'm@ge.tt', 'password' : 'qweqwe' })

	class H(Base):
		f = property(type = str, required = True)
		g = property(type = int)

		foo = accessor()

		#j = accessor()

		#@f.get
		#def f(self):
		#	return self.f

		@__builtin__.property
		def user(self):
			print('user')

		def share(self):
			print('share')

		fileid = None

		@f.get
		def f(self):
			return self.read_attribute('f') + ' you'

	print H.properties()

	h = H()
	h.foo = 5

	print h.__dict__
	#h = H({ 'f' : 'hello', 'g' : 2 })
	#print(h.attributes)
	#h.f = 5