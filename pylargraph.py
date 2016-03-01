# Import python modules #
# TwitterSearch and serial will probably need to be imported using pip
# run the commands:
# pip install TwitterSearch
# pip install pyserial

from TwitterSearch import *
import math # Used to manipulate numbers
import time # Used for sleep() and to deal with dates in ik.py
import random # Used to generate random numbers for tests
import serial # Used to talk to the serial port
import sys # Used to find out which version of python (2 or 3) is running this script

# Import my modules #

import ik # ik.py converts x,y mm to string lengths in whole steps.
import twti # twti.py searches twitter and returns the most recent tweetID and the count of tweets for the chosen keywords (set in twti.py).
import myNotify # myNotify.py sends an email (useful if we plan to change pen colour when a full page has been plotted.


# Polargraph settings
# Serial settings
COMPORT = "COM8"
#COMPORT = "/dev/ttyUSB0"
BAUD = 57600

# Physical dimensions
# These are the dimensions that define the machine. Note: The home position in 'x' will be halfway between the motors but height is user defined
# TBD: The pulley and stepper motor settings are also defined in ik.py - there is some redundancy/overlap there. Fix...
polargraphWidthInMM = 622 # Width between pulleys
polargraphHeightInMM = 1165 # Height of machine
polargraphHomeXInMM = polargraphWidthInMM/2 # Home postition X
polargraphHomeYInMM = 120 # Home position Y
polargraphPulleyCircumferenceInMM = 92 # Effective circumference of pulleys
polargraphStepsPerRev = 200 # Number of whole steps per revolution for motors
polargraphStepsMultiplier = 16 # Stepper driver multiplier
polargraphMotorMaxSpeed = 1200 # Max motor speed
polargraphMotorAcceleration = 800 # How quickly the motor accelerates to get to its top speed
polargraphPenUpSetting = 63 # Servo 'up' position
polargraphPenDownSetting = 125 # Servo 'down' position

pageWidthInMM = 420 # Drawing area in mm
pageHeightInMM = 594 # Drawing area in mm
pageXOffsetInMM = 95 # How far (in mm) from the edge of the left pullley is the paper?
pageYOffsetInMM = 240 # How far (in mm) down from the imaginary line drawn between motor spindles?

# Calculate where the home position is in steps (Tested this and it revealed an error in my previously asserted home position. Updated measurements)
polargraphHomeXInSteps, polargraphHomeYInSteps, len1, len2 = ik.getStringLengths(polargraphHomeXInMM, polargraphHomeYInMM)
print("Debug: Calculated home position = %s, %s, lengths %s, %s" %(polargraphHomeXInSteps, polargraphHomeXInSteps, len1, len2))

# Grid dimensions
# (Define the grid cell size and the grid is calculated from that and the page width. An offset is also calculated
# to allow centering the grid within the page or drawing area)
cellWidthInMM = 10
cellHeightInMM = 25
numberOfCols = int(math.floor(pageWidthInMM / cellWidthInMM))
numberOfRows = int(math.floor(pageHeightInMM / cellHeightInMM))
xOffSetRemainder = math.floor((pageWidthInMM - (numberOfCols * cellWidthInMM)) / 2)
yOffSetRemainder = math.floor((pageHeightInMM - (numberOfRows * cellHeightInMM)) / 2)


# Global variable for serial coms function
# This exists to tell the next call of the comms functions
# that the previous exit was because a 'READY' was seen after
# exiting the function so the next call doesn't have to wait
# for the polargraph to send another 'READY' message.
polargraphReadySeen = False

# Global variables for TwitterSearch
tweetLastSeenID = 0
lastTweetCount = 0

