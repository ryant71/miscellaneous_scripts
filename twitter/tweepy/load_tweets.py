
# https://stackoverflow.com/questions/39333040/tweepy-and-python-how-to-list-all-followers

import time
import couchdb
import tweepy
from auth import consumer_key, consumer_secret, \
        access_token, access_token_secret, screen_name

sleeptime = 4
exception_sleeptime = 60*15

couch_server = 'http://10.0.4.62:5984/'
couch_database = 'twitter_data'
couch_user = 'twload'
couch_pass = 'twit'


def make_twapi():
    oauth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    oauth.set_access_token(access_token, access_token_secret)
    return tweepy.API(oauth)


def make_couchdb(couch_server, couch_database, couch_user, couch_pass):
    couch = couchdb.Server(couch_server)
    couch.resource.credentials = (couch_user, couch_pass)
    return couch[couch_database]


def couch_load(couch, json_data):
    couch.save(json_data)


def main(screen_name):
    api = make_twapi()
    couch = make_couchdb(couch_server, couch_database, couch_user, couch_pass)
    pages = tweepy.Cursor(api.user_timeline, screen_name=screen_name).pages()
    pnum = 0
    while True:
        try:
            page = next(pages)
            time.sleep(sleeptime)
        except tweepy.TweepError:  # rate limit exceeded (180 queries per 15m)
            print('Sleeping...')
            time.sleep(exception_sleeptime)
            page = next(pages)
        except StopIteration:
            print('break')
            break
        pnum += 1
        print('## Page number: %d' % pnum)
        for entry in page:
            output = '\t[%s] fc=%-3d rc=%-4d %s' % (
                                                     entry.created_at,
                                                     entry.favorite_count,
                                                     entry.retweet_count,
                                                     entry.text)
            print(output)
            json_data = entry._json
            couch_load(couch, json_data)


if __name__ == "__main__":

    main(screen_name)
