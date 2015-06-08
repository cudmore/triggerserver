#May 30, 2015
#simulate the scan image frame clock
#todo: rewrite this and enclode running of frame clock in a function
#call this function from within triggerserver.py

import RPi.GPIO as GPIO
import math
import time

class siSimulate:
    def __init__(self):

        self.siSimulateFramePin = 22 # input 6 on arduino

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.siSimulateFramePin, GPIO.OUT)

        self.delay = 500 #ms
        self.dur = 10000 #ms
        self.interval = 330 #ms

        self.frameNumber = 0

        print '=== siSimulate'
        print '   pin=', self.siSimulateFramePin
        print '   dur=', self.dur
        print '   delay=', self.delay
        print '   interval=', self.interval

    def Set(self, delay, dur, interval):
        self.delay = delay
        self.dur = dur
        self.interval = interval
            
    def Go(self):
        for a in range(self.dur):
            if a>self.delay:
                #running
                if math.floor(float(a)/float(self.interval)) == float(a)/float(self.interval):
                    #frame
                    self.frameNumber += 1
                    print '\tframe', self.frameNumber, 'at', a, 'ms'
                    GPIO.output(self.siSimulateFramePin, 0)
                else:
                    #running, no frame
                    GPIO.output(self.siSimulateFramePin, 1)
            else:
                #not running
                GPIO.output(self.siSimulateFramePin, 1)

            time.sleep(0.001) #seconds 
    
        #not running
        GPIO.output(self.siSimulateFramePin, 0)
        
        print '\tsiSimulate put out', self.frameNumber, 'frames'

if __name__ == '__main__':
    self = siSimulate()
    self.Go()