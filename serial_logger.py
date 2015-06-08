#Author: Robert H Cudmore
#Web: http://robertcudmore.org
#Date: may 31, 2015
#Purpose: Idea is to have a single python process to just log ALL incoming serial text

import os
import time
from datetime import datetime
import serial

#home
#serialPort = '/dev/ttyACM0';
#work
#serialPort = '/dev/ttyUSB0';

#
serialPort = '/dev/ttyACM0' # home
if not os.path.exists(serialPort):
	serialPort = '/dev/ttyUSB0' # work
	if not os.path.exists(serialPort):
		print 'Error initializing serial port'
		serialPort = ''
serialBaud = 115200;
ser = serial.Serial(serialPort,serialBaud,timeout=1)

savepath = '/home/pi/video/' + time.strftime('%Y%m%d') + '/'
if not os.path.exists(savepath):
    print 'serial_logger() is making output directory:', savepath
    os.makedirs(savepath)
print 'serial_logger is saving to folder:', savepath


#one file each time we run
timestamp = time.strftime('%Y%m%d') + '_' + time.strftime('%H%M%S')
masterfilename = savepath + timestamp + '.txt'
masterfileid = open(masterfilename, 'w')
print 'serial_logger is writing to master file:', masterfilename

#when we receive command from raspberry
trialfilename = ''
trialfileid = None

while 1:

    try:
        nowDate = time.strftime('%Y%m%d')
        nowTimestamp = datetime.now().strftime("%H:%M:%S.%f")
        nowSeconds = time.time()
        
        line = ser.readline() # throw away any part lines
        line = line.rstrip()
        
        if len(line)>0:
            print nowDate + ',' + nowTimestamp + ',' + str(nowSeconds) + ',' + line
        
        #break apart line
        if len(line.split(",")) == 3:
            thisTimeStr, thisEvent, thisValStr = line.split(',')
    	    #print thisTimeStr, thisEvent, thisValStr
    	    
            #if thisEvent == 'raspberry.newtrialnumber':
            #    print '   serial_logger is now saving to TRIAL:', thisValStr
            if thisEvent == 'raspberry.newtrialname':
                trialfilename = savepath + thisValStr
                #open trialfilename
                trialfileid = open(trialfilename, 'w')
                print '\n\n===serial_logger is now saving to FILE:', trialfilename
                
            if thisEvent == 'raspberry.stoptrial':
                #close trialfilename
                if trialfileid is not None:
                    print '===serial_logger is closing file:', trialfilename, '\n\n'
                    trialfileid.write(nowDate + ',' + nowTimestamp + ',' + str(nowSeconds) + ',' + line + '\n')
                    trialfileid.close()
                    trialfileid = None
                    trialfilename = ''
                    
        #always write serial input to file
        if masterfileid is not None:
            masterfileid.write(nowDate + ',' + nowTimestamp + ',' + str(nowSeconds) + ',' + line + '\n')
        if trialfileid is not None:
            trialfileid.write(nowDate + ',' + nowTimestamp + ',' + str(nowSeconds) + ',' + line + '\n')
                
    except (KeyboardInterrupt, SystemExit):
        if masterfileid is not None:
            print '\n===serial_logger is closing master file:', masterfilename
            masterfileid.close()
            masterfileid = None
            masterfilename = ''
        raise
    except:
    	print '   ERROR: error in serial_logger ... THIS NEEDS TO BE FIXED'
    	pass

    time.sleep(0.01)