import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QApplication


class PartialActionWidget(QLabel):
    def __init__(self, parent=None, index='0', actionName=''):
        super(PartialActionWidget, self).__init__(parent)

        self.actionNameLabel = QLabel(actionName, objectName="actionNameLabel")
        self.actionNameLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.actionNameLabel.setScaledContents(True)
        self.actionNameLabel.setStyleSheet('''
                                            color: rgb(255, 255, 255);
                                            font-size: 12px;
                                            font-family: Arial''')
        layout = QVBoxLayout()
        layout.addWidget(self.actionNameLabel)
        self.setLayout(layout)

    def set_backgroundcolor(self, color):
        self.setStyleSheet('''QLabel {background-color: ''' + color + '''; border-radius: 10px;}''')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = PartialActionWidget()
    win.show()
    sys.exit(app.exec_())