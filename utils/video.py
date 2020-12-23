from PyQt5.QtCore import *
import numpy as np
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import time
import cv2
import sys
import os
from optparse import OptionParser

canRestart = True
width = 1280
height = 720

def restart(twice):
    os.execl(sys.executable, sys.executable, *[sys.argv[0], "-t", twice])

class ProcessThread(QThread):
    image = np.ndarray(())
    process_slot = pyqtSignal()

    def __init__(self, parent=None):
        super(ProcessThread, self).__init__(parent)
        
    def readCap(self):
        global width, height
        # cap = cv2.VideoCapture(0)
        # cap.set(3, width)
        # cap.set(4, height)

        dev = 0
        gst_str = ('v4l2src device=/dev/video{} ! '
                   'video/x-raw, width=(int){}, height=(int){} ! '
                   'videoconvert ! appsink').format(dev, width, height)
        
        cap =  cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)


        while True:
            prev_time = time.time()     
            ret, frame_read = cap.read()             
            frame_rgb = cv2.cvtColor(frame_read, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (width, height),
                                       interpolation=cv2.INTER_LINEAR)
            ProcessThread.image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            print(1 / (time.time() - prev_time))
            self.process_slot.emit()
        cap.release()
        del cap

    def run(self):
        self.readCap()



class WinForm(QMainWindow):
  
    def __init__(self, parent=None):
        
        super(WinForm, self).__init__(parent)     
        self.setWindowTitle("Demo")  
        global width, height               
        self.resize(width, height)                      

        self.label1 = QLabel()                    
        self.label1.resize(width, height)               
        self.label1.setScaledContents(True)      

        layout = QGridLayout()                      
        layout.addWidget(self.label1, 0, 0, 1, 1)   

        main_frame = QWidget()                    
        main_frame.setLayout(layout)               
        self.setCentralWidget(main_frame)          
        self.initThread()                           

    def initThread(self):
        self.processThread = ProcessThread()        
        self.processThread.process_slot.connect(self.handleDisplay)
        self.processThread.start()                

    def handleDisplay(self):
        height, width, channel = ProcessThread.image.shape
        bytesPerLine = 3 * width
        self.qImg = QImage(ProcessThread.image.data, width, height, bytesPerLine,
                           QImage.Format_RGB888).rgbSwapped()
       
        self.label1.setPixmap(QPixmap.fromImage(self.qImg))


if __name__ == '__main__':
    parser = OptionParser(usage="usage:%prog [optinos] filepath")
    parser.add_option("-t", "--twice", type="int",
                      dest="twice", default=1, help="运行次数")
    options, _ = parser.parse_args()
    app = QApplication(sys.argv)
    win = WinForm()
    win.show()
    app.exec_()
    if canRestart:
        restart(str(options.twice + 1))