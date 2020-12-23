import datetime


class Action:
    __slots__ = 'confirm_label', 'confirm_num', 'label_list', 'time_list', 'confirm_time', 'done', 'index', \
                'allow_close', 'timer'

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
            if (len(self.time_list) > 1) and (self.time_list[-1] - self.time_list[0]).seconds > self.confirm_time:
                self.done = True
                return True
        if (label == self.confirm_label):
            if (len(self.label_list) < self.confirm_num):
                self.label_list.append(label)
            self.time_list.append(datetime.datetime.now())
        return False

    def __str__(self):
        return "动作\t" + str(self.index) + "\t" + str(self.confirm_label)