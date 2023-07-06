'''
Created on August 17, 2020

@author: Krienglit

@desc: UNIX Python3++ Scripts
'''


import sys
import getopt
import xmlrpc.client as xmlrpclib

url = None
db = None
username = None
password = None
add_name = None
add_login = None
add_pass = None

# Receive arguments from CLI
argv = sys.argv[1:]

# Filter arguments parameter
try:
	opts,args = getopt.getopt(argv,'x',['host=','db=','user=','pass=','add_name=','add_login=','add_pass='])
except:
	sys.exit('invalid arguments 001')

# Check invalid arguments
if len(args) != 0:
	sys.exit('invalid arguments 002')

# Store arguments
for row in opts:
	if row[0] == '--host':	# --host  ODOO server  IP address
		url = row[1]
		continue
	if row[0] == '--db':	# --db ODOO database name
		db = row[1]
		continue
	if row[0] == '--user':	# --user ODOO Administrator username
		username = row[1]
		continue
	if row[0] == '--pass':	# --pass ODOO Administrator password
		password = row[1]
		continue
	if row[0] == '--add_name':	# --add_name target name to add to database
		add_name = row[1]
		continue
	if row[0] == '--add_pass':	# --add_pass target password to add to database
		add_pass = row[1]
		continue
	if row[0] == '--add_login':	# --add_login target login username to add to database
		add_login = row[1]
		continue

if (url is None) or (db is None) or (username is None) or (password is None) or (add_name is None) or (add_login is None) or (add_pass is None):
	sys.exit('invalid arguments 003')



print('-----------------------------------')
print('ODOO IP:'+url)
print('DB Name:'+db)
print('ODOO Login:'+username)
print('ODOO Password:'+password)
print('> Add Account')
print('> Name:'+add_name)
print('> Login:'+add_login)
print('> Password:'+add_pass)
print('-----------------------------------')


try:
	common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
	uid = common.authenticate(db, username, password, {})   
	models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url)) 
	user_id=models.execute_kw(db, uid, password, 'res.users', 'create', [{'name':add_name, 'login':add_login, 'password':add_pass }])
	print('done!')
except Exception as e:
	sys.exit(e)
