import os

import cv2
from PyQt5.QtCore import QThread


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