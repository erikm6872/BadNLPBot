from flask import Flask, request
from flask_restful import Resource, Api
from twython import Twython
from twython import TwythonStreamer

from config import *
import time
import re
import random
import requests
from sqlalchemy import create_engine
from json import dumps

app = Flask(__name__)
api = Api(app)

config = Settings()

tweets = []
acc_tweets = []

start_t = time.time()

match_pattern = r'[@].*|RT|http.*|.*\\n.*|[^a-zA-Z0-9!\?\.]'  # Pattern to reject
all_words = []
bigram_hash = {}
config = Settings()


class TweetStreamer(TwythonStreamer):
    delay = 0

    def __init__(self, config_t=config, start_t_t=start_t):
        self.config_t = config_t
        self.start_t_t = start_t_t
        super(TweetStreamer, self).__init__(config_t.credentials.CONSUMER_KEY, config_t.credentials.CONSUMER_SECRET, config_t.credentials.ACCESS_KEY,
                                    config_t.credentials.ACCESS_SECRET)

    def on_success(self, data):
        if time.time() > self.start_t_t + self.config_t.read_time:
            self.disconnect()
        if 'text' in data:
            tweets.append(data['text'])

    def on_error(self, status_code, data):
        print('TweetStreamer Error: ' + repr(status_code) + ': ' + repr(data))
        if status_code == 420:
            self.delay += 1
            print("delay=" + repr(self.delay))
            time.sleep(self.delay)
            self.config_t.read_time += self.delay



class TwitterAccess(Twython):
    def __init__(self):
        super(TwitterAccess, self).__init__(config.credentials.CONSUMER_KEY, config.credentials.CONSUMER_SECRET, config.credentials.ACCESS_KEY,
                                            config.credentials.ACCESS_SECRET)


def create_hash_table(tweet_list):
    for tweet in tweet_list:
        for i in range(len(tweet)-1):
            cur_word = tweet[i]
            next_word = tweet[i+1]

            all_words.append(cur_word)
            all_words.append(next_word)

            # Check the current and next words against the ban lists
            # if cur_word in banned_phrases.keys() and next_word == banned_phrases[cur_word]:
            if config.phrase_banned(cur_word, next_word) or config.word_banned(cur_word) \
                    or config.word_banned(next_word):
                pass
            # elif cur_word in banned_words or next_word in banned_words:
            #    pass

            else:
                if cur_word not in bigram_hash:
                    bigram_hash[cur_word] = {}

                if next_word not in bigram_hash[cur_word]:
                    bigram_hash[cur_word][next_word] = 1
                else:
                    bigram_hash[cur_word][next_word] += 1


def create_tweet(max_len):
    text = ""
    cur_word = "@"  # Begin with a word we know isn't in the list

    # Start with a randomly chosen word in the hash table
    while cur_word not in bigram_hash:
        cur_word = all_words[random.randint(1, len(all_words))]
    text += cur_word.capitalize()

    num_words = 1

    # Loop until one of the break conditions is met
    while True:
        # Get the next word in the tweet (most common word following cur_word) and remove that word from the hash table
        try:
            next_word = max(bigram_hash[cur_word], key=bigram_hash[cur_word].get)
            bigram_hash[cur_word].pop(next_word)
        # If a KeyError or ValueError is thrown, it means that there isn't a next word in the list
        except ValueError:
            break
        except KeyError:
            break

        cur_word = next_word

        # If the tweet will be too long when the next word is added, break
        if len(text) + len(cur_word) + 1 > max_len:
            break
        else:
            text += " " + cur_word
            num_words += 1

    # Make sure the number of words in the tweet meets the minimum length
    if num_words < config.min_len:
        return None
    else:
        print("Tweet generation successful: ", end='')
        try:
            print("'" + text + "' (" + str(len(text)) + " chars)")
        except TypeError:
            print()
            pass
        return text

class GetTweetTimed(Resource):
    def get(self, read_time):
        t = GetTweet()
        return t.get(read_time)

class GetTweet(Resource):

    def get(self, read_time=10):
        global start_t
        global acc_tweets
        global tweets
        global all_words
        global bigram_hash

        global config

        try:
            config = Settings()
            print()

        except RequiredFileNotFoundException as e:
            return {'Error': e.msg}
            exit(1)

        except MalformedConfigurationError as e:
            return {'Error': e.msg}
            exit(1)

        all_words = []
        tweets = []
        acc_tweets = []
        bigram_hash = {}

        start_t = time.time()
        while time.time() < start_t + read_time:
            try:
                stream = TweetStreamer()
                stream.statuses.filter(track='twitter', language='en')
            except requests.exceptions.ChunkedEncodingError:
                pass

        for x in tweets:
            raw_text = x.split(' ')
            text = []
            for word in raw_text:
                if not re.match(match_pattern, word):
                    text.append(word)
            acc_tweets.append(text)

        create_hash_table(acc_tweets)
        tweet_text = None
        tweet_info = "\n[" + repr(read_time) + "s/" + repr(len(tweets)) + " tweets]"
        while tweet_text is None:
            tweet_text = create_tweet(140 - len(tweet_info))

        return {'tweet_text': tweet_text, 'tweet_info': tweet_info}

api.add_resource(GetTweetTimed, '/tweet/<int:read_time>')
api.add_resource(GetTweet, '/tweet')

if __name__ == '__main__':
    app.run()
