##TODO##
# Add stop button functionality

#Imports
import RPi.GPIO as GPIO

#Globals
DELAY_TIME = 0.0005
PINS = {
	"LEFT_SENSOR": 20,
	"MIDDLE_SENSOR": 21,
	"RIGHT_SENSOR": 22
}


def init():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(PINS["LEFT_SENSOR"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(PINS["MIDDLE_SENSOR"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(PINS["RIGHT_SENSOR"], GPIO.IN, pull_up_down=GPIO.PUD_UP)

def start():
	init()
	while True:
		if GPIO.input(PINS["LEFT_SENSOR"]) and not GPIO.input(PINS["MIDDLE_SENSOR"]):
			#Move to the left
			print('move to the left')
		elif not GPIO.input(PINS["RIGHT_SENSOR"]) and not GPIO.input(PINS["MIDDLE_SENSOR"]):
			#Move to the right
			print('move to the right')

start()
