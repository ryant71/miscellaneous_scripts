#!/bin/bash

[ -z "$1" ] && { echo "Usage: $0 <host>:<port>"; exit; } || host=$1

echo "quit" \
| openssl s_client -connect ${host} 2>&1 \
| sed -n '/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/p' \
| openssl x509 -noout -subject -issuer -enddate

