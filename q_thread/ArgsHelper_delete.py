import configparser
import os


class ArgsHelper_delete:

    __slots__ = 'image', 'video', 'video_looping', 'rtsp', 'rtsp_latency', 'usb', 'onboard', 'copy_frame', 'do_resize', 'width', 'height', 'category_num', 'model'
    
    slots = list(__slots__)

    def __init__(self, config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        for k in self.slots:
            if config['Model'][k] == 'True':
                setattr(self, k, True)
            elif config['Model'][k] == 'False':
                setattr(self, k, False)
            elif config['Model'][k] == 'None':
                setattr(self, k, None)
            else:
                setattr(self, k, config['Model'][k])
        self.rtsp_latency = int(self.rtsp_latency)
        self.width = int(self.width)
        self.height = int(self.height)
        self.category_num = int(self.category_num)
        self.usb = int(self.usb)

if __name__ == "__main__":
    print(os.getcwd())
    helper = ArgsHelper_delete('appsettings.ini')
    print(helper.model)
    print(helper.copy_frame)
    print(type(helper.copy_frame))
    print(helper.rtsp)
    print(type(helper.rtsp))
    print(None)
    print(type(helper.width))
    print(helper.video)
    print(type(helper.video))
    print(type(helper.category_num))
    