#   bot.py
#   Erik McLaughlin
#   1/16/17

from twython import Twython
from twython import TwythonStreamer
import time
import re

cred_file = "credentials.txt"

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_KEY = ''
ACCESS_SECRET = ''

acc_tweets = []
rej_tweets = []
start_t = -1
read_time = 10

match_pattern = r'^[a-zA-Z0-9 !\.@:/]+$'


class TweetStreamer(TwythonStreamer):
    def on_success(self, data):
        if time.time() > start_t + read_time:
            self.disconnect()
        if 'text' in data:
            if re.match(match_pattern, data['text']):
                acc_tweets.append(data['text'])
                #print(data['text'])
            else:
                rej_tweets.append(data['text'])

    def on_error(self, status_code, data):
        print(status_code)


def read_creds(fname):
    data = []
    with open(fname) as file:
        for line in file:
            data.append(line.strip())

    return data[0], data[1], data[2], data[3]


def main():
    global CONSUMER_KEY
    global CONSUMER_SECRET
    global ACCESS_KEY
    global ACCESS_SECRET

    global start_t
    global acc_tweets

    CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET = read_creds(cred_file)

    while True:
        start_t = time.time()
        stream = TweetStreamer(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)
        stream.statuses.filter(track='twitter')

        #for x in acc_tweets:
        #    print(x)

        twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)
        #twitter.update_status(status=str(len(acc_tweets)) + " accepted, " + str(len(rej_tweets)) + " rejected tweets")
        print(str(len(acc_tweets)) + " accepted, " + str(len(rej_tweets)) + " rejected tweets")

main()
