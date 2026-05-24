"""专注历史网格 — 7列星期 × 12周，月份通过边框颜色区分 + 滚动条"""
import os, sqlite3, datetime
from PyQt6.QtWidgets import QWidget, QToolTip
from PyQt6.QtCore import Qt, QSize
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
    """7列星期 × 12周，月份通过边框色相区分，支持纵向滚动"""

    GAP = 3
    PAD = 8
    COLS = 7
    WEEKS = 6

    # 月份之间色相步进距离（°）
    _HUE_STEP = 55
    _DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, username: str = "default", parent=None):
        super().__init__(parent)
        self._username = username
        self._data: dict[str, float] = {}
        self._max_minutes = 1.0
        self._month_hues: dict[tuple[int, int], int] = {}
        self.setMinimumHeight(260)
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
        rows = _db.get_week_data(self._username, self.WEEKS)
        self._data = {r[0]: r[1] for r in rows}
        self._max_minutes = max(self._data.values()) if self._data else 1.0
        self._rebuild_month_hues()
        self.update()
        self._adjust_height()

    def _rebuild_month_hues(self):
        """为区间内每个月份分配一个循环色相"""
        today = datetime.date.today()
        start = today - datetime.timedelta(days=self.COLS * self.WEEKS - 1)
        seen: set[tuple[int, int]] = set()
        hues: dict[tuple[int, int], int] = {}
        for i in range(self.COLS * self.WEEKS):
            d = start + datetime.timedelta(days=i)
            key = (d.year, d.month)
            if key not in seen:
                seen.add(key)
                idx = len(seen) - 1
                hues[key] = (idx * self._HUE_STEP + 200) % 360
        self._month_hues = hues

    def _cell_size(self) -> tuple[int, int]:
        w = self.width() - self.PAD * 2
        cell = max(8, (w - self.GAP * (self.COLS - 1)) // self.COLS)
        return cell, cell

    def _header_h(self, cell: int) -> int:
        return max(14, cell + 2)

    def _content_height(self) -> int:
        """12行数据 + 列头 + 边距的完整高度"""
        c, _ = self._cell_size()
        step = c + self.GAP
        return self.PAD * 2 + self._header_h(c) + self.GAP + (self.WEEKS - 1) * step + c

    def _adjust_height(self):
        ideal = self._content_height()
        if abs(self.height() - ideal) > 2:
            self.setFixedHeight(ideal)

    def sizeHint(self):
        return QSize(max(self.minimumWidth(), self.width()), self._content_height())

    def _month_border(self, d: datetime.date):
        """根据月份返回边框颜色（1日 = 醒目，其余 = 柔和）"""
        key = (d.year, d.month)
        hue = self._month_hues.get(key, 200)
        if d.day == 1:
            return QColor.fromHsl(hue, 180, 110, 210), 2
        else:
            return QColor.fromHsl(hue, 60, 170, 80), 1

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c, _ = self._cell_size()
        g, p = self.GAP, self.PAD
        step = c + g
        hh = self._header_h(c)

        today = datetime.date.today()
        start = today - datetime.timedelta(days=self.COLS * self.WEEKS - 1)
        total = self.COLS * self.WEEKS

        # ── 列头：Mon Tue Wed Thu Fri Sat Sun ──
        painter.setPen(QPen(QColor(128, 128, 128, 140), 0))
        font = QFont("Arial", max(6, c // 2), QFont.Weight.Light)
        painter.setFont(font)
        for col in range(self.COLS):
            x = p + col * step
            painter.drawText(x, p, step, hh,
                             Qt.AlignmentFlag.AlignCenter,
                             self._DAY_NAMES[col])

        # ── 网格主体 ──
        y0 = p + hh + g  # 第一行 y 坐标
        for i in range(total):
            d = start + datetime.timedelta(days=i)
            col = d.weekday()
            row = (self.WEEKS - 1) - (i // self.COLS)  # 最新周在顶部
            x = p + col * step
            y = y0 + row * step

            date_str = d.isoformat()
            mins = self._data.get(date_str, 0.0)

            # 填充
            if mins <= 0:
                painter.fillRect(int(x), int(y), c, c, QColor(60, 60, 60, 25))
            else:
                intensity = min(mins / max(self._max_minutes, 1), 1.0)
                gv = int(180 - (1.0 - intensity) * 100)
                base = QColor(20, gv, 50, 200)
                light = QColor(40, min(255, gv + 40), 80, 220)
                grad = QLinearGradient(x, y, x + c, y + c)
                grad.setColorAt(0.0, light)
                grad.setColorAt(1.0, base)
                painter.fillRect(int(x) + 1, int(y) + 1, c - 2, c - 2, grad)

            # 月份边框
            border_color, bw = self._month_border(d)
            painter.setPen(QPen(border_color, bw))
            painter.drawRect(int(x), int(y), c, c)

            # 今日高亮
            if d == today:
                painter.setPen(QPen(QColor(59, 130, 246, 180), 2))
                painter.drawRect(int(x) - 1, int(y) - 1, c + 2, c + 2)

        painter.end()

    def mouseMoveEvent(self, event):
        c, _ = self._cell_size()
        g, p = self.GAP, self.PAD
        step = c + g
        hh = self._header_h(c)
        y0 = p + hh + g
        mx, my = event.position().x(), event.position().y()
        col = int((mx - p) // step)
        row = int((my - y0) // step)

        if 0 <= col < self.COLS and 0 <= row < self.WEEKS:
            week_idx = (self.WEEKS - 1) - row  # row 0 → 最新周
            day_idx = week_idx * self.COLS + col
            if 0 <= day_idx < self.COLS * self.WEEKS:
                today = datetime.date.today()
                start = today - datetime.timedelta(days=self.COLS * self.WEEKS - 1)
                d = start + datetime.timedelta(days=day_idx)
                mins = self._data.get(d.isoformat(), 0.0)
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    f"{d.isoformat()}: {mins:.0f} min focused",
                    self,
                )
        super().mouseMoveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_height()
