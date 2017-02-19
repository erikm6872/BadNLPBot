#   bot.py
#   Erik McLaughlin
#   1/16/17

from twython import Twython
from twython import TwythonStreamer
import time
import re
import random
import requests

cred_file = "credentials.txt"
cfg_file = "settings.cfg"

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_KEY = ''
ACCESS_SECRET = ''

tweets = []
acc_tweets = []

start_t = -1
read_time = 0

banned_words = ['']

match_pattern = r'[@].*|RT|http.*|.*\\n.*|[^a-zA-Z0-9!\?\.]'  # Pattern to reject
all_words = []
bigram_hash = {}


class TweetStreamer(TwythonStreamer):
    def on_success(self, data):
        if time.time() > start_t + read_time:
            self.disconnect()
        if 'text' in data:
            tweets.append(data['text'])
            #print(data['text'])

    def on_error(self, status_code, data):
        print(status_code)


def create_hash_table(tweet_list):
    for tweet in tweet_list:
        for i in range(len(tweet)-1):
            cur_word = tweet[i]
            next_word = tweet[i+1]

            all_words.append(cur_word)
            all_words.append(next_word)

            if cur_word not in bigram_hash:
                bigram_hash[cur_word] = {}

            if next_word not in bigram_hash[cur_word]:
                bigram_hash[cur_word][next_word] = 1
            else:
                bigram_hash[cur_word][next_word] += 1

    #print(bigram_hash)


def read_creds(fname):
    data = []
    with open(fname) as file:
        for line in file:
            data.append(line.strip())

    return data[0], data[1], data[2], data[3]


def read_cfg(fname):
    data = []
    with open(fname) as file:
        for line in file:
            data.append(line.strip())

    return int(data[0])  # , data[1], data[2], data[3]


def create_tweet():
    text = ""
    cur_word = "@"  # Begin with a word we know isn't in the list
    while cur_word not in bigram_hash:
        cur_word = all_words[random.randint(1, len(all_words))]
    cur_word = cur_word.capitalize()
    text += cur_word
    while len(text) < 130:
        try:
            next_word_options = list(bigram_hash[cur_word].keys())
        except KeyError:
            break
        cur_word = next_word_options[random.randint(0, len(next_word_options)-1)]   # Todo: remove random elements
        text += " " + cur_word
    #print(text)
    return text


def main():
    global CONSUMER_KEY
    global CONSUMER_SECRET
    global ACCESS_KEY
    global ACCESS_SECRET

    global start_t
    global read_time
    global acc_tweets
    global tweets
    global all_words
    global bigram_hash

    CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET = read_creds(cred_file)
    read_time = read_cfg(cfg_file)

    while True:
        all_words = []
        tweets = []
        acc_tweets = []
        bigram_hash = {}

        start_t = time.time()
        print("Collecting tweets for " + repr(read_time) + " seconds...")
        while time.time() < start_t + read_time:
            try:
                stream = TweetStreamer(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)
                stream.statuses.filter(track='twitter', language='en')
            except requests.exceptions.ChunkedEncodingError as e:
                #print("Error: " + repr(e))
                pass

        print("Tweets collected. Processing...")
        for x in tweets:
            raw_text = x.split(' ')
            text = []
            for word in raw_text:
                if not re.match(match_pattern, word):
                    text.append(word)
            acc_tweets.append(text)

        create_hash_table(acc_tweets)
        tweet_text = create_tweet()


        twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)
        print("")
        #print(tweet_text + " ** " + repr(len(tweet_text)) + "\n")   #Print

        twitter.update_status(status=tweet_text)


main()
