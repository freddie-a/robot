#include<AFMotor.h>
AF_DCMotor motor1(1); //Front Left
AF_DCMotor motor2(2); //Back Left
AF_DCMotor motor3(3); //Front Right
AF_DCMotor motor4(4); //Back Right

//Pins
int data;

//Variables
int instruction;

//Setup serial connection + motor speeds
void setup() {
  Serial.begin(9600);
  motor1.setSpeed(200);
  motor2.setSpeed(200);
  motor3.setSpeed(200);
  motor4.setSpeed(200);
  
}

void loop() {
  if (Serial.available()) {
    if (Serial.available() > 0) {
      int instruction_segment = Serial.read();
      instruction += instruction_segment; 
    } else {
      instruction = Serial.read();
    }
    switch (instruction) {
      case 0: //Forward - run all motors forwards for 50ms then stop
        motor1.run(FORWARD);
        motor2.run(FORWARD);
        motor3.run(FORWARD);
        motor4.run(FORWARD);
        delay(50);
        motor1.run(RELEASE);
        motor2.run(RELEASE);
        motor3.run(RELEASE);
        motor4.run(RELEASE);
        break;
      case 180: //Backward - run all motors backwards for 50ms then stop
        motor1.run(BACKWARD);
        motor2.run(BACKWARD);
        motor3.run(BACKWARD);
        motor3.run(BACKWARD);
        delay(50);
        motor1.run(RELEASE);
        motor2.run(RELEASE);
        motor3.run(RELEASE);
        motor4.run(RELEASE);
        break;
      case 270: //Left - run front left + back right forwards, back left + front right backwards for 50ms then stop
        motor1.run(FORWARD);
        motor2.run(BACKWARD);
        motor3.run(BACKWARD);
        motor4.run(FORWARD);
        delay(50);
        motor1.run(RELEASE);
        motor2.run(RELEASE);
        motor3.run(RELEASE);
        motor4.run(RELEASE);
        break;
      case 90: //Right - run front left + back right backwards, back left + front right forwards for 50 ms then stop
        motor1.run(BACKWARD);
        motor2.run(FORWARD);
        motor3.run(FORWARD);
        motor4.run(BACKWARD);
        delay(50);
        motor1.run(RELEASE);
        motor2.run(RELEASE);
        motor3.run(RELEASE);
        motor4.run(RELEASE);
        break;
      case 000:
        motor1.run(RELEASE);
        motor2.run(RELEASE);
        motor3.run(RELEASE);
        motor4.run(RELEASE);
    }
  }
}