from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys, cv2, time, os
import numpy as np
import argparse
from threading import Thread

import pycuda.autoinit  # This is needed for initializing CUDA driver

from q_thread.custom_classes import get_cls_dict
from utils.camera import add_camera_args, Camera
from utils.display import open_window, set_display, show_fps
from utils.visualization import BBoxVisualization
from utils.yolo_with_plugins import TrtYOLO


from ArgsHelper import ArgsHelper


WINDOW_NAME = 'TrtYOLODemo'


class DetectTensorRT(QThread):

    image_Signal = pyqtSignal(np.ndarray)

    def __init__(self, args, parent=None):
        super(DetectTensorRT, self).__init__(parent)
        self.args = args
        self.cam = None
        self.trt_yolo = None
        self.conf_th = 0.3
        self.vis = None

    def load_tensorRT(self):
        if self.args.category_num <= 0:
            raise SystemExit('ERROR: bad category_num (%d)!' % self.args.category_num)
        if not os.path.isfile(self.args.model):
            raise SystemExit('ERROR: file model not found!' % self.args.model)

        self.cam = Camera(self.args)
        if not self.cam.isOpened():
            raise SystemExit('ERROR: failed to open camera!')

        cls_dict = get_cls_dict('appsettings.ini')
        yolo_dim = self.args.model.split('-')[-1].split('.')[0]
        if 'x' in yolo_dim:
            dim_split = yolo_dim.split('x')
            if len(dim_split) != 2:
                raise SystemExit('ERROR: bad yolo_dim (%s)!' % yolo_dim)
            w, h = int(dim_split[0]), int(dim_split[1])
        else:
            h = w = int(yolo_dim)
        if h % 32 != 0 or w % 32 != 0:
            raise SystemExit('ERROR: bad yolo_dim (%s)!' % yolo_dim)

        # self.trt_yolo = TrtYOLO(self.args.model, (h, w), self.args.category_num)
        self.trt_yolo = TrtYOLO(self.args.model, (h, w), self.args.category_num, cuda_ctx=pycuda.autoinit.context)
        self.vis = BBoxVisualization(cls_dict)

    def loop_and_detect(self):
        full_scrn = False
        fps = 0.0
        tic = time.time()
        while True:
            img = self.cam.read()
            if img is None:
                break
            boxes, confs, clss = self.trt_yolo.detect(img, self.conf_th)
            img = self.vis.draw_bboxes(img, boxes, confs, clss)
            img = show_fps(img, fps)
            self.image_Signal.emit(img)
            toc = time.time()
            curr_fps = 1.0 / (toc - tic)
            # calculate an exponentially decaying average of fps number
            fps = curr_fps if fps == 0.0 else (fps*0.95 + curr_fps*0.05)
            tic = toc

    def run(self):
        try:
            self.load_tensorRT()
            self.loop_and_detect()
        finally:
            self.cam.release()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    args = ArgsHelper(image=None, video=None, video_looping=False,rtsp=None, rtsp_latency=200, usb=0, onboard=None, copy_frame=False, do_resize=False, width=640, height=480, category_num=80, model='yolov4-tiny-416')
    thread1 = DetectTensorRT(args)
    thread1.start()
    sys.exit(app.exec_())