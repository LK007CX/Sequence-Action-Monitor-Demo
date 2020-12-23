import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView, QTableWidgetItem, QApplication


class HistoryTableWidget(QTableWidget):
    def __init__(self, parent=None, rowCount=20, columnCount=2):
        super(HistoryTableWidget, self).__init__(parent)
        self.setRowCount(rowCount)
        self.setColumnCount(columnCount)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 表格只读
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 设置表格整行选中
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.horizontalHeader().setVisible(False)  # 隐藏水平表头
        self.setHeight()
        #self.setShowGrid(False)
        self.setStyleSheet('''text-align: center;
                            font-family: Microsoft YaHei;
                            font-size:14px;''')

    def appendHistory(self, column, startTime, result=None):
        item0 = QTableWidgetItem(startTime)
        item0.setTextAlignment(Qt.AlignCenter)
        item1 = QTableWidgetItem(result)
        item1.setTextAlignment(Qt.AlignCenter)
        self.setItem(column, 0, item0)
        self.setItem(column, 1, item1)

    def setHeight(self):
        for i in range(self.rowCount()):
            self.setRowHeight(i, 29.5)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = HistoryTableWidget()
    win.show()
    sys.exit(app.exec_())