#Open and connect serial port at baud and a timeout of secs
serialPort = serial.Serial(COMPORT,BAUD,timeout=10)
    

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
        # First find out how many bytes to read there are waiting in the buffer.

        numberOfBytesWaiting = serialPort.in_waiting
        # Uncomment the following two lines to see how many (if any) bytes are waiting.
        #if numberOfBytesWaiting > 0:
        #    print("Debug: Bytes waiting in serial port = %s" % numberOfBytesWaiting)

        # Read the number of bytes waiting as ASCII text (remove the terminating chars and decode bytes to ascii)
        # Note strip() used with no parameters should strip whitespace chars (i.e. tab, space, linefeed etc)

        dataRead = serialPort.read(numberOfBytesWaiting).strip().decode()
        #print("Debug: dataRead is '%s'" % dataRead)

        # A short delay allows the serial buffer to fill up else we get partial reads of the 'READY' message.

        time.sleep(0.1)
        
        # If dataRead contains the text 'READY' or the write command has run and a subsequent read returned 'READY' and
        # set the polargraphReadySeen flag (is this now redundant?), check the exitFlag status, if it has been set we can exit the function
        # by returning 'DONE' (we can ignore the returned value whereever we call this function from), otherwise we write the command, set the exit flag
        # and go thru these steps again.
        
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
    # Build the commands to setup the machine. Pulls settings from config variables at top of this script
    setupCommand = ["C02,0.36,END\n"] #Set pen width in mm
    setupCommand.append("C24,"+str(polargraphWidthInMM)+","+str(polargraphHeightInMM)+",END\n") #Set machine size in mm
    setupCommand.append("C29,"+str(polargraphPulleyCircumferenceInMM)+",END\n") #Set mm per revolution
    setupCommand.append("C30,"+str(polargraphStepsPerRev)+",END\n") #Set native motor steps per revolution
    setupCommand.append("C31,"+str(polargraphMotorMaxSpeed)+",1,END\n") #Set motor speed
    setupCommand.append("C32,"+str(polargraphMotorAcceleration)+",1,END\n") #Set motor acceleration
    setupCommand.append("C37,"+str(polargraphStepsMultiplier)+",END\n") #Set micro stepping multiplier
    setupCommand.append("C45,"+str(polargraphPenUpSetting)+","+str(polargraphPenDownSetting)+",1,END\n") #Sets pen lift range
    setupCommand.append("C09,"+str(polargraphHomeXInSteps)+","+str(polargraphHomeYInSteps)+",END\n") #Set pen position as home (you can then manually set the pen to a known position) 311mm x 120mm is home on my machine
    setupCommand.append("C13,"+str(polargraphPenUpSetting)+",END\n") #Set drop pen position
    setupCommand.append("C14,"+str(polargraphPenDownSetting)+",END\n") #Set lift pen position

    print("Debug: Command list contains %s" %(setupCommand,))
    print("")
    print("Setting up the controller...")
    print("")

    for each in setupCommand:
        writeCommandToPolargraph(each)    
    
    print("")
    print("Setup done!")

    # Check the version of Python you are running, and select the appropriate input version
    majorVersion = sys.version_info[0]
    print("Debug: Python running this is has major version no %s" % majorVersion)

    if majorVersion == 2:
        # Python 2.x
        raw_input("Manually set pen to home position and press enter to continue when done")
    else:
        # Python 3.x
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

    #print("Debug:X: cellWidth: %s, page offset: %s, offset remainder: %s" %(cellWidthInMM, pageXOffsetInMM, xOffSetRemainder))
    #print("Debug:Y: cellWidth: %s, page offset: %s, offset remainder: %s" %(cellHeightInMM, pageYOffsetInMM, yOffSetRemainder))
    xCoordsInMM = int(round((xCell * cellWidthInMM) + pageXOffsetInMM + (xOffSetRemainder / 2)))
    yCoordsInMM = int(round((yCell * cellHeightInMM) + cellHeightInMM + pageYOffsetInMM + (yOffSetRemainder / 2)))

    return xCoordsInMM, yCoordsInMM


