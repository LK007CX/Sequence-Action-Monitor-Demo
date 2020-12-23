#!/bin/bash

set -e

# yolov4-tiny
#wget https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg -q --show-progress --no-clobber
#wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights -q --show-progress --no-clobber

echo "Creating yolov4-tiny-288.cfg and yolov4-tiny-288.weights"
cat yolov4-tiny.cfg | sed -e '6s/batch=64/batch=1/' | sed -e '8s/width=416/width=288/' | sed -e '9s/height=416/height=288/' > yolov4-tiny-288.cfg
echo >> yolov4-tiny-288.cfg
ln -sf yolov4-tiny.weights yolov4-tiny-288.weights
echo "Creating yolov4-tiny-416.cfg and yolov4-tiny-416.weights"
cat yolov4-tiny.cfg | sed -e '6s/batch=64/batch=1/' > yolov4-tiny-416.cfg
echo >> yolov4-tiny-416.cfg
ln -sf yolov4-tiny.weights yolov4-tiny-416.weights

echo
echo "Done."
