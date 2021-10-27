from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, QTime

# for firebase/database
import pyrebase

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("SMART FRIDGE")
        MainWindow.resize(770, 569)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
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
        self.title = QtWidgets.QLabel(self.frame)
        self.title.setGeometry(QtCore.QRect(300, 10, 181, 31))
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.title.setFont(font)
        self.title.setStyleSheet("background-color: rgb(254, 202, 39);\n"
"border-radius: 10px;")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setObjectName("title")
        #Status
        self.status = QtWidgets.QLabel(self.frame)
        self.status.setGeometry(QtCore.QRect(10, 490, 521, 71))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.status.sizePolicy().hasHeightForWidth())
        self.status.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(16)
        font.setItalic(True)
        self.status.setFont(font)
        self.status.setStyleSheet("background-color: rgb(254, 200, 30);\n"
"border: rgb(255,255,255);\n"
"border-thick:10px;\n"
"border-radius: 10px;\n"
"")
        self.status.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.status.setObjectName("status")
        #Remove Button
        self.RemoveItem = QtWidgets.QPushButton(self.frame)
        self.RemoveItem.clicked.connect(self.RemoveItemclicked)
        self.RemoveItem.setGeometry(QtCore.QRect(650, 490, 101, 71))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(17)
        font.setItalic(True)
        self.RemoveItem.setFont(font)
        self.RemoveItem.setStyleSheet("background-color: rgb(254, 200, 30);\n"
"border:none;\n"
"border-radius: 10px;\n"
"")
        self.RemoveItem.setObjectName("RemoveItem")
        #Add Button
        self.AddItem = QtWidgets.QPushButton(self.frame)
        self.AddItem.clicked.connect(self.AddItemclicked)
        self.AddItem.setGeometry(QtCore.QRect(540, 490, 101, 71))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(17)
        font.setItalic(True)
        self.AddItem.setFont(font)
        self.AddItem.setStyleSheet("background-color: rgb(254, 200, 30);\n"
"border: none;\n"
"border-radius: 10px\n"
"\n"
"")
        self.AddItem.setObjectName("AddItem")

        self.calendarWidget = QtWidgets.QCalendarWidget(self.frame)
        self.calendarWidget.setGeometry(QtCore.QRect(420, 50, 331, 431))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(16)
        self.calendarWidget.setFont(font)
        self.calendarWidget.setStyleSheet("background-color: rgb(254, 166, 27);\n"
"alternate-background-color: rgba(50, 51, 51, 66);\n"
"color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(0, 0, 0, 255), stop:0.05 rgba(14, 8, 73, 255), stop:0.36 rgba(28, 17, 145, 255), stop:0.6 rgba(126, 14, 81, 255), stop:0.75 rgba(234, 11, 11, 255), stop:0.79 rgba(244, 70, 5, 255), stop:0.86 rgba(255, 136, 0, 255), stop:0.935 rgba(239, 236, 55, 255));\n"
"selection-color: rgba(18, 0, 255, 255);\n"
"selection-background-color: rgb(152, 131, 255);\n"
"border:none;\n"
"border-radius: 15px;")
        self.calendarWidget.setObjectName("calendarWidget")
        
        #SHOW TIME
        self.Time = QtWidgets.QLabel(self.frame)

        timer = QTimer(MainWindow)
        timer.timeout.connect(self.showTime)
        timer.start(1000)

        self.Time.setGeometry(QtCore.QRect(10, 10, 141, 31))
        font = QtGui.QFont()
        font.setFamily("Tiro Gurmukhi")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.Time.setFont(font)
        self.Time.setStyleSheet("background-color: rgb(254, 200, 30);\n"
"border-radius: 10px;")
        self.Time.setAlignment(QtCore.Qt.AlignCenter)
        self.Time.setObjectName("Time")

        # Items in Fridge
        self.tableWidget = QtWidgets.QTableWidget(self.frame)
        self.tableWidget.setGeometry(QtCore.QRect(10, 50, 401, 431))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.tableWidget.setFont(font)
        self.tableWidget.setStyleSheet("background-color: rgb(254, 200, 30);\n"
"selection-background-color: rgb(252, 68, 40);\n"
"alternate-background-color: rgba(254, 165, 32, 102);\n"
"border: none;\n"
"border-radius: 10px;")
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setColumnWidth(0,180)
        self.tableWidget.setColumnWidth(1,180)
        self.loaddata()
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(16)
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
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        item.setBackground(QtGui.QColor(253, 133, 35))
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.tableWidget.setHorizontalHeaderItem(1, item)


        self.Mode = QtWidgets.QLabel(self.frame)
        self.Mode.setGeometry(QtCore.QRect(610, 10, 141, 31))
        font = QtGui.QFont()
        font.setFamily("Tiro Gurmukhi")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.Mode.setFont(font)
        self.Mode.setStyleSheet("background-color: rgb(254, 200, 30);\n"
"border-radius: 10px;")
        self.Mode.setAlignment(QtCore.Qt.AlignCenter)
        self.Mode.setObjectName("Mode")
        self.horizontalLayout.addWidget(self.frame)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setTabOrder(self.AddItem, self.RemoveItem)
        MainWindow.setTabOrder(self.RemoveItem, self.calendarWidget)
        MainWindow.setTabOrder(self.calendarWidget, self.tableWidget)

    def showTime(self):
        currentTime = QTime.currentTime()
        displayText = currentTime.toString("hh : mm : ss")
        self.Time.setText(displayText)

    def AddItemclicked(self):
        self.Mode.setText("Add Item Mode")
        Add = True
        Remove = False

    def RemoveItemclicked(self):
        self.Mode.setText("Remove Item Mode")
        Add = False
        Remove = True

    def loaddata(self):
        data = []

        firebaseConfig = { 'apiKey': "AIzaSyA2NIKjW9kD31eeRnFDZhpW02q443AoIBA",
        'authDomain': "smart-fridge-94bff.firebaseapp.com",
        'databaseURL': "https://smart-fridge-94bff-default-rtdb.firebaseio.com",
        'projectId': "smart-fridge-94bff",
        'storageBucket': "smart-fridge-94bff.appspot.com",
        'messagingSenderId': "625536633101",
        'appId': "1:625536633101:web:d4951c5cc692fac0364844"
        }
        firebase = pyrebase.initialize_app(firebaseConfig)
        db = firebase.database()
        things = db.child("items").get()

        row = 0
        self.tableWidget.setRowCount(35)

        for things in things.each():
            val = things.val()
            self.tableWidget.setItem(row,0,QtWidgets.QTableWidgetItem(val['Item']))
            self.tableWidget.setItem(row,1,QtWidgets.QTableWidgetItem(val['Weight']))
            row = row+1
            
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.title.setText(_translate("MainWindow", "SMART FRIDGE"))

        timer = QTimer(MainWindow)
        self.status.setText(a)
        timer.start(1000)
        
        self.RemoveItem.setText(_translate("MainWindow", "REMOVE \n"
"ITEM"))
        self.AddItem.setText(_translate("MainWindow", "ADD \n"
"ITEM"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Item Name"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Weight"))
        self.Mode.setText(_translate("MainWindow", "Add Item Mode"))

if __name__ == "__main__":
    Add = True
    Remove = False
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    a = "Ready!"
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
