#! /usr/bin/python3
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse

import numpy as np
import tensorflow as tf
import pandas as pd

# for firebase/database
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# for barcode
import pyzbar.pyzbar as pyzbar
import cv2

# for reading files in dir
import os
from datetime import datetime
import time
import sys

# Raspi lib
import RPi.GPIO as GPIO
from picamera.array import PiRGBArray
from picamera import PiCamera

EMULATE_HX711=False

referenceUnit = -22.5

wait_time = 1

if not EMULATE_HX711:
    from hx711 import HX711
else:
    from emulated_hx711 import HX711
    
#Button Pins
addButton = 19 # Pin 35
subButton = 16 # Pin 36
    
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(addButton,GPIO.IN)
GPIO.setup(subButton,GPIO.IN)

#Servo setup
GPIO.setup(17,GPIO.OUT)
servo1 = GPIO.PWM(17,50) #Pin 11 for servo1 and freq = 50 Hz
GPIO.setup(18,GPIO.OUT)
servo2 = GPIO.PWM(18,50) #Pin 12 for servo1 and freq = 50 Hz

# Fetch the service account key JSON file contents
cred = credentials.Certificate('fir-listview-4994a-firebase-adminsdk.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fir-listview-4994a.firebaseio.com//'
})

down = False
item = []
weight = []

def cleanAndExit():
    print("Cleaning...")

    if not EMULATE_HX711:
        GPIO.cleanup()
        
    print("Bye!")
    sys.exit()

def weight_init():
    
    global hx
    hx = HX711(5, 6) # Pin 29 and 31
    hx.set_reading_format("MSB","MSB")
    hx.set_reference_unit(referenceUnit)
    hx.reset()
    hx.tare()

    print("Tare done! Add weight now...")

def load_graph(model_file):
    graph = tf.Graph()
    graph_def = tf.compat.v1.GraphDef()

    with open(model_file, "rb") as f:
        graph_def.ParseFromString(f.read())
    with graph.as_default():
        tf.import_graph_def(graph_def)

    return graph


def read_tensor_from_image_file(file_name,
                                input_height=299,
                                input_width=299,
                                input_mean=0,
                                input_std=255):
    input_name = "file_reader"
    output_name = "normalized"
    file_reader = tf.io.read_file(file_name, input_name)
    if file_name.endswith(".png"):
        image_reader = tf.image.decode_png(
            file_reader, channels=3, name="png_reader")
    elif file_name.endswith(".gif"):
        image_reader = tf.squeeze(
            tf.image.decode_gif(file_reader, name="gif_reader"))
    elif file_name.endswith(".bmp"):
        image_reader = tf.image.decode_bmp(file_reader, name="bmp_reader")
    else:
        image_reader = tf.image.decode_jpeg(
            file_reader, channels=3, name="jpeg_reader")
    float_caster = tf.cast(image_reader, tf.float32)
    dims_expander = tf.expand_dims(float_caster, 0)
    resized = tf.compat.v1.image.resize_bilinear(
        dims_expander, [input_height, input_width])
    normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
    sess = tf.compat.v1.Session()
    result = sess.run(normalized)

    return result


def load_labels(label_file):
    label = []
    proto_as_ascii_lines = tf.io.gfile.GFile(label_file).readlines()
    for l in proto_as_ascii_lines:
        label.append(l.rstrip())
    return label


def decode(im):
    # Find barcodes and QR codes
    decodedObjects = pyzbar.decode(im)

    '''
    # Print results
    for obj in decodedObjects:
        print('Type : ', obj.type)
        print('Data : ', obj.data, '\n')
    '''

    return decodedObjects

def arm_up():
    #servo1.start(0)
    #servo2.start(0)

    servo1.ChangeDutyCycle(7.5)
    time.sleep(1.5)
    servo1.ChangeDutyCycle(7.5)
    time.sleep(0.5)
    servo1.ChangeDutyCycle(0)
    servo2.ChangeDutyCycle(7.8)
    time.sleep(1.5)
    servo2.ChangeDutyCycle(7.8)
    time.sleep(0.5)
    servo2.ChangeDutyCycle(0)

    print("Armed up !!")

