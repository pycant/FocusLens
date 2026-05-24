"""统计面板 — 进度条 + 胶囊信息 + 时序图 + 分心记录表"""
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QFrame, QTableWidget, QHeaderView,
    QTableWidgetItem, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QPolygonF


class CapsuleLabel(QLabel):
    """胶囊式信息标签"""
    def __init__(self, text="", color="#3b82f6", parent=None):
        super().__init__(text, parent)
        self._color = color
        self._apply_style(color)
        self.setWordWrap(True)

    def set_color(self, color: str):
        self._color = color
        self._apply_style(color)

    def _apply_style(self, color: str):
        self.setStyleSheet(f"""
            background-color: {color}18;
            border: 1px solid {color}40;
            border-radius: 10px;
            padding: 3px 10px;
            font-size: 9pt;
        """)


class FocusTimeline(QWidget):
    """专注度时序迷你图 — 显示最近 60 秒的专注变化"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(64)
        self.setMaximumHeight(90)
        self._data: list[float] = []  # 0-100 distraction degree

    def add_point(self, val: float):
        self._data.append(val)
        if len(self._data) > 60:
            self._data.pop(0)
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        pad = 4
        plot_w = w - pad * 2
        plot_h = h - pad * 2

        # 背景
        painter.fillRect(0, 0, w, h, Qt.GlobalColor.transparent)

        # 填充区域 (mountain chart)
        n = len(self._data)
        if n < 2:
            return

        path = []
        for i, val in enumerate(self._data):
            x = pad + (i / (n - 1)) * plot_w
            y = pad + (1 - val / 100.0) * plot_h
            path.append((x, y))

        # 画线 + 填充
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            avg = (self._data[i] / 100.0 + self._data[i + 1] / 100.0) / 2
            r = int(34 + avg * 188)
            g = int(197 - avg * 160)
            b = int(94 - avg * 60)
            painter.setPen(QPen(QColor(r, g, b, 200), 2))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # 填充底部区域（山形图）
        if len(path) >= 2:
            pts = [QPointF(path[0][0], pad + plot_h)]
            pts += [QPointF(x, y) for x, y in path]
            pts.append(QPointF(path[-1][0], pad + plot_h))
            painter.setBrush(QBrush(QColor(59, 130, 246, 30)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(QPolygonF(pts))

        painter.end()


class DistractionTable(QWidget):
    """分心事件记录表"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Time", "Duration"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().hide()
        self._table.setMaximumHeight(160)
        self._table.setStyleSheet("""
            QTableWidget {
                background: transparent; border: none;
                font-size: 8pt; gridline-color: rgba(128,128,128,0.15);
            }
            QHeaderView::section {
                background: transparent; border: none;
                font-weight: bold; font-size: 8pt;
                padding: 2px 4px;
            }
        """)
        layout.addWidget(self._table)

    def add_entry(self, duration: float):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        row = self._table.rowCount()
        self._table.insertRow(0)
        self._table.setItem(0, 0, self._make_item(ts))
        self._table.setItem(0, 1, self._make_item(f"{duration:.1f}s"))
        if self._table.rowCount() > 20:
            self._table.removeRow(self._table.rowCount() - 1)

    def _make_item(self, text: str):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    def clear(self):
        self._table.setRowCount(0)


class StatisticsWidget(QWidget):
    """专注度统计面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._distraction_count = 0
        self._session_started = False
        self._session_start_time = 0.0
        self._degree = 0.0

        self.setMinimumWidth(200)
        self.setMaximumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── 区块 1: 分心程度进度条 ──
        sec1 = self._make_section("FOCUS LEVEL")
        sec1_layout = sec1.layout()

        self._degree_bar = QProgressBar()
        self._degree_bar.setRange(0, 100)
        self._degree_bar.setValue(0)
        self._degree_bar.setTextVisible(False)
        self._degree_bar.setFixedHeight(14)
        self._degree_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(128,128,128,0.15);
                border: none; border-radius: 7px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #22c55e, stop:0.5 #eab308, stop:1 #ef4444);
                border-radius: 7px;
            }
        """)
        sec1_layout.addWidget(self._degree_bar)

        self._degree_label = QLabel("Distraction: 0%")
        self._degree_label.setStyleSheet("font-size: 8pt; color: #6b7280;")
        sec1_layout.addWidget(self._degree_label)

        layout.addWidget(sec1)

        # ── 区块 2: 胶囊信息行 ──
        info_row = QHBoxLayout()
        info_row.setSpacing(4)
        self._distraction_cap = CapsuleLabel("0 distractions", "#f59e0b")
        info_row.addWidget(self._distraction_cap)
        self._state_cap = CapsuleLabel("Idle", "#6b7280")
        info_row.addWidget(self._state_cap)
        self._time_cap = CapsuleLabel("0s", "#3b82f6")
        info_row.addWidget(self._time_cap)
        info_row.addStretch()
        layout.addLayout(info_row)

        # ── 区块 3: 专注度时序图 ──
        sec3 = self._make_section("FOCUS TIMELINE")
        self._timeline = FocusTimeline()
        sec3.layout().addWidget(self._timeline)
        layout.addWidget(sec3)

        # ── 区块 4: 分心记录表 ──
        sec4 = self._make_section("DISTRACTION RECORDS")
        self._dist_table = DistractionTable()
        sec4.layout().addWidget(self._dist_table)
        layout.addWidget(sec4)

        layout.addStretch()

        # 计时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)

    def _make_section(self, title: str) -> QFrame:
        """创建带标题边框的区块"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: 1px solid rgba(128,128,128,0.2);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 6)
        layout.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            font-size: 7pt; font-weight: bold;
            color: rgba(128,128,128,0.6);
            letter-spacing: 1px; border: none;
        """)
        layout.addWidget(title_lbl)
        return frame

    # ── 公开 API ──

    def reset_session(self):
        self._distraction_count = 0
        self._session_started = True
        self._session_start_time = time.time()
        self._degree = 0.0
        self._degree_bar.setValue(0)
        self._timeline.add_point(0)
        self._dist_table.clear()

    def increment_distraction(self):
        self._distraction_count += 1
        self._distraction_cap.setText(f"{self._distraction_count} distractions")

    def update_degree(self, degree: float):
        self._degree = degree
        self._degree_bar.setValue(int(degree))
        self._degree_label.setText(f"Distraction: {int(degree)}%")
        self._timeline.add_point(degree)

    def update_state(self, state_text: str):
        raw = state_text.replace("Status: ", "")
        if "Focused" in raw:
            color = "#22c55e"
        elif "Eyes Closed" in raw or "No Face" in raw:
            color = "#ef4444"
        else:
            color = "#6b7280"
        self._state_cap.set_color(color)
        self._state_cap.setText(raw)

    def add_distraction_entry(self, duration: float):
        self._dist_table.add_entry(duration)

    def _update_time(self):
        if self._session_started and self._session_start_time > 0:
            elapsed = int(time.time() - self._session_start_time)
            self._time_cap.setText(f"{elapsed}s")
