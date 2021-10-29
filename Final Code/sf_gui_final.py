#! /usr/bin/python3

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf
import pandas as pd

# for GUI Pyqt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, QTime

# for firebase/database
import pyrebase

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

wait_time = 0.2

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

#Setup
down = False
item = []
weight = []

firebaseConfig = { 'apiKey': "AIzaSyA2NIKjW9kD31eeRnFDZhpW02q443AoIBA",
        'authDomain': "smart-fridge-94bff.firebaseapp.com",
        'databaseURL': "https://smart-fridge-94bff-default-rtdb.firebaseio.com",
        'projectId': "smart-fridge-94bff",
        'storageBucket': "smart-fridge-94bff.appspot.com",
        'messagingSenderId': "625536633101",
        'appId': "1:625536633101:web:d4951c5cc692fac0364844"
        }

quotes = ['Health is a state of complete mental, social and physical well-being, not merely the absence of disease or infirmity.', 
'Health is a state of complete harmony of the body, mind and spirit. When one is free from physical disabilities and mental distractions, the gates of the soul open.', 
'To ensure good health: eat lightly, breathe deeply, live moderately, cultivate cheerfulness, and maintain an interest in life.', 
'Physical fitness is the first requisite of happiness.', 
'The human body has been designed to resist an infinite number of changes and attacks brought about by its environment. The secret of good health lies in successful adjustment to changing stresses on the body.', 
'To keep the body in good health is a duty…otherwise we shall not be able to keep the mind strong and clear.', 
'Good health is not something we can buy. However, it can be an extremely valuable savings account.', 
'You can’t control what goes on outside, but you CAN control what goes on inside.', 
'The cheerful mind perseveres, and the strong mind hews its way through a thousand difficulties.', 
'It is health that is the real wealth, and not pieces of gold and silver.', 
'Keeping your body healthy is an expression of gratitude to the whole cosmos- the trees, the clouds, everything.', 
'Divide each difficulty into as many parts as is feasible and necessary to resolve it, and watch the whole transform.', 
'Every negative belief weakens the partnership between mind and body', 
'The doctor of the future will give no medicine, but will instruct his patients in care of the human frame, in diet, and in the cause and prevention of disease.', 
'I have chosen to be happy because it is good for my health.', 
'A sad soul can be just as lethal as a germ.', 
'If you know the art of deep breathing, you have the strength, wisdom and courage of ten tigers.', 
'Remain calm, because peace equals power.', 
'Healthy citizens are the greatest asset any country can have.', 
'A good laugh and a long sleep are the best cures in the doctor’s book.', 
'If you keep good food in your fridge, you will eat good food.', 
'One must eat to live, not live to eat.', 
'Exercising should be about rewarding the body with endorphins and strength. Not about punishing your body for what you’ve eaten.', 
'Don’t dig your grave with your own knife and fork.', 
'Your goals, minus your doubts, equal your reality.', 
'You don’t drown by falling in water. You drown by staying there.']

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
                                input_height=224,
                                input_width=224,
                                input_mean=0,
                                input_std=255):
    input_name = "file_reader" #MOBILE = 224 INCEPTION 299
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
    down = False
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
            dt_string = now.strftime("%d/%m/%Y - %H:%M:%S")

            firebase = pyrebase.initialize_app(firebaseConfig)
            db = firebase.database()

            things = db.child("items").get()
            for fruits in things.each():
                val = things.val()
                #print(val)
                for n in val.values():
                    for k,v in val.items():
                        #print(v['Item']) 
                        if (v['Item']) == j :
                            present = True
                            #print(present)
                            break
                        else :
                            present = False
                            #print(present)
                    break
                break

            if present :
                things = db.child("items").order_by_child("Item").equal_to(j).get()
                for fruits in things.each():
                    #print("1")
                    val = []
                    val = things.val()
                    #print(val)
                    for m in val.values():
                        for k,v in val.items():
                            #print (v['Item'])
                            if v['Item'] == j :
                                cWeight = v['Weight']
                    iWeight = int(cWeight) + i
                    uWeight = str(iWeight)
                    print(uWeight)
                    db.child("items").child(fruits.key()).update({'Weight' : uWeight,'TimeStamp':dt_string})
                    print("Updated Successfully in Firebase")
            else :
                wg = str(i)
                data = {
                'Item': j,
                'TimeStamp': dt_string,
                'Weight': wg
                }
                db.child("items").push(data)
                print("Added Successfully in Firebase")

            # Testing End
            '''
            For ADD Button
            Add = True
            Remove = False
            '''

            if Add:
                things = db.child("items").get()
                for fruits in things.each():
                    val = things.val()
                    for k,v in val.items():
                        if (v['Item']) == j :
                            present = True
                            break
                        else :
                            present = False
                    break  

                if present :
                    things = db.child("items").order_by_child("Item").equal_to(j).get()
                    for fruits in things.each():
                        #print("1")
                        val = []
                        val = things.val()
                        #print(val)
                        for k,v in val.items():
                            #print (v['Item'])
                            if v['Item'] == j :
                                cWeight = v['Weight']
                        iWeight = int(cWeight) + int(i)
                        uWeight = str(iWeight)
                        print(uWeight)
                        db.child("items").child(fruits.key()).update({'Weight' : uWeight,'TimeStamp':dt_string})
                        print("Updated Successfully in Firebase")
                else :
                    wg = str(i)
                    data = {
                    'Item': j,
                    'TimeStamp': dt_string,
                    'Weight': wg
                    }
                    db.child("items").push(data)
                    print("Added Successfully in Firebase")


            if Remove:
                things = db.child("items").get()
                for fruits in things.each():
                    val = things.val()
                    for k,v in val.items():
                        if (v['Item']) == j:
                            present = True
                            print(present)
                            break
                        else :
                            present = False
                            print(present)
                    break  

                if present :
                    things = db.child("items").order_by_child("Item").equal_to(j).get()
                    for fruits in things.each():
                        #print("1")
                        val = []
                        val = things.val()
                        #print(val)
                        for k,v in val.items():
                            #print (v['Item'])
                            if v['Item'] == j :
                                cWeight = v['Weight']
                        iWeight = int(cWeight) - int(i)
                        uWeight = str(iWeight)
                        print(uWeight)
                        db.child("items").child(fruits.key()).update({'Weight' : uWeight,'TimeStamp':dt_string})
                        print("Updated Successfully in Firebase")

                else :
                    wg = str(i)
                    data = {
                    'Item': j,
                    'TimeStamp': dt_string,
                    'Weight': wg
                    }
                    db.child("items").push(data)
                    print("Added Successfully in Firebase")
                
            del item[const]
            del weight[const]

