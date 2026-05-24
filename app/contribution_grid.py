"""GitHub 风格专注贡献图 — 方格矩阵 + 数据库持久化"""
import os, sqlite3, datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QToolTip
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "focus_stats.db",
)


class FocusDB:
    """SQLite 专注时间数据库"""

    def __init__(self, db_path: str = DB_PATH):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS focus_log (
                username TEXT,
                date TEXT,
                minutes REAL,
                PRIMARY KEY (username, date)
            )
        """)
        self._conn.commit()

    def log_focus(self, username: str, minutes: float):
        date = datetime.date.today().isoformat()
        self._conn.execute("""
            INSERT INTO focus_log (username, date, minutes)
            VALUES (?, ?, ?)
            ON CONFLICT(username, date) DO UPDATE SET minutes = minutes + ?
        """, (username, date, minutes, minutes))
        self._conn.commit()

    def get_week_data(self, username: str, weeks: int = 12) -> list[tuple[str, float]]:
        """返回最近 N 周的每日专注数据"""
        cutoff = (datetime.date.today() - datetime.timedelta(weeks=weeks)).isoformat()
        cursor = self._conn.execute("""
            SELECT date, minutes FROM focus_log
            WHERE username = ? AND date >= ?
            ORDER BY date ASC
        """, (username, cutoff))
        return cursor.fetchall()

    def close(self):
        self._conn.close()


# 单例
_db = FocusDB()


class ContributionGrid(QWidget):
    """GitHub 风格贡献方格图"""

    CELL = 12
    GAP = 3
    PAD = 4

    def __init__(self, username: str = "default", parent=None):
        super().__init__(parent)
        self._username = username
        self._data: dict[str, float] = {}  # date -> minutes
        self._max_minutes = 1.0
        self.setMinimumHeight(140)
        self.setMouseTracking(True)
        self._refresh()

    def set_username(self, name: str):
        self._username = name
        self._refresh()

    def log_today(self, minutes: float):
        if minutes > 0:
            _db.log_focus(self._username, minutes)
            self._refresh()

    def _refresh(self):
        rows = _db.get_week_data(self._username)
        self._data = {r[0]: r[1] for r in rows}
        self._max_minutes = max(self._data.values()) if self._data else 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c, g, p = self.CELL, self.GAP, self.PAD
        step = c + g
        today = datetime.date.today()
        total_days = 84
        start = today - datetime.timedelta(days=total_days - 1)

        for i in range(total_days):
            d = start + datetime.timedelta(days=i)
            col = i // 7
            row = d.weekday()
            x = p + col * step
            y = p + row * step

            date_str = d.isoformat()
            mins = self._data.get(date_str, 0.0)
            if mins <= 0:
                color = QColor(60, 60, 60, 30)
            else:
                intensity = min(mins / max(self._max_minutes, 1), 1.0)
                gv = int(200 - (1.0 - intensity) * 120)
                color = QColor(30, gv, 60, 200)

            painter.fillRect(x, y, c, c, color)
            painter.setPen(QPen(QColor(128, 128, 128, 20), 0.5))
            painter.drawRect(x, y, c, c)

            if d == today:
                painter.setPen(QPen(QColor(59, 130, 246, 100), 1.5))
                painter.drawRect(x - 1, y - 1, c + 2, c + 2)

        # 月份标签
        painter.setPen(QPen(QColor(128, 128, 128, 120), 0))
        font = QFont("Arial", 6)
        painter.setFont(font)
        for w in range(12):
            month = (start + datetime.timedelta(weeks=w)).strftime("%b")
            painter.drawText(p + w * step, p - 2, step, 8, Qt.AlignmentFlag.AlignLeft, month)

        painter.end()

    def mouseMoveEvent(self, event):
        c = self.CELL
        g = self.GAP
        p = self.PAD
        step = c + g

        mx, my = event.position().x(), event.position().y()
        col = int((mx - p) // step)
        row = int((my - p) // step)
        day_offset = col * 7 + row

        today = datetime.date.today()
        total_days = 84
        start = today - datetime.timedelta(days=total_days - 1)
        d = start + datetime.timedelta(days=day_offset)

        if 0 <= day_offset < total_days and 0 <= row < 7:
            mins = self._data.get(d.isoformat(), 0.0)
            QToolTip.showText(
                event.globalPosition().toPoint(),
                f"{d.isoformat()}: {mins:.0f} min focused",
                self,
            )
        super().mouseMoveEvent(event)

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        step = self.CELL + self.GAP
        return QSize(step * 12 + self.PAD * 2, step * 7 + self.PAD * 2 + 10)
