"""统计面板 — 进度条 + 胶囊信息 + 时序图 + 贡献网格 + 分心记录"""
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QFrame, QTableWidget, QHeaderView,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QPolygonF
from PyQt6.QtCore import QPointF

from app.contribution_grid import ContributionGrid


class CapsuleLabel(QLabel):
    """胶囊式信息标签"""
    def __init__(self, text="", color="#3b82f6", parent=None):
        super().__init__(text, parent)
        self._color = color
        self._apply(color)

    def set_color(self, color: str):
        self._color = color
        self._apply(color)

    def _apply(self, color: str):
        self.setStyleSheet(f"""
            background-color: {color}18;
            border: 1px solid {color}40;
            border-radius: 10px;
            padding: 3px 10px;
            font-size: 9pt;
        """)


class FocusTimeline(QWidget):
    """专注度时序迷你山形图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.setMaximumHeight(80)
        self._data: list[float] = []

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

        w, h, pad = self.width(), self.height(), 4
        pw, ph = w - pad * 2, h - pad * 2
        n = len(self._data)
        if n < 2:
            return

        path = []
        for i, val in enumerate(self._data):
            x = pad + (i / (n - 1)) * pw
            y = pad + (1 - val / 100.0) * ph
            path.append((x, y))

        # 线条
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            avg = (self._data[i] / 100.0 + self._data[i + 1] / 100.0) / 2
            r = int(34 + avg * 188)
            g = int(197 - avg * 160)
            b = int(94 - avg * 60)
            painter.setPen(QPen(QColor(r, g, b, 200), 2))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # 填充
        if len(path) >= 2:
            pts = [QPointF(path[0][0], pad + ph)]
            pts += [QPointF(x, y) for x, y in path]
            pts.append(QPointF(path[-1][0], pad + ph))
            painter.setBrush(QBrush(QColor(59, 130, 246, 30)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(QPolygonF(pts))

        painter.end()


class DistractionTable(QWidget):
    """分心记录表"""

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
        self._table.setMaximumHeight(140)
        self._table.setStyleSheet("""
            QTableWidget {
                background: transparent; border: none;
                font-size: 8pt; gridline-color: rgba(128,128,128,0.15);
            }
            QHeaderView::section {
                background: transparent; border: none;
                font-weight: bold; font-size: 7pt; padding: 2px;
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
        if self._table.rowCount() > 15:
            self._table.removeRow(self._table.rowCount() - 1)

    def _make_item(self, text: str):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    def clear(self):
        self._table.setRowCount(0)


def _section(title: str) -> QFrame:
    """创建带标题边框的区块"""
    f = QFrame()
    f.setStyleSheet("""
        QFrame {
            border: 1px solid rgba(128,128,128,0.2);
            border-radius: 8px; padding: 4px;
        }
    """)
    layout = QVBoxLayout(f)
    layout.setContentsMargins(8, 4, 8, 6)
    layout.setSpacing(4)
    lbl = QLabel(title)
    lbl.setStyleSheet("font-size: 7pt; font-weight: bold; color: rgba(128,128,128,0.6); letter-spacing: 1px; border: none;")
    layout.addWidget(lbl)
    return f


class StatisticsWidget(QWidget):
    """专注度统计面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._distraction_count = 0
        self._session_started = False
        self._session_start_time = 0.0
        self._focused_seconds = 0
        self._last_tick_focused = False
        self._degree = 0.0

        self.setMinimumWidth(200)
        self.setMaximumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── 1. 专注程度进度条 ──
        s1 = _section("FOCUS LEVEL")
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
        s1.layout().addWidget(self._degree_bar)

        self._degree_label = QLabel("Distraction: 0%")
        self._degree_label.setStyleSheet("font-size: 8pt; color: rgba(128,128,128,0.7);")
        s1.layout().addWidget(self._degree_label)
        layout.addWidget(s1)

        # ── 2. 胶囊信息行 ──
        cap_row = QHBoxLayout()
        cap_row.setSpacing(4)

        self._distraction_cap = CapsuleLabel("0 distractions", "#f59e0b")
        cap_row.addWidget(self._distraction_cap)

        self._state_cap = CapsuleLabel("Idle", "#6b7280")
        cap_row.addWidget(self._state_cap)

        cap_row.addStretch()
        layout.addLayout(cap_row)

        # ── 专注时间（单独一行，胶囊下方） ──
        self._focus_time_cap = CapsuleLabel("Focus Time: 0s", "#22c55e")
        layout.addWidget(self._focus_time_cap)

        # ── 3. 时序图 ──
        s3 = _section("FOCUS TIMELINE (60s)")
        self._timeline = FocusTimeline()
        s3.layout().addWidget(self._timeline)
        layout.addWidget(s3)

        # ── 4. 贡献网格 ──
        s4 = _section("FOCUS HISTORY")
        self._grid = ContributionGrid()
        s4.layout().addWidget(self._grid)
        layout.addWidget(s4)

        # ── 5. 分心记录 ──
        s5 = _section("DISTRACTION RECORDS")
        self._dist_table = DistractionTable()
        s5.layout().addWidget(self._dist_table)
        layout.addWidget(s5)

        layout.addStretch()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

    def _tick(self):
        if not self._session_started:
            return
        now = int(time.time())
        elapsed = now - int(self._session_start_time)
        # 专注时间：只在 focused 状态增加
        if self._last_tick_focused:
            self._focused_seconds += 1
            self._grid.log_today(1 / 60.0)  # 每秒记录 1/60 分钟

        total_str = str(elapsed)
        focus_str = str(self._focused_seconds)
        self._focus_time_cap.setText(f"Focus Time: {focus_str}s / {total_str}s")
        self._focus_time_cap._apply("#22c55e" if self._last_tick_focused else "#6b7280")

    # ── 公开 API ──

    def set_grid_username(self, name: str):
        self._grid.set_username(name)

    def reset_session(self):
        self._distraction_count = 0
        self._session_started = True
        self._session_start_time = time.time()
        self._focused_seconds = 0
        self._last_tick_focused = False
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
            self._last_tick_focused = True
            self._state_cap.set_color("#22c55e")
        elif "Eyes Closed" in raw or "No Face" in raw:
            self._last_tick_focused = False
            self._state_cap.set_color("#ef4444")
        else:
            self._last_tick_focused = False
            self._state_cap.set_color("#6b7280")
        self._state_cap.setText(raw)

    def add_distraction_entry(self, duration: float):
        self._dist_table.add_entry(duration)

    def set_username(self, name: str):
        self._grid.set_username(name)
