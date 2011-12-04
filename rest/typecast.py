import properties

class TypeCastError(StandardError):
	pass

def to_int(value, to):
	return int(float(value))

def to_float(value, to):
	return float(value)

def to_bool(value, to):
	return value not in ['false', 'False', 0, None, False, 'null', 'nil', 'None', '0']

def to_list(value, to):
	return list(value)

def to_dict(value, to):
	return dict(value)

def to_model(value, to):
	if not isinstance(value, dict):
		raise TypeCastError('Expected dict got %s' % value)

	return to(value)

TYPES = {
	int: to_int,
	float: to_float,
	bool: to_bool,
	list: to_list,
	dict: to_dict,
	properties.Base: to_model
}

def types(t):
	for type, func in TYPES.items():
		if issubclass(t, type):
			return func

	raise TypeCastError('Unknown type %s' % t)

def cast(value, to):
	if isinstance(to, list):
		if len(to) != 1 or not isinstance(value, list):
			raise TypeCastError("Can't type cast %s to %s" % (value, to))

		to = to[0]

		return [types(to)(v, to) for v in value]

	return types(to)(value, to)

if __name__ == '__main__':
	import base

	class R(base.Resource):
		pass

	print __module__
