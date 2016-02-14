import math

# Distances should all be in 'whole steps' (except for actual measurements where specified)

# Note: There are differences in the way Python 2 & 3 handle rounding
# Added the float() functions when calculating wholeStepsPerMM

motorDistance = 622 # in mm (622 on my machine)
motorStepsPerRev = 200
motorStepsMultiplier = 16
pulleyCircumference = 92 # in mm (this is mm per revolution)
microStepsPerMM = round((motorStepsPerRev * motorStepsMultiplier) / pulleyCircumference)
# The native coordinate system is in WHOLE STEPS!!!
wholeStepsPerMM = float(motorStepsPerRev) / float(pulleyCircumference)
motorDistanceInSteps = wholeStepsPerMM * motorDistance
motorDistanceMidPointInSteps = motorDistanceInSteps / 2

def printInfo():
    print("")
    print("Whole Steps Per MM = %s" % wholeStepsPerMM)
    print("Micro Steps Per MM = %s" % microStepsPerMM)
    print("Distance between motors in steps = %s" % motorDistanceInSteps)
    print("Mid-point between motors in steps = %s" % motorDistanceMidPointInSteps)

# getStringLengths() accepts a two integers that specify coordinates in mm

def getStringLengths(x,y):
    #print("Debug: x = %s" % x)
    #print("Debug: y = %s" % y)
    #c = motorDistanceInSteps - x
    c = motorDistance - x
    len1 = math.sqrt((x*x)+(y*y))
    #len1 = int(round(math.sqrt((x*x)+(y*y))))
    len2 = math.sqrt((c*c)+(y*y))
    #len2 = int(round(math.sqrt((c*c)+(y*y))))
    steps1 = len1 * wholeStepsPerMM
    steps2 = len2 * wholeStepsPerMM

    #round the values to the nearest integer for output
    len1 = int(round(len1))
    len2 = int(round(len2))
    steps1 = int(round(steps1))
    steps2 = int(round(steps2))
    return steps1,steps2,len1,len2

def test1():
    # Test the output of the function
    # On my machine, the home position is at 311mm from the left
    # by 120mm from the top. In the polargraph software, this give me
    # string lengths of 333mm x 333mm and 'native' coords of 725,725
    result = getStringLengths(311,120)
    print("")
    print("Position to generate coordinates for, are 311mm x 120mm")
    print("Expected results are 333mm x 333mm and (725,725)")
    print("getStringLength() returns: String lengths: %smm x %smm and native coords are: (%s,%s)" % (result[2],result[3],result[0],result[1]))


# If script is called on its own (i.e. not as an imported module) run this
if __name__ == "__main__": 
    printInfo()
    test1()


