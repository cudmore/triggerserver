#Author: Robert H Cudmore
#Web: http://robertcudmore.org
#Date: 20150504
#Purpose: general purpose routines

import os
import time
from datetime import datetime #to get fractional seconds
import json

savepath = '/home/pi/video/' + time.strftime('%Y%m%d') + '/'
logfilepath = ''

def init():
    global savepath
    print 'making output directory:', savepath
    if not os.path.exists(savepath):
        os.makedirs(savepath)

def newlogfile():
    global savepath
    global logfilepath
    logfilepath = savepath + GetTimestamp() + '.txt'
    print 'bUtil is saving to:', logfilepath
    
def GetTimestamp(): #use this to generate .avi
    return time.strftime('%Y%m%d') + '_' + time.strftime('%H%M%S')

def GetTimestampSeconds(): #use this to generate .avi
    #return time.strftime('%Y%m%d') + '_' + time.strftime('%H%M%S.%f').rstrip('0')
    return time.strftime('%Y%m%d') + '_' + datetime.now().strftime("%H%M%S.%f")

def logfileWrite(timestamp, myStr):
    global logfilepath
    if logfilepath:
        with open(logfilepath, 'a') as textfile:
            textfile.write(str(timestamp) + '\t' + myStr + '\n')

def logfileWrite2(myStr):
    global logfilepath
    if logfilepath:
        with open(logfilepath, 'a') as textfile:
            textfile.write(myStr + '\n')

def logfileWriteDict(theDict):
    global logfilepath
    if logfilepath:
        with open(logfilepath, 'a') as textfile:
            json.dump(theDict, textfile)