def arm_down():
    #servo1.start(0)
    #servo2.start(0)

    servo2.ChangeDutyCycle(4.4)
    time.sleep(1)
    servo2.ChangeDutyCycle(4.4)
    time.sleep(0.5)
    servo2.ChangeDutyCycle(0)
    servo1.ChangeDutyCycle(7.0)
    time.sleep(1)
    servo1.ChangeDutyCycle(6.5)
    time.sleep(1)
    servo1.ChangeDutyCycle(6.0)
    time.sleep(1)
    servo1.ChangeDutyCycle(5.5)
    time.sleep(1)
    servo1.ChangeDutyCycle(5.0)
    time.sleep(1)
    servo1.ChangeDutyCycle(4.8)
    time.sleep(1)
    servo1.ChangeDutyCycle(4.7)
    time.sleep(0.5)
    servo1.ChangeDutyCycle(0)
    time.sleep(0.5)
    #servo1.stop()
    
    down = True
    print("Arm down !!")

# Display barcode and QR code location
def display(im, decodedObjects):

    # Loop over all decoded objects
    for decodedObject in decodedObjects:
        points = decodedObject.polygon

        # If the points do not form a quad, find convex hull
        if len(points) > 4:
            hull = cv2.convexHull(
                np.array([point for point in points], dtype=np.float32))
            hull = list(map(tuple, np.squeeze(hull)))
        else:
            hull = points

        # Number of points in the convex hull
        n = len(hull)

        # Draw the convext hull
        for j in range(0, n):
            cv2.line(im, hull[j], hull[(j+1) % n], (255, 0, 0), 3)

    # Display results
    cv2.imshow("Results", im)


def Check_for_barcode(file_name):
    # Read image
    im = cv2.imread(file_name)
    decodedObjects = decode(im)

    for obj in decodedObjects:

        if(len(obj.data) > 0):
            return True
            break

def giveItemTable(imageFolder):
    
    #df = pd.DataFrame(columns=['Item','Quantity','Time'])
    #counter = 0
    const = 0
    
    for files in os.listdir(folder_path + imageFolder):
        file_name = os.path.join(folder_path + imageFolder, files)
        print(file_name)

        if(Check_for_barcode(file_name)):
            # Read image
            im = cv2.imread(file_name)
            decodedObjects = decode(im)

            for obj in decodedObjects:
                # variable for database
                thing = obj.data
                print(thing)
                item.append(thing)
        
        else: 
            graph = load_graph(model_file)
            t = read_tensor_from_image_file(
                file_name,
                input_height=input_height,
                input_width=input_width,
                input_mean=input_mean,
                input_std=input_std)

            input_name = "import/" + input_layer
            output_name = "import/" + output_layer
            input_operation = graph.get_operation_by_name(input_name)
            output_operation = graph.get_operation_by_name(output_name)

            with tf.compat.v1.Session(graph=graph) as sess:
                results = sess.run(output_operation.outputs[0], {
                    input_operation.outputs[0]: t
                })
            results = np.squeeze(results)

            top_k = results.argsort()[-5:][::-1]
            labels = load_labels(label_file)

            #variable for database
            thing = labels[top_k[0]] #input item name as string
            print(thing)
            item.append(thing)
        
        for (i, j) in zip(weight, item):
            dt_string = now.strftime("%d-%m-%Y:%H:%M:%S")
            time = now.strftime("Date: %d/%m/%Y Time: %H:%M:%S")
            #datetime.now().strftime("%H:%M:%S")
            #tab = [item,val,time]
            #df = pd.DataFrame(tab, index=[counter])
            print("Item: ",j)
            print("Weight: ",i)
            print("Time: ",time)

            data =  { 'fruitname': j,
                       'fruitWeight': i,
                        'dateTimes': time
                    }
        
            ref=db.reference('SmartFridge')
            box_ref=ref.child("DateTime:"+dt_string)
            box_ref.set(data)
            print("Added successfully to Firebase")
            #counter = counter + 1

            if GPIO.input(addButton):
                ref=db.reference('SmartFridge')
                box_ref=ref.child("DateTime:"+dt_string)
                box_ref.set(data)
                print("Added successfully") 

            if GPIO.input(subButton):
                ref=db.reference('SmartFridge')
                box_ref=ref.child("DateTime:"+dt_string)
                box_ref.set(data)
                print("Removed successfully")
                
            del item[const]
            del weight[const]
     

        '''
        for i in top_k:
            print(labels[i], results[i])
        '''
        #dateString= datetime.now().date()
        #print(df.head())

def delete_processed_images(imageFolder):
    for files in os.listdir(folder_path + imageFolder):
        file_name = os.path.join(folder_path + imageFolder, files)
        print(file_name)
        
        if os.path.exists(file_name):
            os.remove(file_name)
            print(file_name + " is deleted.")
        else:
            print(file_name + " is already deleted.")