def scaleHeight(val, scaleHeight):
    # This function scales the given value (val) so that it fits within the given cell height (scaleHeight)
    # Returns an integer so it will cause some loss of resolution but that is acceptable for the twitter graph
    result = int(val * (scaleHeight/100))

    return result


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


def drawLineGraph(xCell, yCell, val):
    # This function will draw a line graph data point
   
    xCoordsInMM, yCoordsInMM = getCellCoordinates(xCell, yCell)
    # If this is the first cell in the row then we need to add a moveTo() func
    if xCell == 0:
        print("Debug: xCell == 0. Doing a move")
        moveTo(xCoordsInMM, yCoordsInMM)
    drawTo((xCoordsInMM+cellWidthInMM), (yCoordsInMM-val), 2)
    pen("up")

# funtion to test the move and draw functions

def test1():
    print("Test 1: Testing wrapper functions")
    print("")

    # test pen() function
    pen("down")
    pen("up")

    # Move (don't draw) to the 4 corners of a box that defines the notional drawing area (end at the home position)
    # These coords are from my machine, are in mm and define the corners of the page extents
    
    # top left, top right, bottom right, top left
    moveTo(95,240)
    moveTo(515,240)
    moveTo(515,834)
    moveTo(95,834)
    moveTo(95,240)

    # home
    moveTo(305,120)
    

    # Draw a box around the notional drawing area (end at the home position)
    # These coords are from my machine, are in mm and will draw the page edges

    # top left, top right, bottom right, top left
    moveTo(95,240)
    drawTo(515,240,2)
    drawTo(515,834,2)
    drawTo(95,834,2)
    drawTo(95,240,2)
    # home
    moveTo(305,120)

    # Testing the 'blip' function. This draws a 'blip' of the given value in the chosen cell
    # def drawBlip(xCell, yCell, blipVal)
    drawBlip(0,0,25)
    
    input("Test completed, press enter to continue") 

# Test the grid and graphing functions

def test2():    
    print("Starting draw loop")
    for y in range(numberOfRows, 0, -1):
        for x in range(0,numberOfCols):
            print("Debug: x = %s of %s" %(x, numberOfCols))
            print("Debug: y = %s of %s" %(y, numberOfRows))
            #print("Calling twitter search using tweetLastSeenID = %s" %tweetLastSeenID)
            #tweetLastSeenID, lastTweetCount = twitSearch(tweetLastSeenID)
            print("Debug: lastTweetCount = %s" %lastTweetCount)
            #drawBlip(x,y,lastTweetCount)
            #drawBlip(x,y,random.randint(0,100))
            drawLineGraph(x,y,random.randint(0,25))
            print("sleeping...")
            #time.sleep(60)


# Get the number of twitter search results and graph that using one of the draw funtions in a grid

def graphTwitterSearchResults():
    print("Starting draw loop")
    for y in range(numberOfRows, 0, -1):
        print("Debug: y = %s of %s" %(y, numberOfRows))
        for x in range(0,numberOfCols):
            print("Debug: x = %s of %s" %(x, numberOfCols))
            print("Calling twitter search using tweetLastSeenID = %s" %tweetLastSeenID)
            global tweetLastSeenID
            result = twti.twitSearch(tweetLastSeenID)
            print("Debug: twitter search results = %s" % (result,))
            tweetLastSeenID = result[0]
            #drawBlip(x,y,lastTweetCount)
            #drawBlip(x,y,random.randint(0,100))
            #drawLineGraph(x,y,int(result[1]))

            # This should constrain the graph height to the defined cell height in mm
            # It calls the drawLineGraph() function and passes in the result of the scaleHeight() function
            # which takes the twitter search result and the cellHeightInMM and returns the value scaled
            drawLineGraph(x,y,scaleHeight(int(result[1]), cellHeightInMM))

            print("sleeping for 60 secs...")
            time.sleep(60)

# Setup the Polargraph once
setupPolargraph()  

# Do forever
while True:
    
    # Draw a graph of twitter search results
    graphTwitterSearchResults()
    
