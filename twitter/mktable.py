#!/usr/bin/env python

import os
import datetime
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, DateTime, select

scriptdir = os.path.dirname(os.path.abspath(__file__))
engine = sa.create_engine('sqlite:///%s/twitter.db' % scriptdir)

metadata = sa.MetaData()
usertbl = sa.Table('user', metadata,
        Column('id',Integer,primary_key = True),
        Column('screen_name', String(50), nullable = False),
        Column('name', String(50), nullable = False),
        Column('date', DateTime, nullable = False),
        Column('last_updated', DateTime, onupdate=datetime.datetime.now))

usertbl.create(engine, checkfirst=True)

