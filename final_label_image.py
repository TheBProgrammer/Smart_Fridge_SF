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

referenceUnit = -21.7

if not EMULATE_HX711:
    from hx711 import HX711
else:
    from emulated_hx711 import HX711
    
#Button Pins
addButton = 18
subButton = 19
    
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(addButton,GPIO.IN)
GPIO.setup(subButton,GPIO.IN)

# Fetch the service account key JSON file contents
cred = credentials.Certificate('fir-listview-4994a-firebase-adminsdk.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fir-listview-4994a.firebaseio.com//'
})



def cleanAndExit():
    print("Cleaning...")

    if not EMULATE_HX711:
        GPIO.cleanup()
        
    print("Bye!")
    sys.exit()

def weight_init():
    
    global hx
    hx = HX711(5, 6)
    hx.set_reading_format("MSB","MSB")
    hx.set_reference_unit(referenceUnit)
    hx.reset()
    hx.tare()

    print("Tare done! Add weight now...")

def load_graph(model_file):
    graph = tf.Graph()
    graph_def = tf.GraphDef()

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
    file_reader = tf.read_file(file_name, input_name)
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
    resized = tf.image.resize_bilinear(
        dims_expander, [input_height, input_width])
    normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
    sess = tf.Session()
    result = sess.run(normalized)

    return result


def load_labels(label_file):
    label = []
    proto_as_ascii_lines = tf.gfile.GFile(label_file).readlines()
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
    
    df = pd.DataFrame(columns=['Item','Quantity','Time'])
    counter = 0
    
    for files in os.listdir(folder_path + imageFolder):
        file_name = os.path.join(folder_path + imageFolder, files)
        print(file_name)

        if(Check_for_barcode(file_name)):
            # Read image
            im = cv2.imread(file_name)
            decodedObjects = decode(im)

            for obj in decodedObjects:
                # variable for database
                Item = obj.data
                print(item)
        
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

            with tf.Session(graph=graph) as sess:
                results = sess.run(output_operation.outputs[0], {
                    input_operation.outputs[0]: t
                })
            results = np.squeeze(results)

            top_k = results.argsort()[-5:][::-1]
            labels = load_labels(label_file)

            #variable for database
            item = labels[top_k[0]] #input item name as string
            print(item)
            
        time = datetime.now().strftime("%H:%M:%S")
        tab = [item,val,time]
        df = pd.DataFrame(tab, index=[counter])
        counter = counter + 1

        data =  { 'fruitname': item,
          'fruitWeight': val,
          'dateTimes': time
          }

        if GPIO.input(addButton):
            ref=db.reference('SmartFridge')
            #box_ref=ref.child("DateTime:"+dt_string)
            box_ref.set(data)
            print("Added successfully") 

        if GPIO.input(subButton):
            ref=db.reference('SmartFridge')
            #box_ref=ref.child("DateTime:"+dt_string)
            box_ref.put(data)
            print("Removed successfully") 

    '''
    for i in top_k:
        print(labels[i], results[i])
    '''
    dateString= datetime.now().date()
    print(df.head())


if __name__ == "__main__":

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
            val = int(hx.get_weight(5))
            print(val)
            
            if val > 50 and GPIO.input(addButton):

                print("Weight detected - Add")
                time.sleep(5)
                print("image capture started")

                camera.capture(rawCapture, format = "bgr")
                ret, im = rawCapture.array
                now = datetime.now()
                img_name = folder_path + "captured_images/Add/"+ str(now) + "_{}.png".format(val)
                cv2.imwrite(img_name, im)
                rawCapture.truncate(0)

                print("image capture completed")
                print("please remove the item and place a new one")
                time.sleep(30) #30 seconds for user to remove fruit

                flag = 0

            elif val > 50 and GPIO.input(subButton):

                print("Weight detected - Sub")
                time.sleep(5)
                print("image capture started")

                camera.capture(rawCapture, format = "bgr")
                ret, im = rawCapture.array
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
            

            if ((int(next_now.strftime('%H')) == int(now.strftime('%H'))) and (int(next_now.strftime('%M')) - int(now.strftime('%M')) > 1) and flag == 0) or ((int(next_now.strftime('%H')) > int(now.strftime('%H'))) and (int(next_now.strftime('%M')) > 1) and flag == 0):
                #turn camera off
                cap.release()

                if GPIO.input(addButton):
                    giveItemTable("captured_images/Add")

                if GPIO.input(subButton):
                    giveItemTable("captured_images/Sub")
                
                flag = 1


                
        except (KeyboardInterrupt, SystemExit):
            hx.power_down()
            cleanAndExit()
            cap.release()
            cv2.destroyAllWindows()