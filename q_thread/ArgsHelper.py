class ArgsHelper:

    __slots__ = 'image', 'video', 'video_looping', 'rtsp', 'rtsp_latency', 'usb', 'onboard', 'copy_frame', 'do_resize', 'width', 'height', 'category_num', 'model'
    
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
         

if __name__ == "__main__":
    args = {'image': None, 'video': None, 'video_looping': False, 'rtsp': None, 'rtsp_latency': 200, 'usb': 0, 'onboard': None, 'copy_frame': False, 'do_resize': False, 'width': 640, 'height': 480, 'category_num': 80, 'model': 'yolov4-tiny-416'}
    helper = ArgsHelper(image=None, video=None, video_looping=False,rtsp=None, rtsp_latency=200, usb=0, onboard=None, copy_frame=False, do_resize=False, width=640, height=480, category_num=80, model='yolov4-tiny-416')
    print(helper.model)