"""可折叠事件日志 — 显示最近分心事件"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class SessionLog(QWidget):
    """侧边栏底部的可折叠事件日志"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self._events: list[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 标题行（可点击折叠）
        title_row = QWidget()
        title_row.setStyleSheet("background: transparent;")
        title_layout = QVBoxLayout(title_row)
        title_layout.setContentsMargins(4, 2, 4, 2)

        self._toggle_btn = QPushButton("📋 Event Log  ▼")
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                text-align: left; font-weight: bold;
                font-size: 10pt; padding: 2px 0;
            }
            QPushButton:hover { color: #3b82f6; }
        """)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle)
        title_layout.addWidget(self._toggle_btn)
        layout.addWidget(title_row)

        # 日志列表
        self._list = QListWidget()
        self._list.setMaximumHeight(150)
        self._list.setStyleSheet("""
            QListWidget {
                background: transparent; border: 1px solid rgba(128,128,128,0.2);
                border-radius: 6px; font-size: 8pt;
            }
            QListWidget::item {
                padding: 2px 6px; border-bottom: 1px solid rgba(128,128,128,0.1);
            }
        """)
        layout.addWidget(self._list)

        # 清空按钮
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                color: #6b7280; font-size: 8pt; text-align: right;
            }
            QPushButton:hover { color: #ef4444; }
        """)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.clicked.connect(self._list.clear)
        layout.addWidget(self._clear_btn)

    def add_event(self, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M")
        self._events.append(f"[{ts}] {msg}")
        item = QListWidgetItem(f"  [{ts}] {msg}")
        self._list.insertItem(0, item)
        if self._list.count() > 50:
            self._list.takeItem(self._list.count() - 1)

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._list.setVisible(not self._collapsed)
        self._clear_btn.setVisible(not self._collapsed)
        self._toggle_btn.setText("📋 Event Log  ▼" if not self._collapsed else "📋 Event Log  ▶")
