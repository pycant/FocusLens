"""圆形仪表盘组件 — QPainter 绘制，适配主题颜色"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPainterPath


class ArcGauge(QWidget):
    """环形仪表盘

    用法:
        gauge = ArcGauge("Focus", value=75, max=100, color="#22c55e")
        gauge.setValue(85)
    """

    def __init__(self, title: str = "", value: float = 0, max_val: float = 100,
                 color: str = "#22c55e", parent=None):
        super().__init__(parent)
        self._title = title
        self._value = value
        self._max = max_val
        self._color = QColor(color)
        self._bg_arc = QColor(60, 60, 60, 40)
        self._text_color = QColor(200, 200, 200)
        self.setMinimumSize(80, 100)
        self.setMaximumWidth(160)

    def setValue(self, v: float):
        self._value = max(0, min(v, self._max))
        self.update()

    def setColor(self, c: str):
        self._color = QColor(c)
        self.update()

    def setTextColor(self, c: QColor):
        self._text_color = c
        self.update()

    def setBgArc(self, c: QColor):
        self._bg_arc = c
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(120, 140)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        side = min(w, h - 24)
        rect_x = (w - side) // 2
        rect_y = 16
        arc_rect = (rect_x, rect_y, side, side)

        # 百分比
        pct = self._value / self._max if self._max > 0 else 0.0
        span = int(270 * pct)  # 270度圆弧
        start_angle = 135 * 16  # 从135度开始

        # 背景弧
        pen = QPen(self._bg_arc, max(6, side // 12))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(*arc_rect, start_angle, 270 * 16)

        # 前景弧（变色）
        if pct < 0.5:
            arc_color = self._color.lighter(150)
        elif pct < 0.8:
            arc_color = self._color
        else:
            arc_color = QColor("#ef4444")  # 高值变红
        pen2 = QPen(arc_color, max(6, side // 12))
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen2)
        if span > 0:
            painter.drawArc(*arc_rect, start_angle, span * 16)

        # 中心数值
        val_str = f"{int(self._value)}"
        font = QFont("Arial", side // 5, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(self._text_color)
        painter.drawText(
            rect_x, rect_y, side, side,
            Qt.AlignmentFlag.AlignCenter,
            val_str,
        )

        # 标题
        if self._title:
            font2 = QFont("Arial", 9)
            painter.setFont(font2)
            painter.setPen(QColor(self._text_color).lighter(120))
            painter.drawText(
                0, h - 18, w, 18,
                Qt.AlignmentFlag.AlignCenter,
                self._title,
            )

        painter.end()
