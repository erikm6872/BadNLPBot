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
banned_words_file = "banned_words.txt"
banned_phrase_file = "banned_phrases.txt"

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_KEY = ''
ACCESS_SECRET = ''

tweets = []
acc_tweets = []

start_t = -1
read_time = 0
min_len = 5
banned_words = []
banned_phrases = {}

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
            if cur_word in banned_phrases.keys() and next_word == banned_phrases[cur_word]:
                pass
            else:
            #if cur_word != "most" or next_word != "fucked":
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


#   Read the settings file (default: settings.cfg)
def read_cfg(fname):
    data = []
    with open(fname) as file:
        for line in file:
            data.append(line.strip())

    return int(data[0]), data[1], int(data[2])


#   Read the banned words and phrases file.
def read_ban_files(word_fname, phrase_fname):
    global banned_words
    global banned_phrases

    with open(word_fname) as word_file:
        for line in word_file:
            banned_words.append(line.strip())

    with open(phrase_fname) as phrase_file:
        for line in phrase_file:
            words = line.strip().split(',')
            banned_phrases[words[0]] = words[1]


def create_tweet(max_len):
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

        if len(text) + len(cur_word) + 1 > max_len:
            break
        else:
            text += " " + cur_word
            num_words += 1

    # Make sure the number of words in the tweet meets the minimum length
    if num_words < min_len:
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
    read_ban_files(banned_words_file, banned_phrase_file)

    while True:
        all_words = []
        tweets = []
        acc_tweets = []
        bigram_hash = {}

        start_t = time.time()
        print("[" + time.strftime("%m/%d/%y %H:%M:%S") + "] Collecting tweets for " + repr(read_time) + " seconds...")
        while time.time() < start_t + read_time:
            try:
                stream = TweetStreamer(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)
                stream.statuses.filter(track='twitter', language='en')
            except requests.exceptions.ChunkedEncodingError as e:
                #print("Error: " + repr(e))
                pass

        print("[" + time.strftime("%m/%d/%y %H:%M:%S") + "]" + repr(len(tweets)) + " tweets collected. Processing...")
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

        tweet_text += tweet_info

        twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)
        print("")
        twitter.update_status(status=tweet_text)
        print("[" + time.strftime("%m/%d/%y %H:%M:%S") + "] Tweet posted successfully.")


main()
