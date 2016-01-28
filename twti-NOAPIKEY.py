from TwitterSearch import *
import time
import random
import serial
import ik

COMPORT = "COM6"
BAUD = 57600
TIMEOUT = "timeout=0"

# Global variable for serial coms function
# This exists to tell the next call of the comms functions
# that the previous exit was because a 'READY' was seen after
# exiting the function so the next call doesn't have to wait
# for the polargraph to send another 'READY' message.
polargraphReadySeen = False

#Open serial port at baud and a timeout of secs
serialPort = serial.Serial(COMPORT,BAUD,timeout=10)
# Wait a while for the controller to respond
time.sleep(3)
#serialPort.read(1000)

tweetLastSeenID = 0
lastTweetCount = 0
lastX = 0
lastY = 0

def twitSearch(tweetLastSeen):
    #print("In function twitSearch()")
    tweetSearchCount = 0
    try:
        tso = TwitterSearchOrder()
        tso.set_keywords(['disaster'])
        tso.set_language('en')
        tso.set_include_entities(False)
        if tweetLastSeen > 0:
            #print("I have a previous value for lastseen_id, asking for 100 results")
            tso.set_since_id(tweetLastSeen)
            tso.set_count(100)
        else:
            #print("No value for lastseen_id, asking for one result")
            tso.set_count(1)

        ts = TwitterSearch(
            consumer_key = '',
            consumer_secret = '',
            access_token = '',
            access_token_secret = '')

        def my_callback_function(current_ts_instance): # accepts ONE argument: an instance of TwitterSearch
            #print("In callback function")
            queries, tweets_seen = current_ts_instance.get_statistics()
            #print("%s queries & %s tweets seen" %(queries, tweets_seen))
            if queries > 0 and (queries % 5) == 0: # trigger delay every 5th query
                #print("Thats 5 queries. Sleeping for 60 secs")
                time.sleep(60) # sleep for 60 seconds

        #print("About to iterate over search results from TwitterSearch instance")
        #for tweet in ts.search_tweets_iterable(tso, callback=my_callback_function):
        for tweet in ts.search_tweets_iterable(tso):    
            queries, tweets_seen = ts.get_statistics()
            #print( '@%s tweeted: %s' % ( tweet['user']['screen_name'], tweet['text'] ) )
            tweetLastSeenID = tweet['id']
            #print( '@%s tweet ID' %(tweetLastSeenID) )
            return tweetLastSeenID, tweets_seen
            break



    except TwitterSearchException as e:
        print(e)

    
def generatePolargraphCommands(lastTweetCount, lastX, lastY):
    #print("In generatePolargraphCommands()")
    xGridSize = 100
    yGridSize = 100
    commandList = []
    #Pen down
    commandList.append("C13,END\n")
    #Move pen to peak
    tempString = "C17,"+str(int(lastX+(xGridSize/2)))+","+str(int(lastY+(lastTweetCount)))+",2,END\n"
    #print(tempString)
    commandList.append(tempString)
    #Move pen to bottom of graph
    lastX = int(lastX+xGridSize)
    tempString = "C17,"+str(lastX)+","+str(int(lastY))+",2,END\n"
    #print(tempString)
    commandList.append(tempString)
    commandList.append("C14,END\n")
    return commandList, lastX, lastY