def delete_processed_images(imageFolder):
    for files in os.listdir(folder_path + imageFolder):
        file_name = os.path.join(folder_path + imageFolder, files)
        print(file_name)
        
        if os.path.exists(file_name):
            os.remove(file_name)
            print(file_name + " is deleted.")
        else:
            print(file_name + " is already deleted.")

#*****************************************
class Stream(QtCore.QObject):
    newText = QtCore.pyqtSignal(str)

    def write(self, text):
        self.newText.emit(str(text))
#*****************************************


class Ui_SmartFridge(object):
    def setupUi(self, SmartFridge):
        SmartFridge.setObjectName("SmartFridge")
        SmartFridge.resize(996, 693)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(15)
        SmartFridge.setFont(font)
        self.centralwidget = QtWidgets.QWidget(SmartFridge)
        self.centralwidget.setMinimumSize(QtCore.QSize(996, 693))
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 178, 102, 255), stop:0.55 rgba(235, 148, 61, 255), stop:0.98 rgba(0, 0, 0, 255), stop:1 rgba(0, 0, 0, 0));\n"
"gridline-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(0, 0, 0, 255), stop:0.05 rgba(14, 8, 73, 255), stop:0.36 rgba(28, 17, 145, 255), stop:0.6 rgba(126, 14, 81, 255), stop:0.75 rgba(234, 11, 11, 255), stop:0.79 rgba(244, 70, 5, 255), stop:0.86 rgba(255, 136, 0, 255), stop:0.935 rgba(239, 236, 55, 255));")
        self.frame.setObjectName("frame")
        self.gridLayout = QtWidgets.QGridLayout(self.frame)
        self.gridLayout.setObjectName("gridLayout")
        
        #Calender
        self.calendarWidget = QtWidgets.QCalendarWidget(self.frame)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(16)
        self.calendarWidget.setFont(font)
        self.calendarWidget.setStyleSheet("background-color: rgb(254, 177, 31);\n"
"alternate-background-color: rgba(50, 51, 51, 66);\n"
"color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(0, 0, 0, 255), stop:0.05 rgba(14, 8, 73, 255), stop:0.36 rgba(28, 17, 145, 255), stop:0.6 rgba(126, 14, 81, 255), stop:0.75 rgba(234, 11, 11, 255), stop:0.79 rgba(244, 70, 5, 255), stop:0.86 rgba(255, 136, 0, 255), stop:0.935 rgba(239, 236, 55, 255));\n"
"selection-color: rgba(18, 0, 255, 255);\n"
"selection-background-color: rgb(152, 131, 255);\n"
"border:none;\n"
"border-radius: 15px;")
        self.calendarWidget.setObjectName("calendarWidget")
        self.gridLayout.addWidget(self.calendarWidget, 8, 2, 1, 1)

        #SHOW TIME
        self.Time = QtWidgets.QLabel(self.frame)

        timer = QTimer(SmartFridge)
        timer.timeout.connect(self.showTime)
        timer.start(1000)

        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(17)
        font.setBold(True)
        font.setWeight(75)
        self.Time.setFont(font)
        self.Time.setStyleSheet("background-color: rgb(255, 211, 47);\n"
"border-radius: 10px;")
        self.Time.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.Time.setIndent(15)
        self.Time.setObjectName("Time")
        self.gridLayout.addWidget(self.Time, 1, 2, 1, 1)

        #Add Item Button
        self.AddItem = QtWidgets.QPushButton(self.frame)
        self.AddItem.clicked.connect(self.AddItemclicked)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(17)
        font.setItalic(True)
        self.AddItem.setFont(font)
        self.AddItem.setStyleSheet("\n"
"background-color: rgb(255, 211, 47);\n"
"border: none;\n"
"border-radius: 10px\n"
"\n"
"")
        self.AddItem.setIconSize(QtCore.QSize(12, 12))
        self.AddItem.setObjectName("AddItem")
        self.gridLayout.addWidget(self.AddItem, 13, 2, 1, 1)

        #Quotes
        i = 0
        self.Quotes = QtWidgets.QLabel(self.frame)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(18)
        self.Quotes.setFont(font)
        self.Quotes.setLineWidth(11)
        self.Quotes.setAlignment(QtCore.Qt.AlignCenter)
        self.Quotes.setObjectName("Quotes")
        self.gridLayout.addWidget(self.Quotes, 0, 0, 1, 3)
        self.Quotes.setText(quotes[i])
        i++

        #status
        self.status = QtWidgets.QTextEdit(self.frame)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(15)
        self.status.setFont(font)
        self.status.setStyleSheet("background-color: rgb(255, 211, 47);\n"
"border: rgb(255,255,255);\n"
"border-radius: 10px;\n"
"")
        self.status.setObjectName("status")
        self.gridLayout.addWidget(self.status, 9, 2, 1, 1)

        #Shopping List
        self.ShoppingList = QtWidgets.QTextEdit(self.frame)
        self.ShoppingList()
        self.ShoppingList.setStyleSheet("background-color: rgb(255, 211, 47);\n"
"border: rgb(255,255,255);\n"
"border-radius: 10px;\n"
"")
        self.ShoppingList.setObjectName("ShoppingList")
        self.gridLayout.addWidget(self.ShoppingList, 8, 1, 1, 1)

        #Title
        self.title = QtWidgets.QLabel(self.frame)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(25)
        font.setBold(True)
        font.setWeight(75)
        self.title.setFont(font)
        self.title.setStyleSheet("background-color: rgb(255, 211, 47);\n"
"border-radius: 10px;")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setObjectName("title")
        self.gridLayout.addWidget(self.title, 1, 0, 1, 2)

        #Remove Item Button
        self.RemoveItem = QtWidgets.QPushButton(self.frame)
        self.RemoveItem.clicked.connect(self.RemoveItemclicked)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(17)
        font.setItalic(True)
        self.RemoveItem.setFont(font)
        self.RemoveItem.setStyleSheet("background-color: rgb(255, 211, 47);\n"
"border:none;\n"
"border-radius: 10px;\n"
"")
        self.RemoveItem.setObjectName("RemoveItem")
        self.gridLayout.addWidget(self.RemoveItem, 13, 0, 1, 1)

        #Mode
        self.Mode = QtWidgets.QLabel(self.frame)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.Mode.setFont(font)
        self.Mode.setStyleSheet("background-color: rgb(255, 211, 47);\n"
"border-radius: 10px;")
        self.Mode.setAlignment(QtCore.Qt.AlignCenter)
        self.Mode.setObjectName("Mode")
        self.gridLayout.addWidget(self.Mode, 13, 1, 1, 1)

        #Freshness Notification
        self.FreshnessNotification = QtWidgets.QLabel(self.frame)
        self.freshness()
        self.FreshnessNotification.setStyleSheet("background-color: rgb(255, 211, 47);\n"
"border: rgb(255,255,255);\n"
"border-radius: 10px;\n"
"")
        self.FreshnessNotification.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.FreshnessNotification.setObjectName("FreshnessNotification")
        self.gridLayout.addWidget(self.FreshnessNotification, 9, 1, 1, 1)

        #Table
        self.tableWidget = QtWidgets.QTableWidget(self.frame)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(20)
        self.tableWidget.setFont(font)
        self.tableWidget.setStyleSheet("background-color: rgb(255, 211, 47);\n"
"alternate-background-color: rgba(254, 165, 32, 102);\n"
"border: none;\n"
"border-radius: 10px;")
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setAutoScroll(True)
        self.tableWidget.setAutoScrollMargin(3)
        self.tableWidget.setDragDropOverwriteMode(False)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(2)

        self.tableWidget.setColumnWidth(0,350)
        self.tableWidget.setColumnWidth(1,350)
        self.loaddata()

        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(25)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        item.setBackground(QtGui.QColor(253, 133, 35))
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(25)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        item.setBackground(QtGui.QColor(253, 133, 35))
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.tableWidget.setHorizontalHeaderItem(1, item)
        self.gridLayout.addWidget(self.tableWidget, 8, 0, 2, 1)
        self.horizontalLayout.addWidget(self.frame)
        SmartFridge.setCentralWidget(self.centralwidget)

        self.retranslateUi(SmartFridge)
        QtCore.QMetaObject.connectSlotsByName(SmartFridge)

        sys.stdout = Stream(newText=self.onUpdateText)

    def onUpdateText(self, text):
        cursor = self.status.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.status.setTextCursor(cursor)
        self.status.ensureCursorVisible()

    def __del__(self):
        sys.stdout = sys.__stdout__

    def freshness(self):
        Notes = []
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y - %H:%M:%S")
        nows = datetime.strptime(dt_string, "%d/%m/%Y - %H:%M:%S")

        things = db.child("items").get()
        for things in things.each():
        val = things.val()
        Time_Stamp = val['TimeStamp']
        item_date = datetime.strptime(Time_Stamp, "%d/%m/%Y - %H:%M:%S")
        expiry = item_date + timedelta(days=2)
        if expiry < nows:
             print("Item "+val['Item']+" is not fresh")
        else:
            notes = db.child("notes").get()
            for notes in notes.each():
                note = notes.val()
                Notes.append(note['notes'])
            
        print("### NOTES ###")
        new_Notes = list(set(Notes))
        for i in range(0,len(new_Notes)):
            j = 1
            print(str(j)+"."+" "+new_Notes[i])
            j+=1


    def ShoppingList(self):
        value = db.child("Shopping List").get()
        for value in value.each():
            val = value.val()
            if val['buy']:
                text = val['item']
                cursor = self.ShoppingList.textCursor()
                cursor.movePosition(QtGui.QTextCursor.End)
                cursor.insertText(text)
                self.ShoppingList.setTextCursor(cursor)
                self.ShoppingList.ensureCursorVisible()

    def closeEvent(self, event):
        """Shuts down application on close."""
        # Return standard output to defaults.
        sys.stdout = sys.__stdout__
        super().closeEvent(event)

    def showTime(self):
        currentTime = QTime.currentTime()
        displayText = currentTime.toString("hh : mm : ss")
        self.Time.setText(displayText)

    def AddItemclicked(self):
        self.Mode.setText("Add Item Mode")
        print("Add Item Mode")
        now = datetime.now()
        Add = True
        Remove = False
        '''
        if down == True:
            down = False
            servo1.start(0)
            servo2.start(0)
            arm_up()
            time.sleep(2)
        '''
        while True:
            val = int(hx.get_weight(5))
            print(val)
            if val > 50:
                print (val)
                weight.append(val)
                    
                time.sleep(5)
                print("Image Capture Started")

                camera.capture(rawCapture, format = "bgr")
                im = rawCapture.array
                now = datetime.now()
                img_name = folder_path + "captured_images/Add/"+ str(now) + "_{}.png".format(val)
                cv2.imwrite(img_name, im)
                rawCapture.truncate(0)

                print("Image capture completed")
                print("Please remove the item and place a new one")
                time.sleep(50) #30 seconds for user to remove fruit

                flag = 0
            next_now = datetime.now()
            if ((int(next_now.strftime('%H')) == int(now.strftime('%H'))) and (int(next_now.strftime('%M')) - int(now.strftime('%M')) > wait_time) and flag == 0) or ((int(next_now.strftime('%H')) > int(now.strftime('%H'))) and (int(next_now.strftime('%M')) > wait_time) and flag == 0):
                print("Processing Images. Please wait..")
                arm_down()
                cap.release()
                #if GPIO.input(addButton):
                giveItemTable("captured_images/Add")
                time.sleep(5)
                #delete_processed_images("captured_images/Add")
                print("Processing Done!!")
                servo1.start(0)
                servo2.start(0)
                arm_up()
                down = False
                self.Mode.setText( "Press any button to continue...")
                break


    def RemoveItemclicked(self):
        self.Mode.setText("Remove Item Mode")
        print("Remove Item Mode")
        Add = False
        Remove = True
        now = datetime.now()
        '''
        if down == True:
            down = False
            servo1.start(0)
            servo2.start(0)
            arm_up()
            time.sleep(2)
           '''
        while True:
            val = int(hx.get_weight(5))
            print(val)
            if val > 50:
                print("Weight detected - Sub")
                time.sleep(5)
                print("Image Capture Started")

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
            next_now = datetime.now()
            if ((int(next_now.strftime('%H')) == int(now.strftime('%H'))) and (int(next_now.strftime('%M')) - int(now.strftime('%M')) > wait_time) and flag == 0) or ((int(next_now.strftime('%H')) > int(now.strftime('%H'))) and (int(next_now.strftime('%M')) > wait_time) and flag == 0):
                print("Processing Images. Please wait..")
                arm_down()
                cap.release()
                #if GPIO.input(addButton):
                giveItemTable("captured_images/Sub")
                time.sleep(5)
                #delete_processed_images("captured_images/Sub")
                print("Processing Done!!")
                servo1.start(0)
                servo2.start(0)
                arm_up()
                down = False
                self.Mode.setText( "Press any button to continue...")
                break

    def loaddata(self):
        data = []

        firebase = pyrebase.initialize_app(firebaseConfig)
        db = firebase.database()
        things = db.child("items").get()

        row = 0
        self.tableWidget.setRowCount(len(things.val()))

        for things in things.each():
            val = things.val()
            self.tableWidget.setItem(row,0,QtWidgets.QTableWidgetItem(val['Item']))
            self.tableWidget.setItem(row,1,QtWidgets.QTableWidgetItem(val['Weight']))
            row = row+1

    def retranslateUi(self, SmartFridge):
        _translate = QtCore.QCoreApplication.translate
        SmartFridge.setWindowTitle(_translate("SmartFridge", "Smart Fridge"))
        #self.Time.setText(_translate("SmartFridge", "Time"))
        self.AddItem.setText(_translate("SmartFridge", "ADD \n"
"ITEM"))
        self.title.setText(_translate("SmartFridge", "SMART FRIDGE"))
        self.RemoveItem.setText(_translate("SmartFridge", "REMOVE \n"
"ITEM"))
        self.Mode.setText("Press any button to continue...")
        self.FreshnessNotification.setText(_translate("SmartFridge", "Freshness"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("SmartFridge", "Item Name"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("SmartFridge", "Weight \n(in grams)"))


if __name__ == "__main__":


    print("Arming Up ! Please wait...")
    servo1.start(0)
    servo2.start(0)
    arm_up()
    down = False
    time.sleep(2)
    weight_init()

    folder_path = "/home/pi/Smart_Fridge/"
    file_name = folder_path + "test-images/apple.jpeg"
    model_file = folder_path + "model/output_graph.pb"
    label_file = folder_path + "model/output_labels.txt"
    input_height = 224
    input_width = 224 #MOBILLENET 224 ; INCEPTION 299
    input_mean = 0
    input_std = 255
    input_layer = "Placeholder"
    output_layer = "final_result"

    flag = 0

    camera = PiCamera()
    camera.resolution = (640, 480)
    rawCapture = PiRGBArray(camera, size=(640, 480))
    # allow the camera to warmup
    time.sleep(0.2)
    
    cap = cv2.VideoCapture(0)
    now = datetime.now()

    import sys
    app = QtWidgets.QApplication(sys.argv)
    SmartFridge = QtWidgets.QMainWindow()
    ui = Ui_SmartFridge()
    ui.setupUi(SmartFridge)
    SmartFridge.show()
    sys.exit(app.exec_())
