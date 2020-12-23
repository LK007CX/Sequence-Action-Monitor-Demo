import sqlite3
import sys

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QDateEdit, QPushButton, QLabel, QSplitter, QTableWidget, \
    QAbstractItemView, QHeaderView, QTableWidgetItem, QMessageBox, QVBoxLayout, QApplication


class DataGrid(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("查询")
        self.resize(750, 500)
        self.initUI()
        self.totalList = []

    def initUI(self):
        # 操作布局
        operatorLayout = QHBoxLayout()
        self.dateLabel = QLabel("选择日期")
        self.dateLabel.setFixedWidth(120)
        self.dateEdit = QDateEdit(QDate.currentDate())
        self.dateEdit.setDisplayFormat("yyyy-MM-dd")
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setMinimumDate(QDate.currentDate().addDays(-365))
        self.dateEdit.setMaximumDate(QDate.currentDate().addDays(0))
        self.queryDataButton = QPushButton("查询数据")
        self.clearButton = QPushButton("清空")

        self.queryDataButton.clicked.connect(self.queryDataTrigger)
        self.queryDataButton.setEnabled(True)
        self.clearButton.clicked.connect(self.clearTrigger)
        self.clearButton.setEnabled(False)
        operatorLayout.addWidget(self.dateLabel)
        operatorLayout.addWidget(self.dateEdit)
        operatorLayout.addWidget(self.queryDataButton)
        operatorLayout.addWidget(self.clearButton)
        operatorLayout.addWidget(QSplitter())
        # 状态布局
        statusLayout = QHBoxLayout()
        self.totalRecordLabel = QLabel()
        self.totalRecordLabel.setFixedWidth(70)
        statusLayout.addWidget(QSplitter())
        statusLayout.addWidget(self.totalRecordLabel)
        # 设置表格属性
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(9)
        self.tableWidget.setHorizontalHeaderLabels(["开始时间", "动作1", "动作2", "动作3", "动作4", "动作5", "动作6", "动作7", "判断结果"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 创建界面
        mainLayout = QVBoxLayout(self)
        mainLayout.addLayout(operatorLayout)
        mainLayout.addWidget(self.tableWidget)
        mainLayout.addLayout(statusLayout)
        self.setLayout(mainLayout)

    def queryDataTrigger(self):
        try:
            queryDate = self.dateEdit.date().toString("yyyy-MM-dd")
            conn = sqlite3.connect("/home/edit/ichia_ai_monitor/db/" + queryDate + ".db")
            c = conn.cursor()
            c.execute('select * from result')
            for col in (c.description):
                # print(col[0], end='\t')
                pass
            while 1:
                row = c.fetchone()
                if not row:
                    break
                templist = [row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]]
                # print(str(row[0]) + '\t' + row[1] + '\t' + row[2] + '\t' + row[3]+ '\t' + row[4]+ '\t' + row[6] + '\t' + row[7] + '\t' + row[8] + '\t' + row[9])
                self.totalList.append(templist)
            c.close()
            conn.close()

            self.tableWidget.setRowCount(len(self.totalList))
            for i in range(0, len(self.totalList)):
                for j in range(0, 9):
                    item = QTableWidgetItem(self.totalList[i][j])
                    self.tableWidget.setItem(i, j, item)

            self.totalRecordLabel.setText("总数: " + str(len(self.totalList)))
            self.queryDataButton.setEnabled(False)
            self.clearButton.setEnabled(True)
        except Exception as e:
            print(e)
            QMessageBox.information(self, "Error", "没有相关数据", QMessageBox.Yes, QMessageBox.Yes)

    def clearTrigger(self):
        self.totalList.clear()
        for i in range(self.tableWidget.rowCount()):
            self.tableWidget.removeRow(0)
        self.queryDataButton.setEnabled(True)
        self.clearButton.setEnabled(False)
        self.totalRecordLabel.setText("")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = DataGrid()
    win.show()
    sys.exit(app.exec_())