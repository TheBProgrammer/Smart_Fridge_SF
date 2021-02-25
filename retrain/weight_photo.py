#! /usr/bin/python3

from __future__ import print_function
from datetime import datetime
import sys
import pyzbar.pyzbar as pyzbar
import numpy as np
import cv2
import datetime

EMULATE_HX711=False

referenceUnit = 113

if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711

def cleanAndExit():
    print("Cleaning...")

    if not EMULATE_HX711:
        GPIO.cleanup()
        
    print("Bye!")
    sys.exit()

def weight_init():
    
    global hx
    hx = HX711(5, 6)

    # I've found out that, for some reason, the order of the bytes is not always the same between versions of python, numpy and the hx711 itself.
    # Still need to figure out why does it change.
    # If you're experiencing super random values, change these values to MSB or LSB until to get more stable values.
    # There is some code below to debug and log the order of the bits and the bytes.
    # The first parameter is the order in which the bytes are used to build the "long" value.
    # The second paramter is the order of the bits inside each byte.
    # According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
    hx.set_reading_format("MSB","MSB")

    # HOW TO CALCULATE THE REFFERENCE UNIT
    # To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
    # In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
    # and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
    # If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
    #hx.set_reference_unit(113)
    hx.set_reference_unit(referenceUnit)

    hx.reset()

    hx.tare()

    print("Tare done! Add weight now...")


if __name__ == "__main__":
    folder_path = "/home/pi/Smart_Fridge/weight_captured_images/"
    
    cap = cv2.VideoCapture(0)
    weight_init()
    
    while True:
        try:
            val = int(hx.get_weight(5))
            print(val)

            if val > 100 :
                ret, im = cap.read()
                now = datetime.now()
                img_name = folder_path + str(now) + "_{}.png".format(val)
                cv2.imwrite(img_name, im)

            time.sleep(0.1)

                
        except (KeyboardInterrupt, SystemExit):
            hx.power_down()
            cleanAndExit()
            cap.release()
            cv2.destroyAllWindows()
            
