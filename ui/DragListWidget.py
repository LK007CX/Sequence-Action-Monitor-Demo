import sys

from PyQt5.QtCore import Qt, QSize, QRect, QPoint
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QCursor
from PyQt5.QtWidgets import QListWidget, QRubberBand, QListWidgetItem, QLabel, QApplication


class DragListWidget(QListWidget):
    # 可以往外拖的QListWidget

    def __init__(self, *args, **kwargs):
        super(DragListWidget, self).__init__(*args, **kwargs)
        # self.resize(400, 400)
        # 隐藏横向滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 不能编辑
        self.setEditTriggers(self.NoEditTriggers)
        # 开启拖功能
        self.setDragEnabled(True)
        # 只能往外拖
        self.setDragDropMode(self.DragOnly)
        # 忽略放
        self.setDefaultDropAction(Qt.IgnoreAction)
        # ****重要的一句（作用是可以单选，多选。Ctrl、Shift多选，可从空白位置框选）****
        # ****不能用ExtendedSelection,因为它可以在选中item后继续框选会和拖拽冲突****
        self.setSelectionMode(self.ContiguousSelection)
        # 设置从左到右、自动换行、依次排列
        self.setFlow(self.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(self.Adjust)
        # item的间隔
        self.setSpacing(5)
        # 橡皮筋(用于框选效果)
        self._rubberPos = None
        self._rubberBand = QRubberBand(QRubberBand.Rectangle, self)

        # self.initItems()

    # 实现拖拽的时候预览效果图
    # 这里演示拼接所有的item截图(也可以自己写算法实现堆叠效果)
    def startDrag(self, supportedActions):
        items = self.selectedItems()
        drag = QDrag(self)
        mimeData = self.mimeData(items)
        # 由于QMimeData只能设置image、urls、str、bytes等等不方便
        # 这里添加一个额外的属性直接把item放进去,后面可以根据item取出数据
        mimeData.setProperty('myItems', items)
        drag.setMimeData(mimeData)
        pixmap = QPixmap(self.viewport().visibleRegion().boundingRect().size())
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        for item in items:
            rect = self.visualRect(self.indexFromItem(item))
            painter.drawPixmap(rect, self.viewport().grab(rect))
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.viewport().mapFromGlobal(QCursor.pos()))
        drag.exec_(supportedActions)

    def mousePressEvent(self, event):
        # 列表框点击事件,用于设置框选工具的开始位置 q
        super(DragListWidget, self).mousePressEvent(event)
        if event.buttons() != Qt.LeftButton or self.itemAt(event.pos()):
            return
        self._rubberPos = event.pos()
        self._rubberBand.setGeometry(QRect(self._rubberPos, QSize()))
        self._rubberBand.show()

    def mouseReleaseEvent(self, event):
        # 列表框点击释放事件,用于隐藏框选工具
        super(DragListWidget, self).mouseReleaseEvent(event)
        self._rubberPos = None
        self._rubberBand.hide()

    def mouseMoveEvent(self, event):
        # 列表框鼠标移动事件,用于设置框选工具的矩形范围
        super(DragListWidget, self).mouseMoveEvent(event)
        if self._rubberPos:
            pos = event.pos()
            lx, ly = self._rubberPos.x(), self._rubberPos.y()
            rx, ry = pos.x(), pos.y()
            size = QSize(abs(rx - lx), abs(ry - ly))
            self._rubberBand.setGeometry(
                QRect(QPoint(min(lx, rx), min(ly, ry)), size))

    def makeItem(self, size, cname):

        item = QListWidgetItem(self)
        item.setData(Qt.UserRole + 1, cname)  # 把颜色放进自定义的data里面
        item.setSizeHint(size)
        label = QLabel(self)  # 自定义控件
        label.setMargin(2)  # 往内缩进2
        label.resize(size)
        # pixmap = QPixmap(size.scaled(100, 100, Qt.IgnoreAspectRatio))  # 调整尺寸
        # pixmap.fill(QColor(cname))
        label.setText(cname)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet('''background-color: brown; color: white;border-radius: 5px;
        ''')
        self.setItemWidget(item, label)

    def initItems(self, name_list):
        self.clearItem()
        size = QSize(100, 30)
        for cname in name_list:
            self.makeItem(size, cname)

    def clearItem(self):
        # 情况所有Item
        for _ in range(self.count()):
            item = self.takeItem(0)
            self.removeItemWidget(item)
            del item


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = DragListWidget()
    win.show()
    sys.exit(app.exec_())