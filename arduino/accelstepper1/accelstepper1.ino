// Robert Cudmore
// http://robertcudmore.org
// May 24, 2015

// (1) run stepper motor with AccelStepper
// (2) read rotary encoder with Encoder
// (3) read scan image frame clock pin (siStart, siFrame, siStop)
// (4) read pins from Raspberry to start/stop the experiment
// Log 1-4 to serial

// to assign any pin to low level interrupt, see
// http://www.geertlangereis.nl/Electronics/Pin_Change_Interrupts/PinChange_en.html

// i am using easydriver motor controller
// http://www.schmalzhaus.com/EasyDriver/

#include <AccelStepper.h> // http://www.airspayce.com/mikem/arduino/AccelStepper/index.html
#include <Encoder.h> // http://www.pjrc.com/teensy/td_libs_Encoder.html

////////////////////////////////////////////////////////////////////////
float programVersion = 0.9;

//stepper motor
int motorStepPin = 5;
int motorDirPin = 4;
int motorResetPin = 6; // normally high input signal will reset the internal translator and disable all output drivers when pulled low.
unsigned int motorResetVal = 1;
AccelStepper stepper(AccelStepper::DRIVER,motorStepPin,motorDirPin);
int motorRunning = 0;
int maxSpeed = 1000;
int stepperDirection = 1; // 1 is CCW, -1 is CW
int stepperSpeed = 500;
unsigned int stepperDelay = 0; //ms
unsigned int stepperDuration = 1000; //ms

//rotary encoder
int encoderPinA = 2;
int encoderPinB = 3;
Encoder myEncoder(encoderPinA, encoderPinB);
long encoderPos  = -999;
long newEncoderPos = -999;

//to receive si frames
int turnOnTicks = 5;
int turnOffTicks = 50;
unsigned int downCount = 0;
unsigned int upCount = 0;
int siRunning = 0;
int siNumFrames = 0;

// program state
volatile int goReceived = 0;    //A0
volatile int stopReceived = 0;  //A1
volatile int siIsUp = 0;      //A2
volatile int gotFrame = 0;      //A2

int outRaspScanOnOff = 8; //when we decide si starts/stops
int outRaspFrame = 10; //when we receive a si frame

// main go/stop is from raspberry
unsigned int isRunning = 0;
unsigned long startTime = 0; //millis() we received Go from Raspberry
unsigned long now = 0;

////////////////////////////////////////////////////////////////////////
void setup()
{  
  Serial.begin(115200);
  
  // stepper motor
  motorResetVal = 1; // normally high input signal will reset the internal translator and disable all output drivers when pulled low.
  motorRunning = 0; //set in loop()
  maxSpeed = 1000;
  stepperDirection = 1;
  stepperSpeed = 500;
  stepperDelay = 0;
  stepperDuration = 1000;
  stepper.setMaxSpeed(maxSpeed);
  stepper.setSpeed(stepperDirection * stepperSpeed);	
  pinMode(motorResetPin, OUTPUT);
  digitalWrite(motorResetPin, motorResetVal);
  
  // rotary encoder
  encoderPos = myEncoder.read();
  newEncoderPos = encoderPos;
  
  // si frames (si frame clock is A2)
  siRunning = 0;
  siNumFrames = 0;
    
  now = 0;
  InitializeIO();
  InitializeInterrupt();
  siIsUp = 0;
  gotFrame = 0;
  goReceived = 0;
  stopReceived = 0;
  
  // program control from raspberry (start pin is A0, stop pin is A1)
  isRunning = 0;
  startTime = 0;
  pinMode(outRaspScanOnOff, OUTPUT);
  digitalWrite(outRaspScanOnOff, 0);
  pinMode(outRaspFrame, OUTPUT);
  digitalWrite(outRaspFrame, 0);
  
  Serial.println("Arduino accelstepper1 version " + String(programVersion) + " is ready...");
} // setup

////////////////////////////////////////////////////////////////////////
//callback for frame clock pin using xxx
void InitializeIO() {
  pinMode(A0, INPUT);
  digitalWrite(A0, LOW);
  pinMode(A1, INPUT);
  digitalWrite(A1, LOW);
  pinMode(A2, INPUT);
  digitalWrite(A2, LOW);
}
////////////////////////////////////////////////////////////////////////
void InitializeInterrupt() {
  cli();
  PCICR =0x02;
  PCMSK1 = 0b00000111;
  sei();
}
////////////////////////////////////////////////////////////////////////
ISR(PCINT1_vect) {
  if (digitalRead(A0)==1) goReceived=1; 
  if (digitalRead(A1)==1) stopReceived=1; 
  //if (digitalRead(A0)==1) Serial.println("A0"); 
  if (digitalRead(A2)==1) siIsUp=1; else gotFrame=1;
  //if (digitalRead(A2)==1) gotFrame=0; else gotFrame=1;
}

