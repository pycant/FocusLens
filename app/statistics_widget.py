"""胶囊式统计面板 — 仪表盘 + 折叠日志"""
import os, time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor

from app.focus_gauge import ArcGauge
from app.session_log import SessionLog


class CapsuleLabel(QLabel):
    """胶囊式信息标签"""
    def __init__(self, text="", color="#3b82f6", parent=None):
        super().__init__(text, parent)
        self._bg = color
        self.setStyleSheet(f"""
            background-color: {color}22;
            border: 1px solid {color}44;
            border-radius: 10px;
            padding: 4px 10px;
            font-size: 9pt;
        """)
        self.setWordWrap(True)


class StatisticsWidget(QWidget):
    """专注度统计面板 — 胶囊式布局 + 可折叠仪表盘 + 事件日志"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._distraction_count = 0
        self._session_started = False
        self._session_start_time = 0.0
        self._gauges_visible = True
        self._degree = 0.0

        self.setMinimumWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ── 标题行 ──
        title_row = QHBoxLayout()
        title_row.setContentsMargins(4, 0, 4, 0)

        self._toggle_gauges_btn = QPushButton("📊 Focus Statistics  ▼")
        self._toggle_gauges_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                text-align: left; font-weight: bold; font-size: 10pt;
                padding: 2px 0;
            }
            QPushButton:hover { color: #3b82f6; }
        """)
        self._toggle_gauges_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_gauges_btn.clicked.connect(self._toggle_gauges)
        title_row.addWidget(self._toggle_gauges_btn)
        title_row.addStretch()
        layout.addLayout(title_row)

        # ── 仪表盘区域（可折叠） ──
        self._gauges_widget = QWidget()
        self._gauges_widget.setStyleSheet("background: transparent;")
        gauges_layout = QHBoxLayout(self._gauges_widget)
        gauges_layout.setContentsMargins(2, 2, 2, 6)
        gauges_layout.setSpacing(4)

        self._focus_gauge = ArcGauge("Focus Score", 0, 100, "#22c55e")
        gauges_layout.addWidget(self._focus_gauge)

        self._time_gauge = ArcGauge("Session", 0, 100, "#3b82f6")
        gauges_layout.addWidget(self._time_gauge)

        self._density_gauge = ArcGauge("Density", 0, 100, "#f59e0b")
        gauges_layout.addWidget(self._density_gauge)

        layout.addWidget(self._gauges_widget)

        # ── 胶囊信息行 ──
        info_row = QHBoxLayout()
        info_row.setSpacing(4)
        self._distraction_cap = CapsuleLabel("⚠ 0 distractions", "#f59e0b")
        info_row.addWidget(self._distraction_cap)
        self._state_cap = CapsuleLabel("○ Idle", "#6b7280")
        info_row.addWidget(self._state_cap)
        info_row.addStretch()
        layout.addLayout(info_row)

        # 专注时长
        self._focus_time_cap = CapsuleLabel("⏱ 0s", "#3b82f6")
        layout.addWidget(self._focus_time_cap)

        # ── 分隔线 ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: rgba(128,128,128,0.2);")
        layout.addWidget(sep)

        # ── 事件日志 ──
        self._log = SessionLog()
        layout.addWidget(self._log, stretch=1)

        # 计时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)

    def _toggle_gauges(self):
        self._gauges_visible = not self._gauges_visible
        self._gauges_widget.setVisible(self._gauges_visible)
        self._toggle_gauges_btn.setText(
            "📊 Focus Statistics  ▼" if self._gauges_visible else "📊 Focus Statistics  ▶"
        )

    def reset_session(self):
        self._distraction_count = 0
        self._session_started = True
        self._session_start_time = time.time()
        self._degree = 0.0
        self._focus_gauge.setValue(0)
        self._time_gauge.setValue(0)
        self._density_gauge.setValue(0)
        self._log.add_event("Session started")

    def increment_distraction(self):
        self._distraction_count += 1
        self._distraction_cap.setText(f"⚠ {self._distraction_count} distractions")
        self._log.add_event("Distraction detected")

    def update_degree(self, degree: float):
        self._degree = degree
        self._focus_gauge.setValue(100 - degree)  # 100-degree = focus score

    def update_state(self, state_text: str):
        # 解析状态文本着色
        if "Focused" in state_text:
            color = "#22c55e"
            icon = "●"
        elif "Eyes Closed" in state_text or "No Face" in state_text:
            color = "#ef4444"
            icon = "○"
        else:
            color = "#6b7280"
            icon = "○"
        self._state_cap.setStyleSheet(f"""
            background-color: {color}22;
            border: 1px solid {color}44;
            border-radius: 10px;
            padding: 4px 10px;
            font-size: 9pt;
        """)
        self._state_cap.setText(f"{icon} {state_text.replace('Status: ', '')}")

    def update_density(self, density: float):
        self._density_gauge.setValue(density)

    def log_event(self, msg: str):
        self._log.add_event(msg)

    def _update_time(self):
        if self._session_started and self._session_start_time > 0:
            elapsed = int(time.time() - self._session_start_time)
            self._focus_time_cap.setText(f"⏱ {elapsed}s")
            # session gauge: cap at 1 hour
            self._time_gauge.setValue(min(100, elapsed / 36))
