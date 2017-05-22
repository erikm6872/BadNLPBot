#   bot.py
#   Erik McLaughlin
#   1/16/17

from config import *
from twython import Twython
from twython import TwythonStreamer
import time
import re
import random
import requests

config = None

tweets = []
acc_tweets = []

start_t = None

match_pattern = r'[@].*|RT|http.*|.*\\n.*|[^a-zA-Z0-9!\?\.]'  # Pattern to reject
all_words = []
bigram_hash = {}


class TweetStreamer(TwythonStreamer):
    def __init__(self):
        super(TweetStreamer, self).__init__(config.credentials.CONSUMER_KEY, config.credentials.CONSUMER_SECRET, config.credentials.ACCESS_KEY,
                                            config.credentials.ACCESS_SECRET)

    def on_success(self, data):
        if time.time() > start_t + config.read_time:
            self.disconnect()
        if 'text' in data:
            tweets.append(data['text'])

    def on_error(self, status_code, data):
        print(status_code)


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


def main():

    global start_t
    global acc_tweets
    global tweets
    global all_words
    global bigram_hash

    global config

    print("--------- Twitter Bot ---------")
    try:
        config = Settings()
        print()

    except RequiredFileNotFoundException as e:
        print("Error: " + e.msg)
        exit(1)

    except MalformedConfigurationError as e:
        print("Error: " + e.msg)
        exit(1)

    while True:
        all_words = []
        tweets = []
        acc_tweets = []
        bigram_hash = {}

        start_t = time.time()
        print("[" + time.strftime(config.time_format) + "] Collecting tweets for " + repr(config.read_time) + " seconds...")
        while time.time() < start_t + config.read_time:
            try:
                stream = TweetStreamer()
                stream.statuses.filter(track='twitter', language='en')
            except requests.exceptions.ChunkedEncodingError:
                pass

        print("[" + time.strftime(config.time_format) + "]" + repr(len(tweets)) + " tweets collected. Processing...")
        for x in tweets:
            raw_text = x.split(' ')
            text = []
            for word in raw_text:
                if not re.match(match_pattern, word):
                    text.append(word)
            acc_tweets.append(text)

        create_hash_table(acc_tweets)
        tweet_text = None
        tweet_info = "\n[" + repr(config.read_time) + "s/" + repr(len(tweets)) + " tweets]"
        while tweet_text is None:
            tweet_text = create_tweet(140 - len(tweet_info))

        tweet_text += tweet_info

        twitter = TwitterAccess()
        twitter.update_status(status=tweet_text)
        print("[" + time.strftime(config.time_format) + "] Tweet posted successfully.\n\n")


main()
