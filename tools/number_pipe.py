#!/usr/bin/env python

"""
lib: https://github.com/daviddrysdale/python-phonenumbers
ported from: http://code.google.com/p/libphonenumber/

Example uses:

# valid Nigerian number
(desktop)ryant@spitfire: ~$ echo "+234xxxxxxxxxx" | number_pipe.py 
+234xxxxxxxxxx

# Ghana prefix + Nigeria area code
(desktop)ryant@spitfire: ~$ echo "+233xxxxxxxxxx" | number_pipe.py 
<chirrup chirrup>

# numbers from FB
ryant@spitfire ~$ cut -d, -f1 msisdnemail.csv | wc -l
3249

ryant@spitfire ~$ cut -d, -f1 msisdnemail.csv | number_pipe.py | wc -l
unparsable number: +Whenu
unparsable number: +80180510739
unparsable number: +Adefowora
3089

country_name_for_number(phonenumbers.parse("+27xxyyyyyyy", None), "en")

"""

import sys
import string
import phonenumbers
from phonenumbers import is_valid_number, parse

if len(sys.argv)<=1:
    args = sys.stdin.readlines()
    if type(args)==type([]):
        if len(args)==1:
            args = string.split(args[0])
else:
    args = sys.argv
    args = args[1:]

if not args:
    sys.stderr.write('What are you passing me\n')
    sys.stderr.flush()
    sys.exit()

args = [arg.strip() for arg in args]

# spit out valid number
# don't spit out invalid number
# todo: option to reverse that and spit out the bad ones 
for arg in args:
    if not arg.startswith('+'):
        arg = '+' + arg
    try:
        num = parse(arg, None)
    except phonenumbers.phonenumberutil.NumberParseException:
        sys.stderr.write('unparsable number: %s\n' % (arg,))
        sys.stderr.flush()
        continue
    if (is_valid_number(num)):
        print(arg)


