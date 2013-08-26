// The program will perform two tasks:
//
//   1. Analog input to get the values registered in
//      a photodiode, which is the main task.
//   2. Count the revolutions of the ball bearing, this will
//      be done using the digital port 3 and using interruption.
//      It will say the degrees that the ball bearing has rotated,
//      in reference with the last time obtained.
//
// An LED will flash when the speed of revolution is constant,
// with a certain error fixed in the variable "percentage".
//
// Angles are measured from 0 to 1023
//
//   This program for Arduino Uno reads two channels and sends the data
//   out through the serial port in 4 bytes.
//   For synchronization purposes, the following scheme was chosen:
//   A0 data:   A09 (MSB) A08 A07 A06 A05 A04 A03 A02 A01 A00 (LSB)
//   A1 data:   A19 (MSB) A18 A17 A16 A15 A14 A13 A12 A11 A10 (LSB)
//   sent as byte 1:   1 1 1 A09 A08 A07 A06 A05
//       and byte 2:   0 1 1 A04 A03 A02 A01 A00
//       and byte 3:   0 1 1 A19 A18 A17 A16 A15
//       and byte 4:   0 1 1 A14 A13 A12 A11 A10
//
//    (This arrangement was chosen for hystorical reasons; there are
//     many other possibilities. 3 bytes would be enough, but this could
//     possibly create a nonsymmetry between the channels.
//
//


int sensePin = A0;  //pin used for the photodiode

//stuff used for counting the revolutions

int led = 13; //led attached to pin 13
int state = LOW;  //volatille for interruptions
int x =0;  //count each time there is an interruption

double tpd =1;  //time per degree
int degree =0;
int count_degree =1;
volatile int interruption =LOW;
byte lb;
byte hb;
int photodiode;
boolean running = true;


unsigned long  ntime =0;  //new time
unsigned long  otime =0;  //output time (time between interruptions)
unsigned long time;  //time spent running the program

//loop of setup

void setup()
{
  pinMode(led, OUTPUT); //set the led pin as an output pin
  attachInterrupt(0, count, RISING); //define the interruption
  Serial.begin (115200); //start the serial port with 115,200 baud
}

//loop for the interruption

void count()
{
  interruption =HIGH; //set the variable "interruption" as HIGH
  state = !state;
}

void send_pair(int x,int y) {          
  // shift sample by 3 bits, and select higher byte  
  hb=highByte(x<<3); 
  // set 3 most significant bits and send out
  Serial.write(hb|0b11100000); 
  // select lower byte and clear 3 most significant bits
  lb=(lowByte(x))&0b00011111;
  // set bits 5 and 6 and send out
  Serial.write(lb|0b01100000);
  // shift sample by 3 bits, and select higher byte  
  hb=highByte(y<<3); 
  // set 3 most significant bits and send out
  Serial.write(hb|0b01100000); 
  // select lower byte and clear 3 most significant bits
  lb=(lowByte(y))&0b00011111;
  // set bits 5 and 6 and send out
  Serial.write(lb|0b01100000);
}

//main loop

void loop()
{
  photodiode = analogRead(sensePin);
  
  digitalWrite(led, state);
  
  time = micros();  //time since program started
  otime = time - ntime; //total time - time in last interruption
  degree = otime / tpd;

  //if loop for printing the degrees
  
  if (degree < 1024 && running)
  {
    send_pair(degree,photodiode);
    /*
    Serial.print(degree);
    Serial.print(" ");
    Serial.print(time);
    Serial.print(" ");
    Serial.println(tpd);
    */
  }
  else
  {
    running = false;
  }
  

  
  //if loop when there is an interruption
  
  if (interruption)
  {
    x++;
    ntime = time;
    tpd = otime / 1024.; //time per degree of the last turn
    interruption =LOW; //set the variable "interruption" as LOW
    running = true;
  }
}
