#!/usr/bin/env python

"""
...
"""

# https://www.karambelkar.info/2015/01/how-to-use-twitters-search-rest-api-most-effectively./

import sys
import time

from datetime import datetime, timedelta
from auth import consumer_key, consumer_secret, \
        access_token_key, access_token_secret, screen_name

import tweepy


sleeptime = 1
exception_sleeptime = 60*15

match_by_date = True
days_to_keep = 30
cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

delete_last_n_tweets = 1
delete_matching = 'me // automatically checked by'
keep_matching = '#keeper'
keybase_matching = 'GF-1BjCID_I45YXm_UIqknVq0gjbAvKhGLOC'


def vprint(msg):
    if verbose:
        print(msg)


def make_twapi():
    appauth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    appauth.set_access_token(access_token_key, access_token_secret)
    return tweepy.API(appauth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def get_tweet_list(pages):
    pnum = 0
    tweet_list = []
    while True:
        try:
            page = next(pages)
            time.sleep(sleeptime)
        except tweepy.TweepError:  # rate limit exceeded (180 queries per 15m)
            vprint('Sleeping...')
            time.sleep(exception_sleeptime)
            page = next(pages)
        except StopIteration: # no more pages
            vprint('Done')
            break
        pnum += 1
        vprint('### Page number: %d ####' % pnum)
        for entry in page:
            tweet_list.append(entry)
    return tweet_list


def print_tweet(entry, msg=""):
    try:
        media_url = entry.entities['media'][0]['media_url']
    except KeyError:
        media_url = ''
    output = '[%d][%s](%s)fc=%-3d,rc=%-4d %s %s' % (
        entry.id,
        entry.created_at,
        msg,
        entry.favorite_count,
        entry.retweet_count,
        entry.text,
        media_url)
    vprint(output)


def last_tweets_manage(api, tweet_list, do_delete):
    print('list count =' + str(len(tweet_list)))
    tweet_list_subset = []
    if delete_matching:
        tweet_list_subset += [tweet for tweet in tweet_list if delete_matching in tweet.text]
    if match_by_date:
        tweet_list_subset += [tweet for tweet in tweet_list if tweet.created_at < cutoff_date]
    else:
        tweet_list_subset = tweet_list[::-1][:delete_last_n_tweets]
        if len(tweet_list_subset) <= delete_last_n_tweets:
            return
    for item in tweet_list_subset:
        if item.favorite_count >= 10:
            print_tweet(item, 'KEEP favourite')
        elif keep_matching in item.text:
            print_tweet(item, 'KEEP match')
        elif keybase_matching in item.text:
            print_tweet(item, 'KEEP keybase')
        else:
            print_tweet(item, 'DELETE')
            if do_delete:
                api.destroy_status(item.id)


def main(screen_name, do_delete):
    api = make_twapi()
    pages = tweepy.Cursor(api.user_timeline, screen_name=screen_name).pages()
    tweet_list = get_tweet_list(pages)
    last_tweets_manage(api, tweet_list, do_delete)


if __name__ == "__main__":

    if '-d' in sys.argv:
        do_delete = True
        print('Running in delete mode')
    else:
        do_delete = False
        print('Not deleting tweets. Use \'-d\' to run in delete mode')

    global verbose
    if '-v' in sys.argv:
        verbose = True
    else:
        verbose = False

    main(screen_name, do_delete)
