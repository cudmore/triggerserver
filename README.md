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