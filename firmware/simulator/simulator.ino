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
byte lb;
byte hb;
int r;
int t;
int s;
const double pi = 3.141592;

void setup() {
  // initialize serial communications at 115200 bps:
  Serial.begin(115200);
}

void loop() {
  r = 1023;//random(1024);
  t = 0;
  while(t<=r) {
    s = (int)1023*pow(sin(2*pi*t/1024.),2);
    send_pair(t,s);
    t++;
  }
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
