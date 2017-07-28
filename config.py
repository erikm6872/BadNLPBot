#   config.py
#   Erik McLaughlin
#   3/30/17


class RequiredFileNotFoundException(FileNotFoundError):
    def __init__(self, fname):
        self.msg = "Required file '" + fname + "' not found."
        super(RequiredFileNotFoundException, self).__init__(self.msg)


class MalformedConfigurationError(Exception):
    def __init__(self, msg=None):
        self.msg = msg
        super(MalformedConfigurationError, self).__init__(msg)


class Settings:
    # Default settings
    cred_file = "credentials.txt"
    banned_words_file = "banned_words.txt"
    banned_phrases_file = "banned_phrases.txt"
    read_time = 600
    min_len = 10
    time_format = "%m/%d/%y %H:%M:%S"
    lang = 'en'
    banned_words = []
    banned_phrases = {}

    def __init__(self, fname="settings.cfg"):
        self.read_settings(fname)
        self.read_ban_files(self.banned_words_file, self.banned_phrases_file)
        self.credentials = Credentials(self.cred_file)

    # Read configuration values from settings cfg
    def read_settings(self, fname):
        print("Reading config file '" + fname + "'...")
        try:
            with open(fname) as file:
                for line in file:

                    if line[0] != "#" and len(line) > 1:

                        data = line.strip().split('=')

                        key = data[0]
                        try:
                            val = data[1]
                        except IndexError:
                            raise MalformedConfigurationError("Configuration key '" + key + "' has no associated value")

                        if key == "read_time":
                            self.read_time = int(val)
                        elif key == "min_words":
                            self.min_len = int(val)
                        elif key == "cred_file":
                            self.cred_file = val.strip("'")
                        elif key == "ban_words":
                            self.banned_words_file = val.strip("'")
                        elif key == "ban_phrase":
                            self.banned_phrases_file = val.strip("'")
                        elif key == "time_format":
                            self.time_format = val.strip("'")
                        elif key == "lang":
                            self.lang = val.strip("'")
                        else:
                            raise MalformedConfigurationError("'" + key + "' is not a valid configuration key.")

        except FileNotFoundError:
            raise RequiredFileNotFoundException(fname)

    # Read the banned words and phrases file
    def read_ban_files(self, word_fname, phrase_fname):
        print("Reading ban files '" + word_fname + "', '" + phrase_fname + "'...")
        if word_fname is not None:
            try:
                with open(word_fname) as word_file:
                    for line in word_file:
                        self.banned_words.append(line.strip())
            except FileNotFoundError:
                print("Warning: '" + word_fname + "' not found. No words will be banned.")
        else:
            print("Warning: No banned words file specified.")

        if phrase_fname is not None:
            try:
                with open(phrase_fname) as phrase_file:
                    for line in phrase_file:
                        words = line.strip().split(',')
                        self.banned_phrases[words[0]] = words[1]
            except FileNotFoundError:
                print("Warning: '" + phrase_fname + "' not found. No phrases will be banned.")
        else:
            print("Warning: No banned phrases file specified.")

    # Check whether a word is in the ban list
    def word_banned(self, word):
        if word in self.banned_words:
            return True
        else:
            return False

    # Check if a combination of two words is in the banned phrase list
    def phrase_banned(self, word_one, word_two):
        if word_one in self.banned_phrases.keys() and word_two == self.banned_phrases[word_one]:
            return True
        else:
            return False


class Credentials:
    CONSUMER_KEY = ''
    CONSUMER_SECRET = ''
    ACCESS_KEY = ''
    ACCESS_SECRET = ''

    def __init__(self, fname):
        self.read_credentials(fname)

    def read_credentials(self, fname):
        print("Reading credentials file '" + fname + "'...")
        try:
            with open(fname) as file:
                for line in file:
                    data = line.strip().split("=")
                    key = data[0].upper()
                    val = data[1]

                    if key == "CONSUMER_KEY":
                        self.CONSUMER_KEY = val
                    elif key == "CONSUMER_SECRET":
                        self.CONSUMER_SECRET = val
                    elif key == "ACCESS_KEY":
                        self.ACCESS_KEY = val
                    elif key == "ACCESS_SECRET":
                        self.ACCESS_SECRET = val
                    else:
                        print("Warning: credential '" + key + "' not recognized.")

        except FileNotFoundError:
            raise RequiredFileNotFoundException(fname)

        if self.CONSUMER_KEY is None or self.CONSUMER_SECRET is None or self.ACCESS_KEY is None or self.ACCESS_SECRET is None:
            print("Warning: Incomplete credentials")
