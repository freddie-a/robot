##FUNCTIONS WE NEED##
# Move *direction* for *distance* at *speed*
# Brake
# Rotate *degrees*
# Get Position
# Get Speed

##Libraries
import RPi.GPIO as GPIO
import serial
import time

##Global Variables
PORT = "/dev/ttyACM0"
SERIAL_CONN = serial.Serial(PORT, 9600)
SPEED = 0
DIRECTION = 0
GPIO_TRIGGER = 18
GPIO_ECHO = 24

def init():
	SERIAL_CONN.flushInput()
	ultrasonic_sensor_initialise()

def ultrasonic_sensor_initialise():
	GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
	GPIO.setup(GPIO_ECHO, GPIO.IN)

def get_distance(): #Depends where we mount the sensor (or if we have multiple sensors)
	#Send the pulse and start the clock
	GPIO.output(GPIO_TRIGGER, True)
	START_TIME = time.time()
	time.sleep(0.00001)
	GPIO.output(GPIO_TRIGGER, False)

	while not GPIO.input(GPIO_ECHO):
		#Do a thing
		print('yes not done')

	END_TIME = time.time()
	TIME_TAKEN = END_TIME - START_TIME
	DISTANCE = (TIME_TAKEN * 34300) / 2

	return(DISTANCE) #in cm

def rotate_degrees():
	#TODO - work out calculations for motor speed

def get_speed():
	#TODO

#Assuming ultrasonic sensor is attached to the back
def move(DIRECTION, DISTANCE, SPEED=100): #Speed as a %, not sure how to implement yet
	INITIAL_DISTANCE = get_distance()
	while (get_distance() - INITIAL_DISTANCE) < DISTANCE:
		SERIAL_CONN.write(DIRECTION) #TODO speed
	brake()

def brake():
	SERIAL_CONN.write(000)
	#Hopefully this will stop fairly briskly, we can test and see if it's enough
