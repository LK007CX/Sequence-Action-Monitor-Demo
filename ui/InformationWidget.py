import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QApplication


class InformationWidget(QLabel):
    def __init__(self, parent=None):
        super(InformationWidget, self).__init__(parent)

        self.numLabel = QLabel("0", objectName="numLabel")
        self.numLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.numLabel.setScaledContents(True)
        self.numLabel.setStyleSheet('''
                            color: rgb(255, 255, 255);
                            font-size: 45px;
                            font-weight: bold;
                            font-family: Arial''')

        self.descLabel = QLabel("描述", objectName="descLabel")
        self.descLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.descLabel.setScaledContents(True)
        self.descLabel.setStyleSheet('''
                            color:rgb(255, 255, 255);
                            font-size:15px;
                            font-weight:normal;
                            font-family:Arial''')

        layout = QVBoxLayout()
        layout.addWidget(self.numLabel)
        layout.addWidget(self.descLabel)
        self.setLayout(layout)

    def set_backgroundcolor(self, color):
        self.setStyleSheet('''QLabel {background-color: ''' + color + '''; border-radius: 10px;}''')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = InformationWidget()
    win.show()
    sys.exit(app.exec_())