"""分心提醒横幅 — 嵌入主窗口内部，不开新窗口，不抢焦点"""
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QFont


class DistractionOverlay(QWidget):
    """嵌入主窗口底部的分心提醒横幅"""

    ACTION_CONTINUE = "continue"
    ACTION_PAUSE = "pause"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("distractionBanner")

        # 嵌入父窗口，不设任何 windowFlags
        self.setStyleSheet("""
            #distractionBanner {
                background-color: #c92a2a;
                border-radius: 8px;
            }
        """)
        self.setFixedHeight(72)
        self.hide()

        self._result = self.ACTION_CONTINUE
        self._fade_anim: QPropertyAnimation | None = None
        self._auto_close = QTimer(self)
        self._auto_close.setSingleShot(True)
        self._auto_close.timeout.connect(self.fade_out)

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)

        icon = QLabel("⚠")
        icon.setFont(QFont("Arial", 18))
        icon.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(icon)

        text_layout = QVBoxLayout()
        self._title = QLabel("Distraction Detected")
        self._title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self._title.setStyleSheet("color: white; background: transparent;")
        text_layout.addWidget(self._title)

        self._detail = QLabel("Please refocus")
        self._detail.setFont(QFont("Arial", 9))
        self._detail.setStyleSheet("color: #ffcccc; background: transparent;")
        text_layout.addWidget(self._detail)
        layout.addLayout(text_layout, stretch=1)

        self._pause_btn = QPushButton("Pause")
        self._pause_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.2); color: white;
                border: 1px solid rgba(255,255,255,0.4);
                border-radius: 4px; padding: 4px 12px; font-size: 10pt;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.3); }
        """)
        self._pause_btn.clicked.connect(self._on_pause)
        layout.addWidget(self._pause_btn)

        self._dismiss_btn = QPushButton("OK")
        self._dismiss_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.25); color: white;
                border: none; border-radius: 4px; padding: 4px 14px; font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.4); }
        """)
        self._dismiss_btn.clicked.connect(self.fade_out)
        layout.addWidget(self._dismiss_btn)

    def show_alert(self, degree: float, duration: float):
        self._result = self.ACTION_CONTINUE
        self._detail.setText(
            f"Degree: {degree:.0f}%  |  Duration: {duration:.1f}s"
        )
        self._auto_close.stop()
        self._auto_close.start(5000)

        if self._fade_anim:
            self._fade_anim.stop()

        self.setWindowOpacity(1.0)
        self.show()

    def fade_out(self):
        if self._fade_anim and self._fade_anim.state() == QPropertyAnimation.State.Running:
            return
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(400)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self._hide_safe)
        self._fade_anim.start()

    def _hide_safe(self):
        try:
            self.hide()
            self.setWindowOpacity(1.0)
        except Exception:
            pass

    def _on_pause(self):
        self._result = self.ACTION_PAUSE
        self.fade_out()

    def get_result(self) -> str:
        return self._result

    windowOpacity = pyqtProperty(
        float,
        lambda self: QWidget.windowOpacity(self),
        lambda self, v: QWidget.setWindowOpacity(self, v),
    )
