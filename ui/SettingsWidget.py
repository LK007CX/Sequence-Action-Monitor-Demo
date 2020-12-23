import configparser
import os
import sys


from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from DragListWidget import DragListWidget
from DropListWidget import DropListWidget

class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super(SettingsWidget, self).__init__(parent)
        self.setWindowTitle("设置")
        #self.resize(750, 650)
        self.namesList = []
        self.namesPath = ''

        self.modelLabel = QLabel("模型文件选择")
        self.modelLineEdit = QLineEdit()
        self.modelToolButton = QToolButton()

        self.namesLabel = QLabel("names文件选择")
        self.namesLineEdit = QLineEdit()
        self.namesToolButton = QToolButton()

        self.threshLabel = QLabel("调节置信度")
        self.threshSlider = QSlider()
        self.threshToolButton = QToolButton()

        self.nameResultLabel = QLabel("检测标签列表")
        self.nameResultLineEdit = QLineEdit()

        self.splitWidget = QLabel()
        self.actionLabel = QLabel("检测动作顺序配置")
        self.tipsLabel = QLabel("""        Step1：拖拽左侧方块至右侧区域；
        Step2：点击\"保存动作设置\"以保存配置；""")

        self.dragListWidget = DragListWidget()
        self.dropListWidget = DropListWidget()

        self.resetActionPushButton = QPushButton("重置动作设置")
        self.saveActionPushButton = QPushButton("保存动作设置")
    
        self.initUI()

    
    def initUI(self):
        self.modelLabel.setMinimumWidth(150)
        self.modelLabel.setMaximumWidth(150)
        self.modelLineEdit.setReadOnly(True)
        self.modelToolButton.setText('...')
        self.modelToolButton.setStyleSheet('''border-color:red;''')
        #self.modelToolButton.clicked.connect(self.modelTrigger)

        self.namesLabel.setMinimumWidth(150)
        self.namesLabel.setMaximumWidth(150)
        self.namesLineEdit.setReadOnly(True)
        self.namesToolButton.setText('...')
        


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = SettingsWidget()
    win.show()
    sys.exit(app.exec_())
