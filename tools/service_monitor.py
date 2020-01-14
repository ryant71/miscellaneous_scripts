#!/usr/bin/env python

import os
import sys
import time
import socket
import logging

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from subprocess import Popen, PIPE
from daemonize import Daemonize

# import config file
try:
	import config
except ImportError:
	# Exit here without logging
	print('Cannot find config.py file')
	sys.exit(1)



def email_alert(sender, recipients, subject, body=None):
	msg = MIMEMultipart()
	msg['Subject'] = subject
	msg['From'] = sender
	msg['To'] = recipients
	if not body:
		body = 'Watchdog has alerted you!'
	body = MIMEText(body)
	msg.attach(body)
	s = smtplib.SMTP(host='127.0.0.1', port=25)
	s.sendmail(sender, recipients, msg.as_string())


# get the process name from the PID
#    for nginx, the equiv of " ps -q $(cat /var/run/nginx.pid) -o comm= "
# assumption: anything that needs monitoring will have a pid file...
# added bypass param
def check_name_from_pid(pidfile, service, bypass=False):
	if bypass:
		return True
	logger.info('Checking pidfile %s for %s' % (pidfile, service))
	try:
		with open(pidfile, 'rb') as pid:
			pid = pid.readline().strip()
	except IOError:
		logger.info('Cannot open pidfile')
		return False

	logger.info('PID from %s is %s' % (pidfile, pid))
	try:
		p = Popen(['ps', '-q', str(pid),'-o', 'comm='], shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
		process_name, err = p.communicate()
	except Exception as e:
		logfile.info(str(e))

	process_name = process_name.strip()
	if process_name != service:
		logger.info('Discovered process name does not match configured process name')
		return False
	logger.info('Process name is okay')
	return True


# check host and port by opening up and closing socket
#
def check_port(host, port, bypass=False):
	if bypass:
		return True
	sock = socket.socket()
	try:
		sock.connect((host, port))
	except socket.error as msg:
		logger.info(str(msg))
		return False
	sock.close()
	logger.info('Service %s, Port %d is okay' % (host, port))
	return True


# restart with restart command
#
def try_restart(restart_command):
	logger.info('Attempting restart')
	# split restart_command into a list
	restart_list = restart_command.split()
	p = Popen(restart_list, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
	out, err = p.communicate()
	logger.info(out)
	logger.info(err)


# Main function is a config checker...
#
def main():
	try:
		pidfile = config.pidfile
		service = config.service
		host = config.host
		port = int(config.port)
		restart_command = config.restart_command
		check_rate = int(config.check_rate)
		restart_rate = int(config.restart_rate)
		fail_after = int(config.fail_after)
		recipients = config.recipients
		sender = config.sender
	except (NameError, TypeError):
		logger.info('Config error')
		sys.exit()

	logger.info('Starting WatchDog')
	logger.info('Check rate is %d seconds' % check_rate)
	logger.info('Restart rate is %d seconds' % restart_rate)
	logger.info('Fail after is %d restart attempts' % fail_after)

	subject = 'Service %s alert' % service

	fail_count = 0
	while True:
		logger.info('Service %s fail_count=%d' % (service, fail_count))
		if fail_count >= fail_after:
			body = 'Fail_count (%d) reached, exiting' % fail_count
			logger.info(body)
			try:
				email_alert(sender, recipients, subject, body)
			except Exception as e:
				logger.info('Email error (%s)' % str(e))
			sys.exit()
		time.sleep(check_rate)
		logger.info('Checking %s' % service)
		if not check_name_from_pid(pidfile, service, bypass=False) or not check_port(host, port, bypass=False):
			body = 'Service %s is down' % service
			email_alert(sender, recipients, subject, body)		
			fail_count += 1
			# increase check rate
			logger.info('Setting check_rate to restart_rate')
			check_rate = restart_rate
			try_restart(restart_command)
			time.sleep(check_rate)
		else:
			if check_rate==restart_rate:
				# there was a problem but now there isn't
				logger.info('Service %s was restarted' % service)
				logger.info('Setting check_rate back to normal')
				check_rate = config.check_rate
				# reset fail count
				fail_count = 0
				body = 'Service %s restarted after %s tries' % (service, fail_count)
				email_alert(sender, recipients, subject, body)


if __name__=="__main__":

	# kill this monitor with: kill $(cat /var/run/service_monitor.pid)
	this_pidfile = '/var/run/service_monitor.pid'
	# set up logging
	try:
		logfile = config.logfile
	except NameError:
		print('Config error')
		sys.exit()

	script_name = os.path.basename(__file__)
	logger = logging.getLogger(script_name)
	logger.setLevel(logging.DEBUG)
	logger.propagate = False
	formatter = logging.Formatter('[%(asctime)s]: %(name)s: %(message)s')
	fh = logging.FileHandler(logfile, 'a+')
	fh.setFormatter(formatter)
	logger.addHandler(fh)
	keep_fds = [fh.stream.fileno()]

	print('Pre-check')
	if not check_port(config.host, config.port):
		print('Be aware that the service you are going to monitor is not running...')
		print('... starting the monitor anyway')

	print('\n... tail -f %s' % config.logfile)

	daemon = Daemonize(app="service_monitor.py", pid=this_pidfile, action=main, keep_fds=keep_fds)
	daemon.start()
