import datetime
import sys
import time

import qdarkstyle
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QHBoxLayout, QTextEdit, QPushButton, QMessageBox, QApplication


from ui.DataGrid import DataGrid
from ui.HistoryTableWidget import HistoryTableWidget
from ui.InformationWidget import InformationWidget
from ui.PartialActionWidget import PartialActionWidget
from ui.SettingsGrid import SettingsGrid


class Winform(QMainWindow):
    def __init__(self, parent=None):
        super(Winform, self).__init__(parent)
        self.resize(1920, 1080)
        self.setWindowTitle("艾聚达")
        self.setWindowIcon(QIcon("image/edgetechlogo.png"))
        self.centralwidget = QWidget(self)

        self.tableWidgetIndex = 0
        self.actionWidgetList = []

        self.edgedataLabel = QLabel(self.centralwidget)
        self.edgedataLabel.setPixmap(QPixmap(QImage("image/edgetech.png")))
        self.edgedataLabel.setGeometry(QRect(10, 10, 250, 100))
        self.edgedataLabel.setScaledContents(True)
        self.edgedataLabel.setAlignment(Qt.AlignCenter)

        self.titleLabel = QLabel(self.centralwidget, objectName="titleLabel")
        self.titleLabel.setGeometry(QRect(260, 10, 190, 100))
        self.titleLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.titleLabel.setText("晴灵AI监控")
        self.titleLabel.setScaledContents(True)
        self.titleLabel.setStyleSheet('''color: white;
                                    font-size:30px;
                                    text-align: center;
                                    font-family: Microsoft YaHei''')

        self.okLabel = InformationWidget(self.centralwidget)
        self.okLabel.setGeometry(QRect(10, 120, 220, 100))
        self.okLabel.setScaledContents(True)
        self.okLabel.set_backgroundcolor("#556B2F")
        self.okLabel.numLabel.setText("0")
        self.okLabel.descLabel.setText("合格数")

        self.ngLabel = InformationWidget(self.centralwidget)
        self.ngLabel.setGeometry(QRect(240, 120, 220, 100))
        self.ngLabel.setScaledContents(True)
        self.ngLabel.set_backgroundcolor("#A52A2A")
        self.ngLabel.numLabel.setText("0")
        self.ngLabel.descLabel.setText("不合格数")

        self.totalLabel = InformationWidget(self.centralwidget)
        self.totalLabel.setGeometry(QRect(10, 230, 220, 100))
        self.totalLabel.setScaledContents(True)
        # self.totalLabel.set_backgroundcolor("#FF7F50")
        self.totalLabel.set_backgroundcolor("orangered")

        self.totalLabel.numLabel.setText("0")
        self.totalLabel.descLabel.setText("总数")

        self.yieldLabel = InformationWidget(self.centralwidget)
        self.yieldLabel.setGeometry(QRect(240, 230, 220, 100))
        self.yieldLabel.setScaledContents(True)
        # self.yieldLabel.set_backgroundcolor("#778899")
        self.yieldLabel.set_backgroundcolor("steelblue")

        self.yieldLabel.numLabel.setText("0")
        self.yieldLabel.descLabel.setText("合格率")

        self.actionWidgetContainer = QWidget(self.centralwidget)
        self.actionQHboxLayout = QHBoxLayout(self.actionWidgetContainer)
        self.actionWidgetContainer.setGeometry(QRect(10, 340, 450, 75))

        self.tableWidget = HistoryTableWidget(self.centralwidget, rowCount=20)
        self.tableWidget.setGeometry(QRect(10, 425, 450, 595))

        self.videoLabel = QLabel(self.centralwidget)
        self.videoLabel.setStyleSheet(''' QLabel {background-color: #2d2d2d}''')
        self.videoLabel.setGeometry(QRect(470, 10, 1440, 810))
        self.videoLabel.setScaledContents(True)

        self.FPSLabel = QLabel(self.centralwidget)
        self.FPSLabel.setStyleSheet('''color:red;''')
        self.FPSLabel.setAttribute(Qt.WA_TranslucentBackground)
        self.FPSLabel.setGeometry(QRect(1760, 10, 150, 30))

        self.TimeLabel = QLabel(self.centralwidget)
        self.TimeLabel.setStyleSheet('''color:red;''')
        self.TimeLabel.setAttribute(Qt.WA_TranslucentBackground)
        self.TimeLabel.setGeometry(QRect(1760, 40, 150, 30))

        self.currLabel = QLabel(self.centralwidget)
        self.currLabel.setStyleSheet('''color:red;''')

        self.currLabel.setAttribute(Qt.WA_TranslucentBackground)
        self.currLabel.setGeometry(QRect(1760, 70, 150, 30))

        self.testBox = QTextEdit(self.centralwidget)
        self.testBox.setAttribute(Qt.WA_TranslucentBackground)
        self.testBox.setGeometry(QRect(470, 710, 500, 110))

        self.statusLabel = QLabel(self.centralwidget)
        self.statusLabel.setStyleSheet('''background-color: green; border-radius: 15px''')
        self.statusLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.statusLabel.setText('run')
        self.statusLabel.setGeometry(QRect(475, 15, 30, 30))

        self.historyLabelA = QLabel(self.centralwidget)
        self.historyLabelA.setStyleSheet(''' QLabel {background-color: #2d2d2d}''')
        self.historyLabelA.setGeometry(QRect(470, 826, 352.5, 190))
        self.historyLabelA.setScaledContents(True)

        self.historyLabelB = QLabel(self.centralwidget)
        self.historyLabelB.setStyleSheet(''' QLabel {background-color: #2d2d2d}''')
        self.historyLabelB.setGeometry(QRect(832.5, 826, 352.5, 190))
        self.historyLabelB.setScaledContents(True)

        self.historyLabelC = QLabel(self.centralwidget)
        self.historyLabelC.setStyleSheet(''' QLabel {background-color: #2d2d2d}''')
        self.historyLabelC.setGeometry(QRect(1195, 826, 352.5, 190))
        self.historyLabelC.setScaledContents(True)

        self.historyLabelD = QLabel(self.centralwidget)
        self.historyLabelD.setStyleSheet(''' QLabel {background-color: #2d2d2d}''')
        self.historyLabelD.setGeometry(QRect(1557.5, 826, 352.5, 190))
        self.historyLabelD.setScaledContents(True)

        self.setCentralWidget(self.centralwidget)
        self.startPushButton = QPushButton(objectName="startPushButton")
        self.startPushButton.setText("Start")
        # self.startPushButton.setIconSize(QSize(25, 25))
        self.startPushButton.setStyleSheet('''background-color: white;
                                            color: black;
                                            font-size:13px;
                                            text-align: center;
                                            font-family: Microsoft YaHei;''')

        self.historyPushButton = QPushButton(objectName="historyPushButton")
        self.historyPushButton.setText("历史记录")
        # self.historyPushButton.setIconSize(QSize(25, 25))
        self.historyPushButton.setStyleSheet('''font-size:13px;
                                            text-align: center;
                                            font-family: Microsoft YaHei;''')

        self.restartPushButton = QPushButton(objectName="restartPushButton")
        self.restartPushButton.setText("重启应用")
        # self.restartPushButton.setIconSize(QSize(25, 25))
        self.restartPushButton.setStyleSheet('''font-size:13px;
                                            text-align: center;
                                            font-family: Microsoft YaHei;''')

        self.exitPushButton = QPushButton(objectName="exitPushButton")
        self.exitPushButton.setText("退出程序")
        # self.exitPushButton.setIconSize(QSize(25, 25))
        self.exitPushButton.setStyleSheet('''font-size:13px;
                                            text-align: center;
                                            font-family: Microsoft YaHei;''')

        self.settingsPushButton = QPushButton(objectName="settingsPushButton")
        self.settingsPushButton.setText("设置")
        # self.settingsPushButton.setIconSize(QSize(25, 25))
        self.settingsPushButton.setStyleSheet('''font-size:13px;
                                            text-align: center;
                                            font-family: Microsoft YaHei;''')

        self.statusBar = self.statusBar()
        self.statusBar.addWidget(self.historyPushButton)
        self.statusBar.addWidget(self.settingsPushButton)
        self.statusBar.addWidget(self.restartPushButton)
        self.statusBar.addWidget(self.exitPushButton)
        self.statusBar.addPermanentWidget(QLabel("艾聚达信息技术（苏州）有限公司", objectName="AutoDept"))

        # 历史记录界面
        self.dataGrid = DataGrid()
        self.settingsGrid = SettingsGrid()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    win = Winform()
    win.show()
    app.exec_()