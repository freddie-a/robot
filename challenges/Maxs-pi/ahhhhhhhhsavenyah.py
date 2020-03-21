import RPi.GPIO as GPIO
from time import sleep
GPIO.setmode(GPIO.BOARD)
GPIO.setup(32, GPIO.OUT)


pwm = GPIO.PWM(32, 50)
pwm.start(0)
'''
GPIO.output(32, True)
pwm.ChangeDutyCycle(9)
sleep(5)
pwm.ChangeDutyCycle(7.5)
sleep(5)
pwm.ChangeDutyCycle(5)
sleep(5)
GPIO.output(32, False)
pwm.ChangeDutyCycle(0)
'''
pwm.ChangeDutyCycle(15)
sleep(1)
pwm.ChangeDutyCycle(5)
sleep(1)
pwm.ChangeDutyCycle(17)
sleep(1)
pwm.ChangeDutyCycle(3)
sleep(1)
for i in range(11):
	pwm.ChangeDutyCycle(i+5)
	sleep(1)
pwm.stop()




GPIO.cleanup()
