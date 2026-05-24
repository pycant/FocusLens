"""分心事件日志 — CSV 记录"""
import csv
import os
from datetime import datetime
from typing import Optional

from config.settings import PROJECT_DIR


class DistractionLogger:
    """CSV 日志记录器 — 原项目 log_event 的封装"""

    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = log_dir or PROJECT_DIR
        self.log_file = os.path.join(self.log_dir, "distraction_log.csv")
        self._ensure_header()

    def _ensure_header(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Distraction", "Degree", "Duration"])

    def log(self, message: str, degree: float = 0.0, duration: float = 0.0):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, message, f"{degree:.1f}", f"{duration:.1f}s"])