def writeCommandToPolargraph(command):
    # Attempt to simplify the serial read/write logic
    # Write one command only and return ready to calling function (let calling function deal with iterables)

    global polargraphReadySeen
    
    print("")
    print("=================================")
    print("Call to writeCommandToPolargraph")
    print("")
    
    exitFlag = False
    
    while True:
        # Read the serial port buffer and assign the result to the dataRead variable

        #print("")
        #print("Debug: Reading serial port section starts here:")

        # Reading the serial port by bytes avoids the need to skip the check if we have previously seen 'READY'
        # and also empties the buffer so we don't get out of sync if there is a long delay.
        numberOfBytesWaiting = serialPort.in_waiting
        #if numberOfBytesWaiting > 0:
        #    print("Debug: Bytes waiting in serial port = %s" % numberOfBytesWaiting)

        # Read the data as ASCII text (remove the terminating chars and decode bytes to ascii)
        # Note strip() used with no parameters should strip whitespace chars (i.e. tab, space, linefeed etc)
        dataRead = serialPort.read(numberOfBytesWaiting).strip().decode()
        #print("Debug: dataRead is '%s'" % dataRead)

        # A short delay allows the serial buffer to fill up else we get partial reads of the 'READY' message.
        time.sleep(0.1)
        

        # If dataRead contains the text 'READY' or the write command has run and a subsequent read returned 'READY' and
        # set the polargraphReadySeen flag (is this now redundant?)
        #if dataRead == "READY" or polargraphReadySeen == True:
        if "READY" in dataRead or polargraphReadySeen == True:
            #print("Debug: In 'READY' case: dataRead should be 'READY' (is '%s') or polargraphReadySeen should be true (is '%s')" % (dataRead, polargraphReadySeen))
            if not exitFlag:
                #print("Debug: exitFlag should be false here. Is %s" % exitFlag)
                print("Write command: %s" % command)
                #serialPort.flush()
                serialPort.write(command.encode('ascii'))

                polargraphReadySeen = False
                exitFlag = True
                
            else:
                #print("Debug: exitFlag should be true here. Is '%s'. Setting polargraphReadySeen flag to true" % exitFlag)
                print("MSG: '%s'" % dataRead)
                print("")
                print("Exiting writeCommandToPolargraph2")
                print("=================================")
                print("")

                polargraphReadySeen = True
                return "DONE"
            
        # If dataRead is empty
        elif not dataRead:
            #print("Debug: dataRead is '%s', ignoring..." % dataRead)
            pass
        # If dataRead doesn't contain 'READY' or is not 'NULL' then it is probably an error message or other info
        else:
            #print("Debug: data categorised as 'Not null' or not 'READY'. Print data and move on. dataRead is '%s'" % dataRead)
            print("MSG: '%s'" % dataRead)

def setupPolargraph():
    setupCommand = ["C02,0.36,END\n"] #Set pen width in mm
    setupCommand.append("C24,610,1165,END\n") #Set machine size in mm
    setupCommand.append("C29,92,END\n") #Set mm per revolution
    setupCommand.append("C30,200,END\n") #Set native motor steps per revolution
    setupCommand.append("C31,1200,1,END\n") #Set motor speed
    setupCommand.append("C32,800,1,END\n") #Set motor acceleration
    setupCommand.append("C37,16,END\n") #Set micro stepping multiplier
    setupCommand.append("C45,63,125,1,END\n") #Sets pen lift range
    #setupCommand.append("C09,789,1002,END\n") #Set pen position
    #setupCommand.append("C01,711,711,END\n") #Move to pen position (711,711 = home)
    setupCommand.append("C09,711,711,END\n") #Set pen position as home (you can then manually set the pen to a known position) 305mm x 119mm is home on my machine
    setupCommand.append("C13,63,END\n") #Set drop pen position
    setupCommand.append("C14,125,END\n") #Set lift pen position
    #setupCommand.append("")

    print("")
    print("Setting up the controller...")
    print("")
    for each in setupCommand:
        writeCommandToPolargraph(each)    
    
    print("")
    print("Setup done!")
    input("Manually set pen to home position and press enter to continue when done")
    print("")


#Call polargraph setup function
setupPolargraph()
        
def test1():
    # Servo Up/Down 
    commandList = ["C13,63,END\n","C14,125,END\n"]
    print("Test 1: Sending pen up/down commands to Polargraph")
    print("")
    
    for each in commandList:
        print("Command to send: '%s'" % each.strip())
        writeCommandToPolargraph(each)
        #input("Command completed, press enter to continue") 
    #input("Test completed, press enter to continue") 

def test2():
    # Move
    commandList = ["C01,564,1237,END\n","C01,1237,564,END\n","C01,2131,1826,END\n","C01,1826,2131,END\n","C01,305,119,END\n"]
    print("Test 2: Move to top left then move to all 4 corners of the page ending up where we started")
    print("")
    
    for each in commandList:
        print("Command to send: '%s'" % each.strip())
        writeCommandToPolargraph(each)
        #input("Command completed, press enter to continue") 
    #input("Test completed, press enter to continue") 

