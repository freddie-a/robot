#Imports
from evdev import InputDevice, categorize, ecodes
from time import sleep
import serial

#Setting up serial connection to Arduino
port = "/dev/ttyACM0"
s1 = serial.Serial(port, 9600)
s1.flushInput()

#Setting up gamepad as DS4 controller
gamepad = InputDevice('/dev/input/event4')
print('Initialising.')
sleep(0.5)
print('Initialising..')
sleep(0.5)
print('Initializing...')
sleep(1)
print('READY')

#Button codes
triangleBtn = 307
squareBtn = 308
xBtn = 304
circleBtn = 305
r2Btn = 313
l2Btn = 312

def start():
 for event in gamepad.read_loop():
  #If buttons being pressed (gets rid of motion controls)
  if event.value == 1:
   print(event.code)
   #If triangle pressed, tell motors to go forwards until triangle is no longer held down
   if event.code == triangleBtn:
    while triangleBtn in gamepad.active_keys():
     s1.write("f".encode())
     sleep(0.05)
   #If X pressed, tell motors to go backwards until X is no longer held down
   elif event.code == xBtn:
    while xBtn in gamepad.active_keys():
     s1.write(str.encode("b"))
     sleep(0.05)
   #If square pressed, tell motors to go left until square is no longer held down
   elif event.code == squareBtn:
    while squareBtn in gamepad.active_keys():
     s1.write(str.encode("l"))
     sleep(0.05)
   #If circle pressed, tell motors to go right until circle is no longer held down
   elif event.code == circleBtn:
    while circleBtn in gamepad.active_keys():
     s1.write(str.encode("r"))
     sleep(0.05)
