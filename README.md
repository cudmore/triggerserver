# triggerserver
Raspberry Pi + Arduino + ScanImage

This is a hand-copied version of my trigger server software. The idea is to have a Raspberry Pi be the master control for a trial based experiment. Each trial is started by the Pi, the Pi triggers an Arduino and ScanImage (via TTL).

###Overview

- Raspberry is the master (triggerserver.py), a trial starts with Arduino and ScanImage getting triggered via TTL
- As ScanImage runs, the arduino received FrameClock TTLs and send them out its serial (AcellStepper1)
- The serial is continuously logged to a file (serial_logger.py)  

- For each trial, Arduino is turning on a stepper motor and running it for a duration and speed, logging these event out the serial
- For each trial, Arduino is reading a rotary encoder and logging this to serial.

- For each trial, Raspberry is saving video to a file (VideoThread.py), this is run from triggersevrer as a separate thread to utilize the 4-cores on the Raspberry 2.

- As video runs in VideoThread.py, ScanImage frames are logged and frame numbers are overlaid on the video.

- The video appears as an analog feed (plug into rca monitor) as long as triggerserver.py is running

###Hardware
####Raspberry
- Raspberry Pi 2
- Raspberry Pi Noir camera
- 4x 800-900 nm IR LEDs

####Arduino
- Arduino Uno (also Demilanove)
- Big Easy stepper driver
- Nema stepper motor
- Rotary encoder

####Shared
- 8 channel voltage converter to go from 5V DIO on Arduino to 3V DIO on Pi
- 12V 2A power for motor controller and IR LED

###To Do

Just get rid of the Arduino and have Raspberry do everyhting. Before I do this I need to look at the timing jitter as ScanImage frame clock is coming into low level interrupts on the Pi (while the Pi is running other code).
