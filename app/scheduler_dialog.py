"""自动化任务配置对话框 — 定时开关检测 + 开机自启"""
import os, sys, shutil
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QSpinBox, QGroupBox, QPushButton,
    QFormLayout, QWidget, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config.settings import FocusCamSettings


def set_auto_start(enabled: bool, app_name="FocusCam"):
    """Windows 开机自启：创建/删除 快捷方式到 Startup 文件夹"""
    try:
        startup = os.path.join(os.environ.get("APPDATA", ""),
                               r"Microsoft\Windows\Start Menu\Programs\Startup")
        if not os.path.isdir(startup):
            return False
        link_path = os.path.join(startup, f"{app_name}.lnk")
        if enabled:
            # 创建 VBS 快捷方式（Python 标准库不能直接创建 .lnk）
            vbs_path = os.path.join(startup, f"{app_name}.vbs")
            script_path = os.path.abspath(sys.argv[0])
            python_exe = sys.executable
            with open(vbs_path, "w") as f:
                f.write(f'CreateObject("WScript.Shell").Run "{python_exe} \"{script_path}\"", 0, False\n')
        else:
            for fname in os.listdir(startup):
                if fname.startswith(app_name):
                    os.remove(os.path.join(startup, fname))
        return True
    except Exception:
        return False


class SchedulerDialog(QDialog):
    """自动化任务配置对话框"""

    def __init__(self, settings: FocusCamSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Automation Settings")
        self.setMinimumWidth(400)
        self._original = settings
        self._settings = settings
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── 开机自启 ──
        boot_group = QGroupBox("Auto Start on Boot")
        boot_layout = QVBoxLayout(boot_group)
        self._auto_boot_cb = QCheckBox("Launch FocusCam when Windows starts")
        self._auto_boot_cb.setChecked(self._settings.auto_start_on_boot)
        boot_layout.addWidget(self._auto_boot_cb)
        layout.addWidget(boot_group)

        # ── 定时调度 ──
        sched_group = QGroupBox("Scheduled Detection")
        sched_layout = QFormLayout(sched_group)

        self._sched_enable_cb = QCheckBox("Enable scheduled detection")
        self._sched_enable_cb.setChecked(self._settings.schedule_enabled)
        self._sched_enable_cb.toggled.connect(self._on_sched_toggle)
        sched_layout.addRow("", self._sched_enable_cb)

        # 每日时间范围
        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("Start:"))
        self._start_h = QSpinBox()
        self._start_h.setRange(0, 23)
        self._start_h.setValue(self._settings.schedule_start_hour)
        self._start_h.setSuffix(" h")
        time_row.addWidget(self._start_h)
        self._start_m = QSpinBox()
        self._start_m.setRange(0, 59)
        self._start_m.setValue(self._settings.schedule_start_minute)
        self._start_m.setSuffix(" m")
        time_row.addWidget(self._start_m)
        time_row.addStretch()
        time_row.addWidget(QLabel("End:"))
        self._end_h = QSpinBox()
        self._end_h.setRange(0, 23)
        self._end_h.setValue(self._settings.schedule_end_hour)
        self._end_h.setSuffix(" h")
        time_row.addWidget(self._end_h)
        self._end_m = QSpinBox()
        self._end_m.setRange(0, 59)
        self._end_m.setValue(self._settings.schedule_end_minute)
        self._end_m.setSuffix(" m")
        time_row.addWidget(self._end_m)
        sched_layout.addRow("Daily range:", time_row)

        # 番茄钟模式
        pomo_row = QHBoxLayout()
        pomo_row.addWidget(QLabel("Work:"))
        self._work_spin = QSpinBox()
        self._work_spin.setRange(1, 120)
        self._work_spin.setValue(self._settings.schedule_work_minutes)
        self._work_spin.setSuffix(" min")
        pomo_row.addWidget(self._work_spin)
        pomo_row.addWidget(QLabel("Break:"))
        self._break_spin = QSpinBox()
        self._break_spin.setRange(1, 30)
        self._break_spin.setValue(self._settings.schedule_break_minutes)
        self._break_spin.setSuffix(" min")
        pomo_row.addWidget(self._break_spin)
        pomo_row.addStretch()
        sched_layout.addRow("Pomodoro:", pomo_row)

        info = QLabel("ℹ Automation runs in background. User Start/Stop always takes priority.")
        info.setStyleSheet("color: #6b7280; font-size: 8pt;")
        sched_layout.addRow("", info)

        layout.addWidget(sched_group)

        # ── 按钮 ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6; color: white;
                border: none; border-radius: 6px; padding: 6px 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280; color: white;
                border: none; border-radius: 6px; padding: 6px 16px;
            }
            QPushButton:hover { background-color: #4b5563; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)
        self._on_sched_toggle(self._sched_enable_cb.isChecked())

    def _on_sched_toggle(self, enabled: bool):
        for w in [self._start_h, self._start_m, self._end_h, self._end_m,
                  self._work_spin, self._break_spin]:
            w.setEnabled(enabled)

    def _save(self):
        self._settings.auto_start_on_boot = self._auto_boot_cb.isChecked()
        set_auto_start(self._settings.auto_start_on_boot)
        self._settings.schedule_enabled = self._sched_enable_cb.isChecked()
        self._settings.schedule_start_hour = self._start_h.value()
        self._settings.schedule_start_minute = self._start_m.value()
        self._settings.schedule_end_hour = self._end_h.value()
        self._settings.schedule_end_minute = self._end_m.value()
        self._settings.schedule_work_minutes = self._work_spin.value()
        self._settings.schedule_break_minutes = self._break_spin.value()
        self._settings.save()
        self.accept()

    def get_settings(self) -> FocusCamSettings:
        return self._settings
