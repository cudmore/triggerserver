# triggerserver
Raspberry Pi + Arduino + ScanImage

Note: This is a hand-copied version of my trigger server software, it is not up to date.

##Purpose

Have a Raspberry Pi be the master control for a trial based experiment. Each trial is started by the Pi, the Pi triggers an Arduino and ScanImage (via TTL) and then saves Arduino based timestamped events to a file while recording real-time timestamped video.

##Overview

- Raspberry is the master (triggerserver.py), at the start of a trial Raspberry triggers both Arduino and ScanImage with a digital TTL.

- As ScanImage runs, the Arduino (AcellStepper1.ino) received FrameClock TTLs and sends them back out as digital TTL and  logs their time out to serial port.

- The serial data coming from Arduino is continuously saved to a file on the Raspberry (serial_logger.py). Each serial event has an Arduino based milli-second timestamp. Serial_logger.py runs in its own process so it can be fast, independent and stateless. Exampe events are: trigger start, ScanImage start, ScanImage frame, motor start, motor stop, rotary encoder turn, et. etc.)

- For each trial, Arduino is turning on a stepper motor and running it for a duration and speed, logging these event out the serial

- For each trial, Arduino is reading a rotary encoder and logging this to serial.

- For each trial, Raspberry is saving video to a file (VideoThread.py), this is run from triggerserver.py as a separate thread to utilize the 4-cores on the Raspberry 2. As video is recorded in VideoThread.py, ScanImage frames are received from Arduino via a digital TTL and frame numbers are overlaid onto saved video. The real-time video output also appears as an analog feed, just plug Raspberry Pi analog output into an analog video monitor.

##Hardware (~$200)

####Raspberry
- [Raspberry Pi 2][1], $40
- Raspberry [Pi Noir camera][2], [Python library][9], $30
- [4x 840-850 nm IR LEDs][7], $1 each (960 nm IR LEDs do not work well with Pi Noir camera)

####Arduino
- Arduino Uno (also using Duemilanove '2009'), $25
- [EasyDriver][3] stepper motor driver, $15
- [Bipolar Nema stepper motor][4], $15
- Rotary encoder, [Honeywell-600-128-CBL][5], [.pdf spec sheet][6], $37

####Shared
- [8 channel logic level converter][8] to go from 5V DIO on Arduino to 3V DIO on Pi, $8
- 12V 2A power for motor controller and IR LED, $10
- breadboard, $6.00
  
##Example usage

- Start serial_logger.py  

        python serial_logger.py
    
- Start an interactive [ipython][10] session

        sudo ipython

- In ipython, create and control a triggerserver object.

        import triggerserver
    
        # create a triggerserve object (this turns on a continuous real-time analog video feed)
        t = triggerserver.triggerserver()
    
        #start a trial
        t.Go()
        
        #once the trial is finished, start another trial
        t.Go()
    
##To Do

Get rid of the Arduino and have Raspberry do everyhting. Before I do this I need to look at the timing jitter as ScanImage frame clock is coming into low level interrupts on the Pi (while the Pi is running other code).

