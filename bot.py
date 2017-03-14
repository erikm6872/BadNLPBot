#   bot.py
#   Erik McLaughlin
#   1/16/17

from twython import Twython
from twython import TwythonStreamer
import time
import re
import random
import requests

cfg_file = "settings.cfg"

cred_file = "credentials.txt"
banned_words_file = None
banned_phrases_file = None
read_time = 600
min_len = 10
banned_words = []
banned_phrases = {}

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_KEY = ''
ACCESS_SECRET = ''

tweets = []
acc_tweets = []

start_t = None

match_pattern = r'[@].*|RT|http.*|.*\\n.*|[^a-zA-Z0-9!\?\.]'  # Pattern to reject
all_words = []
bigram_hash = {}


class TweetStreamer(TwythonStreamer):
    def on_success(self, data):
        if time.time() > start_t + read_time:
            self.disconnect()
        if 'text' in data:
            tweets.append(data['text'])

    def on_error(self, status_code, data):
        print(status_code)


class RequiredFileNotFoundException(FileNotFoundError):
    def __init__(self, fname):
        self.msg = "Required file '" + fname + "' not found."
        super(RequiredFileNotFoundException, self).__init__(self.msg)


class MalformedConfigurationError(Exception):
    def __init__(self, msg=None):
        self.msg = msg
        super(MalformedConfigurationError, self).__init__(msg)


def create_hash_table(tweet_list):
    for tweet in tweet_list:
        for i in range(len(tweet)-1):
            cur_word = tweet[i]
            next_word = tweet[i+1]

            all_words.append(cur_word)
            all_words.append(next_word)

            # Check the current and next words against the ban lists
            if cur_word in banned_phrases.keys() and next_word == banned_phrases[cur_word]:
                pass
            elif cur_word in banned_words or next_word in banned_words:
                pass

            else:
                if cur_word not in bigram_hash:
                    bigram_hash[cur_word] = {}

                if next_word not in bigram_hash[cur_word]:
                    bigram_hash[cur_word][next_word] = 1
                else:
                    bigram_hash[cur_word][next_word] += 1


#   Read the credentials file (default: credentials.txt)
def read_creds(fname):
    data = []
    try:
        with open(fname) as file:
            for line in file:
                data.append(line.strip())
    except FileNotFoundError:
        raise RequiredFileNotFoundException(fname)

    return data[0], data[1], data[2], data[3]


#   Read the settings file (default: settings.cfg)
def read_cfg(fname):

    read_time_cfg = None
    min_words = None
    cred_fname = cred_file
    words_fname = None
    phrase_fname = None

    try:
        with open(fname) as file:
            for line in file:

                if line[0] != "#" and len(line) > 1:

                    cfg_val = line.strip().split('=')

                    key = cfg_val[0]
                    try:
                        val = cfg_val[1]
                    except IndexError:
                        raise MalformedConfigurationError("Configuration key '" + key + "' has no associated value")

                    if key == "read_time":
                        read_time_cfg = int(val)
                    elif key == "min_words":
                        min_words = int(val)
                    elif key == "cred_file":
                        cred_fname = val.strip("'")
                    elif key == "ban_words":
                        words_fname = val.strip("'")
                    elif key == "ban_phrase":
                        phrase_fname = val.strip("'")

                    else:
                        print("Warning: Configuration key '" + key + "' not recognized")
                        # raise MalformedConfigurationError("'" + key + "' is not a valid configuration key.")

    except FileNotFoundError:
        raise RequiredFileNotFoundException(fname)

    return read_time_cfg, min_words, cred_fname, words_fname, phrase_fname


#   Read the banned words and phrases file.
def read_ban_files(word_fname, phrase_fname):
    global banned_words
    global banned_phrases

    if word_fname is not None:
        try:
            with open(word_fname) as word_file:
                for line in word_file:
                    banned_words.append(line.strip())
        except FileNotFoundError:
            print("Warning: '" + word_fname + "' not found. No words will be banned.")
    else:
        print("Warning: No banned words file specified.")

    if phrase_fname is not None:
        try:
            with open(phrase_fname) as phrase_file:
                for line in phrase_file:
                    words = line.strip().split(',')
                    banned_phrases[words[0]] = words[1]
        except FileNotFoundError:
            print("Warning: '" + phrase_fname + "' not found. No phrases will be banned.")
    else:
        print("Warning: No banned phrases file specified.")


def create_tweet(max_len):
    text = ""
    cur_word = "@"  # Begin with a word we know isn't in the list

    # Start with a randomly chosen word in the hash table
    while cur_word not in bigram_hash:
        cur_word = all_words[random.randint(1, len(all_words))]
    cur_word = cur_word.capitalize()
    text += cur_word

    num_words = 1

    # Loop until one of the break conditions is met
    while True:

        # Get the next word in the tweet (most common word following cur_word) and remove that word from the hash table
        try:
            next_word = max(bigram_hash[cur_word], key=bigram_hash[cur_word].get)
            bigram_hash[cur_word].pop(next_word)
        # If a ValueError is thrown, it means that there isn't a next word in the list
        except ValueError:
            break

        cur_word = next_word

        # If the tweet will be too long when the next word is added, break
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
    global acc_tweets
    global tweets
    global all_words
    global bigram_hash

    global read_time
    global min_len
    global cred_file
    global banned_words_file
    global banned_phrase_file

    print("--------- Twitter Bot ---------")
    try:

        print("Reading config files...")
        read_time, min_len, cred_file, banned_words_file, banned_phrase_file = read_cfg(cfg_file)

        print("Reading credentials files...")
        CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET = read_creds(cred_file)

        print("Reading ban files...")
        read_ban_files(banned_words_file, banned_phrase_file)
        print()

    except RequiredFileNotFoundException as e:
        print("Error: " + e.msg)
        exit(1)

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
            except requests.exceptions.ChunkedEncodingError:
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
        twitter.update_status(status=tweet_text)
        print("[" + time.strftime("%m/%d/%y %H:%M:%S") + "] Tweet posted successfully.\n\n")


main()
