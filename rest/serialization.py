import xml.dom.minidom
import json

"""
doc = Document()
root = doc.createElement('users')

doc.appendChild(root)

print doc.toprettyxml('    ')
"""

class SerializationError(StandardError):
	pass

class SerializableList(list):
	def __init__(self, cls, method):
		super(SerializableList, self).__init__()
		
		self._cls = cls
		self._method = method

	def serialize(self, opts = {}):
		return getattr(self, 'to_%s' % self._method)(opts)

	def to_json(self, opts = {}):
		return '[%s]' % [obj.to_json() for obj in self].join(',')

	def to_xml(self, opts = {}):
		pass

	def to_formdata(self, opts = {}):
		pass

class FormData(object):
	@classmethod
	def from_formdata(cls, string):
		pass

	def to_formdata(self, opts = {}):
		pass

class Json(object):
	@classmethod
	def from_json(cls, string):
		attrs = json.loads(string)
		if isinstance(attrs, list):
			return [cls(obj) for obj in attrs]
		elif isinstance(attrs, dict):
			return cls(attrs)
		else:
			raise SerializationError('Unexpected json received ' + string)

	def to_json(self, opts = {}):
		return json.dumps(self.attributes, indent = opts.get('indent', 0))

class Xml(object):
	@classmethod
	def from_xml(cls, string):
		pass

	def to_xml(self, opts = {}):
		#doc = xml.dom.minidom.Document()

		root = xml.dom.minidom.Element(_name(self).lower())
		#doc.appendChild(root)

		for name, value in self.attributes.items():
			attr = xml.dom.minidom.Element(name)

			txt = xml.dom.minidom.Text()
			txt.data = value.to_xml if hasattr(value, 'to_xml') else value
			attr.appendChild(txt)

			attr.setAttribute('type', _name(value))

			root.appendChild(attr)

		return root.toprettyxml(' ' * opts.get('indent', 0))

class Base(FormData, Json, Xml):
	serialization = parsing = 'json'

	@classmethod
	def parse(cls, string):
		name = 'from_%s' % cls.parsing
	
		if hasattr(cls, name):
			return getattr(cls, name)(string)
		else:
			raise StandardError('Unkown parsing strategy %s' % cls.parsing)

	def serialize(self, opts = {}):
		name = 'to_%s' % self.serialization

		if hasattr(self, name):
			return getattr(self, name)(opts)
		else:
			raise StandardError('Unknown serialization strategy %s' % self.serialization)

def _normalize_options(props, include, exclude):
	if include and exclude:
		raise StandardError('Only include or exclude can be specified not both')
	elif exclude:
		include = [name for name in props if name not in exclude]

	for name in include:
		pass

def _name(obj):
	return obj.__class__.__name__

"""
def serialize(cls, obj, opts = {}):
	if hasattr(obj, 'serialize'):
		return obj.serialize()
	elif isinstance(obj, dict):
		return cls(obj).serialize(opts)
	elif hasattr(obj, '__iter__'):
		return SerializableList(cls, cls.serialization).serialize()
	else:
		raise SerializationError("Can't serialize given object " + obj)
"""

if __name__ == '__main__':
	class User(Base):
		def __init__(self):
			self.attributes = {
				'id' : 1,
				'username' : 'mka',
				'password' : 'pass',
				'emails' : ['f@ge.tt', 'm@ge.tt', 'hello@gmail.com']
			}


	print User().to_xml(2)
