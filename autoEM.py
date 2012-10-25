#!/usr/bin/python2.7
##################################################################################
#-*- coding: utf-8 -*-
# 
# Filename: autoEM.py
#
# Copyright (C) 2012 -  You-Tang Lee (YodaLee) <lc85301@gmail.com>
# All Rights reserved.
#
# This file is part of project: autoEM
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##################################################################################

import os
import os.path
import sys
import getpass
import traceback
import time
import collections
from optparse import OptionParser, make_option

#third part library
import paramiko

program = sys.argv[0]
LANUCH_DIR = os.path.dirname(os.path.abspath(sys.path[0]))

# If launched from source directory
if program.startswith('./') or program.startswith('bin/'):
    sys.path.insert(0, LANUCH_DIR)

program_name = sys.argv[0]
program_version = '0.1.0'
def version():
	sys.stderr.write(
'%s Ver %s\n\
Copyright (C) 2012 YodaLee\n\
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.\n\
This is free software: you are free to change and redistribute it.\n\
There is NO WARRANTY, to the extent permitted by law.\n\
Written by YodaLee <lc85301@gmail.com>.\n' % (program_name, program_version)
)

#sftp = paramiko.SFTPClient.from_transport(t)
#try:
#	sftp.mkdir("autoEM")
#except IOError:
#	print '(autoEM folder already exists)'
#sftp.put(filename, filename)

default_command="""
#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin 
export PATH

source ~/.bashrc
rm -rf ~/autoEM/sondata/%s
em ~/autoEM/%s.son
"""
def exec_command(filename):
	#setup log file
	info = get_user_info()
	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(info.hostname, username=info.username, password = info.password)
		stdin, stdout, stderr = ssh.exec_command('source ~/.bashrc; nohup em ~/autoEM/%s </dev/null >em.log 2>&1 &' % filename)
		#stdout.readline()
		stderr.readline()
	except exception, e:
		print '*** Caught exception %s: %s ***' % (e.__class__, e)
		traceback.print_exc()
	finally:
		ssh.close()
		sys.exit(1)

def get_user_info():
	"""get username and password"""
	# get hostname
	hostname = ''
	username = ''
	password = ''
	port = 22
	hostname = raw_input('Hostname: ')
	if len(hostname) == 0:
		print '*** Hostname required. ***'
		sys.exit(1)
	if hostname.find('@') >= 0 :
		username, hostname = hostname.split('@')
	if hostname.find(':') >= 0:
		hostname, portstr = hostname.split(':')
		port = int(portstr)
	## get username
	if username == '':
		default_username = getpass.getuser()
		username = raw_input('Username [%s]: ' % default_username)
		if len(username) == 0:
			username = default_username
	password = getpass.getpass('Password for %s@%s: ' % (username, hostname))

	# get host key, if we know one
	hostkeytype = None
	hostkey = None
	try:
		host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
	except IOError:
		try:
			# try ~/ssh/ too, because windows can't have a folder named ~/.ssh/
			host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
		except IOError:
			print '*** Unable to open host keys file ***'
			host_keys = {}
	if host_keys.has_key(hostname):
		hostkeytype = host_keys[hostname].keys()[0]
		hostkey = host_keys[hostname][hostkeytype]
		print 'Using host key of type %s' % hostkeytype

	Info = collections.namedtuple("Info", "username, hostname, password, port, hostkeytype, hostkey")
	return Info(username, hostname, password, port, hostkeytype, hostkey)

def add_workstaion():
	"""upload command to workstation"""

def download_file(filename):
	"""download file to workstation"""
	info = get_user_info()
	t = paramiko.Transport((info.hostname,info.port))
	t.connect(username=info.username, password=info.password, hostkey=info.hostkey)
	sftp = paramiko.SFTPClient.from_transport(t)
	sftp.get("autoEM/"+filename, filename)
	sftp.close()
	t.close()

def upload_file(filename):
	"""upload file to workstation"""
	info = get_user_info()
	t = paramiko.Transport((info.hostname,info.port))
	t.connect(username=info.username, password=info.password, hostkey=info.hostkey)
	sftp = paramiko.SFTPClient.from_transport(t)
	sftp.put(filename, "autoEM/" + filename)
	sftp.close()
	t.close()

def main():
	#"""the main function of autoEM"""
	option_list = [
		make_option('-u', '--upload', action='store', dest='upload',
					default=False, help='upload a file to workstation'),
		make_option('-d', '--download', action='store', dest='download',
					default=False, help='download a file from workstation'),
		make_option('-a', '--add', action='store',dest='add',
					default=False, help='add workstion to available list'),
		make_option('-r', '--run', action='store', dest='run',
					default=False, help='run simulation on workstation'),
		make_option('-m', '--monitor', action='store_true', dest='monitor',
					default=False, help='monitor the situation of workstation'),
		make_option('-v', '--version', action='store_true', dest='version',
					default=False, help='show version information')
		]
	parser = OptionParser(usage = 'Usage: autoEM [OPTION...] PAGE...',
						option_list=option_list)
	options, args = parser.parse_args()

	if options.add:
		add_workstaion()
		sys.exit(0)
	if options.version:
		version()
		sys.exit(0)
	if options.upload:
		#here we assume the upload file is placed with program file
		program_dir = os.getcwd()
		uploadfile = os.path.join(program_dir, options.upload)
		if os.path.isfile(uploadfile) and not os.path.islink(uploadfile):
			if not uploadfile.endswith(".son"):
				print("The file you specify may not be a sonnet file, upload will continue.")
			upload_file(options.upload)
		else:
			sys.stderr.write("Can't find the upload file\n")
			sys.exit(1)
		sys.exit(0)
	if options.download:
		#also, download the file to folder with program
		download_file(options.download)
		sys.exit(0)
	if options.run:
		#run the specify command, this command will delete extension automatically
		sonfile = os.path.splitext(options.run)[0]
		exec_command(sonfile)
		sys.exit(0)
	if len(args) == 0:
		sys.stderr.write("No specify action to be done.\n")
		sys.exit(1)
		
	
if __name__ == '__main__':
	try:
		main()
	except (Exception, KeyboardInterrupt), e:
		if type(e) == KeyboardInterrupt:
			print '\nAborted.'
		else:
			print 'error:', e
