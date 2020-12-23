import configparser
import sys, os
sys.path.append('../')
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QLabel, QApplication


class DropListWidget(QListWidget):
    # 可以拖进来的QListWidget

    def __init__(self, *args, **kwargs):
        super(DropListWidget, self).__init__(*args, **kwargs)
        # self.resize(400, 400)
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
            config.read('appsettings.ini')
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
        config.read('appsettings.ini')
        config.remove_section('Logic')
        config.add_section('Logic')
        with open('appsettings.ini', 'w') as f:
            config.write(f)

    def saveActions(self):
        if len(self.actionList) == 0:
            return
        config = configparser.ConfigParser()
        config.read('appsettings.ini')
        config.remove_section('Logic')
        config.add_section('Logic')
        for i in range(len(self.actionList)):
            config.set('Logic', 'action' + str(i), self.actionList[i])
        with open('appsettings.ini', 'w') as f:
            config.write(f)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = DropListWidget()
    win.show()
    sys.exit(app.exec_())