import os
import time

from PyQt5.QtCore import QThread


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
            dir_list = sorted(dir_list, key=lambda x: os.path.getctime(os.path.join(file_path, x)))
            temp_list = []
            # print(dir_list)
            for val in dir_list:
                pwd = '/home/edit/ichia_ai_monitor'
                # print(pwd + '/' + 'video' + '/' + val)
                temp_list.append(pwd + '/' + 'video' + '/' + val)
            return temp_list

    def deleteFileByIndex(self, temp_list):
        try:
            length = len(temp_list)
            if length < 30:
                pass
            delete_list = temp_list[0: (length - 30)]
            for val in delete_list:
                if not os.path.exists(val):
                    break
                os.remove(val)
            print("已删除" + str(len(delete_list)) + "个视频")
        except Exception as e:
            print(e)

    def run(self):
        while True:
            # pwd = os.getcwd()
            pwd = '/home/edit/ichia_ai_monitor'
            temp_list = self.sortFile(pwd + '/video')
            # print(temp_list)
            self.deleteFileByIndex(temp_list)
            time.sleep(60)