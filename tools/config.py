pidfile = '/var/run/nginx.pid'
service = 'nginx'
host = '127.0.0.1'
port = 80
restart_command = 'service nginx restart'
check_rate = 10
restart_rate = 2
fail_after = 5

logfile = '/var/log/watchdog.log'

recipients='xxx@gmail.com'
sender='xxx@gmail.com'