def test3():
    # Move & Draw
    #ommandList = ["C01,630,1200,END\n","C17,1200,630,END\n","C17,2000,1800,END\n","C17,1800,2000,END\n","C17,630,1200,END\n"]
    commandList = ["C01,601,1219,END\n","C17,1217,608,END\n","C17,2077,1788,END\n","C17,1791,2076,END\n","C17,601,1212,END\n"]
    print("Test 3: Move to top left then draw a line to all 4 corners of the page ending up where we started")
    print("")
    
    for each in commandList:
        print("Command to send: '%s'" % each.strip())
        writeCommandToPolargraph(each)
        #input("Command completed, press enter to continue") 
    #input("Test completed, press enter to continue") 

def test4():
    # Move & Draw
    commandList = ["C01,601,1219,END\n","C17,1217,608,2,END\n","C17,2077,1788,2,END\n","C17,1791,2076,2,END\n","C17,601,1212,2,END\n"]
    print("Test 4: Move to top left then draw a line to all 4 corners of the page ending up where we started")
    print("")
    
    for each in commandList:
        print("Command to send: '%s'" % each.strip())
        writeCommandToPolargraph(each)
        #input("Command completed, press enter to continue") 
    #input("Test completed, press enter to continue") 

def test5():
    # Move & Draw
    #ommandList = ["C01,630,1200,END\n","C17,1200,630,END\n","C17,2000,1800,END\n","C17,1800,2000,END\n","C17,630,1200,END\n"]
    commandList = ["C01,601,1219,END\n","C17,1217,608,1,END\n","C17,2077,1788,1,END\n","C17,1791,2076,1,END\n","C17,601,1212,1,END\n"]
    print("Test 5: Same as test 3 but supplying the segment length. Move to top left then draw a line to all 4 corners of the page ending up where we started")
    print("")
    
    for each in commandList:
        print("Command to send: '%s'" % each.strip())
        writeCommandToPolargraph(each)
        #input("Command completed, press enter to continue") 
    #input("Test completed, press enter to continue"

def test6():
    # Random Draw based on cartesian co-ods (convert with ik.py)
    result = ik.getStringLengths((711,711))
    print(result)
    

  

while True:
    #print("Calling twitter search")
    #tweetLastSeenID, lastTweetCount = twitSearch(tweetLastSeenID)
    #print("Result of twitSearch(): Tweet Count=%s, Most recent Tweet ID=%s" %(lastTweetCount, tweetLastSeenID))
    #print("")
    #commandList, lastX, lastY = generatePolargraphCommands(lastTweetCount, lastX, lastY)
    #print("Generated polargraph commands:")
    #print(commandList)

    #Test code for the generatePolargraphCommands() function
    #lastX = 0
    #lastY = 0
    #for x in range(0,10):
    #    pseudoTweetCount = random.randrange(1, 100, 1)
    #    #print("pseudoTweetCount = %s" %pseudoTweetCount)
    #    commandList, lastX, lastY = generatePolargraphCommands(pseudoTweetCount, lastX, lastY)
    #    print(commandList)


    # Servo Up/Down ### Pass
    #test1()

    # Move ### ?
    #test2()

    # test3()
    # See https://github.com/euphy/polargraph/wiki/Polargraph-machine-commands-and-responses
    # Search page for "Move pen direct"
    # Default is 2 !?! but it looks like the segment length is NOT optional so yeah - that might be why this fails.

    # Move & Draw. case with no segment length supplied. ###Fail 
    #test3()    
    #print("sleeping...")
    #time.sleep(25) 

    # Move & Draw. Segment length = 2 ###Pass
    #test4()
    #print("sleeping...")
    #time.sleep(25)

    # Move & Draw Segment length = 1. ###Pass
    #test5()
    #print("sleeping...")
    #time.sleep(25)

    test6()
    time.sleep(10)
