
# https://stackoverflow.com/questions/39333040/tweepy-and-python-how-to-list-all-followers

"""
permanent view create via fauxton

	_design/get_ids/_view/get_ids_idx

function (doc) {
  emit(doc.id, 1)
}

"""

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


def main():
    # api = make_twapi()
    couch = make_couchdb(couch_server, couch_database, couch_user, couch_pass)
    # pages = tweepy.Cursor(api.user_timeline, screen_name=screen_name).pages()
    results = couch.view('_design/get_ids/_view/get_ids_idx')
    for result in results:
        docid = result['id']
        doc = couch.get(docid)
        print(doc['text'])

if __name__ == "__main__":

    main()
