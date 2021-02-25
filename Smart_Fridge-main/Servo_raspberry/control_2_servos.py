# Import libraries
import RPi.GPIO as GPIO
import time

# Set GPIO numbering mode
GPIO.setmode(GPIO.BOARD)

# Set pins 11 & 12 as outputs, and define as PWM servo1 & servo2
GPIO.setup(11,GPIO.OUT)
servo1 = GPIO.PWM(11,50) # pin 11 for servo1
GPIO.setup(12,GPIO.OUT)
servo2 = GPIO.PWM(12,50) # pin 12 for servo2

# Start PWM running on both servos, value of 0 (pulse off)
servo1.start(0)
servo2.start(0)
try:
    # Move arm in working position
    while True:
        servo1.ChangeDutyCycle(7.5)
        time.sleep(1.5)
        servo1.ChangeDutyCycle(7.5)
        time.sleep(0.5)
        servo1.ChangeDutyCycle(0)
        servo2.ChangeDutyCycle(8.5)
        time.sleep(0.5)
        servo2.ChangeDutyCycle(0)
        time.sleep(5)
        # Move arm in rest position.
        #while True:	
        servo2.ChangeDutyCycle(4.6)
        time.sleep(0.5)
        servo2.ChangeDutyCycle(4.6)
        time.sleep(0.5)
        servo1.ChangeDutyCycle(6.5)
        time.sleep(1)
        
	
	#servo1.ChangeDutyCycle(6.5)
	#time.sleep(2)
	#servo1.ChangeDutyCycle(3.5)
	#time.sleep(2)
	#servo1.ChangeDutyCycle(4.5)
	#time.sleep(5)
		
finally:
	#Clean things up at the end
	servo1.stop()
	servo2.stop()
	GPIO.cleanup()
	print ("Goodbye")
