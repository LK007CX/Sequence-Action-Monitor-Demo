import sys
sys.path.append('q_thread')
sys.path.append('ui')

import qdarkstyle
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ArgsHelper import ArgsHelper
from ArgsHelper_delete import ArgsHelper_delete
from DetectTensorRT import DetectTensorRT
from VideoWidget import VideoWidget
from SettingsWidget import SettingsWidget


class Winform(QMainWindow):

    def __init__(self, parent=None):
        super(Winform, self).__init__(parent)
        self.setWindowTitle("Multichannel Camera Demo")

      
        self.settingsAction = QAction('&Settings', self)
        self.exitAction = QAction('&Exit', self)
        self.historyAction = QAction('&History', self)
        self.restartAction = QAction('&Restart', self)
        self.settingsToolBar = self.addToolBar('Settings')
        self.historyToolBar = self.addToolBar('History')
        self.exitToolBar = self.addToolBar('Exit')
        self.restartToolBar = self.addToolBar('Restart')
        self.videoWidget1 = VideoWidget("Source 1")
        self.central = QWidget()
        self.statusBar = QStatusBar()
        # custom widget
        #self.settingsWidget = SettingsWidget()

        self.resize(QSize(1280, 720))
        self.initUI()
        self.initThread()
    
    def initUI(self):
        self.settingsAction.setShortcut('Ctrl+S')
        self.settingsAction.setStatusTip('Settings')
        # self.settingsAction.triggered.connect(self.settingsTrigger)

        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(qApp.quit)

        self.historyAction.setShortcut('Ctrl+H')
        self.historyAction.setStatusTip('History')
        # self.historyAction.triggered.connect(qApp.quit)

        self.restartAction.setShortcut('Ctrl+R')
        self.restartAction.setStatusTip('Restart')
        # self.restartAction.triggered.connect(qApp.quit)

        self.settingsToolBar.addAction(self.settingsAction)

        self.historyToolBar.addAction(self.historyAction)

        self.exitToolBar.addAction(self.exitAction)

        self.restartToolBar.addAction(self.restartAction)
        
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.videoWidget1, 0, 0)

        self.central.setLayout(gridLayout)
        self.setCentralWidget(self.central)

        self.statusBar.addPermanentWidget(QLabel("Multichanner Camera Demo"))
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('Loading model...')

    def initThread(self):
        args = ArgsHelper_delete('appsettings.ini')
        self.thread1 = DetectTensorRT(args)
        self.thread1.image_Signal.connect(self.videoWidget1.handleDisplay)
        self.thread1.start()

    # def settingsTrigger(self):
    #     self.settingsWidget.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    winform = Winform()
    winform.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    winform.show()
    sys.exit(app.exec_())
