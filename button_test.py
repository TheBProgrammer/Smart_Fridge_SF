import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

GPIO.setup(35, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(36, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
  add_state = GPIO.input(35)
  sub_state = GPIO.input(36)
  
  if add_state == False:
    print ('Add Button Pressed')
    time.sleep(0.2)
    
  if sub_state == False:
    print ('Subtract Button Pressed')
    time.sleep(0.2)    

  if (add_state == False && sub_state == False):
    print ('Add and subtract Button Pressed')
    time.sleep(0.2)        
    
