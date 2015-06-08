#Author: Robert H Cudmore
#Web: http://robertcudmore.org
#Date: 20150430
#
#Purpose: Master python code to start stop acquisition
#   1 - start/stop video with VideoThread
#   2 - start/stop arduino with digital pins
#   3 - see serial_logger.py to log all serial data from arduino to file

'''
Auxiliary .py code...
(1) siSimulate.py : simulate scan image frame clock
   scan image frame clock is simulated (on rasp pin 22) using another thread
   see: 'siSimulate.py'

(2) serial_logger.py : log ALL serial events coming from arduino to a file

(3) qt.py : pyqt wrapper around *this that provides buttons to control experiment

(4) ser_read_qt3.py : make a pyqtgraph plot of incoming serial from arduino
   To Do: merge this with serial_logger

'''

'''
use this code...
    qt.py : qt inerface
    triggerserver.py : backend to run exp, read serial, save files
    ser_read_qt3.py : to make qt plot of incoming data
    siSimulate.py : simulate si on pin xxx
    
    accellstepper1. : arduino code  
'''

'''
===========================================
Arduino accelstepper1 version 0.90 is ready...
accelstepper1 commands are:
   help : print this help
   reset : same as reset button on arduino
   printstate
   go : simulate go pin from raspberry
   stop : simulate stop pin from raspberry
   motor_stop : trumped by raspberry go/stop
   motor_start : trumped by raspberry go/stop
   motor_set_direction= : -1==CW, 1==CCW
   motor_set_speed= : units???
   motor_set_delay= : ms
   motor_set_duration= : ms
   motor_set_reset= : 1==turn motor controller on, 0==turn off

printstate
arduino.beginprintstate
arduino.programVersion=0.90
arduino.isRunning=0
arduino.startTime=0
arduino.siRunning=0
arduino.siNumFrames=0
arduino.stepperDirection=1
arduino.stepperSpeed=500
arduino.stepperDelay=0
arduino.stepperDuration=1000
arduino.motorResetVal=1
arduino.endprintstate
'''

'''
Python tricks...
%load_ext autoreload
%autoreload 2

sudo kill -9 $(ps aux | grep '[p]ython' | awk '{print $2}')
'''

import time
from datetime import datetime #to get fractional seconds
import serial

import RPi.GPIO as GPIO

import sys
import os
sys.path.insert(0, '/home/pi/Sites/Common')
import bUtil
import VideoThread
import siSimulate #to simulate ScanImage when not on scope

