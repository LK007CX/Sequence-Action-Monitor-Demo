#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import os
import cv2
import sys
sys.path.append('/opt/nvidia/jetson-gpio/lib/python/')
sys.path.append('/opt/nvidia/jetson-gpio/lib/python/Jetson/GPIO')
import Jetson.GPIO as GPIO
import time
import darknet
import datetime
import numpy as np
import configparser
from collections import deque
import copy
import sqlite3
import qdarkstyle
from optparse import OptionParser
from threading import Timer
'''
2020年8月28日：尝试使用拖拽事件修改配置；已解决。
2020年8月28日：尝试解决相机短线问题（相机重连机制）;已解决
2020年8月28日：程序重启后，相机未释放，无法读取image；读取image的flag置位后延时1秒，确保相机得到释放

NO SECOND
2020年9月8日：可以运行，尝试加入保存视频
2020年9月9日：尝试加入超时机制
2020年9月10日：现场运行OK，设置界面问题
2020年9月14日：加入中英文对照
2020年11月23日：不加远程推送
'''

canRestart = True

def restart(twice):
    os.execl(sys.executable, sys.executable, *[sys.argv[0], "-t", twice])


class SaveVideoThread(QThread):
    """
    保存视频。
    """
    def __init__(self, parent=None):
        super(SaveVideoThread, self).__init__(parent)
        self.out = None

        self.save_str = ''

    def defineSaveWork(self, save_str, width, height):
        self.save_str = save_str
        print("开始保存视频\n视频将会存储至：\t\t\t" + self.save_str)
        # self.out = cv2.VideoWriter(self.save_str, cv2.VideoWriter_fourcc(*"I420"), 10.0, (width, height))
        # self.out = cv2.VideoWriter(self.save_str, cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (width, height))
        self.out = cv2.VideoWriter(self.save_str, cv2.VideoWriter_fourcc(*"DIVX"), 10.0, (width, height))
        # self.out = cv2.VideoWriter(self.save_str, cv2.VideoWriter_fourcc(*"DIVX"), 10.0, (640, 360))
    
    def endSaveWork(self, circle_result):
        if self.out != None:
            self.out.release()
            self.out = None
        try:
            if circle_result == "OK":
                os.remove(self.save_str)
                print("作业循环OK，已删除OK视频。\n")
            elif circle_result == 'NG':
                print("作业循环NG，已存储NG视频至：\t\t" + str(self.save_str) + "\n")
        except Exception as e:
            print(e)

    def writeFrame(self, image):
        if self.out != None:
            self.out.write(image)
            pass

class DeleteVideoThread(QThread):
    """
    删除指定文件夹里的前n个文件，按时间排序
    """
    def _init__(self, parent=None):
        super(DeleteVideoThread, self).__init_(parent)
        pass
    
    def sortFile(self, file_path):
        dir_list = os.listdir(file_path)
        if not dir_list:
            return
        else:
            # 注意，这里使用lambda表达式，将文件按照最后修改时间顺序升序排列
            # os.path.getmtime() 函数是获取文件最后修改时间
            # os.path.getctime() 函数是获取文件最后创建时间
            dir_list = sorted(dir_list,key=lambda x: os.path.getctime(os.path.join(file_path, x)))
            temp_list = []
            #print(dir_list)
            for val in dir_list:
               
                pwd = '/home/edit/ichia_ai_monitor'
                #print(pwd + '/' + 'video' + '/' + val)
                temp_list.append(pwd + '/' + 'video' + '/' + val)
            return temp_list
    
    def deleteFileByIndex(self, temp_list):
        try:
            length = len(temp_list)
            if length < 30:
                pass
            delete_list = temp_list[0 : (length-30)]
            for val in delete_list:
                if not os.path.exists(val):
                    break
                os.remove(val)
            print("已删除" + str(len(delete_list)) + "个视频")
        except Exception as e:
            print(e)
    
    def run(self):
        while True:
            #pwd = os.getcwd()
            pwd = '/home/edit/ichia_ai_monitor'
            temp_list = self.sortFile(pwd + '/video')
            #print(temp_list)
            self.deleteFileByIndex(temp_list)
            time.sleep(60)

class Action:

    __slots__ = 'confirm_label', 'confirm_num', 'label_list', 'time_list', 'confirm_time', 'done', 'index', 'allow_close', 'timer'

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.label_list = []
        self.time_list = []
        self.done = False
    
    def allow_rotate(self, label):
        if (len(self.label_list) == self.confirm_num) and (self.done != True):
            if self.confirm_time == 0:
                self.done = True
                return True
            if self.confirm_num == 1:
                self.done = True
                return True
            if (len(self.time_list)>1) and (self.time_list[-1] - self.time_list[0]).seconds > self.confirm_time:
                self.done = True
                return True
        if (label == self.confirm_label):
            if(len(self.label_list) < self.confirm_num):
                self.label_list.append(label)
            self.time_list.append(datetime.datetime.now())
        return False
    
    def __str__(self):
        return "动作\t" + str(self.index) + "\t" + str(self.confirm_label)
    

