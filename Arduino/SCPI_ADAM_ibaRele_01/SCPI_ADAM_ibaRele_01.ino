/*
Vrekrer_scpi_parser library.
SCPI Dimmer example.

Demonstrates the control of the brightness of a LED using SCPI commands.

Hardware required:
A LED attached to digital pin 9
or a resistor from pin 9 to pin 13 to use the built-in LED

Commands:
  *IDN?
    Gets the instrument's identification string

  SYSTem:LED:BRIGhtness <value>
    Sets the LED's brightness to <value>
    Valid values : 0 (OFF) to 10 (Full brightness)

  SYSTem:LED:BRIGhtness?
    Queries the current LED's brightness value

  SYSTem:LED:BRIGhtness:INCrease
    Increases the LED's brightness value by one

  SYSTem:LED:BRIGhtness:DECrease
    Decreases the LED's brightness value by one
*/


#include "Arduino.h"
#include "Vrekrer_scpi_parser.h"

uint8_t lcdEnabled = 0;
// LCD
#include <Wire.h> // Library for I2C communication
#include <LiquidCrystal_I2C.h> // Library for LCD
LiquidCrystal_I2C lcd = LiquidCrystal_I2C(0x27, 20, 4); // Change to (0x27,20,4) for 20x4 LCD.


SCPI_Parser my_instrument;
int brightness = 0;
const int ledPin = 10;
//const int relayPin = 6; // Na CNC Shielde je to Y dir pin
//const int relay2Pin = 3; // Na CNC Shielde je to Y step pin
const int intensity[11] = {0, 3, 5, 9, 15, 24, 38, 62, 99, 159, 255};

#define RelayCount 2
int relayPin[RelayCount] = {6, 3};
unsigned long relayOnTimestamp[RelayCount];
unsigned long relayOffTimestamp[RelayCount];
unsigned long relayOnTime[RelayCount] = {0, 0};
unsigned long relayOffTime[RelayCount] = {0, 0};

#include <AccelStepper.h>

// Define stepper motor connections and motor interface type. Motor interface type must be set to 1 when using a driver:
const int motor1DirPin = 5;
const int motor1StepPin = 2;
const int motorInterfaceType = 1;
const int motor1EnablePin = 8;
const int motor1EndPin = 9;
const int motor1PresentPin = 12; // If connector is connected, pin is shorted to GND
uint8_t motor1Enabled = 0;


const int motor2DirPin = 7;
const int motor2StepPin = 4;
const int motor2nterfaceType = 1;
const int motor2EnablePin = 8;
const int motor2EndPin = 11;
const int motor2PresentPin = 13; // If connector is connected, pin is shorted to GND
uint8_t motor2Enabled = 0;

int motorIsHome(int motorEndPin, int EndLogicHighWhenHome)
{
  return (digitalRead(motorEndPin) == EndLogicHighWhenHome);
}

// Define a stepper and the pins it will use
AccelStepper stepper1 = AccelStepper(motorInterfaceType, motor1StepPin, motor1DirPin);
// Define a stepper and the pins it will use
AccelStepper stepper2 = AccelStepper(motorInterfaceType, motor2StepPin, motor2DirPin);

int motorGoHome(AccelStepper stepper1, int motorEndPin, int EndLogicHighWhenHome);

void setup()
{
  my_instrument.RegisterCommand(F("*IDN?"), &Identify);
  my_instrument.RegisterCommand(F("MEAS"), &Meas);
  my_instrument.RegisterCommand(F("MOT"), &Motor);
  my_instrument.RegisterCommand(F("REL"), &SetRelay);
  my_instrument.RegisterCommand(F("REL?"), &GetRelay);
  my_instrument.RegisterCommand(F("LCD"), &Lcd);
  
  my_instrument.SetCommandTreeBase(F("SYSTem:LED"));
  my_instrument.RegisterCommand(F(":BRIGhtness"), &SetBrightness);
  my_instrument.RegisterCommand(F(":BRIGhtness?"), &GetBrightness);
  my_instrument.RegisterCommand(F(":BRIGhtness:INCrease"), &IncDecBrightness);
  my_instrument.RegisterCommand(F(":BRIGhtness:DECrease"), &IncDecBrightness);
  
  Serial.begin(9600);
  pinMode(ledPin, OUTPUT);

  uint8_t i;
  for(i = 0; i < RelayCount; i++){
    pinMode(relayPin[i], OUTPUT);
    digitalWrite(relayPin[i], HIGH); // rele vyp . reset
  }
  
  pinMode(LED_BUILTIN, INPUT);
  analogWrite(ledPin, 0);

  Serial.println("Ready.");
}

void loop()
{
  my_instrument.ProcessInput(Serial, "\n");
  stepper1.run();
  stepper2.run();
  relayTimeout();
}

void Identify(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  interface.println(F("Vrekrer,Arduino SCPI Dimmer,#01,v0.4"));
}

void GetRelay(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  uint8_t i;
  for(i = 0; i < RelayCount; i++){
    interface.print(HIGH == digitalRead(relayPin[i]) ? '0' : '1');
    interface.print(",");
  }
  interface.println("");
}

void Lcd(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  if (parameters.Size() == 0){
    lcd.clear();
  }
  if (parameters.Size() > 2) {
    int x = constrain(String(parameters[0]).toInt(), 0, 19);
    int y = constrain(String(parameters[1]).toInt(), 0, 3);
    lcd.setCursor(x,y);
    lcd.print(parameters[2]);
  }
}