if __name__ == "__main__":

    print("Arming Up ! Please wait...")
    servo1.start(0)
    servo2.start(0)
    arm_up()
    time.sleep(20)
    weight_init()
    
    folder_path = "/home/pi/Smart_Fridge/"
    file_name = folder_path + "test-images/apple.jpeg"
    model_file = folder_path + "model/output_graph.pb"
    label_file = folder_path + "model/output_labels.txt"
    input_height = 299
    input_width = 299
    input_mean = 0
    input_std = 255
    input_layer = "Placeholder"
    output_layer = "final_result"

    # no nee to use the parsers, i have added the default values
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", help="image to be processed")
    parser.add_argument("--graph", help="graph/model to be executed")
    parser.add_argument("--labels", help="name of file containing labels")
    parser.add_argument("--input_height", type=int, help="input height")
    parser.add_argument("--input_width", type=int, help="input width")
    parser.add_argument("--input_mean", type=int, help="input mean")
    parser.add_argument("--input_std", type=int, help="input std")
    parser.add_argument("--input_layer", help="name of input layer")
    parser.add_argument("--output_layer", help="name of output layer")
    args = parser.parse_args()

    if args.graph:
        model_file = args.graph
    if args.image:
        file_name = args.image
    if args.labels:
        label_file = args.labels
    if args.input_height:
        input_height = args.input_height
    if args.input_width:
        input_width = args.input_width
    if args.input_mean:
        input_mean = args.input_mean
    if args.input_std:
        input_std = args.input_std
    if args.input_layer:
        input_layer = args.input_layer
    if args.output_layer:
        output_layer = args.output_layer

    flag = 0

    camera = PiCamera()
    camera.resolution = (640, 480)
    rawCapture = PiRGBArray(camera, size=(640, 480))
    # allow the camera to warmup
    time.sleep(0.2)
    
    cap = cv2.VideoCapture(0)
    now = datetime.now()
    
    
    while True:
        try:
            if down == True:
                down = False
                servo1.start(0)
                servo2.start(0)
                arm_up()
            time.sleep(2)
            val = int(hx.get_weight(5))
            print(val)
            
            if val > 50 :
            #and GPIO.input(addButton):

                print("Weight detected - Add")
                print (val)
                weight.append(val)
                
                time.sleep(5)
                print("image capture started")

                camera.capture(rawCapture, format = "bgr")
                im = rawCapture.array
                now = datetime.now()
                img_name = folder_path + "captured_images/Add/"+ str(now) + "_{}.png".format(val)
                cv2.imwrite(img_name, im)
                rawCapture.truncate(0)

                print("image capture completed")
                print("please remove the item and place a new one")
                time.sleep(20) #30 seconds for user to remove fruit

                flag = 0

            elif val > 50 and GPIO.input(subButton):

                print("Weight detected - Sub")
                time.sleep(5)
                print("image capture started")

                camera.capture(rawCapture, format = "bgr")
                im = rawCapture.array
                now = datetime.now()
                img_name = folder_path + "captured_images/Sub/"+ str(now) + "_{}.png".format(val)
                cv2.imwrite(img_name, im)
                rawCapture.truncate(0)

                print("Image capture completed")
                print("Please remove the item and place a new one")
                time.sleep(30) #30 seconds for user to remove fruit

                flag = 0
                
            else:
                cap.release()
                
            time.sleep(0.1)

            next_now = datetime.now()
            

            if ((int(next_now.strftime('%H')) == int(now.strftime('%H'))) and (int(next_now.strftime('%M')) - int(now.strftime('%M')) > wait_time) and flag == 0) or ((int(next_now.strftime('%H')) > int(now.strftime('%H'))) and (int(next_now.strftime('%M')) > wait_time) and flag == 0):
                #turn camera off
                print("Processing Images. Please wait..")
                arm_down()
                cap.release()
                

                #if GPIO.input(addButton):
                giveItemTable("captured_images/Add")
                time.sleep(5)
                delete_processed_images("captured_images/Add")
                print("Processing Done!!")
                servo1.start(0)
                servo2.start(0)
                arm_up()
                down = False

                if GPIO.input(subButton):
                    giveItemTable("captured_images/Sub")
                    time.sleep(5)
                    delete_processed_images("captured_images/Sub")
                    print("Processing Done!!")
                    servo1.start(0)
                    servo2.start(0)
                    arm_up()
                    down = False
                    
                flag = 1


                
        except (KeyboardInterrupt, SystemExit):
            hx.power_down()
            arm_down()
            servo1.stop()
            servo2.stop()
            GPIO.cleanup()
            print("Goodbye")
            cleanAndExit()
            cap.release()
            cv2.destroyAllWindows()