////////////////////////////////////////////////////////////////////////
void ParseSerialInput(String str) {
  int handled = 0;
  if (str=="reset") {
     handled = 1;
     setup();
  }
  if (str=="help") {
    handled = 1;
    printhelp();
  }
  if (str=="printstate") {
    handled = 1;
    printstate();
  }
  if (str=="go") {
    //simulate raspberry goPin(A0) -->> 1
    handled = 1;
    isRunning = 1;
    startTime = millis();
  }
  if (str=="stop") {
    //simulate raspberry stopPin(A1) -->> 1
    handled = 1;
    isRunning = 0;
    startTime = 0;
  }
  if (str=="motor_stop") {
    // may 26, now handled in loop()
    handled = 1;
    motorRunning = 0;
    LogEvent(now, "motor_stop", 0);
  }
  if (str=="motor_start") {
    // may 26, now handled in loop()
    handled = 1;
    motorRunning = 1;
    LogEvent(now, "motor_start", 1);
  }
  if (handled==0) {
    int indexOfEqual = str.indexOf("=");
    if (indexOfEqual >= 0) {
      String lhs = str.substring(0,indexOfEqual);
      String rhsStr = str.substring(indexOfEqual+1,str.length()); //will be 0 if str stars with letter
      int rhs = rhsStr.toInt();
      //if (lhs=="logevent") {
      //  //mechanism where raspberry can send 'logevent' that is echoed by arduino serial and seved by serial_logger.py'
      //  handled = 1;
      //  Serial.println(String (now) + "," + lhs + "," + rhsStr);
      //  //LogEvent(now, lhs, rhsStr);
      //}
      if (lhs=="motor_set_direction") {
        handled = 1;
        if (rhs<maxSpeed) {
          stepperDirection = rhs;
          //digitalWrite(motorDirPin, rhs); //there does not seem to be an interface for this???
          stepper.setSpeed(stepperDirection * stepperSpeed);
          LogEvent(now, lhs, rhs);
          LogEvent(now, "motor_set_speed", stepperDirection * stepperSpeed);
        }
      }
      if (lhs=="motor_set_speed") {
        handled = 1;
        if (rhs<maxSpeed) {
          stepperSpeed = rhs;
          stepper.setSpeed(stepperDirection * stepperSpeed);
          LogEvent(now, lhs, stepperDirection * stepperSpeed);
        }
      }
      if (lhs=="motor_set_delay") {
        handled = 1;
        stepperDelay = rhs;
        LogEvent(now, lhs, rhs);
      }
      if (lhs=="motor_set_duration") {
        handled = 1;
        stepperDuration = rhs;
        LogEvent(now, lhs, rhs);
      }
      if (lhs=="motor_set_reset") {
        handled = 1;
        motorResetVal = rhs;
        LogEvent(now, lhs, rhs);
      }
  
      if (handled==0) {
        //just echo back to serial
        handled=1;
        Serial.println(String (now) + "," + lhs + "," + rhsStr);
      }
    } // indexOfEqual
  } // handled ==0
  
  if (handled==0) {
    //just echo back to serial
    handled=1;
    Serial.println(String (now) + "," + str);
  }
  
} // ParseSerialInput

////////////////////////////////////////////////////////////////////////
void printhelp() {
//  Serial.println("===========================================");
//  Serial.println("accelstepper1 commands are:");
//  Serial.println("   help : print this help");
//  Serial.println("   reset : same as reset button on arduino");
//  Serial.println("   get_state");
//  Serial.println("   go : simulate go pin from raspberry");
//  Serial.println("   stop : simulate stop pin from raspberry");
//  Serial.println("   motor_stop : trumped by raspberry go/stop");
//  Serial.println("   motor_start : trumped by raspberry go/stop");
//  Serial.println("   motor_set_direction= : -1==CW, 1==CCW");
//  Serial.println("   motor_set_speed= : units???");
//  Serial.println("   motor_set_delay= : ms");
//  Serial.println("   motor_set_duration= : ms");
//  Serial.println("   motor_set_reset= : 1==turn motor controller on, 0==turn off");
}

