# Usage

Tested with python 2.7.2

	import api

	gett = api.Gett({ 'apikey' : '...', 'email' : '...', 'password' : '...' })
	# or 
	gett = api.Gett('<refreshtoken as string>')

	# authenticate and fetch the user information
	user = gett.user()

	print user.shares()
	# or
	print api.Share.all(gett.token)
	# or
	print api.Share.all(user)

	print user.share('8gt4').files()

	share = user.create_share({ 'title' : 'hello' })
	share.create_file({ 'filename' : 'world' })

	print share.file(0)
