from TwitterSearch import *
import datetime
import time




tweetLastSeenID = 0
lastTweetCount = 0

twitterSearchCount = 0

def twitSearch(tweetLastSeen):
    #print("Debug: In function twitSearch()")
    tweetSearchCount = 0
    try:
        tso = TwitterSearchOrder()
        #tso.set_keywords(['disaster','banking'], or_operator = True)
        tso.set_keywords(['disaster','poverty','banking','homless'], or_operator = True)
        #tso.add_keyword('poverty')
        #tso.add_keyword('disaster')
        #tso.add_keyword('banking')
        tso.set_language('en')
        tso.set_include_entities(False)
        tso.set_result_type('recent')

        if tweetLastSeen > 0:
            print("Debug: I have a previous value for lastseen_id, setting since_id() to: %s and asking for 100 results" % tweetLastSeen)
            tso.set_since_id(tweetLastSeen)
            tso.set_count(100)
        else:
            print("Debug: No value for lastseen_id, asking for one result")
            tso.set_count(1)

        print("Debug: The tso search string looks like this")
        print(tso.create_search_url())

        ts = TwitterSearch(
            consumer_key = '',
            consumer_secret = '',
            access_token = '',
            access_token_secret = '')

##        def my_callback_function(current_ts_instance): # accepts ONE argument: an instance of TwitterSearch
##            #print("In callback function")
##            queries, tweets_seen = current_ts_instance.get_statistics()
##            #query = current_ts_instance.get_statistics()
##            print("%s queries & %s tweets seen" %(queries, tweets_seen))
##            print("%s query" %(query))
##            #if queries > 0 and (queries % 5) == 0: # trigger delay every 5th query
##                #print("Thats 5 queries. Sleeping for 60 secs")
##                #time.sleep(60) # sleep for 60 seconds

        #queries, tweets_seen = ts.get_statistics()
        #print("Debug: %s queries & %s tweets seen" %(queries, tweets_seen))

        #print("Debug: About to iterate over search results from TwitterSearch instance")
        #for tweet in ts.search_tweets_iterable(tso, callback=my_callback_function):
                
        tweets_seen = 0        
        currentTweetID = 0
        lastTweetID = 0

        for tweet in ts.search_tweets_iterable(tso):    
            queries, tweets_seen_by_stats = ts.get_statistics()
            print("Debug: stats: %s queries & %s tweets seen" %(queries, tweets_seen_by_stats))
            rateLimitRemaining = ts.get_metadata()['x-rate-limit-remaining']
            rateLimitReset = ts.get_metadata()['X-Rate-Limit-Reset']
            print("Debug: Rate limit resets at %s and has %s queries remaining" %(datetime.datetime.fromtimestamp(int(rateLimitReset)), rateLimitRemaining))
            currentTweetID = tweet['id']
            print("Debug: Current tweetID %s" % currentTweetID)
            if currentTweetID > lastTweetID:
                print("Debug: Seen a more recent tweetID, updating lastTweetID")
                lastTweetID = currentTweetID
                tweets_seen = tweets_seen_by_stats
                break
            print( 'Debug: In tweet iter @%s tweet id: %s' % ( tweet['user']['screen_name'], tweet['id'] ) )
            tweets_seen = tweets_seen + 1
            print("Debug: tweets_seens: %s" % tweets_seen)
            
        print('Debug: about to return tweet ID @%s' % lastTweetID )
        global twitterSearchCount
        twitterSearchCount = twitterSearchCount + 1
        print("Debug: This is twitter search number: %s" % twitterSearchCount)
        
        return lastTweetID, tweets_seen

    except TwitterSearchException as e:
        print(e)

# If script is called on its own (i.e. not as an imported module) run this
if __name__ == "__main__": 

    while True:
        print("Running standalone: Calling twitter search")
        print("Global var tweetLastSeenID is : %s" % tweetLastSeenID)
        try:
            result = twitSearch(tweetLastSeenID)
            tweetLastSeenID = result[0]
        except:
            # twitSearch failed to return a value setting tweets seen value to zero
            # and leaving the last tweet ID unchanged
            print("Debug: Twitter search prodced an error, continuting with previous values")
            
            input("So there has been that annoying twitterSearch error... can we recover? Press return to see...")
            result = 0
            result = twitSearch(tweetLastSeenID)
            tweetLastSeenID = result[0]
        print(tweetLastSeenID)
        print("Result of twitSearch(): Tweet Count=%s, Most recent Tweet ID=%s" %(lastTweetCount, tweetLastSeenID))
        print("sleeping for 60 secs...")
        print("")
        time.sleep(60)
