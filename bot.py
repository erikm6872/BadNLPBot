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
min_len = 5
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


#   Read the credentials file (default: credentials.txt)
def read_creds(fname):
    data = []
    with open(fname) as file:
        for line in file:
            data.append(line.strip())

    return data[0], data[1], data[2], data[3]


#   Read the settings file (default:
def read_cfg(fname):
    data = []
    with open(fname) as file:
        for line in file:
            data.append(line.strip())

    return int(data[0]), data[1], int(data[2])


def create_tweet():
    text = ""
    cur_word = "@"  # Begin with a word we know isn't in the list

    # Start with a randomly chosen word in the hash table
    while cur_word not in bigram_hash:
        cur_word = all_words[random.randint(1, len(all_words))]
    cur_word = cur_word.capitalize()
    text += cur_word
    num_words = 1
    while True:
        try:
            next_word_options = list(bigram_hash[cur_word].keys())
        except KeyError:
            break

        # Get the next word in the tweet (most common word following cur_word) and remove that word from the hash table
        try:
            next_word = max(bigram_hash[cur_word], key=bigram_hash[cur_word].get)
            bigram_hash[cur_word].pop(next_word)
        except ValueError:
            break

        cur_word = next_word

        if len(text) + len(cur_word) > 140:
            break
        else:
            text += " " + cur_word
            num_words += 1

    # Make sure the number of words in the tweet meets the minimum length
    if num_words < min_len:
        #print("Generated tweet does not meet minimum word length (" + str(min_len) + "), regenerating...")
        return None
    else:
        print("Tweet generation successful: ", end='')
        try:
            print("'" + text + "' (" + str(len(text)) + " chars)")
        except TypeError:
            print()
            pass
        return text


def main():
    global CONSUMER_KEY
    global CONSUMER_SECRET
    global ACCESS_KEY
    global ACCESS_SECRET

    global start_t
    global read_time
    global min_len
    global acc_tweets
    global tweets
    global all_words
    global bigram_hash

    CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET = read_creds(cred_file)
    read_time, pattern, min_len = read_cfg(cfg_file)

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
        tweet_text = None
        while tweet_text is None:
            tweet_text = create_tweet()

        twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)
        print("")
        #print(tweet_text + " ** " + repr(len(tweet_text)) + "\n")   #Print

        twitter.update_status(status=tweet_text)


main()
