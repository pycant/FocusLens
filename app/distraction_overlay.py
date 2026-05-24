"""非模态分心提醒 — 浮动通知，不强制中断用户操作

替代原项目 messagebox.showwarning() 强制弹窗问题。
支持多种提醒方式：浮动提示、提示音、系统通知。
"""
import os
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QRect, pyqtProperty
from PyQt6.QtGui import QFont

from config.settings import ALERT_METHODS, PROJECT_DIR


class DistractionOverlay(QWidget):
    """浮动分心提醒 — 非模态，自动消失

    类似 toast 通知，出现在屏幕角落，
    不会抢焦点、不会中断用户操作。
    """

    ACTION_CONTINUE = "continue"
    ACTION_PAUSE = "pause"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.setSingleShot(True)
        self._auto_close_timer.timeout.connect(self.fade_out)

        self._opacity = 1.0
        self._fade_anim: QPropertyAnimation | None = None

        self._build_ui()
        self._result = self.ACTION_CONTINUE

    def _build_ui(self):
        self.setFixedSize(360, 160)

        container = QWidget(self)
        container.setObjectName("container")
        container.setStyleSheet("""
            #container {
                background-color: rgba(30, 30, 30, 220);
                border: 2px solid #ff6b35;
                border-radius: 12px;
            }
        """)
        container.setGeometry(0, 0, 360, 160)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("⚠️ Distraction Detected")
        title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #ff6b35; background: transparent;")
        layout.addWidget(title)

        self._message_label = QLabel("You seem distracted. Please refocus.")
        self._message_label.setWordWrap(True)
        self._message_label.setStyleSheet("color: #e0e0e0; background: transparent;")
        self._message_label.setFont(QFont("Arial", 10))
        layout.addWidget(self._message_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._dismiss_btn = QPushButton("Got it")
        self._dismiss_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b35; color: white;
                border: none; border-radius: 6px; padding: 6px 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e85d2a; }
        """)
        self._dismiss_btn.clicked.connect(self.fade_out)
        btn_layout.addWidget(self._dismiss_btn)

        self._pause_btn = QPushButton("Pause Detection")
        self._pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #555; color: #ccc;
                border: none; border-radius: 6px; padding: 6px 12px;
            }
            QPushButton:hover { background-color: #666; color: white; }
        """)
        self._pause_btn.clicked.connect(self._on_pause)
        btn_layout.addWidget(self._pause_btn)

        layout.addLayout(btn_layout)

    def show_alert(self, degree: float, duration: float):
        """显示分心提醒"""
        self._result = self.ACTION_CONTINUE
        self._message_label.setText(
            f"Distraction degree: {degree:.1f}%\n"
            f"Duration: {duration:.1f}s\n"
            f"Take a moment to refocus."
        )
        self._auto_close_timer.stop()
        self._auto_close_timer.start(5000)  # 5 秒后自动消失
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()

    def fade_out(self):
        if self._fade_anim and self._fade_anim.state() == QPropertyAnimation.State.Running:
            return
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(400)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self.hide)
        self._fade_anim.start()

    def _on_pause(self):
        self._result = self.ACTION_PAUSE
        self.fade_out()

    def get_result(self) -> str:
        return self._result

    # 动画属性
    def get_window_opacity(self):
        return self.windowOpacity()

    def set_window_opacity(self, value):
        self.setWindowOpacity(value)

    windowOpacity = pyqtProperty(float, get_window_opacity, set_window_opacity)