Get these [IR led strips](http://www.ledlightsworld.com/infrared-led-strips-c-1_79.html)

##Estimated cost
- About $200

- What is the price of a traditional lab setup?

    - The following prices are estimates. The precise type of equipment you buy will change the price drastically. I am listing these prices for the type of equipment I would normally buy for this type of experiment. A more traditional system would be as follows
        
    - Master 8, $4000
        
    - National Instruments Data Acquisition cards, $700
        
    - Windows 7 computer, $1400
        
    - USB Camera with lens, $1500
        
     - Total Cost ~$7,800
        
##Example log file

	#date, time, linux epoch seconds, arduinoMillis, event, value
	20150603,15:17:01.114085,1433359021.11,73167078,raspberry.newtrialname,20150603_151658_t16.txt
	
    #the next block tells us the state/parameters of the Arduino for this trial
    20150603,15:17:01.629955,1433359021.63,arduino.beginprintstate
	20150603,15:17:02.117877,1433359022.12,arduino.programVersion=0.90
	20150603,15:17:02.130108,1433359022.13,arduino.isRunning=0
	20150603,15:17:02.141770,1433359022.14,arduino.startTime=0
	20150603,15:17:02.153535,1433359022.15,arduino.siRunning=0
	20150603,15:17:02.165232,1433359022.17,arduino.siNumFrames=0
	20150603,15:17:02.177105,1433359022.18,arduino.stepperDirection=1
	20150603,15:17:02.189204,1433359022.19,arduino.stepperSpeed=70
	20150603,15:17:02.201035,1433359022.2,arduino.stepperDelay=40000
	20150603,15:17:02.212996,1433359022.21,arduino.stepperDuration=40000
	20150603,15:17:02.225191,1433359022.23,arduino.motorResetVal=1
	20150603,15:17:02.237084,1433359022.24,arduino.endprintstate
      
 	#date, time, linux epoch seconds, arduinoMillis, event, value
	20150603,15:17:02.249092,1433359022.25,73168081,goReceived,1 
    20150603,15:17:02.618032,1433359022.62,73168081,siStart,73168081
	20150603,15:17:02.629949,1433359022.63,73168081,siFrame,1
	20150603,15:17:02.641413,1433359022.64,73168378,siFrame,2
	20150603,15:17:02.915083,1433359022.92,73168675,siFrame,3
        ...
        ...
        ...
	20150603,15:18:20.394068,1433359100.39,73245893,siFrame,263
	20150603,15:18:20.422795,1433359100.42,73245910,encoderPos,-14620
	20150603,15:18:20.439312,1433359100.44,73245960,encoderPos,-14621
	20150603,15:18:20.489681,1433359100.49,73246005,encoderPos,-14622
	20150603,15:18:20.534848,1433359100.53,73246038,encoderPos,-14623
	20150603,15:18:20.567254,1433359100.57,73246076,encoderPos,-14624
	20150603,15:18:20.606516,1433359100.61,73246142,encoderPos,-14625
	20150603,15:18:20.671678,1433359100.67,73246168,encoderPos,-14626
	20150603,15:18:20.697181,1433359100.7,73246190,siFrame,264
	20150603,15:18:20.719721,1433359100.72,73246219,encoderPos,-14627
	20150603,15:18:20.748554,1433359100.75,73246239,encoderPos,-14628
	20150603,15:18:20.769442,1433359100.77,73246256,encoderPos,-14629
	20150603,15:18:20.785193,1433359100.79,73246266,encoderPos,-14630
	20150603,15:18:20.797553,1433359100.8,73246280,encoderPos,-14631
	20150603,15:18:20.810039,1433359100.81,73246292,encoderPos,-14630
	20150603,15:18:20.822109,1433359100.82,73246310,encoderPos,-14629
	20150603,15:18:20.839575,1433359100.84,73246322,encoderPos,-14630
	20150603,15:18:20.851756,1433359100.85,73246338,encoderPos,-14631
	20150603,15:18:20.867477,1433359100.87,73246360,encoderPos,-14630
        ...
        ...
        ...
	20150603,15:19:01.404021,1433359141.4,73287176,siFrame,402
	20150603,15:19:01.701039,1433359141.7,73287473,siFrame,403
	20150603,15:19:01.997524,1433359142.0,73287770,siFrame,404
	20150603,15:19:02.294221,1433359142.29,73287814,siFrame,405
	20150603,15:19:02.338296,1433359142.34,73287816,siStop,73287816
	20150603,15:19:02.350754,1433359142.35,73287817,siStart,73287817
	20150603,15:19:02.362879,1433359142.36,73287818,siStop,73287818
	20150603,15:19:02.374820,1433359142.37,73288835,raspberry.stoptrial,20150603_151658_t16.txt

[1]: http://www.raspberrypi.org/products/raspberry-pi-2-model-b/
[2]: https://www.raspberrypi.org/products/pi-noir-camera/
[3]: https://www.sparkfun.com/products/12779
[4]: https://www.sparkfun.com/products/9238
[5]: http://www.digikey.com/product-detail/en/600128CBL/600CS-ND/53504
[6]: http://sensing.honeywell.com/600%20series_005940-2-en_final_12sep12.pdf
[7]: https://www.sparkfun.com/products/9469
[8]: https://www.adafruit.com/products/395
[9]: https://picamera.readthedocs.org/en/release-1.10/
[10]: http://ipython.org