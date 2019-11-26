import Servo # I dont know how arduinos work
from controller import stick1 # Hoping joysticks will be broken down into vertical(1) and horizontal(0) components
  
  
while 1:
  a = controller.stick1()
  if a > 0: # above normal
    servo(3)
   elif a < 0: # below normal
    servo(-3)
