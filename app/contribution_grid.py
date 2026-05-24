"""GitHub 风格专注贡献图 — 自适应宽度 + 渐变过渡 + 数据库"""
import os, sqlite3, datetime
from PyQt6.QtWidgets import QWidget, QLabel, QToolTip
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "focus_stats.db",
)


class FocusDB:
    def __init__(self, db_path: str = DB_PATH):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS focus_log (
                username TEXT, date TEXT, minutes REAL,
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
        cutoff = (datetime.date.today() - datetime.timedelta(weeks=weeks)).isoformat()
        cur = self._conn.execute(
            "SELECT date, minutes FROM focus_log WHERE username=? AND date>=? ORDER BY date",
            (username, cutoff),
        )
        return cur.fetchall()

    def close(self):
        self._conn.close()


_db = FocusDB()


class ContributionGrid(QWidget):
    """自适应宽度的 GitHub 风格贡献方格"""

    GAP = 3
    PAD = 4
    ROWS = 7

    def __init__(self, username: str = "default", parent=None):
        super().__init__(parent)
        self._username = username
        self._data: dict[str, float] = {}
        self._max_minutes = 1.0
        self.setMinimumHeight(130)
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

    def _cell_size(self) -> tuple[int, int]:
        """根据当前宽度计算格子大小"""
        w = self.width() - self.PAD * 2
        cols = 12
        cell = max(6, (w - self.GAP * (cols - 1)) // cols)
        return cell, cell

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c, _ = self._cell_size()
        g, p = self.GAP, self.PAD
        step = c + g
        today = datetime.date.today()
        total_days = 84
        start = today - datetime.timedelta(days=total_days - 1)

        # 月份标签（顶部，增加左边距避免裁剪）
        label_pad = p + 6
        painter.setPen(QPen(QColor(128, 128, 128, 140), 0))
        font = QFont("Arial", max(5, c // 2), QFont.Weight.Light)
        painter.setFont(font)
        for w in range(12):
            month = (start + datetime.timedelta(weeks=w)).strftime("%b")
            rect = (label_pad + w * step, 2, step, p - 4)
            painter.drawText(*rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, month)

        # 星期标签（左侧，增加上边距避免裁剪）
        painter.setPen(QPen(QColor(128, 128, 128, 120), 0))
        for row_idx, label in enumerate(["Mon", "", "Wed", "", "Fri", "", "Sun"]):
            if label:
                rect2 = (2, p + row_idx * step, label_pad - 4, c)
                painter.drawText(*rect2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

        for i in range(total_days):
            d = start + datetime.timedelta(days=i)
            col = i // 7
            row = d.weekday()
            x = p + col * step
            y = p + row * step

            date_str = d.isoformat()
            mins = self._data.get(date_str, 0.0)

            if mins <= 0:
                painter.fillRect(int(x), int(y), c, c, QColor(60, 60, 60, 25))
                painter.setPen(QPen(QColor(128, 128, 128, 12), 1))
                painter.drawRect(int(x), int(y), c, c)
            else:
                intensity = min(mins / max(self._max_minutes, 1), 1.0)
                gv = int(180 - (1.0 - intensity) * 100)
                base = QColor(20, gv, 50, 200)
                light = QColor(40, min(255, gv + 40), 80, 220)
                # 渐变
                grad = QLinearGradient(x, y, x + c, y + c)
                grad.setColorAt(0.0, light)
                grad.setColorAt(1.0, base)
                painter.fillRect(int(x) + 1, int(y) + 1, c - 2, c - 2, grad)
                painter.setPen(QPen(base.lighter(130), 1))
                painter.drawRect(int(x), int(y), c, c)

            if d == today:
                painter.setPen(QPen(QColor(59, 130, 246, 150), 2))
                painter.drawRect(int(x) - 1, int(y) - 1, c + 2, c + 2)

        painter.end()

    def mouseMoveEvent(self, event):
        c, _ = self._cell_size()
        g, p = self.GAP, self.PAD
        step = c + g
        mx, my = event.position().x(), event.position().y()
        col = int((mx - p) // step)
        row = int((my - p) // step + 0.5)
        idx = col * 7 + row

        today = datetime.date.today()
        start = today - datetime.timedelta(days=83)
        d = start + datetime.timedelta(days=idx)
        if 0 <= idx < 84:
            mins = self._data.get(d.isoformat(), 0.0)
            QToolTip.showText(
                event.globalPosition().toPoint(),
                f"{d.isoformat()}: {mins:.0f} min focused",
                self,
            )
        super().mouseMoveEvent(event)
