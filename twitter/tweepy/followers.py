
# https://stackoverflow.com/questions/39333040/tweepy-and-python-how-to-list-all-followers

import time
import tweepy
from auth import consumer_key, consumer_secret, \
        access_token, access_token_secret

sleeptime = 4

oauth = tweepy.OAuthHandler(consumer_key, consumer_secret)
oauth.set_access_token(access_token, access_token_secret)
api = tweepy.API(oauth)


if __name__ == "__main__":

    pages = tweepy.Cursor(api.followers, screen_name="arkitux").pages()

    while True:
        try:
            page = next(pages)
            time.sleep(sleeptime)
        except tweepy.TweepError:  # rate limit exceeded (180 queries per 15m)
            print('Sleeping...')
            time.sleep(60*15)
            page = next(pages)
        except StopIteration:
            break
        for user in page:
            output = '%15s %20s %5d' % (user.id_str,
                                        user.screen_name,
                                        user.followers_count)
            print(output)
