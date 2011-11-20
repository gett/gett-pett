#import properties
import routes
from routes import ResourceRoutes, RestClient, RestRoutes
import serialization
import properties
from properties import property, accessor

class Resource(serialization.Base, properties.Base, routes.Base):
	pass


if __name__ == '__main__':
	class User(Resource):
		host = 'open.ge.tt'
		routes = routes.ResourceRoutes('/1/u')

		userid = properties.property(required = True, id = True)
		username = properties.property(required = True)

	#import inspect

	#print inspect.getsource(User.__init__)

	u = User({ 'userid' : 0, 'username' : 'mka' })

	print u.to_json(2)

	class Token(Resource):
		host = 'open.ge.tt'
		routes