class ProcessThread(QThread):
    """
    Do yolo detect.
    By the sequence of actions.
    """
    image_Signal = pyqtSignal(np.ndarray, float)
    load_widget_action_Signal = pyqtSignal(list)
    partial_result_Signal = pyqtSignal(list)
    result_Signal = pyqtSignal(int, int, int, float, str, str)
    history_image_Signal = pyqtSignal()
    error_Signal = pyqtSignal(str)    # error signal, by error ID
    status_Signal = pyqtSignal()

    # 保存视频用的信号
    define_save_work_Signal = pyqtSignal(str, int, int)
    end_save_work_Signal = pyqtSignal(str)
    write_frame_Signal = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super(ProcessThread, self).__init__(parent)
        self.image = np.ndarray(())
        self.netMain = None
        self.metaMain = None
        self.altNames = None
        self.configPath = None
        self.weightPath = None
        self.metaPath = None
        self.videoPath = None
        self.videoWidth = None
        self.videoHeight = None
        self.thresh = None
        self.fps = 0
        self.output_pin = 16

        self.actionQueue = CircleQueue()
        self.current_action = None
        self.action_name = []
        self.results = ['', '', '', '', '', '', '']
        self.image_queue = deque([], maxlen=4)

        self.ok = 0
        self.ng = 0
        self.total = 0
        self.percent = 0

        self.log = ''

        self.currentDatetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cap = None
        self.canReadCamera = True

        self.stop_flag = ''
        self.stop_action = None
        self.allow_close = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.time_out)
        
    def GPIO_INI(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.output_pin, GPIO.OUT, initial=GPIO.HIGH)
    
    def myout(self):
        GPIO.output(self.output_pin, GPIO.LOW)
        time.sleep(0.05)
        GPIO.output(self.output_pin, GPIO.HIGH)

    def load_config(self):
        config = configparser.ConfigParser()
        config.read('/home/edit/ichia_ai_monitor/appsettings.ini')
        self.configPath = str(config['Model']['CFG'])
        self.weightPath = str(config['Model']['Weights'])
        self.metaPath = str(config['Model']['Data'])
        self.videoPath = int(config['Video']['VideoPath'])
        self.videoWidth = int(config['Video']['VideoWidth'])
        self.videoHeight = int(config['Video']['VideoHeight'])
        self.thresh = float(config['Model']['Thresh'])
        if not config.has_section('Logic'):
            config.add_section('Logic')

        index = 0
        for key in config['Logic']:
            if config['Logic'][key] == 'Place_fpc':
                self.actionQueue.enqueue(Action(confirm_label='Place_fpc', confirm_num=1, confirm_time=0, index=index))
                self.action_name.append('放片')
            if config['Logic'][key] == 'Jig_front':
                self.actionQueue.enqueue(Action(confirm_label='Jig_front', confirm_num=1, confirm_time=0, index=index))
                self.action_name.append('正翻')
            if config['Logic'][key] == 'Jig_back':
                self.actionQueue.enqueue(Action(confirm_label='Jig_back', confirm_num=1, confirm_time=0, index=index))
                self.action_name.append('反翻')
            if config['Logic'][key] == 'Inspection':
                self.actionQueue.enqueue(Action(confirm_label='Inspection', confirm_num=1, confirm_time=3, index=index))
                self.action_name.append('检测')
            if config['Logic'][key] == 'Receive_fpc':
                self.actionQueue.enqueue(Action(confirm_label='Receive_fpc', confirm_num=1, confirm_time=0, index=index))
                self.action_name.append('收片')
            # self.actionQueue.enqueue(Action(confirm_label=str(config['Logic'][key]), confirm_num=3, confirm_time=0, index=index))
            # self.action_name.append(str(config['Logic'][key]))
            index += 1
        self.current_action = copy.deepcopy(self.actionQueue.first())
        for i in range(len(self.actionQueue)-1):
            self.actionQueue.rotate()
        self.stop_action = None
        self.stop_action = copy.deepcopy(self.actionQueue.first())
        self.actionQueue.rotate()

    def time_out(self):
        print("操作已超时。。。")
        for i in range(len(self.actionQueue)):
            if self.results[i] == '':
                self.results[i] = "NG"
        self.partial_result_Signal.emit(self.results)
        self.circleEndWork(self.currentDatetime, self.results)
        self.currentDatetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.stop_action.label_list = []
        self.stop_action.time_list = []
        self.stop_action.done = False
        self.allow_close = False
        for i in range(len(self.actionQueue)):
            self.actionQueue.rotate()
            if self.actionQueue.first().index == 0:
                self.current_action = copy.deepcopy(self.actionQueue.first())
                break

    def convertBack(self, x, y, w, h):
        xmin = int(round(x - (w / 2)))
        xmax = int(round(x + (w / 2)))
        ymin = int(round(y - (h / 2)))
        ymax = int(round(y + (h / 2)))
        return xmin, ymin, xmax, ymax

    def partial_result(self, index, result):
        self.results[index] = result
        # emit a singal that will display the state of partial result
        self.partial_result_Signal.emit(self.results)

    def normalWork(self, detections, img):
        for detection in detections:
            if detection[0] == bytes(str(self.current_action.confirm_label), encoding="utf-8"):
                x, y, w, h = detection[2][0],\
                    detection[2][1],\
                    detection[2][2],\
                    detection[2][3]
                xmin, ymin, xmax, ymax = self.convertBack(
                    float(x), float(y), float(w), float(h))
                pt1 = (xmin, ymin)
                pt2 = (xmax, ymax)
                cv2.rectangle(img, pt1, pt2, (255, 0, 0), 2)
                cv2.rectangle(img, pt1, (pt1[0] + 150, pt1[1] + 20), (255, 0, 0), -1)
                cv2.putText(img,
                            detection[0].decode() +
                            " [" + str(round(detection[1] * 100, 2)) + "]",
                            (pt1[0] + 5, pt1[1] + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            [255, 255, 255], 1)
                
            if self.current_action.allow_rotate(detection[0].decode()):
                if len(self.current_action.time_list) >= 2:
                    pass
                self.partial_result(self.current_action.index, 'OK')
                history_image = copy.deepcopy(img)
                cv2.putText(history_image,
                            self.current_action.confirm_label,
                            (0, 125), cv2.FONT_HERSHEY_SIMPLEX, 5,
                            [255, 0, 0], 10)
                self.image_queue.append(copy.deepcopy(history_image))
                self.history_image_Signal.emit()
                if self.current_action.index == (len(self.actionQueue)-1):
                    self.circleEndWork(self.currentDatetime, self.results)
                    self.currentDatetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.actionQueue.rotate()
                self.current_action = copy.deepcopy(self.actionQueue.first())
            
                if self.current_action.index == 1:
                    self.allow_close = True
                    self.status_Signal.emit()
                    
                if self.current_action.index == (len(self.actionQueue)-1):
                    self.allow_close = False

            # 强制结束
            # 非正常结束
            if self.current_action.index != (len(self.actionQueue)-1): # 不是正常结束的结束便签检测时机
               
                if detection[0] == bytes(str(self.stop_action.confirm_label), encoding="utf-8"):
                    x, y, w, h = detection[2][0],\
                        detection[2][1],\
                        detection[2][2],\
                        detection[2][3]
                    xmin, ymin, xmax, ymax = self.convertBack(
                        float(x), float(y), float(w), float(h))
                    pt1 = (xmin, ymin)
                    pt2 = (xmax, ymax)
                    cv2.rectangle(img, pt1, pt2, (255, 0, 0), 2)
                    cv2.rectangle(img, pt1, (pt1[0] + 150, pt1[1] + 20), (255, 0, 0), -1)
                    cv2.putText(img,
                                detection[0].decode() +
                                " [" + str(round(detection[1] * 100, 2)) + "]",
                                (pt1[0] + 5, pt1[1] + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                [255, 255, 255], 1)
                if self.stop_action.allow_rotate(detection[0].decode()):
                    if not self.allow_close:
                        self.stop_action.label_list = []
                        self.stop_action.time_list = []
                        self.stop_action.done = False
                        self.allow_close = False
                        return
                    for i in range(len(self.actionQueue)):
                        if self.results[i] == '':
                            self.results[i] = "NG"
                    self.partial_result_Signal.emit(self.results)
                    history_image = copy.deepcopy(img)
                    cv2.putText(history_image,
                                "force close",
                                (0, 125), cv2.FONT_HERSHEY_SIMPLEX, 5,
                                [255, 0, 0], 10)
                    self.image_queue.append(copy.deepcopy(history_image))
                    self.history_image_Signal.emit()
                    self.circleEndWork(self.currentDatetime, self.results)
                    self.currentDatetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    self.stop_action.label_list = []
                    self.stop_action.time_list = []
                    self.stop_action.done = False
                    self.allow_close = False
                    for i in range(len(self.actionQueue)):
                        self.actionQueue.rotate()
                        if self.actionQueue.first().index == 0:
                            self.current_action = copy.deepcopy(self.actionQueue.first())
                            break
            break

    def circleEndWork(self, currentDatatime, result):

        circle_result = "OK"
        for val in result:
            if val == "NG":
                circle_result = 'NG'
                self.myout()
                break
        if circle_result == "OK":
            self.ok += 1
        else:
            self.ng += 1
        self.total = self.ok + self.ng
        self.percent = self.ok / self.total
        self.insertIntoDB(currentDatatime, result, circle_result)
        self.result_Signal.emit(self.ok, self.ng, self.total, self.percent, currentDatatime, circle_result)
        for i in range(len(self.results)):
            self.results[i] = ''
        self.end_save_work_Signal.emit(circle_result)
        self.currentDatetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.define_save_work_Signal.emit('/home/edit/ichia_ai_monitor/video/' + self.currentDatetime + ".avi", self.videoWidth, self.videoHeight)
        
    def insertIntoDB(self, currentDatatime, result, circle_result):
        currentDate = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect("/home/edit/ichia_ai_monitor/db/" + currentDate + ".db")
        c = conn.cursor()
        c.execute('''create table if not exists result(
            id integer primary key autoincrement,
            time text,
            action1 text,
            action2 text,
            action3 text,
            action4 text,
            action5 text,
            action6 text,
            action7 text,
            circleresult text
        )
        ''')
        sqlstr = []
        sqlstr.append(currentDatatime)
        sqlstr.extend(result)
        sqlstr.append(circle_result)
        temp = tuple(sqlstr)
        c.execute('insert into result values (null, ?, ?, ?, ?, ?, ?, ?, ?, ?)',temp)
        conn.commit()
        c.close()
        conn.close()
    
    def cvDrawBoxes(self, detections, img):
        self.normalWork(detections, img)
        return img

    def YOLO(self):
        self.load_config()
        self.GPIO_INI()
        self.load_widget_action_Signal.emit(self.action_name)
        if not os.path.exists(self.configPath):
            raise ValueError("Invalid config path `" +
                            os.path.abspath(self.configPath)+"`")
        if not os.path.exists(self.weightPath):
            raise ValueError("Invalid weight path `" +
                            os.path.abspath(self.weightPath)+"`")
        if not os.path.exists(self.metaPath):
            raise ValueError("Invalid data file path `" +
                            os.path.abspath(self.metaPath)+"`")
        if self.netMain is None:
            self.netMain = darknet.load_net_custom(self.configPath.encode(
                "ascii"), self.weightPath.encode("ascii"), 0, 1)  # batch size = 1
        if self.metaMain is None:
            self.metaMain = darknet.load_meta(self.metaPath.encode("ascii"))
        if self.altNames is None:
            try:
                with open(self.metaPath) as metaFH:
                    metaContents = metaFH.read()
                    import re
                    match = re.search("names *= *(.*)$", metaContents,
                                    re.IGNORECASE | re.MULTILINE)
                    if match:
                        result = match.group(1)
                    else:
                        result = None
                    try:
                        if os.path.exists(result):
                            with open(result) as namesFH:
                                namesList = namesFH.read().strip().split("\n")
                                self.altNames = [x.strip() for x in namesList]
                    except TypeError:
                        pass
            except Exception:
                pass
        self.cap = cv2.VideoCapture(self.videoPath)
        #self.cap = cv2.VideoCapture("c1.avi")
        # self.cap = cv2.VideoCapture("c1_10.avi")

        self.cap.set(3, self.videoWidth)
        self.cap.set(4, self.videoHeight)
        #self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('D', 'I', 'V', 'X'))
        print("Starting the YOLO loop...")
        # Create an image we reuse for each detect
        darknet_image = darknet.make_image(self.videoWidth, self.videoHeight, 3)
        self.define_save_work_Signal.emit('/home/edit/ichia_ai_monitor/video/' + self.currentDatetime + ".avi", self.videoWidth, self.videoHeight)
        while True:
            if not self.canReadCamera:
                break
            prev_time = time.time()
            ret, frame_read = self.cap.read()
            if not ret:
                self.cap.release()
                self.cap = cv2.VideoCapture(self.videoPath)
                self.cap.set(3, self.videoWidth)
                self.cap.set(4, self.videoHeight)
                #self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('D', 'I', 'V', 'X'))
            else:
                frame_rgb = cv2.cvtColor(frame_read, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb,
                                        (self.videoWidth,
                                        self.videoHeight),
                                        interpolation=cv2.INTER_LINEAR)
                darknet.copy_image_from_bytes(darknet_image,frame_resized.tobytes())
                detections = darknet.detect_image(self.netMain, self.metaMain, darknet_image, thresh=self.thresh)
                image = self.cvDrawBoxes(detections, frame_resized)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.write_frame_Signal.emit(image)
                self.fps = round(1/(time.time()-prev_time), 2)
                self.image_Signal.emit(image, self.fps)
        self.cap.release()
        

    def run(self):
        try:
            self.YOLO()
        except Exception as e:
            print(e)
            self.error_Signal.emit(str(e))
        finally:
            GPIO.cleanup()
        


class InformationWidget(QLabel):
    def __init__(self, parent=None):
        super(InformationWidget, self).__init__(parent)

        self.numLabel = QLabel("0", objectName="numLabel")
        self.numLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.numLabel.setScaledContents(True)
        self.numLabel.setStyleSheet('''
                            color: rgb(255, 255, 255);
                            font-size: 45px;
                            font-weight: bold;
                            font-family: Arial''')
        
        self.descLabel = QLabel("描述", objectName="descLabel")
        self.descLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.descLabel.setScaledContents(True)
        self.descLabel.setStyleSheet('''
                            color:rgb(255, 255, 255);
                            font-size:15px;
                            font-weight:normal;
                            font-family:Arial''')

        layout = QVBoxLayout()
        layout.addWidget(self.numLabel)
        layout.addWidget(self.descLabel)
        self.setLayout(layout)

    def set_backgroundcolor(self, color):
        self.setStyleSheet('''QLabel {background-color: ''' + color + '''; border-radius: 10px;}''')


class PartialActionWidget(QLabel):
    def __init__(self, parent=None, index='0', actionName=''):
        super(PartialActionWidget, self).__init__(parent)

        self.actionNameLabel = QLabel(actionName, objectName="actionNameLabel")
        self.actionNameLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.actionNameLabel.setScaledContents(True)
        self.actionNameLabel.setStyleSheet('''
                                            color: rgb(255, 255, 255);
                                            font-size: 12px;
                                            font-family: Arial''')
        layout = QVBoxLayout()
        layout.addWidget(self.actionNameLabel)
        self.setLayout(layout)

    def set_backgroundcolor(self, color):
        self.setStyleSheet('''QLabel {background-color: ''' + color + '''; border-radius: 10px;}''')


class HistoryTableWidget(QTableWidget):
    def __init__(self, parent=None, rowCount=20, columnCount=2):
        super(HistoryTableWidget, self).__init__(parent)
        self.setRowCount(rowCount)
        self.setColumnCount(columnCount)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 表格只读
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 设置表格整行选中
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.horizontalHeader().setVisible(False)  # 隐藏水平表头
        self.setHeight()
        #self.setShowGrid(False)
        self.setStyleSheet('''text-align: center;
                            font-family: Microsoft YaHei;
                            font-size:14px;''')

    def appendHistory(self, column, startTime, result=None):
        item0 = QTableWidgetItem(startTime)
        item0.setTextAlignment(Qt.AlignCenter)
        item1 = QTableWidgetItem(result)
        item1.setTextAlignment(Qt.AlignCenter)
        self.setItem(column, 0, item0)
        self.setItem(column, 1, item1)

    def setHeight(self):
        for i in range(self.rowCount()):
            self.setRowHeight(i, 29.5)


class DataGrid(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("查询")
        self.resize(750, 500)
        self.initUI()
        self.totalList = []

    def initUI(self):
        # 操作布局
        operatorLayout = QHBoxLayout()
        self.dateLabel = QLabel("选择日期")
        self.dateLabel.setFixedWidth(120)
        self.dateEdit = QDateEdit(QDate.currentDate())
        self.dateEdit.setDisplayFormat("yyyy-MM-dd")
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setMinimumDate(QDate.currentDate().addDays(-365))
        self.dateEdit.setMaximumDate(QDate.currentDate().addDays(0))
        self.queryDataButton = QPushButton("查询数据")
        self.clearButton = QPushButton("清空")
	
        self.queryDataButton.clicked.connect(self.queryDataTrigger)
        self.queryDataButton.setEnabled(True)
        self.clearButton.clicked.connect(self.clearTrigger)
        self.clearButton.setEnabled(False)
        operatorLayout.addWidget(self.dateLabel)
        operatorLayout.addWidget(self.dateEdit)
        operatorLayout.addWidget(self.queryDataButton)
        operatorLayout.addWidget(self.clearButton)
        operatorLayout.addWidget( QSplitter())
        # 状态布局
        statusLayout =  QHBoxLayout()
        self.totalRecordLabel =  QLabel()
        self.totalRecordLabel.setFixedWidth(70)
        statusLayout.addWidget(QSplitter())
        statusLayout.addWidget(self.totalRecordLabel)
        # 设置表格属性
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(9)
        self.tableWidget.setHorizontalHeaderLabels(["开始时间", "动作1", "动作2", "动作3", "动作4", "动作5", "动作6", "动作7", "判断结果"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 创建界面
        mainLayout = QVBoxLayout(self)
        mainLayout.addLayout(operatorLayout)
        mainLayout.addWidget(self.tableWidget)
        mainLayout.addLayout(statusLayout)
        self.setLayout(mainLayout)

    def queryDataTrigger(self):
        try:
            queryDate = self.dateEdit.date().toString("yyyy-MM-dd")
            conn = sqlite3.connect("/home/edit/ichia_ai_monitor/db/" + queryDate + ".db")
            c = conn.cursor()
            c.execute('select * from result')
            for col in (c.description):
                #print(col[0], end='\t')
                pass
            while 1:
                row = c.fetchone()
                if not row:
                    break
                templist = [row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]]
                #print(str(row[0]) + '\t' + row[1] + '\t' + row[2] + '\t' + row[3]+ '\t' + row[4]+ '\t' + row[6] + '\t' + row[7] + '\t' + row[8] + '\t' + row[9])
                self.totalList.append(templist)
            c.close()
            conn.close()
            
            self.tableWidget.setRowCount(len(self.totalList))
            for i in range(0, len(self.totalList)):
                for j in range(0, 9):
                    item = QTableWidgetItem(self.totalList[i][j])
                    self.tableWidget.setItem(i, j, item)
          
            self.totalRecordLabel.setText("总数: " + str(len(self.totalList)))
            self.queryDataButton.setEnabled(False)
            self.clearButton.setEnabled(True)
        except Exception as e:
            print(e)
            QMessageBox.information(self, "Error", "没有相关数据", QMessageBox.Yes, QMessageBox.Yes)

    def clearTrigger(self):
        self.totalList.clear()
        for i in range(self.tableWidget.rowCount()):
            self.tableWidget.removeRow(0)
        self.queryDataButton.setEnabled(True)
        self.clearButton.setEnabled(False)
        self.totalRecordLabel.setText("")


class SettingsGrid(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("设置")
        self.resize(750, 650)
        self.nameList = []
        self.dataPath = ''

        self.modelLabel = QLabel("模型文件选择")
        self.modelLabel.setMinimumWidth(150)
        self.modelLabel.setMaximumWidth(150)
        self.modelLineEdit = QLineEdit()
        self.modelLineEdit.setReadOnly(True)
        self.modelToolButton = QToolButton()
        self.modelToolButton.setText('...')
        self.modelToolButton.setStyleSheet('''border-color:red;''')
        self.modelToolButton.clicked.connect(self.modelTrigger)
        modelLayout = QHBoxLayout()
        modelLayout.addWidget(self.modelLabel)
        modelLayout.addWidget(self.modelLineEdit)
        modelLayout.addWidget(self.modelToolButton)

        self.cfgLabel = QLabel("配置文件选择")
        self.cfgLabel.setMinimumWidth(150)
        self.cfgLabel.setMaximumWidth(150)
        self.cfgLineEdit = QLineEdit()
        self.cfgLineEdit.setReadOnly(True)
        self.cfgToolButton = QToolButton()
        self.cfgToolButton.setText('...')
        self.cfgToolButton.setStyleSheet('''border-color:red;''')
        self.cfgToolButton.clicked.connect(self.cfgTrigger)
        cfgLayout = QHBoxLayout()
        cfgLayout.addWidget(self.cfgLabel)
        cfgLayout.addWidget(self.cfgLineEdit)
        cfgLayout.addWidget(self.cfgToolButton)
        
        self.dataLabel = QLabel("数据文件选择")
        self.dataLabel.setMinimumWidth(150)
        self.dataLabel.setMaximumWidth(150)
        self.dataLineEdit = QLineEdit()
        self.dataLineEdit.setReadOnly(True)
        self.dataToolButton = QToolButton()
        self.dataToolButton.setText('...')
        self.dataToolButton.setStyleSheet('''border-color:red;''')
        self.dataToolButton.clicked.connect(self.dataTrigger)
        dataLayout = QHBoxLayout()
        dataLayout.addWidget(self.dataLabel)
        dataLayout.addWidget(self.dataLineEdit)
        dataLayout.addWidget(self.dataToolButton)

        self.threshLabel = QLabel("调节置信度")
        self.threshLabel.setMinimumWidth(150)
        self.threshLabel.setMaximumWidth(150)
        self.threshSlider = QSlider()
        self.threshSlider.setOrientation(Qt.Horizontal)
        self.threshSlider.setMinimum(0)
        self.threshSlider.setMaximum(100)
        self.threshSlider.valueChanged.connect(self.threshTrigger)
        self.threshToolButton = QToolButton()
        self.threshToolButton.setText("%")

        threshLayout = QHBoxLayout()
        threshLayout.addWidget(self.threshLabel)
        threshLayout.addWidget(self.threshSlider)
        threshLayout.addWidget(self.threshToolButton)

        self.nameLabel = QLabel("检测标签列表")
        self.nameLabel.setMinimumWidth(150)
        self.nameLabel.setMaximumWidth(150)
        self.nameLineEdit = QLineEdit()
        self.nameLineEdit.setReadOnly(True)

        nameLayout = QHBoxLayout()
        nameLayout.addWidget(self.nameLabel)
        nameLayout.addWidget(self.nameLineEdit)

        self.splitWidget = QLabel()
        self.splitWidget.setMaximumHeight(2)
        self.splitWidget.setStyleSheet('''background-color: salmon;''')

        self.actionLabel = QLabel("检测动作顺序配置")
        self.tipsLabel = QLabel("""        Step1：拖拽左侧方块至右侧区域；
        Step2：点击\"保存动作设置\"以保存配置；
        注意：最多配置7个动作；相关设置将在应用程序重启后生效。""")

        self.chineseAndEnglishLabel = QLabel("""中英文对照\nPlace_fpc：放片\t\tJig_front：正翻\t\tJig_back：反翻\nInspection：检查\t\tReceive_fpc：收片\tPen：笔""")       
        self.dragListWidget = DragListWidget()
        self.dropListWidget = DropListWidget()
        dragDropLayout = QHBoxLayout()
        dragDropLayout.addWidget(self.dragListWidget)
        dragDropLayout.addWidget(self.dropListWidget)
        
        self.resetActionPushButton = QPushButton("重置动作设置")
        self.resetActionPushButton.clicked.connect(self.dropListWidget.clearItem)
        self.saveActionPushButton = QPushButton("保存动作设置")
        self.saveActionPushButton.clicked.connect(self.dropListWidget.saveActions)
        operationLayout = QHBoxLayout()
        operationLayout.addWidget(self.resetActionPushButton)
        operationLayout.addWidget(QSplitter())
        operationLayout.addWidget(self.saveActionPushButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(modelLayout)
        mainLayout.addLayout(cfgLayout)
        mainLayout.addLayout(dataLayout)
        mainLayout.addLayout(threshLayout)
        mainLayout.addLayout(nameLayout)
        mainLayout.addWidget(self.splitWidget)
        mainLayout.addWidget(self.actionLabel)
        mainLayout.addWidget(self.tipsLabel)
        mainLayout.addWidget(self.chineseAndEnglishLabel)
        mainLayout.addLayout(dragDropLayout)
        mainLayout.addLayout(operationLayout)
        self.setLayout(mainLayout)
        self.load_config()
    
    def load_config(self):
        config = configparser.ConfigParser()
        config.read('/home/edit/ichia_ai_monitor/appsettings.ini')
        self.modelLineEdit.setText(str(config['Model']['Weights']).split('/')[-1]) 
        self.cfgLineEdit.setText(str(config['Model']['CFG']).split('/')[-1]) 
        self.dataLineEdit.setText(str(config['Model']['data']).split('/')[-1])
        self.dataPath = str(config['Model']['data'])
        temp = int(float(config['Model']['Thresh']) * 100)
        self.threshSlider.setValue(int(float(config['Model']['Thresh']) * 100))
        self.threshToolButton.setText(str(int(float(config['Model']['Thresh']) * 100)) + "%")
        self.nameTrigger()
        self.dragListWidget.initItems(self.nameList)

    def nameTrigger(self):
        try:
            with open(self.dataPath) as metaFH:
                metaContents = metaFH.read()
                import re
                match = re.search("names *= *(.*)$", metaContents,
                                    re.IGNORECASE | re.MULTILINE)
                if match:
                    result = match.group(1)
                else:
                    result = None
                try:
                    if os.path.exists(result):
                        with open(result) as namesFH:
                            namesList = namesFH.read().strip().split("\n")
                            self.nameList = [x.strip() for x in namesList]
                            temp = ''
                            for val in self.nameList:
                                temp += val
                                temp += '、'
                            temp = temp[0:-1]
                            self.nameLineEdit.setText(temp)
                except TypeError:
                    pass
        except Exception as e:
            print(e)

    def modelTrigger(self):
        openfile_name = QFileDialog.getOpenFileName(self, '选择模型文件', '/home/edit/ichia_ai_monitor/', 'Weights file(*.weights)')
        if openfile_name[0] != '':
            self.modifyTrigger("Model", "weights", str(openfile_name[0]))
            self.modelLineEdit.setText(str(openfile_name[0]).split('/')[-1]) 
    
    def modifyTrigger(self, str1, str2, str3):
        config = configparser.ConfigParser()
        config.read('/home/edit/ichia_ai_monitor/appsettings.ini')
        config.set(str1, str2, str3)
        with open('/home/edit/ichia_ai_monitor/appsettings.ini', 'w') as f:
            config.write(f)
    
    def cfgTrigger(self):
        openfile_name = QFileDialog.getOpenFileName(self, '选择配置文件', '/home/edit/ichia_ai_monitor/', 'cfg file(*.cfg)')
        if openfile_name[0] != '':
            self.modifyTrigger("Model", "cfg", str(openfile_name[0]))
            self.cfgLineEdit.setText(str(openfile_name[0]).split('/')[-1]) 
    
    def dataTrigger(self):
        openfile_name = QFileDialog.getOpenFileName(self, '选择data文件', '/home/edit/ichia_ai_monitor/', 'cfg file(*.data)')
        if openfile_name[0] != '':
            
            self.modifyTrigger("Model", "data", str(openfile_name[0]))
            self.dataLineEdit.setText(str(openfile_name[0]).split('/')[-1])
            self.dataPath = openfile_name[0]
            self.nameTrigger()
            self.dragListWidget.initItems(self.nameList)
            try:
                old_data = ''
                with open(openfile_name[0], 'r') as f:
                    for line in f:
                        key = line.split(' ')[0]
                        if key == 'names':
                            temp = line.split(' ')[2].split('/')[-1]
                            parentPath = os.path.dirname(openfile_name[0])
                            line = 'names = ' + parentPath + '/' + temp
                        old_data += line
                
                with open(openfile_name[0], 'w') as f:
                    f.write(old_data)
            except Exception as e:
                print(e)
            
    def threshTrigger(self, val):
        self.threshToolButton.setText(str(val) + "%")
        self.modifyTrigger("Model", "thresh", str(val / 100))


class DropListWidget(QListWidget):
    # 可以拖进来的QListWidget

    def __init__(self, *args, **kwargs):
        super(DropListWidget, self).__init__(*args, **kwargs)
        #self.resize(400, 400)
        self.setAcceptDrops(True)
        # 设置从左到右、自动换行、依次排列
        # self.setFlow(self.LeftToRight)
        # self.setWrapping(True)
        self.setResizeMode(self.Adjust)
        # item的间隔
        self.setSpacing(5)
        self.actionList = []
        self.loadItem()

    def loadItem(self):
        try:
            config = configparser.ConfigParser()
            config.read('/home/edit/ichia_ai_monitor/appsettings.ini')
            r = config.items('Logic')
            action = [val[1] for val in r]
            for val in action:
                self.makeItem(QSize(100, 30), val)
        except Exception as e:
            print(e)

    def makeItem(self, size, cname):
        if self.count() == 7:
            return
        item = QListWidgetItem(self)
        item.setData(Qt.UserRole + 1, cname)  # 把数据放进自定义的data里面
        item.setSizeHint(size)
        label = QLabel(self)  # 自定义控件
        label.setMargin(2)  # 往内缩进2
        label.resize(size)
        # pixmap = QPixmap(size.scaled(200, 50, Qt.IgnoreAspectRatio))  # 调整尺寸
        # pixmap.fill(QColor(cname))
        # label.setPixmap(pixmap)
        label.setText("动作" + str(self.count()) + "          " + cname)
        label.setStyleSheet('''background-color: orangered; color: white;border-radius: 5px;
        ''')
        self.setItemWidget(item, label)
        self.actionList.append(cname)

    def dragEnterEvent(self, event):
        mimeData = event.mimeData()
        if not mimeData.property('myItems'):
            event.ignore()
        else:
            event.acceptProposedAction()

    def dropEvent(self, event):
        # 获取拖放的items
        items = event.mimeData().property('myItems')
        event.accept()
        for item in items:
            # 取出item里的data并生成item
            self.makeItem(QSize(100, 30), item.data(Qt.UserRole + 1))
    
    def clearItem(self):
        # 情况所有Item
        for _ in range(self.count()):
            item = self.takeItem(0)
            self.removeItemWidget(item)
            del item
        self.actionList.clear()

        config = configparser.ConfigParser()
        config.read('test14.ini')
        config.remove_section('Logic')
        config.add_section('Logic')
        with open('test14.ini', 'w') as f:
            config.write(f)

    def saveActions(self):
        if len(self.actionList) == 0:
            return
        config = configparser.ConfigParser()
        config.read('/home/edit/ichia_ai_monitor/appsettings.ini')
        config.remove_section('Logic')
        config.add_section('Logic')
        for i in range(len(self.actionList)):
            config.set('Logic', 'action' + str(i), self.actionList[i] )
        with open('/home/edit/ichia_ai_monitor/appsettings.ini', 'w') as f:
            config.write(f)
        

class DragListWidget(QListWidget):
    # 可以往外拖的QListWidget

    def __init__(self, *args, **kwargs):
        super(DragListWidget, self).__init__(*args, **kwargs)
        # self.resize(400, 400)
        # 隐藏横向滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 不能编辑
        self.setEditTriggers(self.NoEditTriggers)
        # 开启拖功能
        self.setDragEnabled(True)
        # 只能往外拖
        self.setDragDropMode(self.DragOnly)
        # 忽略放
        self.setDefaultDropAction(Qt.IgnoreAction)
        # ****重要的一句（作用是可以单选，多选。Ctrl、Shift多选，可从空白位置框选）****
        # ****不能用ExtendedSelection,因为它可以在选中item后继续框选会和拖拽冲突****
        self.setSelectionMode(self.ContiguousSelection)
        # 设置从左到右、自动换行、依次排列
        self.setFlow(self.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(self.Adjust)
        # item的间隔
        self.setSpacing(5)
        # 橡皮筋(用于框选效果)
        self._rubberPos = None
        self._rubberBand = QRubberBand(QRubberBand.Rectangle, self)

        # self.initItems()

    # 实现拖拽的时候预览效果图
    # 这里演示拼接所有的item截图(也可以自己写算法实现堆叠效果)
    def startDrag(self, supportedActions):
        items = self.selectedItems()
        drag = QDrag(self)
        mimeData = self.mimeData(items)
        # 由于QMimeData只能设置image、urls、str、bytes等等不方便
        # 这里添加一个额外的属性直接把item放进去,后面可以根据item取出数据
        mimeData.setProperty('myItems', items)
        drag.setMimeData(mimeData)
        pixmap = QPixmap(self.viewport().visibleRegion().boundingRect().size())
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        for item in items:
            rect = self.visualRect(self.indexFromItem(item))
            painter.drawPixmap(rect, self.viewport().grab(rect))
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.viewport().mapFromGlobal(QCursor.pos()))
        drag.exec_(supportedActions)

    def mousePressEvent(self, event):
        # 列表框点击事件,用于设置框选工具的开始位置 q
        super(DragListWidget, self).mousePressEvent(event)
        if event.buttons() != Qt.LeftButton or self.itemAt(event.pos()):
            return
        self._rubberPos = event.pos()
        self._rubberBand.setGeometry(QRect(self._rubberPos, QSize()))
        self._rubberBand.show()

    def mouseReleaseEvent(self, event):
        # 列表框点击释放事件,用于隐藏框选工具
        super(DragListWidget, self).mouseReleaseEvent(event)
        self._rubberPos = None
        self._rubberBand.hide()

    def mouseMoveEvent(self, event):
        # 列表框鼠标移动事件,用于设置框选工具的矩形范围
        super(DragListWidget, self).mouseMoveEvent(event)
        if self._rubberPos:
            pos = event.pos()
            lx, ly = self._rubberPos.x(), self._rubberPos.y()
            rx, ry = pos.x(), pos.y()
            size = QSize(abs(rx - lx), abs(ry - ly))
            self._rubberBand.setGeometry(
                QRect(QPoint(min(lx, rx), min(ly, ry)), size))

    def makeItem(self, size, cname):
        
        item = QListWidgetItem(self)
        item.setData(Qt.UserRole + 1, cname)  # 把颜色放进自定义的data里面
        item.setSizeHint(size)
        label = QLabel(self)  # 自定义控件
        label.setMargin(2)  # 往内缩进2
        label.resize(size)
        # pixmap = QPixmap(size.scaled(100, 100, Qt.IgnoreAspectRatio))  # 调整尺寸
        # pixmap.fill(QColor(cname))
        label.setText(cname)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet('''background-color: brown; color: white;border-radius: 5px;
        ''')
        self.setItemWidget(item, label)

    def initItems(self, name_list):
        self.clearItem()
        size = QSize(100, 30)
        for cname in name_list:
            self.makeItem(size, cname)
    
    def clearItem(self):
        # 情况所有Item
        for _ in range(self.count()):
            item = self.takeItem(0)
            self.removeItemWidget(item)
            del item


class Winform(QMainWindow):
    def __init__(self, parent=None):
        super(Winform, self).__init__(parent)
        self.resize(1920, 1080)
        self.setWindowTitle("艾聚达")
        self.setWindowIcon(QIcon("/home/edit/ichia_ai_monitor/image/edgetechlogo.png"))
        self.centralwidget = QWidget(self)

        self.tableWidgetIndex = 0
        self.actionWidgetList = []

        self.edgedataLabel = QLabel(self.centralwidget)
        self.edgedataLabel.setPixmap(QPixmap(QImage("/home/edit/ichia_ai_monitor/image/edgetech.png")))
        self.edgedataLabel.setGeometry(QRect(10, 10, 250, 100))
        self.edgedataLabel.setScaledContents(True)
        self.edgedataLabel.setAlignment(Qt.AlignCenter)

        self.titleLabel = QLabel(self.centralwidget, objectName="titleLabel")
        self.titleLabel.setGeometry(QRect(260, 10, 190, 100))
        self.titleLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.titleLabel.setText("晴灵AI监控")
        self.titleLabel.setScaledContents(True)
        self.titleLabel.setStyleSheet('''color: white;
                                    font-size:30px;
                                    text-align: center;
                                    font-family: Microsoft YaHei''')

        self.okLabel = InformationWidget(self.centralwidget)
        self.okLabel.setGeometry(QRect(10, 120, 220, 100))
        self.okLabel.setScaledContents(True)
        self.okLabel.set_backgroundcolor("#556B2F")
        self.okLabel.numLabel.setText("0")
        self.okLabel.descLabel.setText("合格数")

        self.ngLabel = InformationWidget(self.centralwidget)
        self.ngLabel.setGeometry(QRect(240, 120, 220, 100))
        self.ngLabel.setScaledContents(True)
        self.ngLabel.set_backgroundcolor("#A52A2A")
        self.ngLabel.numLabel.setText("0")
        self.ngLabel.descLabel.setText("不合格数")

        self.totalLabel = InformationWidget(self.centralwidget)
        self.totalLabel.setGeometry(QRect(10, 230, 220, 100))
        self.totalLabel.setScaledContents(True)
        # self.totalLabel.set_backgroundcolor("#FF7F50")
        self.totalLabel.set_backgroundcolor("orangered")

        self.totalLabel.numLabel.setText("0")
        self.totalLabel.descLabel.setText("总数")

        self.yieldLabel = InformationWidget(self.centralwidget)
        self.yieldLabel.setGeometry(QRect(240, 230, 220, 100))
        self.yieldLabel.setScaledContents(True)
        #self.yieldLabel.set_backgroundcolor("#778899")
        self.yieldLabel.set_backgroundcolor("steelblue")

        self.yieldLabel.numLabel.setText("0")
        self.yieldLabel.descLabel.setText("合格率")
        
        self.actionWidgetContainer = QWidget(self.centralwidget)
        self.actionQHboxLayout = QHBoxLayout(self.actionWidgetContainer)
        self.actionWidgetContainer.setGeometry(QRect(10, 340, 450, 75))

        self.tableWidget = HistoryTableWidget(self.centralwidget, rowCount=20)
        self.tableWidget.setGeometry(QRect(10, 425, 450, 595))

        self.videoLabel = QLabel(self.centralwidget)
        self.videoLabel.setStyleSheet(''' QLabel {background-color: #2d2d2d}''')
        self.videoLabel.setGeometry(QRect(470, 10, 1440, 810))
        self.videoLabel.setScaledContents(True)

        self.FPSLabel = QLabel(self.centralwidget)
        self.FPSLabel.setStyleSheet('''color:red;''')
        self.FPSLabel.setAttribute(Qt.WA_TranslucentBackground)
        self.FPSLabel.setGeometry(QRect(1760, 10, 150, 30))
        
        self.TimeLabel = QLabel(self.centralwidget)
        self.TimeLabel.setStyleSheet('''color:red;''')
        self.TimeLabel.setAttribute(Qt.WA_TranslucentBackground)
        self.TimeLabel.setGeometry(QRect(1760, 40, 150, 30))

        self.currLabel = QLabel(self.centralwidget)
        self.currLabel.setStyleSheet('''color:red;''')
    
        self.currLabel.setAttribute(Qt.WA_TranslucentBackground)
        self.currLabel.setGeometry(QRect(1760, 70, 150, 30))


        self.testBox = QTextEdit(self.centralwidget)
        self.testBox.setAttribute(Qt.WA_TranslucentBackground)
        self.testBox.setGeometry(QRect(470, 710, 500, 110))

        self.statusLabel = QLabel(self.centralwidget)
        self.statusLabel.setStyleSheet('''background-color: green; border-radius: 15px''')
        self.statusLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.statusLabel.setText('run')
        self.statusLabel.setGeometry(QRect(475, 15, 30, 30))

        self.historyLabelA = QLabel(self.centralwidget)
        self.historyLabelA.setStyleSheet(''' QLabel {background-color: #2d2d2d}''')
        self.historyLabelA.setGeometry(QRect(470, 826, 352.5, 190))
        self.historyLabelA.setScaledContents(True)

        self.historyLabelB = QLabel(self.centralwidget)
        self.historyLabelB.setStyleSheet(''' QLabel {background-color: #2d2d2d}''')
        self.historyLabelB.setGeometry(QRect(832.5, 826, 352.5, 190))
        self.historyLabelB.setScaledContents(True)

        self.historyLabelC = QLabel(self.centralwidget)
        self.historyLabelC.setStyleSheet(''' QLabel {background-color: #2d2d2d}''')
        self.historyLabelC.setGeometry(QRect(1195, 826, 352.5, 190))
        self.historyLabelC.setScaledContents(True)

        self.historyLabelD = QLabel(self.centralwidget)
        self.historyLabelD.setStyleSheet(''' QLabel {background-color: #2d2d2d}''')
        self.historyLabelD.setGeometry(QRect(1557.5, 826, 352.5, 190))
        self.historyLabelD.setScaledContents(True)

        self.setCentralWidget(self.centralwidget)

        self.startPushButton = QPushButton(objectName="startPushButton")
        self.startPushButton.setText("Start")
        #self.startPushButton.setIconSize(QSize(25, 25))
        self.startPushButton.setStyleSheet('''background-color: white;
                                            color: black;
                                            font-size:13px;
                                            text-align: center;
                                            font-family: Microsoft YaHei;''')

        self.historyPushButton = QPushButton(objectName="historyPushButton")
        self.historyPushButton.setText("历史记录")
        #self.historyPushButton.setIconSize(QSize(25, 25))
        self.historyPushButton.setStyleSheet('''font-size:13px;
                                            text-align: center;
                                            font-family: Microsoft YaHei;''')
       


        self.restartPushButton = QPushButton(objectName="restartPushButton")
        self.restartPushButton.setText("重启应用")
        # self.restartPushButton.setIconSize(QSize(25, 25))
        self.restartPushButton.setStyleSheet('''font-size:13px;
                                            text-align: center;
                                            font-family: Microsoft YaHei;''')


        self.exitPushButton = QPushButton(objectName="exitPushButton")
        self.exitPushButton.setText("退出程序")
        #self.exitPushButton.setIconSize(QSize(25, 25))
        self.exitPushButton.setStyleSheet('''font-size:13px;
                                            text-align: center;
                                            font-family: Microsoft YaHei;''')
       

        self.settingsPushButton = QPushButton(objectName="settingsPushButton")
        self.settingsPushButton.setText("设置")
        #self.settingsPushButton.setIconSize(QSize(25, 25))
        self.settingsPushButton.setStyleSheet('''font-size:13px;
                                            text-align: center;
                                            font-family: Microsoft YaHei;''')
       
        self.statusBar = self.statusBar()
        self.statusBar.addWidget(self.historyPushButton)
        self.statusBar.addWidget(self.settingsPushButton)
        self.statusBar.addWidget(self.restartPushButton)
        self.statusBar.addWidget(self.exitPushButton)
        self.statusBar.addPermanentWidget(QLabel("艾聚达信息技术（苏州）有限公司", objectName="AutoDept"))
        self.widgetActionBanding()

        # 历史记录界面
        self.dataGrid = DataGrid()
        self.settingsGrid = SettingsGrid()
        self.initThread()

    def widgetActionBanding(self):
        self.historyPushButton.clicked.connect(self.queryDataTrigger)
        self.settingsPushButton.clicked.connect(self.settingsTrigger)
        self.restartPushButton.clicked.connect(self.close)
        self.exitPushButton.clicked.connect(self.exitApplication)

    def closeEvent(self, event):
        result = QMessageBox.question(self, "提示", "是否关闭应用程序?", QMessageBox.Yes | QMessageBox.No)
        if(result == QMessageBox.Yes):
            self.processThread.canReadCamera = False
            time.sleep(1)
            event.accept()
            try:
                self.processThread.quit()
            except Exception as e:
                print(e)
               
        else:
            event.ignore()

    def exitApplication(self):
        global canRestart
        canRestart = False
        self.close()

    def queryDataTrigger(self):
        self.dataGrid.show()
    
    def settingsTrigger(self):
        self.settingsGrid.show()

    def testUI(self):
        current = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        for i in range(20):
            self.tableWidget.appendRow(i, current, current, "OK")

    def initThread(self):
            
        self.processThread = ProcessThread()
        self.saveVideoThread = SaveVideoThread()
        self.deleteVideoThread = DeleteVideoThread()

        self.processThread.image_Signal.connect(self.handleDisplay)
        self.processThread.load_widget_action_Signal.connect(self.loadActionWidgets)
        self.processThread.partial_result_Signal.connect(self.handlePartialResults)
        self.processThread.result_Signal.connect(self.handleResult)
        self.processThread.history_image_Signal.connect(self.showHistoryImage)
        self.processThread.error_Signal.connect(self.handleError)
        self.processThread.status_Signal.connect(self.handleStatus)

        self.processThread.define_save_work_Signal.connect(self.saveVideoThread.defineSaveWork)
        self.processThread.end_save_work_Signal.connect(self.saveVideoThread.endSaveWork)
        self.processThread.write_frame_Signal.connect(self.saveVideoThread.writeFrame)
        try:
            self.processThread.start()
            self.deleteVideoThread.start()
        except Exception as e:
            print(e)
            self.handleError(str(e))

    def handleError(self, error_str):
        QMessageBox.critical(self, "应用程序遇到些错误", "请检查相机连接和设置后尝试重启应用程序。\n错误信息：\n" + error_str, QMessageBox.Yes, QMessageBox.Yes)

    def handleStatus(self):
        self.statusLabel.setStyleSheet('''background-color: green; border-radius: 15px''')
        self.statusLabel.setText('run')
        self.processThread.timer.start(180000)
        print("开始计时")

    def handleResult(self, ok, ng, total, percent, curr_time, circle_resutl):
        self.okLabel.numLabel.setText(str(ok))
        self.ngLabel.numLabel.setText(str(ng))
        self.totalLabel.numLabel.setText(str(total))
        per = str(round(percent * 100, 2)) + "%"
        self.yieldLabel.numLabel.setText(per)
        if self.tableWidgetIndex == 20:
            self.tableWidgetIndex = 0
        self.tableWidget.appendHistory(self.tableWidgetIndex, curr_time, circle_resutl)
        self.tableWidgetIndex += 1
        self.statusLabel.setStyleSheet('''background-color: yellow; border-radius: 15px''')
        self.statusLabel.setText('wait')
        if self.processThread.timer.isActive():
            self.processThread.timer.stop()
            print("计时器停止")

    def handleDisplay(self, image, fps):
        """
        handle display
        """
        height, width, channel = image.shape  # 视频帧信息
        bytesPerLine = 3 * width
        self.qImg = QImage(image.data, width, height, bytesPerLine,
                           QImage.Format_RGB888).rgbSwapped()
        # 将Qimage显示出来
        self.videoLabel.setPixmap(QPixmap.fromImage(self.qImg))
        self.FPSLabel.setText("当前帧率：" + str(fps))
        self.TimeLabel.setText("当前时间：" + datetime.datetime.now().strftime("%H:%M:%S"))
        self.currLabel.setText("当前标签：" + str(self.processThread.current_action.confirm_label))
        self.testBox.clear()
        self.testBox.append("当前检测标签\t" + str(self.processThread.current_action))
        self.testBox.append("检测列表\t" + str(self.processThread.current_action.label_list))
        self.testBox.append("结果列表\t" + str(self.processThread.results))
        self.testBox.append("是否允许结束流程\t" + str(self.processThread.allow_close))


    def handlePartialResults(self, results):
        for i in range(len(results)):
            if i == len(self.actionWidgetList):
                return
            if results[i] == "OK":
                self.actionWidgetList[i].set_backgroundcolor('green')
            elif results[i] == "NG":
                self.actionWidgetList[i].set_backgroundcolor('red')
            elif results[i] == '':
                self.actionWidgetList[i].set_backgroundcolor('#778899')
            

    def loadActionWidgets(self, action_name):
        for val in action_name:
            actionWidget = PartialActionWidget()
            actionWidget.setScaledContents(True)
            actionWidget.set_backgroundcolor("#778899")
            actionWidget.actionNameLabel.setText(val)
            self.actionQHboxLayout.addWidget(actionWidget)
            self.actionWidgetList.append(actionWidget)
    
    def showHistoryImage(self):
        if len(self.processThread.image_queue) == 1:
            height, width, channel = self.processThread.image_queue[0].shape
            bytesPerLine = 3 * width
            qImg = QImage(self.processThread.image_queue[0].data, width, height, bytesPerLine,QImage.Format_RGB888)
            self.historyLabelA.setPixmap(QPixmap.fromImage(qImg))
        
        if len(self.processThread.image_queue) == 2:
            height, width, channel = self.processThread.image_queue[0].shape
            bytesPerLine = 3 * width
            qImg = QImage(self.processThread.image_queue[0].data, width, height, bytesPerLine,QImage.Format_RGB888)
            self.historyLabelA.setPixmap(QPixmap.fromImage(qImg))
            height, width, channel = self.processThread.image_queue[1].shape
            bytesPerLine = 3 * width
            qImg = QImage(self.processThread.image_queue[1].data, width, height, bytesPerLine,QImage.Format_RGB888)
            self.historyLabelB.setPixmap(QPixmap.fromImage(qImg))
        
        if len(self.processThread.image_queue) == 3:
            height, width, channel = self.processThread.image_queue[0].shape
            bytesPerLine = 3 * width
            qImg = QImage(self.processThread.image_queue[0].data, width, height, bytesPerLine,QImage.Format_RGB888)
            self.historyLabelA.setPixmap(QPixmap.fromImage(qImg))
            height, width, channel = self.processThread.image_queue[1].shape
            bytesPerLine = 3 * width
            qImg = QImage(self.processThread.image_queue[1].data, width, height, bytesPerLine,QImage.Format_RGB888)
            self.historyLabelB.setPixmap(QPixmap.fromImage(qImg))
            height, width, channel = self.processThread.image_queue[2].shape
            bytesPerLine = 3 * width
            qImg = QImage(self.processThread.image_queue[2].data, width, height, bytesPerLine,QImage.Format_RGB888)
            self.historyLabelC.setPixmap(QPixmap.fromImage(qImg))
        
        if len(self.processThread.image_queue) == 4:
            height, width, channel = self.processThread.image_queue[0].shape
            bytesPerLine = 3 * width
            qImg = QImage(self.processThread.image_queue[0].data, width, height, bytesPerLine,QImage.Format_RGB888)
            self.historyLabelA.setPixmap(QPixmap.fromImage(qImg))
            height, width, channel = self.processThread.image_queue[1].shape
            bytesPerLine = 3 * width
            qImg = QImage(self.processThread.image_queue[1].data, width, height, bytesPerLine,QImage.Format_RGB888)
            self.historyLabelB.setPixmap(QPixmap.fromImage(qImg))
            height, width, channel = self.processThread.image_queue[2].shape
            bytesPerLine = 3 * width
            qImg = QImage(self.processThread.image_queue[2].data, width, height, bytesPerLine,QImage.Format_RGB888)
            self.historyLabelC.setPixmap(QPixmap.fromImage(qImg))
            height, width, channel = self.processThread.image_queue[3].shape
            bytesPerLine = 3 * width
            qImg = QImage(self.processThread.image_queue[3].data, width, height, bytesPerLine,QImage.Format_RGB888)
            self.historyLabelD.setPixmap(QPixmap.fromImage(qImg))


class Empty(Exception):
    """Error attempting to access an element from an empty container."""
    pass


class CircleQueue:
    """Queue implementation using circularly linked list for storage."""
    
    class _Node:
        """Lightweight, nonpublic class for storing a singly linked node."""
        __slots = 'element', '_next' # streamline memory usage
    
        def __init__(self, element, next): # initial node's fields
            self._element = element # reference to user's element
            self._next = next # reference to next node
    
    def __init__(self):
        """Create an empty queue."""
        self._tail = None # will represent tail of queue
        self._size = 0 # number of queue elements
    
    def __len__(self):
        """Return the number of elements in the queue."""
        return self._size
    
    def is_empty(self):
        """Return True if the queue is empty."""
        return self._size == 0
    
    def first(self):
        """Return (but do not remove) the element at the front of the queue.
        Raise Empty exception if the queue is empty.
        """ 
        if self.is_empty():
            raise Empty('Queue is empty.')
        head = self._tail._next
        return head._element
    
    def second(self):
        """Return (but do not remove) the element at the second position of the queue.
        Raise Empty exception if the queue is empty.
        """ 
        if self.is_empty():
            raise Empty('Queue is empty.')
        second = self._tail._next._next
        return second._element

    
    def dequeue(self):
        """Remove and return the first element of the queue(i.e., FIFO).
        
        Raise Empty exception if the queue is empty.
        """
        if self.is_empty():
            raise Empty('Queue is empty.')
        oldhead = self._tail._next
        if self._size == 1: # removing only element
            self.tail = None # queue becomes empty
        else:
            self._tail._next = oldhead._next # bypass the old head
        self._size -= 1
        return oldhead._element
    
    def enqueue(self, e):
        """Add an element to the back of queue."""
        newest = self._Node(e, None) # node will be new tail node
        if self.is_empty():
            newest._next = newest # initialize circularly
        else:
            newest._next = self._tail._next # new node points to head
            self._tail._next = newest # old tail points to new node
        self._tail = newest # new node become the tail
        self._size += 1
    
    def rotate(self):
        """Rotate front element to the back of the queue."""
        if self._size > 0:
            self._tail = self._tail._next # old head becomes new tail


if __name__ == '__main__':
    parser = OptionParser(usage="usage:%prog [optinos] filepath")
    parser.add_option("-t", "--twice", type="int",
                      dest="twice", default=1, help="运行次数")
    options, _ = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    win = Winform()
    win.show()
    app.exec_()
    if canRestart:
        restart(str(options.twice + 1))