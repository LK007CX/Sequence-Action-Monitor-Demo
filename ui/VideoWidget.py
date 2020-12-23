from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys


class VideoWidget(QWidget):

    def __init__(self, name, parent=None):
        super(VideoWidget, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.name = name

        self.titleLabel = QLabel()
        self.titleLabel.setStyleSheet('''font-family: Serif;''')
        self.titleLabel.setFixedSize(100, 30)
        self.titleLabel.setText(name)
        titleLayout = QHBoxLayout()
        titleLayout.addWidget(self.titleLabel)
        splitter = QSplitter()
        splitter.setAttribute(Qt.WA_TranslucentBackground)
        titleLayout.addWidget(splitter)

        self.videoLabel = QLabel()
        self.videoLabel.setStyleSheet('''background-color:rgb(45, 45, 45);''')
        self.videoLabel.setScaledContents(True)
        layout = QVBoxLayout(self)
        # layout.addLayout(titleLayout)
        layout.addWidget(self.videoLabel)

        self.setLayout(layout)
    
    def handleDisplay(self, image):
        height, width, channel = image.shape
        bytePerLine = 3 * width
        self.qImg = QImage(image.data, width, height, bytePerLine,
                    QImage.Format_RGB888).rgbSwapped()
        self.videoLabel.setPixmap(QPixmap.fromImage(self.qImg))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    winform = VideoWidget()
    winform.show()
    sys.exit(app.exec_())
