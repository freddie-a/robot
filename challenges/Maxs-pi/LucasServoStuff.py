import RPi.GPIO as GPIO
from time import sleep
GPIO.setmode(GPIO.BOARD)
GPIO.setup(32, GPIO.OUT)

pwm = GPIO.PWM(32, 50)
pwm.start(0)
'''
#for i in range(15):
#    pwm.ChangeDutyCycle(i)
#    sleep(3)
#    print(i)
pwm.ChangeDutyCycle(0)
sleep(3)
print('0')
pwm.ChangeDutyCycle(10)
sleep(3)
print('10')
pwm.ChangeDutyCycle(1)
sleep(3)
print('1')
pwm.ChangeDutyCycle(15)
sleep(3)
print('15')
pwm.ChangeDutyCycle(5)
print('5')
'''
pwm.ChangeDutyCycle(10)
sleep(3)
pwm.ChangeDutyCycle(1)
sleep(5)
'''
i,o,e=select.select( [sys.stdin], [],[], 0.1 )
'''
def set_servo(speed=100):
    speed //= (100/15)
    pwm.ChangeDutyCycle(speed)
set_servo(50)
sleep(2)

async def run_servo_for_time(speed=100, time):
    speed //= (100/15)
    pwm.ChangeDutyCycle(speed)
    await trio.sleep(time)
    pwm.changeDutyCycle(0)

pwm.stop()
GPIO.cleanup()

