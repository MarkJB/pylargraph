import math

#Distances should all be in 'Steps' (except for actual measurements where specified)

motorDistance = 610 # in mm (610 on my machine)
motorStepsPerRev = 200
motorStepsMultiplier = 16
pulleyCircumference = 92 # in mm (this is mm per revolution)
microStepsPerMM = int(round((motorStepsPerRev * motorStepsMultiplier) / pulleyCircumference))
# Looks like the native coordinate system is in WHOLE STEPS!!!
wholeStepsPerMM = motorStepsPerRev / pulleyCircumference
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
    #print("x = %s" % x)
    #print("y = %s" % y)
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
    # On my machine, the home position is at 305mm from the left
    # by 120mm from the top. In the polargraph software, this give me
    # string lengths of 328mm x 328mm and 'native' coords of 711,711
    result = getStringLengths(305,120)
    print("")
    print("Position to generate coordinates for, are 305mm x 120mm")
    print("Expected results are 328mm x 328mm and (711,711)")
    print("getStringLength() returns: String lengths: %smm x %smm and native coords are: (%s,%s)" % (result[2],result[3],result[0],result[1]))

def test2():
    # Test an arbitrary known point to confirm the expected results
    # 100mm x 245mm = a string length (in mm) of 265mm & 566mm
    # Native whole steps = 578,1228
    
    result = getStringLengths(100,245)
    print("")
    print("Position to generate coordinates for, are 100mm x 245mm")
    print("Expected results are 265mm x 566mm and (578,1228)")
    print("getStringLength() returns: String lengths: %smm x %smm and native coords are: (%s,%s)" % (result[2],result[3],result[0],result[1]))
    #print("String lengths are: %s" % (result,))

#Uncomment these to test. Comment when calling from another python module.
#printInfo()
#test1()
#test2()
