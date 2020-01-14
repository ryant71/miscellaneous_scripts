#!/bin/sh

if [ -z "$1" ]; then
    echo "Usage: $(basename $0) <remotedbhost> <mysql options>"
    exit 0
else
    REMOTEHOST=$1
    shift
fi
# select an unused port
# (could make this more flexible)
for port in 3307 3308 3309 3310 3311 3312 3313; do
    if netstat -lnt | grep -q ${port}; then
        continue
    else
        LOCALPORT=${port}
        break
    fi
done

# set up ssh tunnel 
ssh -f -L ${LOCALPORT}:localhost:3306 ${REMOTEHOST} -N 
# connect with local tunnel port with mysql client using cmdline options
mysql -P ${LOCALPORT} -h 127.0.0.1 $@
# you're finished with mysql now, kill the tunnel
# (maybe use $$ to get ssh tunnel's pid)
kill $(ps aux | grep "ssh -f -L ${LOCALPORT}" | grep -v grep | awk '{print $2}')
