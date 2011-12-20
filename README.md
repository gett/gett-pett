# Usage

Tested with python 2.7.2

``` python
import rest

# authenticate and get user information
user = rest.User.login({ 'apikey' : '...', 'email' : '...', 'password' : '...' })
# or 
user = rest.User.login('<refreshtoken as string>')

# fetch all shares
print user.shares()
# or
print rest.Share.all(user.token)
# or
print rest.Share.all(user)
# or
print rest.Share.all('<accesstoken as string>')

# NOTE that the last three calls will not set the accesstoken or user on the share, this
# needs to be done manually.

# get all files in a share. NOTE that this is not a method call.
print user.share('<sharename>').files

# create a share and a file
share = user.create_share({ 'title' : 'hello' })
share.create_file({ 'filename' : 'world.txt' })

print share.file(0)

# create and upload file
share.upload_file('path/to/file')

# download file
file = share.file(0)
blob = file.blob()

# blob is a file like object, which responds to read and close
print blob.read()
```

# Live API

``` python
import rest
import live

user = rest.User.login({ 'apikey' : '...', 'email' : '...', 'password' : '...' })

# Override the event methods
class MyLiveApi(live.Api):
	def on_download(self, sharename, fileid, filename):
		file = user.share(sharename).file(fileid)

		with open('path/to/file') as f:
			file.write(f)

# Create and connect
api = MyLiveApi()
api.connect(user)
```

# Extended live API

``` python
import live

user = live.User.login({ 'apikey' : '...', 'email' : '...', 'password' : '...' })

# Add the file to a upload pool, which uploads files one at a time. Also listens for live API
# events and starts uploading a file when it receives a download request.
user.share('<sharename>').upload_file('path/to/file')

# Attach event listeners to the file
def on_file(file):
	def download(f):
		print 'someone started downloading file %s' % f

	def uploading(f, progress):
		print 'uploading file %s progress %s' % (f, progress)

	def upload(f):
		pring 'finished uploading file %s' % f

	file.on_event('download', download)
	file.on_event('uploading', uploading)
	file.on_event('upload', upload)

file = user.share('<sharename>').upload_file('path/to/another/file', on_file)

# Add listeners directly to the returned file
def error(f, err):
	print 'error %s on file %s' % (err, f)

file.on_event('error', error)
```