////////////////////////////////////////////////////////////////////////
void printstate() {
  Serial.println("arduino.beginprintstate");
  Serial.println("arduino.programVersion=" + String(programVersion));
  Serial.println("arduino.isRunning=" + String(isRunning));
  Serial.println("arduino.startTime=" + String(startTime));
  Serial.println("arduino.siRunning=" + String(siRunning));
  Serial.println("arduino.siNumFrames=" + String(siNumFrames));

  Serial.println("arduino.stepperDirection=" + String(stepperDirection));
  Serial.println("arduino.stepperSpeed=" + String(stepperSpeed));
  Serial.println("arduino.stepperDelay=" + String(stepperDelay));
  Serial.println("arduino.stepperDuration=" + String(stepperDuration));
  Serial.println("arduino.motorResetVal=" + String(motorResetVal));
  Serial.println("arduino.endprintstate");
}

////////////////////////////////////////////////////////////////////////
void LogEvent(unsigned long timestamp, String event, long val) {
  Serial.println(String (timestamp) + "," + event + "," + String(val));
}

////////////////////////////////////////////////////////////////////////
void newtrial(unsigned long theTime) {
    siNumFrames = 0;
    LogEvent(now, "siStart", theTime);
} // newtrial

////////////////////////////////////////////////////////////////////////
void siStop(unsigned long theTime) {
    siRunning = 0;
    digitalWrite(outRaspScanOnOff, 0);
    //siStopTime = theTime;
    //receivedTrigger = 0; //re-arm for next trigger from raspberry
    //wheelIsMoving = 0;
    LogEvent(now, "siStop", theTime);
}

////////////////////////////////////////////////////////////////////////
void update_si_state(unsigned long theTime) {
  if (digitalRead(A2) == HIGH) {
    downCount = 0;
    upCount += 1;
  } else {
    downCount += 1;
    upCount = 0;
  }

  //decide if we should start/stop acquiring
  //if ( (siRunning==0) && (upCount > turnOnTicks) ) {
  if ( siIsUp==1 && siRunning==0) {
    // start acquiring
    siIsUp = 0;
    siRunning = 1;
    digitalWrite(outRaspScanOnOff, 1);
    newtrial(theTime);
    
  } else if ( (siRunning==1) && (downCount > turnOffTicks) ) { 
    // stop acquiring
    siStop(theTime);
  }
  //don't respond to 0 unless 'isAcquiring'
  if (gotFrame == 1 && siRunning) {
    gotFrame = 0; //we received a frame, and we have now processed it -> turn it off
    siNumFrames++;
    //may 25
    digitalWrite(outRaspFrame, 1); // THIS IS FAST, RASPBERRY MAY MISS IT ?
    //delay(5); //ms
    digitalWrite(outRaspFrame, 0); // THIS IS FAST, RASPBERRY MAY MISS IT ?
    LogEvent(theTime, "siFrame", siNumFrames);
  }
  } // update_si_state

////////////////////////////////////////////////////////////////////////
void loop()
{
  now = millis();
  
  digitalWrite(motorResetPin, motorResetVal);
  
  if (Serial.available() > 0) {
    String inString = Serial.readStringUntil('\n');
    ParseSerialInput(inString);
  }

  if (goReceived) {
    goReceived = 0;
    if (isRunning==0) {
      isRunning = 1;
      startTime = now;
      LogEvent(now, "goReceived", 1);
    }
  }
  if (stopReceived) {
    stopReceived= 0;
    if (isRunning==1) {
      isRunning = 0;
      LogEvent(now, "stopReceived", 1);
    }
 }
  
  //only handle si and motor if we are running a trial
  if (isRunning) {
    update_si_state(now);
  
    int motorwasrunning = motorRunning;
    motorRunning = (now>(startTime+stepperDelay)) && (now<(startTime+stepperDelay+stepperDuration));
    if (motorwasrunning==0 && motorRunning==1) {
      LogEvent(now, "motorstart", 1);
    }
    if (motorwasrunning==1 && motorRunning==0) {
      LogEvent(now, "motorstop", 1);
    }
    if (motorRunning) stepper.runSpeed();

  }
  
  //always log encoder position
  newEncoderPos = myEncoder.read();
  int encoderDiff = abs(newEncoderPos - encoderPos);
  //if (newEncoderPos != encoderPos) {
  if (encoderDiff > 0) {
    //Serial.println("new encoder pos=" + String(newEncoderPos));
    LogEvent(now, "encoderPos", encoderPos);
    encoderPos = newEncoderPos;
  }
  
}

