#! /usr/bin/python2
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import time
import sys
import datetime

import argparse

import numpy as np
import tensorflow as tf

# for barcode
import pyzbar.pyzbar as pyzbar
import cv2

# for reading files in dir
import os


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



if __name__ == "__main__":
    folder_path = "/home/konu/Documents/smart_fridge/jetson-fruits-classification/"
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
    
    cap = cv2.VideoCapture(0)
    
    while True:
        try:
            val = int(input("Enter weight"))
            print(val)

            if val > 0 :
                ret, im = cap.read()
                now = datetime.datetime.now()
                img_name = folder_path + "captured_images/"+ str(now) + "_{}.png".format(val)
                cv2.imwrite(img_name, im)
                flag = 0

            time.sleep(0.1)

            next_now = datetime.datetime.now()

            if (((int(next_now.strftime('%H')) == int(now.strftime('%H'))) and (int(next_now.strftime('%M')) - int(now.strftime('%M')) > 5) and flag == 0) or ((int(next_now.strftime('%H')) > int(now.strftime('%H'))) and (int(next_now.strftime('%M')) > 5) and flag == 0)):
                #start processing
                for files in os.listdir(folder_path + "test-images"):
                    file_name = os.path.join(folder_path + "test-images", files)
                    print(file_name)

                    if(Check_for_barcode(file_name)):
                        # Read image
                        im = cv2.imread(file_name)
                        decodedObjects = decode(im)

                        for obj in decodedObjects:
                            # variable for database
                            val = obj.data
                            print(val)

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
                        val = labels[top_k[0]]
                        print(val)

                        '''
                        for i in top_k:
                            print(labels[i], results[i])
                        '''
                
                flag = 1
                
        except (KeyboardInterrupt, SystemExit):
            hx.power_down()
            cleanAndExit()
            cap.release()
            cv2.destroyAllWindows()
            
