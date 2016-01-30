from TwitterSearch import *
import time
import random
import serial
import ik
import math

# Polargraph settings
# Serial settings
COMPORT = "COM6"
BAUD = 57600
# Physical dimensions
polargraphWidthInMM = 610
polargraphHeightInMM = 1165
polargraphHomeXInMM = polargraphWidthInMM/2
polargraphHomeYInMM = 120
pageWidthInMM = 420
pageHeightInMM = 594
pageXOffsetInMM = 95
pageYOffsetInMM = 240
# Grid dimensions
cellWidthInMM = 25
cellHeightInMM = 25
numberOfCols = math.floor(pageWidthInMM / cellWidthInMM)
numberOfRows = math.floor(pageHeightInMM / cellHeightInMM)
xOffSetRemainder = math.floor((pageWidthInMM - (numberOfCols * cellWidthInMM)) / 2)
yOffSetRemainder = math.floor((pageHeightInMM - (numberOfRows * cellHeightInMM)) / 2)


# Global variable for serial coms function
# This exists to tell the next call of the comms functions
# that the previous exit was because a 'READY' was seen after
# exiting the function so the next call doesn't have to wait
# for the polargraph to send another 'READY' message.
polargraphReadySeen = False
#Open serial port at baud and a timeout of secs
serialPort = serial.Serial(COMPORT,BAUD,timeout=10)

# Global variables for TwitterSearch
tweetLastSeenID = 0
lastTweetCount = 0
lastX = 0
lastY = 0

# Other global variables


def twitSearch(tweetLastSeen):
    print("In function twitSearch()")
    tweetSearchCount = 0
    try:
        tso = TwitterSearchOrder()
        tso.set_keywords(['disaster'])
        #tso.add_keyword(['poverty'])
        tso.set_language('en')
        #tso.set_include_entities(False)

        if tweetLastSeen > 0:
            print("I have a previous value for lastseen_id %s, asking for 100 results" % tweetLastSeen)
            tso.set_since_id(tweetLastSeen)
            tso.set_count(100)
        else:
            print("No value for lastseen_id, asking for one result")
            tso.set_count(1)

        ts = TwitterSearch(
            consumer_key = '',
            consumer_secret = '',
            access_token = '',
            access_token_secret = '')

        twitSearchResults = ts.search_tweets_iterable(tso)
        
        queries, tweets_seen = ts.get_statistics()

        print("Debug: Queries done: %i. Tweets received: %i" %(queries, tweets_seen))

        tweetCount = 0
        for tweet in twitSearchResults:
            #print(tweet['id'])
            tweetLastSeenID = tweet['id']
            tweetCount = tweetCount + 1

        print("Debug: I counted %s tweets" % tweetCount)            

        #print("Debug: Querying twitterSeach object for stats now")
        #queries, tweets_seen = ts.get_statistics()
        #print("Debug: Seen %s tweets in this search and used %s queries" %(queries, tweets_seen))
        
        #print("About to iterate over search results from TwitterSearch instance")
        #print("Debug: In 'iterate over tweets' loop now")
        #print("@%s tweeted: %s" % (tweet['user']['screen_name'], tweet['text']))
        #tweetLastSeenID = tweet['id']
        #print("@%s tweet ID" %(tweetLastSeenID) )
        return tweetLastSeenID, tweets_seen
        #break

    except TwitterSearchException as e:
        print(e)
    

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


def pen(upDown):
    if upDown == 'up' or upDown == 'Up' or upDown == 'UP' or upDown == 'False':
        # Pen Up
        writeCommandToPolargraph("C14,END\n")
    elif upDown == 'down' or upDown == 'Down' or upDown == 'DOWN' or upDown == 'True':
        # Pen Down
        writeCommandToPolargraph("C13,END\n")
    else:
        # Does not compute
        print("Debug: pen() takes either up or down. I'm sorry Dave... I can't do that")
        pass

def moveTo(x,y):
    # Assume coords are in mm so convert to native by calling ik.getStringLengths(x,y)
    # ik.getStringLengths(x,y) returns a tuple with 4 items, a pair of native coords
    # followed by the string length in mm
    nativeCoords = ik.getStringLengths(x,y)
    # As this is a move, lift the pen first just to be sure
    pen("up")
    command = "C01," + str(nativeCoords[0]) + "," + str(nativeCoords[1]) + ",END\n"
    print("Debug: moveTo(%s,%s) Command to run: %s" % ( x,y,(command,)))
    writeCommandToPolargraph(command)
    