class triggerserver:
    def __init__(self):
        self.logfile = ''
        
        self.savepath = '/home/pi/video/' + time.strftime('%Y%m%d') + '/'
        if not os.path.exists(self.savepath):
            print 'triggerserver() is making output directory:', self.savepath
            os.makedirs(self.savepath)

        self.isRunning = 0;
        self.frameNumber = 0
        
        #self.NewTrial()
        self.trialFileName = ''
        self.trialNumber = 0
        self.startTime = 0
        self.siStartTime = 0
        self.siStopTime = 0
        self.siFrameTimes = []
          
        #self.videoThread = None
        self.videothread = VideoThread.VideoThread()
        self.videothread.daemon = True # see VideoThread comments, new with TriggerServer
        self.videothread.start()
        
        # GPIO
        self.triggerPin = 18        # output trigger to arduino
        self.toScanImageTriggerPin = 13 # output trigger to scan image
        self.siStartStopPin = 23    # input scanimage start/stop from arduino
        self.siFramePin = 24        # input frame from arduino
  
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.triggerPin, GPIO.OUT)
        GPIO.setup(self.toScanImageTriggerPin, GPIO.OUT)
        GPIO.setup(self.siStartStopPin, GPIO.IN) # has callback
        GPIO.setup(self.siFramePin, GPIO.IN) # has callback

        #GPIO.setup(self.siStartStopPin, GPIO.IN, GPIO.PUD_DOWN)
        #GPIO.setup(self.siFramePin, GPIO.IN, GPIO.PUD_DOWN)

        GPIO.add_event_detect(self.siStartStopPin, GPIO.BOTH, 
            callback=self.startpin_callback)  
        GPIO.add_event_detect(self.siFramePin, GPIO.RISING,
            callback=self.framepin_callback)  

        GPIO.output(self.triggerPin, 0)
        GPIO.output(self.toScanImageTriggerPin, 0)
        
        # used by SerialSendCommand()
        self.serialPort = '/dev/ttyACM0' # home
        if not os.path.exists(self.serialPort):
            self.serialPort = '/dev/ttyUSB0' # work
            if not os.path.exists(self.serialPort):
                print 'triggerserver error initializing serial port'
                self.serialPort = ''
                               
        self.serialBaud = 115200 #115200
        self.serialTimeout = 1
            
        # this should be filled in by a qt interface
        self.motorDelay = 5000 #ms, motor_set_delay=
        self.motorDuration = 5000 #ms, motor_set_duration=
        self.motorDirection = 1
        self.motorSpeed = 70 #units?, motor_set_speed
        self.motorReset = 1 #1 is on, 0 is off
        
        self.sisimulate = 0
        self.sidelay = 100 #scan image always starts a bit after trigger
        self.sidur = 15000
        self.siinterval = 300 #ms

        self.PrintState()
        
    def PrintState(self):
    	print '\ttriggerserver.motorDelay=', self.motorDelay
    	print '\ttriggerserver.motorDuration=', self.motorDuration
    	print '\ttriggerserver.motorDirection=', self.motorDirection
    	print '\ttriggerserver.motorSpeed=', self.motorSpeed
    	print '\ttriggerserver.motorReset=', self.motorReset

    	print '\ttriggerserver.sisimulate=', self.sisimulate
    	print '\ttriggerserver.sidelay=', self.sidelay
    	print '\ttriggerserver.sidur=', self.sidur
    	print '\ttriggerserver.siinterval=', self.siinterval
    	
    #
    def NewTrial(self, timestamp):
        self.trialNumber += 1
        self.startTime = 0
        self.siStartTime = 0
        self.siStopTime = 0
        self.siFrameTimes = []
        self.trialFileName = timestamp + '_t' + str(self.trialNumber) + '.txt'
        print '   triggerserver NewTrial(), trial is now', self.trialNumber, 'trialFileName is', self.trialFileName
        
    #interrupts
    def startpin_callback(self,pin):
        timestamp = time.time() #
        self.siStartStop(timestamp, GPIO.input(pin))
        
    def framepin_callback(self,pin):
        timestamp = time.time() #
        self.siFrame(timestamp)

    # si start/stop/frame
    def siStartStop(self, timestamp, startstop):
        '''callback function for siStartStopPin'''
        #print 'in triggerserver.siStartStop()', self.isRunning
        if not self.isRunning: return 0
        if (startstop):
            self.siStartTime = timestamp
            print timestamp, '\t', 'siStartStop() START received'
        else:
            self.siStopTime = timestamp
            self.Stop()
            print '   ', timestamp, ' triggerserver siStartStop() STOP received'
            
    def siFrame(self, timestamp):
        '''callback function for siFramePin'''
        #print 'in triggerserver.siFrame()', self.isRunning
        if not self.isRunning: return 0
        self.frameNumber+=1
        if self.videothread:
            self.videothread.siFrame(None)
        self.siFrameTimes.append(timestamp)
        print '   ', timestamp, ' triggerserver siFrame() FRAME', self.frameNumber, 'received'
        
    #serial
    def SerialSendCommand(self, cmd):
        ''' Send a serial command '''
        ser = serial.Serial(self.serialPort, self.serialBaud, timeout=self.serialTimeout)
        time.sleep(0.5)
        print '   triggerserver SerialSendCommand() sending cmd: ', cmd
 
        ser.write(cmd + '\n')
        ser.close()

    # user specified start/stop
    def Stop(self):
        ''' STOP '''
        print '\nTiggerServer.Stop()'
        self.isRunning = 0
        
        self.videothread.siStop(None) # this is stopping the save
        self.videothread.stopArm()

        print '   triggerserver is telling arduino to stop (will reset state for next trigger)'
        self.SerialSendCommand('stop')
        
        #on scope
        GPIO.output(self.triggerPin, 0)
        GPIO.output(self.toScanImageTriggerPin, 0)

        logEventStr = 'raspberry.stoptrial' + ',' + self.trialFileName
        self.SerialSendCommand(logEventStr)

    def Go(self):
        ''' GO '''
        
        print '\nTriggerServer.GO()'
        timestamp = bUtil.GetTimestamp() # to name out output files
        print '   triggerserver names of files will start with:', timestamp
        
        self.frameNumber = 0
        self.NewTrial(timestamp)
                
        #
        # start video   
        self.videothread.startArm()
        self.videothread.siStart(timestamp) # this is just starting the save to disk
        
        #
        # trigger with trigger out pin (triggers arduino and si)
        self.isRunning = 1
        self.startTime = time.time()
        
        #
        # set trial parameters
        self.SerialSendCommand('motor_set_reset=' + str(self.motorReset))
        self.SerialSendCommand('motor_set_delay=' + str(self.motorDelay))
        self.SerialSendCommand('motor_set_direction=' + str(self.motorDirection))
        self.SerialSendCommand('motor_set_duration=' + str(self.motorDuration))
        self.SerialSendCommand('motor_set_speed=' + str(self.motorSpeed))
        
        ##
        print '   triggerserver is telling arduino that a trial is starting'
        logEventStr = 'raspberry.newtrialname' + ',' + self.trialFileName
        self.SerialSendCommand(logEventStr)
        
        #logEventStr = 'raspberry.newtrialnumber' + ',' + str(self.trialNumber)
        #self.SerialSendCommand(logEventStr)
        
        #log the state of the arduino to serial
        self.SerialSendCommand('printstate')
        
        #let video get started
        print '   triggerserver sleeping for 0.5 seconds while video warms up'
        time.sleep(0.5)

       
        ##
        print '   triggerserver triggering arduino and scan image to start'
        GPIO.output(self.triggerPin, 0)
        GPIO.output(self.toScanImageTriggerPin, 0)
        GPIO.output(self.triggerPin, 1)
        GPIO.output(self.toScanImageTriggerPin, 1)
        
        time.sleep(0.002)

        GPIO.output(self.triggerPin, 0)
        GPIO.output(self.toScanImageTriggerPin, 0)
        
        if self.sisimulate:
            print '   triggerserver is simulating SI with siSimulate'
            si = siSimulate.siSimulate()
            si.Set(self.sidelay, self.sidur, self.siinterval)
            si.Go()
            
        ## stop will either come from
        # (1) end of si acquisition
        # (2) self.Stop()
        
        
