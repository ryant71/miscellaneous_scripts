#!/usr/bin/env python

import sqlalchemy as sa
from sqlalchemy import func 
from sqlalchemy.sql import and_
import csv
import sys

#infile = sys.argv[0].strip()

engine = sa.create_engine('sqlite:///gvip.db')
meta = sa.MetaData()
meta.bind = engine
connection = engine.connect()
tbl = sa.Table('mongo', meta, autoload=True)

#connection.execute("delete from mongo")
#connection.execute(".mode csv") # does not work
#connection.execute(".import %s mongo" % infile)

# s = select([table.c.col1]).where(table.c.col2==5)

points = [
        (0,4),
        (5,10),
        (11,20),
        (21,40),
        (41,70),
        (71,100),
        (101,200),
        (201,500),
        (501,1000),
        (1000,)
]


results = csv.writer(open('results.csv', 'wb'), delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
for p in points:
    try:
        l,u = p[0],p[1]
        between = True
    except IndexError:
        l, u = p[0], 'infinity' 
        between = False
    span = '%s to %s:' % (str(l), str(u))
    if between:
        s = sa.select([func.count(tbl.c.uid)]).where(
                and_(tbl.c.points >= l, tbl.c.points <= u))
    else:
        s = sa.select([func.count(tbl.c.uid)]).where(tbl.c.points > l) 
    ret = s.execute().fetchone()[0]
    results.writerow([span, ret])
    print('%-17s %7d' % (span, ret))



