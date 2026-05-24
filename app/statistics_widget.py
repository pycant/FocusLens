"""分心统计面板 — 显示当前会话的专注统计"""
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class StatisticsWidget(QWidget):
    """专注度统计面板

    显示：
    - 当前分心程度（进度条 + 百分比）
    - 本次专注时长
    - 分心次数
    - 当前状态文字
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._distraction_count = 0
        self._session_started = False
        self._session_start_time = 0.0
        self._degree = 0.0

        self.setStyleSheet("""
            StatisticsWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        title = QLabel("Focus Statistics")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        # 分心程度进度条
        degree_layout = QVBoxLayout()
        self._degree_label = QLabel("Distraction Level: 0%")
        self._degree_label.setFont(QFont("Arial", 9))
        degree_layout.addWidget(self._degree_label)

        self._degree_bar = QProgressBar()
        self._degree_bar.setRange(0, 100)
        self._degree_bar.setValue(0)
        self._degree_bar.setTextVisible(False)
        self._degree_bar.setFixedHeight(12)
        self._degree_bar.setStyleSheet("""
            QProgressBar {
                background: #e9ecef; border: none; border-radius: 6px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #51cf66, stop:0.5 #fcc419, stop:1 #ff6b35);
                border-radius: 6px;
            }
        """)
        degree_layout.addWidget(self._degree_bar)
        layout.addLayout(degree_layout)

        # 统计信息
        self._focus_time_label = QLabel("Focus Time: 0s")
        self._focus_time_label.setFont(QFont("Arial", 9))
        layout.addWidget(self._focus_time_label)

        self._distraction_count_label = QLabel("Distractions: 0")
        self._distraction_count_label.setFont(QFont("Arial", 9))
        layout.addWidget(self._distraction_count_label)

        self._state_label = QLabel("State: Idle")
        self._state_label.setStyleSheet("color: #868e96;")
        self._state_label.setFont(QFont("Arial", 9))
        layout.addWidget(self._state_label)

        layout.addStretch()

        # 计时更新
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_focus_time)
        self._timer.start(1000)

    def reset_session(self):
        self._distraction_count = 0
        self._session_started = True
        self._session_start_time = time.time()
        self._degree = 0.0

    def increment_distraction(self):
        self._distraction_count += 1
        self._distraction_count_label.setText(
            f"Distractions: {self._distraction_count}"
        )

    def update_degree(self, degree: float):
        self._degree = degree
        self._degree_bar.setValue(int(degree))
        color = "green" if degree < 30 else ("orange" if degree < 60 else "red")
        self._degree_label.setText(
            f'Distraction Level: <span style="color:{color}">{degree:.0f}%</span>'
        )
        self._degree_label.setTextFormat(Qt.TextFormat.RichText)

    def update_state(self, state_text: str):
        self._state_label.setText(state_text)

    def _update_focus_time(self):
        if self._session_started and self._session_start_time > 0:
            elapsed = int(time.time() - self._session_start_time)
            self._focus_time_label.setText(f"Focus Time: {elapsed}s")
