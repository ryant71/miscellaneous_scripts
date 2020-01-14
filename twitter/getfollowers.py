#!/usr/bin/env python

import os
import datetime
import twitter
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker

from myoauth import *

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    screen_name = Column(String(50))
    name = Column(String(50))
    date = Column(DateTime)
    last_updated = Column(DateTime)

    def __repr__(self):
        return u"<User(id='%s', screen_name='%s', name='%s', date='%s', last_updated='%s')>" % (
                    self.id, self.screen_name, self.name.decode('utf'), self.date, self.last_updated)

def printusers(users):
    for user in users:
        screen_name = user.screen_name
        name = user.name
        print('%20s -> %s' % (screen_name, name))


api = twitter.Api(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token_key=access_token_key,
            access_token_secret=access_token_secret)


if __name__=="__main__":

    scriptdir = os.path.dirname(os.path.abspath(__file__))
    engine = sa.create_engine('sqlite:///%s/twitter.db' % scriptdir)

    Session = sessionmaker(bind=engine)
    session = Session()

    metadata = sa.MetaData()
    usertbl = sa.Table('user', metadata, autoload = True, autoload_with=engine)

    users = api.GetFollowers()

    for user in users:
        name = unicode(user.name)
        add_user = User(screen_name=user.screen_name,
                        name=name,
                        date=datetime.datetime.now(),
                        last_updated=datetime.datetime.now())
        print(add_user)
        session.add(add_user)
    session.commit()


