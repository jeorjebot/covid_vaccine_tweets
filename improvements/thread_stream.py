import queue
import threading
import tweepy
import json
from pymongo import MongoClient


"""
TODO automatic reconnection
TODO threading
"""



# Change your hashtags here
WORDS = ['vaccino dosi', 'vaccino', 'vaccini', 'vaccinazione', 'vaccinato', 'vaccinati', 'pfizer', 'biontech', 'moderna', 'astrazeneca', 'curevac'] # This is an OR relation

# Insert your keys here
CONSUMER_KEY = None
CONSUMER_SECRET = None
ACCESS_TOKEN = None
ACCESS_TOKEN_SECRET = None


with open('keys.txt') as keys:
    CONSUMER_KEY = keys.readline().replace('\n', '')
    CONSUMER_SECRET = keys.readline().replace('\n', '')
    ACCESS_TOKEN = keys.readline().replace('\n', '')
    ACCESS_TOKEN_SECRET = keys.readline().replace('\n', '')


class StreamListener(tweepy.StreamListener):    
    #This is a class provided by tweepy to access the Twitter Streaming API. 

    def __init__(self, api, q = queue.Queue()):

        super().__init__(api)
        
        num_worker_threads = 2
        self.q = q
        for i in range(num_worker_threads):
                t = threading.Thread(target=self.load_on_db, args=(i,))
                t.daemon = True
                t.start()
                print(f"Thread {i} started")

    def on_connect(self):
        # Called initially to connect to the Streaming API
        print("You are now connected to the streaming API.")
 
    def on_error(self, status_code):
        # On error - if an error occurs, display the error / status code
        print('An Error has occured: ' + repr(status_code))
        return False
    
    def on_data(self, data):
        self.q.put(data)
        print("arrived")

    def enqueue(self, worker_id):
        while True:
            data = self.q.get()
            self.load_on_db(data, worker_id)
            self.q.task_done()
            
    def load_on_db(data, worker_id):
        #This is the meat of the script...it connects to your mongoDB and stores the tweet
        try:
            client = MongoClient('localhost', 27017, username='mongoadmin', password='pass1234')
            
            # Use test database. If it doesn't exist, it will be created.
            db = client.test
    
            # Decode the JSON from Twitter
            datajson = json.loads(data)
            
            #grab the 'created_at' data from the Tweet to use for display
            created_at = datajson['created_at']
            username = datajson['user']['screen_name']

            #print out a message to the screen that we have collected a tweet
            print(f"Tweet collected at {str(created_at)} from user @{username} | thread {worker_id}")
            
            #insert the data into the mongoDB into a collection called twitter_search
            #if twitter_search doesn't exist, it will be created.
            db.tweets.insert_one(datajson)

        except Exception as e:
            print(e)

# Authentication
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# The 'wait_on_rate_limit=True' is needed to help with Twitter API rate limiting.
api = tweepy.API(auth, wait_on_rate_limit=True,
    wait_on_rate_limit_notify=True)

try:
    api.verify_credentials()
    print("Authentication OK")
except:
    print("Error during authentication")


#Set up the listener. 
listener = StreamListener(api=api) 
streamer = tweepy.Stream(auth=auth, listener=listener)
print("Tracking: " + str(WORDS))
streamer.filter(languages=["it"], track=WORDS)


