#Author: Robert H Cudmore
#Web: http://robertcudmore.org
#Date: 20150504
#Purpose: a video class to spawn circular video recording using the Raspberry Pi Camera module
#
#20150401, switching back to Thread, bailing on MultiProcess
# MP was just not working
#
# 20150504 implementing trigger server
# added
#  self.usePins
#  be sure to set myThread.daemon=True # to stop the tread when iPython exits

import os
import time
from datetime import datetime #to get fractional seconds
import math # for floor()
import RPi.GPIO as GPIO
import picamera
import io
import threading

# don't derive from threading.Thread, have a data member as a thread
# this becomes a normal class, i can call anyhting i want
# make sure startArm() and stopArm() do the work !!!
class VideoThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
        self.isArmed = 0
        self.scanImageStarted = 0
        self.scanImageFrame = 0
        
        self.stream = None

        self.savepath = '/home/pi/video/' + time.strftime('%Y%m%d') + '/'
        if not os.path.exists(self.savepath):
            print '\tVideoThread is making output directory:', self.savepath
            os.makedirs(self.savepath)
        
        self.savename = '' # the prefix to save all files
        
        self.logFileName = None
        self.logFilePath = None
 
        self.beforefilename = ''
        self.afterfilename = ''
        
        self.beforefilepath = ''
        self.afterfilepath = ''
        
        self.bufferSeconds = 10
       
        #incorporating into triggerserver, don't use pins
        self.usePins = 0

        print '\tVideoThread initializing camera'
        self.camera = picamera.PiCamera()
        self.camera.resolution = (640, 480)        
        self.camera.led = 0
        self.camera.start_preview()

        print '\tVideoThread starting circular stream'
        #set up circular buffer
        self.stream = picamera.PiCameraCircularIO(self.camera, seconds=self.bufferSeconds)
        self.camera.start_recording(self.stream, format='h264')
        
    #interrupts
    def startpin_callback(self,pin):
        timestamp = self.GetTimestamp2()
        if GPIO.input(pin): #up start
            self.siStart(timestamp)
        else: #down stop
            self.siStop(timestamp)
        
    def framepin_callback(self,pin):
        timestamp = self.GetTimestamp2()
        if GPIO.input(pin): #up
            self.siFrame(timestamp)

    #
    def siStart(self, timestamp):
        if timestamp is None:
            timestamp = self.GetTimestamp2()
        if self.isArmed and not self.scanImageStarted:
            self.savename = timestamp.split('.')[0]
            self.scanImageFrame = 0
            self.scanImageStarted = 1
            self.logfileWrite(timestamp, 'siStart')
            if self.camera:
                self.camera.annotate_text = 'S'
                self.camera.annotate_background = picamera.Color('black')
            
            #remove fractional seconds
            self.logFileName = self.savename + '_si.txt'
            self.logFilePath = self.savepath + self.logFileName
            self.logfileWrite(timestamp, 'siStart')
            #print '\tVideoThread set log file = ', self.logFilePath
            #print timestamp, '\t', 'siStart'
    def siFrame(self, timestamp):
        if timestamp is None:
            timestamp = self.GetTimestamp2()
        if self.isArmed and self.scanImageStarted:
            self.scanImageFrame += 1
            if self.camera:
                self.camera.annotate_text = str(self.scanImageFrame)
                self.camera.annotate_background = picamera.Color('black')
            self.logfileWrite(timestamp, 'siFrame' + '\t' + str(self.scanImageFrame))
            #print str(timestamp), '\t', 'siFrame', self.scanImageFrame
    def siStop(self, timestamp):
        if timestamp is None:
            timestamp = self.GetTimestamp2()
        if self.isArmed and self.scanImageStarted:
            self.scanImageStarted = 0
            if self.camera:
                self.camera.annotate_text = ''
                self.camera.annotate_background = None
            self.logfileWrite(timestamp, 'siStop')
            self.logFileName = ''
            self.logFilePath = ''
            #print timestamp, '\t', 'siStop'
       
    def logfileWrite(self, timestamp, myStr):
        if self.logFilePath:
            with open(self.logFilePath, 'a') as textfile:
                textfile.write(str(timestamp) + '\t' + myStr + '\n')

    def GetTimestamp(self): #use this to generate .avi
        #returns integer seconds (for file names)
        return time.strftime('%Y%m%d') + '_' + time.strftime('%H%M%S')
    
    def GetTimestamp2(self): #use this to generate .avi
        # returns fraction seconds (for log)
        #datetime.datetime.now().strftime("%H:%M:%S.%f")
        return time.strftime('%Y%m%d') + '_' + datetime.now().strftime("%H%M%S.%f")

    #called from run()
    def write_video(self, stream, beforeFilePath):
        # Write the entire content of the circular buffer to disk. No need to
        # lock the stream here as we're definitely not writing to it
        # simultaneously
        #with io.open(self.savepath + 'before.h264', 'wb') as output:
        with io.open(beforeFilePath, 'wb') as output:
            for frame in stream.frames:
                if frame.frame_type == picamera.PiVideoFrameType.sps_header:
                    stream.seek(frame.position)
                    break
            while True:
                buf = stream.read1()
                if not buf:
                    break
                output.write(buf)
        # Wipe the circular stream once we're done
        stream.seek(0)
        stream.truncate()

    def startArm(self):
        print '\tVideoThread startArm()'

        if self.isArmed == 0:

            timestamp = self.GetTimestamp()
           
            #print 'VideoThread initializing camera'
            #self.camera = picamera.PiCamera()
            #self.camera.resolution = (640, 480)        
            #self.camera.led = 0
            #self.camera.start_preview()

            
            if self.usePins:
                print '\tVideoThread setting up GPIO'
                # digital io
                GPIO.setmode(GPIO.BCM)

                self.scanimageStartPin = 23
                self.scanimageFramePin = 24
                GPIO.setup(self.scanimageStartPin, GPIO.IN, GPIO.PUD_DOWN)
                GPIO.setup(self.scanimageFramePin, GPIO.IN, GPIO.PUD_DOWN)

                GPIO.add_event_detect(self.scanimageStartPin, GPIO.BOTH, callback=self.startpin_callback)  
                GPIO.add_event_detect(self.scanimageFramePin, GPIO.BOTH, callback=self.framepin_callback)  
    
            #self.logFileName = timestamp + '_si.txt'
            #self.logFilePath = self.savepath + self.logFileName
            #self.logfileWrite(timestamp, 'VideoThreadStartArm')
            #print '\tVideoThread set log file = ', self.logFilePath
                        
            #print '\tVideoThread starting circular stream'
            ##set up circular buffer
            #self.stream = picamera.PiCameraCircularIO(self.camera, seconds=self.bufferSeconds)
            #self.camera.start_recording(self.stream, format='h264')
            
            self.isArmed = 1

    def stopArm(self):
        print '\tVideoThread stopArm()'
        timestamp = self.GetTimestamp()
        if self.isArmed == 1:
            self.isArmed = 0
            
            #print '\tclosing camera'
            #self.camera.stop_recording()
            #self.camera.close()
            
            # camera is now initialized in __init__
            #print '\tdeleting self.stream'
            #del self.stream
            
            if self.usePins:
                print '\tVideoThread is releasing GPIO'
                GPIO.remove_event_detect(self.scanimageStartPin)
                GPIO.remove_event_detect(self.scanimageFramePin)
        
            self.logfileWrite(timestamp, 'VideoThreadStopArm')

            self.logFileName = ''
            self.scanImageFrame = 0
            
            print '\tVideoThread stopArm() is done'
            
    #start arm
    def run(self):
        print '\tVideoThread run() is initializing [can only call this once]' 
        lasttime = time.time()
        stillinterval = 1 #second
        while True:
            if self.isArmed:
                timestamp = self.GetTimestamp()
                while (self.isArmed):
                    try:
                        self.camera.wait_recording(0.005)
                        if self.scanImageStarted:
                            #print 'xxx scanImageStarted'
                            #timestamp = self.GetTimestamp()
                            #self.savename
                            self.beforefilename = self.savename + '_before' + '.h264'
                            self.afterfilename = self.savename + '_after' + '.h264'
                            self.beforefilepath = self.savepath + self.beforefilename
                            self.afterfilepath = self.savepath + self.afterfilename
                            # record the frames "after" motion
                            self.camera.split_recording(self.afterfilepath)
                            # Write the 10 seconds "before" motion to disk as well
                            self.write_video(self.stream, self.beforefilepath)
                
                            while self.scanImageStarted:
                                self.camera.wait_recording(0.001)
                
                            self.camera.split_recording(self.stream)
                            print '\tVideoThread received self.scanImageStarted==0'
                        #capture a foo.jpg frame every stillInterval seconds
                        #thistime = time.time()
                        #if thistime > (lasttime+stillinterval):
                        #    lasttime = thistime
                        #    self.camera.capture('foo.jpg', use_video_port=True)
            
                        self.beforefilename = ''
                        self.afterfilename = ''
                        self.beforefilepath = ''
                        self.afterfilepath = ''
                    except:
                        print '\tVideoThread except clause -->>ERROR'
                print '\tVideoThread.run fell out of loop'
            time.sleep(0.05)
        print '\tVideoThread terminating [is never called]'