void Meas(SCPI_C commands, SCPI_P parameters, Stream& interface) {
    // For simplicity no bad parameter check is done.
  if (parameters.Size() > 0) {
    int ch = constrain(String(parameters[0]).toInt(), 0, 5);
    int i = 0;
    float avg = 0;
    for(i = 0; i < 100; i++){
      avg += analogRead(A0 + ch);
    }
    avg /= 100;
    interface.print(ch);
    interface.print(",");
    interface.println(avg);
  }
}

void SetBrightness(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  // For simplicity no bad parameter check is done.
  if (parameters.Size() > 0) {
    brightness = constrain(String(parameters[0]).toInt(), 0, 10);
    analogWrite(ledPin, intensity[brightness]);
  }
}

void Motor(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  // For simplicity no bad parameter check is done.
  if (parameters.Size() > 1) { // potrebujeme aspon 2 parametre
    int m = String(parameters[0]).toInt();
    int cmd = constrain(String(parameters[1]).toInt(), 0, 6300);
    if(m == 1){
      if(motor1Enabled){
        stepper1.moveTo(cmd);
        Serial.println(cmd);
      }
    }
    if(m == 2){
      if(motor2Enabled){
        stepper2.moveTo(cmd);
        Serial.println(cmd);
      }
    }
  }
}

void relayTimeout(void)
{
  int i;
  for(i = 0; i < RelayCount; i++){
    if(relayOnTime[i] > 0){
      if(millis() - relayOnTimestamp[i] >= relayOnTime[i]){
        relayOnTime[i] = 0;
        digitalWrite(relayPin[i], HIGH);
      }
    }
    if(relayOffTime[i] > 0){
      if(millis() - relayOffTimestamp[i] >= relayOffTime[i]){
        relayOffTime[i] = 0;
        digitalWrite(relayPin[i], LOW);        
      }
    } 
  }
}

void SetRelay(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  // For simplicity no bad parameter check is done.
  if (parameters.Size() > 1) { // rele, 0/1
    int relay = constrain(String(parameters[0]).toInt(), 1, 2);
    int onoff = constrain(String(parameters[1]).toInt(), 0, 1);
    relay--; // shift relay index to start from 0
    Serial.println(onoff);
    
    if (parameters.Size() == 2){
      if(!onoff){
        relayOffTime[relay] = 0;
        digitalWrite(relayPin[relay], HIGH);
      }else{
        relayOnTime[relay] = 0;
        digitalWrite(relayPin[relay], LOW);
      }
    }else if (parameters.Size() > 2){
      int Timeout = String(parameters[2]).toInt();
      if(!onoff){
        relayOffTimestamp[relay] = millis();
        relayOffTime[relay] = 100 * (unsigned long)Timeout;
        digitalWrite(relayPin[relay], HIGH);
       
      }else{
        relayOnTimestamp[relay] = millis();
        relayOnTime[relay] = 100 * (unsigned long)Timeout;
        digitalWrite(relayPin[relay], LOW);
      }
      Serial.println(relayOnTime[relay]);
      Serial.println(relayOffTime[relay]);
    }
  }
}

void GetBrightness(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  interface.println(String(brightness, DEC));
}

void IncDecBrightness(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  String last_header = String(commands.Last());
  last_header.toUpperCase();
  if (last_header.startsWith("INC")) {
    brightness = constrain(brightness + 1, 0, 10);
  } else { // "DEC"
    brightness = constrain(brightness - 1, 0, 10);
  }
  analogWrite(ledPin, intensity[brightness]);
}


#define AxisLength 6300
#define MaxHomeSearchSmall (200)
#define MaxHomeSearch (AxisLength + MaxHomeSearchSmall)
int motorGoHome(AccelStepper *stepper, int motorEndPin, int EndLogicHighWhenHome)
{
  Serial.println("Homing... please wait.");
  stepper->setMaxSpeed(500); // rychlost homing
  stepper->setAcceleration(10000);
  long cmd = 0;
  while(motorIsHome(motorEndPin, EndLogicHighWhenHome)) {
    if (stepper->distanceToGo() == 0){
      stepper->moveTo(++cmd);
    }
    stepper->run();
    Serial.println(cmd);
    if(cmd > MaxHomeSearchSmall){
      Serial.println("H ERR 1"); 
      return 1;
    }
  }
  Serial.println("H 2"); 
  stepper->moveTo(-MaxHomeSearch);
  while(!motorIsHome(motorEndPin, EndLogicHighWhenHome)) {
    stepper->run();
    if(stepper->currentPosition() <= -long(MaxHomeSearch)){
      Serial.println("H ERR 2");
      stepper->stop(); 
      return 2;
    }
  }
  Serial.println("H 3"); 
  stepper->stop();
  while(motorIsHome(motorEndPin, EndLogicHighWhenHome)) {
    if (stepper->distanceToGo() == 0){
      stepper->moveTo(++cmd);
    }
    stepper->run();
    if(cmd > MaxHomeSearchSmall){
      Serial.println("H ERR 3"); 
      return 3;
    }
  }
  while(!motorIsHome(motorEndPin, EndLogicHighWhenHome) && (cmd > -MaxHomeSearch)) {
    if (stepper->distanceToGo() == 0){
      stepper->moveTo(--cmd);
    }
    stepper->run();
    if(cmd < -MaxHomeSearch){
      Serial.println("H ERR 4"); 
      return 4;
    }
  }
  Serial.println("Homing done.");
  stepper->setCurrentPosition(0);
  stepper->setMaxSpeed(10000);
  stepper->setAcceleration(10000);
  return 0;
}
