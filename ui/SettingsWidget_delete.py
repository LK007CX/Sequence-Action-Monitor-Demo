import configparser
import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QLineEdit, QToolButton, QHBoxLayout, QWidget, QSlider, QPushButton, QSplitter, \
    QVBoxLayout, QFileDialog, QApplication

from DragListWidget import DragListWidget
from DropListWidget import DropListWidget


class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super(SettingsWidget, self).__init__(parent)
        self.setWindowTitle("设置")
        #self.resize(750, 650)
        self.nameList = []
        self.dataPath = ''

        self.modelLabel = QLabel("模型文件选择")
        self.modelLineEdit = QLineEdit()
        self.modelToolButton = QToolButton()

        self.namesLabel = QLabel("names文件选择")
        self.namesLineEdit = QLineEdit()
        self.namesToolButton = QToolButton()

        self.threshLabel = QLabel("调节置信度")
        self.threshSlider = QSlider()
        self.threshToolButton = QToolButton()

        self.nameLabel = QLabel("检测标签列表")
        self.nameLineEdit = QLineEdit()

        self.splitWidget = QLabel()

        self.actionLabel = QLabel("检测动作顺序配置")

        self.tipsLabel = QLabel("""        Step1：拖拽左侧方块至右侧区域；
        Step2：点击\"保存动作设置\"以保存配置；""")

        self.dragListWidget = DragListWidget()
        self.dropListWidget = DropListWidget()


        self.resetActionPushButton = QPushButton("重置动作设置")

        self.saveActionPushButton = QPushButton("保存动作设置")

        self.initUI()

        self.load_config()

        

    def initUI(self):
        self.modelLabel.setMinimumWidth(150)
        self.modelLabel.setMaximumWidth(150)

        self.modelLineEdit.setReadOnly(True)
        
        self.modelToolButton.setText('...')
        self.modelToolButton.setStyleSheet('''border-color:red;''')
        self.modelToolButton.clicked.connect(self.modelTrigger)

        
        self.namesLabel.setMinimumWidth(150)
        self.namesLabel.setMaximumWidth(150)

        self.namesLineEdit.setReadOnly(True)

        self.namesToolButton.setText('...')
        #self.dataToolButton.setStyleSheet('''border-color:red;''')
        self.dataToolButton.clicked.connect(self.dataTrigger)

        self.splitWidget.setMaximumHeight(2)
        self.splitWidget.setStyleSheet('''background-color: salmon;''')
        self.nameLineEdit.setReadOnly(True)

        self.threshLabel.setMinimumWidth(150)
        self.threshLabel.setMaximumWidth(150)

        self.threshSlider.setOrientation(Qt.Horizontal)
        self.threshSlider.setMinimum(0)
        self.threshSlider.setMaximum(100)
        self.threshSlider.valueChanged.connect(self.threshTrigger)

        self.threshToolButton.setText("%")

        self.nameLabel.setMinimumWidth(150)
        self.nameLabel.setMaximumWidth(150)

        modelLayout = QHBoxLayout()
        modelLayout.addWidget(self.modelLabel)
        modelLayout.addWidget(self.modelLineEdit)
        modelLayout.addWidget(self.modelToolButton)

       

        dataLayout = QHBoxLayout()
        dataLayout.addWidget(self.dataLabel)
        dataLayout.addWidget(self.dataLineEdit)
        dataLayout.addWidget(self.dataToolButton)

        threshLayout = QHBoxLayout()
        threshLayout.addWidget(self.threshLabel)
        threshLayout.addWidget(self.threshSlider)
        threshLayout.addWidget(self.threshToolButton)

        operationLayout = QHBoxLayout()
        operationLayout.addWidget(self.resetActionPushButton)
        operationLayout.addWidget(QSplitter())
        operationLayout.addWidget(self.saveActionPushButton)

        nameLayout = QHBoxLayout()
        nameLayout.addWidget(self.nameLabel)
        nameLayout.addWidget(self.nameLineEdit)

        dragDropLayout = QHBoxLayout()
        dragDropLayout.addWidget(self.dragListWidget)
        dragDropLayout.addWidget(self.dropListWidget)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(modelLayout)
       
        mainLayout.addLayout(dataLayout)
        mainLayout.addLayout(threshLayout)
        mainLayout.addLayout(nameLayout)
        mainLayout.addWidget(self.splitWidget)
        mainLayout.addWidget(self.actionLabel)
        mainLayout.addWidget(self.tipsLabel)
        mainLayout.addLayout(dragDropLayout)
        mainLayout.addLayout(operationLayout)

        self.setLayout(mainLayout)

        self.resetActionPushButton.clicked.connect(self.dropListWidget.clearItem)
        self.saveActionPushButton.clicked.connect(self.dropListWidget.saveActions)

    def load_config(self):
        config = configparser.ConfigParser()
        config.read('appsettings.ini')
        self.modelLineEdit.setText(str(config['Model']['model']).split('/')[-1])
        
        self.dataLineEdit.setText(str(config['Model']['names']).split('/')[-1])
        self.namesPath = str(config['Model']['names'])
        temp = int(float(config['Model']['thresh']) * 100)
        if not config.has_section('Logic'):
            config.add_section('Logic')

        self.threshSlider.setValue(int(float(config['Model']['thresh']) * 100))
        self.threshToolButton.setText(str(int(float(config['Model']['thresh']) * 100)) + "%")
        self.nameTrigger()
        self.dragListWidget.initItems(self.nameList)

    def nameTrigger(self):
        CUSTOM_CLASSES_LIST = []
        with open(self.namesPath) as f:
            for line in f.readlines():
                if line != '':
                    CUSTOM_CLASSES_LIST.append(line.rstrip('\n'))
    
        self.nameLineEdit.setText(str(CUSTOM_CLASSES_LIST))
        self.nameList = CUSTOM_CLASSES_LIST


    def modelTrigger(self):
        openfile_name = QFileDialog.getOpenFileName(self, '选择模型文件', './',
                                                    'Weights file(*.weights)')
        if openfile_name[0] != '':
            self.modifyTrigger("Model", "weights", str(openfile_name[0]))
            self.modelLineEdit.setText(str(openfile_name[0]).split('/')[-1])

    def modifyTrigger(self, str1, str2, str3):
        config = configparser.ConfigParser()
        config.read('appsettings.ini')
        config.set(str1, str2, str3)
        with open('appsettings.ini', 'w') as f:
            config.write(f)

    def dataTrigger(self):
        openfile_name = QFileDialog.getOpenFileName(self, '选择names文件', './',
                                                    'names file(*.names)')
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = SettingsWidget()
    win.show()
    sys.exit(app.exec_())