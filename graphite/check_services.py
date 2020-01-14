#!/usr/bin/env python

import requests
import random
import socket
import yaml
import time
import sys
import os

from monlib import loginfo

graphite_host = 'graphitehost'
graphite_port = graphiteport

yamlfile = '%s/services.yaml' % os.path.dirname(sys.argv[0])

hdict = {
    'somehost1': 'wgcptsomehost1',
    'somehost2': 'wgcptsomehost2',
    'somehost3': 'wgcptsomehost3',
}

try:
    srchost = hdict[socket.gethostname()]
except KeyError:
    srchost = socket.getfqdn()

def openyaml(yamlfile):
    return yaml.load(open(yamlfile))

def get_(dict, key):
    try:
        return dict[key]
    except KeyError:
        return None

def show_keys(dict):
    for key in dict:
        print key

def get_service_info(servicedict):
    url = get_(servicedict, 'url')
    post_data = get_(servicedict, 'post_data')
    succ_resp = get_(servicedict, 'succ_resp')
    user = get_(servicedict, 'user')
    password = get_(servicedict, 'password')
    header = get_(servicedict, 'header')
    return url, post_data, succ_resp, user, password, header

def check_service(servicedict):
    url, post_data, succ_resp, user, password, header = get_service_info(servicedict)
    headers = {'Content-type':'text/xml;charset=UTF-8'}
    if header:
        headers[header.split(':')[0]] = ':'.join(header.split(':')[1:]).strip()
    if post_data:
        r = requests.post(url, data=post_data, headers=headers, auth=(user, password), verify=False)
    else:
        r = requests.get(url, headers=headers, auth=(user, password), verify=False)
    if verbose:
        print(url)
        print(headers)
        print(r.status_code)
        print(r.headers)
        print(r.text)
    return r

def graphitepost(graphite_location, service, trxtime, status_code=None):
    sock = socket.socket()
    if status_code:
        graphite_prefix = 'services.%s.%s.%s.soaptrxtime.status.%s' % (srchost,graphite_location,service,status_code)
    else:
        graphite_prefix = 'services.%s.%s.%s.soaptrxtime' % (srchost,graphite_location,service,)
    message = '%s %f %d\n' % (graphite_prefix, trxtime, time.time())
    if testmode:
        print(message)
    else:
        sock.connect((graphite_host,graphite_port))
        sock.send(message)
    sock.close()

if __name__=='__main__':

    if '-t' in sys.argv:
        testmode = True
        sys.argv.remove('-t')
    else:
        testmode = False
    if '-v' in sys.argv:
        verbose = True
        sys.argv.remove('-v')
    else:
        verbose = False

    services = openyaml(yamlfile)['services']
    try:
        service = sys.argv[1]
    except:
        show_keys(services)
        sys.exit()
    servicedict = get_(services, service)
    graphite_location = get_(servicedict,'graphite_location')
    override_status_code = get_(servicedict, 'override_status_code')
    # random delay
    if not testmode:
        time.sleep(random.randrange(10))
    start = time.time()
    r = check_service(servicedict)
    trxtime = time.time() - start
    if override_status_code:
        status_code = override_status_code
    else:
        status_code = r.status_code
    graphitepost(graphite_location, service, trxtime, status_code)
    loginfo('%s %s %d %f' % (sys.argv[0], service, r.status_code, trxtime))