def drawTo(x,y,segmentLength):
    # Assume coords are in mm so convert to native by calling ik.getStringLengths(x,y)
    # ik.getStringLengths(x,y) returns a tuple with 4 items, a pair of native coords
    # followed by the string length in mm
    nativeCoords = ik.getStringLengths(x,y)
    # As this is a move, drop the pen first just to be sure
    pen("down")
    command = "C17," + str(nativeCoords[0]) + "," + str(nativeCoords[1]) + "," + str(segmentLength) + ",END\n"
    print("Debug: drawTo(%s,%s) Command to run: %s" % ( x,y,(command,)))
    writeCommandToPolargraph(command)
    # and lift the pen afterwards so we don't bleed out the pen on the paper
    # This should be done manually or we end up with lots of servo moves
    #pen("up")

def getCellCoordinates(xCell, yCell):
    # Get the real coordinates (in MM) for the bottom left of the given cell
    # Assume cell coordinates start at zero

    #cellWidthInMM & cellWidthInHeight and offsets are globals

    print("Debug:X: cellWidth: %s, page offset: %s, offset remainder: %s" %(cellWidthInMM, pageXOffsetInMM, xOffSetRemainder))
    print("Debug:Y: cellWidth: %s, page offset: %s, offset remainder: %s" %(cellHeightInMM, pageYOffsetInMM, yOffSetRemainder))
    xCoordsInMM = ((xCell + 1) * cellWidthInMM) + pageXOffsetInMM + xOffSetRemainder
    yCoordsInMM = ((yCell + 1) * cellHeightInMM) + pageYOffsetInMM + yOffSetRemainder

    return xCoordsInMM, yCoordsInMM

def drawBlip(xCell, yCell, blipVal):
    # This function will draw a 'blip' or 'peak' for the given value in the cell specified
    # Do we need to start with a move or assume the pen is in the right place?
    xCoordsInMM, yCoordsInMM = getCellCoordinates(xCell, yCell)
    moveTo(xCoordsInMM, yCoordsInMM)

    # Draw to a point midway along the width of the cell
    # and the result of the twitter search high
    drawTo((xCoordsInMM+(cellWidthInMM/2)),(yCoordsInMM-blipVal),2)

    # Finally draw to the bottom right of the current cell
    drawTo((xCoordsInMM + cellWidthInMM), yCoordsInMM, 2)
    pen("up")
    
def test1():
    # Servo Up/Down 
    #commandList = ["C13,63,END\n","C14,125,END\n"]
    print("Test 1: Testing wrapper functions")
    print("")

    # test pen() function
    #pen("down")
    #pen("up")

    # Move (don't draw) to the 4 corners of a box that defines the notional drawing area (end at the home position)
    # These coords are from my machine, are in mm and define the corners of the page extents
    
    # top left, top right, bottom right, top left
    #moveTo(95,240)
    #moveTo(515,240)
    #moveTo(515,834)
    #moveTo(95,834)
    #moveTo(95,240)

    # home
    #moveTo(305,120)
    

    # Draw a box around the notional drawing area (end at the home position)
    # These coords are from my machine, are in mm and will draw the page edges

    # top left, top right, bottom right, top left
    #moveTo(95,240)
    #drawTo(515,240,2)
    #drawTo(515,834,2)
    #drawTo(95,834,2)
    #drawTo(95,240,2)
    # home
    #moveTo(305,120)

    # Testing the 'blip' function. This draws a 'blip' of the given value in the chosen cell
    # def drawBlip(xCell, yCell, blipVal)
    drawBlip(0,0,25)
    
    #input("Test completed, press enter to continue") 


    

# Setup the Polargraph once
setupPolargraph()  

while True:
    #print("Calling twitter search")
    #tweetLastSeenID, lastTweetCount = twitSearch(tweetLastSeenID)
    #print("Result of twitSearch(): Tweet Count=%s, Most recent Tweet ID=%s" %(lastTweetCount, tweetLastSeenID))
    #print("")

    print("Starting blip loop")
    for y in range(numberOfRows, 0, -1):
        print("Debug: y = %s of %s" %(y, numberOfRows))
        for x in range(0,numberOfCols):
            print("Debug: x = %s of %s" %(x, numberOfCols))
            #print("Calling twitter search using tweetLastSeenID = %s" %tweetLastSeenID)
            #tweetLastSeenID, lastTweetCount = twitSearch(tweetLastSeenID)
            print("Debug: lastTweetCount = %s" %lastTweetCount)
            #drawBlip(x,y,lastTweetCount)
            drawBlip(x,y,random.randint(0,100))
            print("sleeping...")
            #time.sleep(60)
    

    # Run a test
    #test1()
        
    #print("sleeping...")
    #time.sleep(60)

    


