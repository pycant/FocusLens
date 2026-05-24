"""FocusCam 主窗口 — PyQt6 桌面应用"""
import os, datetime, time as _time
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QMessageBox,
    QStatusBar, QApplication, QSplitter, QInputDialog,
    QLineEdit,
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QAction, QFont, QIcon

from config.settings import FocusCamSettings
from core.camera_manager import get_available_cameras
from app.camera_widget import CameraWidget
from app.settings_dialog import SettingsDialog
from app.login_dialog import LoginDialog
from app.distraction_overlay import DistractionOverlay
from app.statistics_widget import StatisticsWidget
from app.scheduler_dialog import SchedulerDialog
from app.theme import apply_theme, THEMES, get_camera_bg, make_button_style, colored_icon, get_btn_color

from utils.logger import DistractionLogger

DEFAULT_USER = "Default User"

_current_theme = "classic_light"


def _lighten(hex_color: str, factor: float = 0.15) -> str:
    try:
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


def _icon(name: str, color_override: str | None = None) -> QIcon:
    return colored_icon(_current_theme, name, color_override)


class MainWindow(QMainWindow):
    """FocusCam 主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FocusCam")
        self.setWindowIcon(_icon("focus"))
        self.setMinimumSize(900, 620)

        self._settings = FocusCamSettings.load()
        self._logger = DistractionLogger()

        global _current_theme
        _current_theme = self._settings.theme_name

        self._username = self._settings.last_username or DEFAULT_USER
        self._distraction_overlay: DistractionOverlay | None = None
        self._side_visible = self._settings.side_panel_visible
        self._sched_timer = QTimer(self)
        self._sched_timer.timeout.connect(self._check_schedule)
        self._sched_timer.start(30000)  # 每 30 秒检查

        self._build_menu_bar()
        self._build_central()
        self._build_status_bar()
        self._apply_widget_styles()

        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._sync_stats)
        self._stats_timer.start(500)

    # ── 菜单栏 ──

    def _build_menu_bar(self):
        mb = self.menuBar()

        # User
        user_menu = mb.addMenu("👤 User")
        sw = QAction("Switch User...", self)
        sw.setIcon(_icon("user"))
        sw.triggered.connect(self._switch_user)
        user_menu.addAction(sw)

        rg = QAction("Register New User (Face Capture)...", self)
        rg.setIcon(_icon("user"))
        rg.triggered.connect(self._register_user)
        user_menu.addAction(rg)
        user_menu.addSeparator()

        st = QAction("Settings...", self)
        st.setIcon(_icon("settings"))
        st.triggered.connect(self._show_settings)
        user_menu.addAction(st)

        at = QAction("Automation...", self)
        at.triggered.connect(self._show_automation)
        user_menu.addAction(at)
        user_menu.addSeparator()

        ex = QAction("Exit", self)
        ex.setIcon(_icon("stop"))
        ex.triggered.connect(self.close)
        user_menu.addAction(ex)

        # View
        view_menu = mb.addMenu("👁 View")
        self._side_action = QAction("Side Panel", self)
        self._side_action.setCheckable(True)
        self._side_action.setChecked(self._side_visible)
        self._side_action.triggered.connect(self._toggle_side_panel)
        view_menu.addAction(self._side_action)
        view_menu.addSeparator()

        self._theme_actions = {}
        for key, meta in THEMES.items():
            a = QAction(meta["label"], self)
            a.setCheckable(True)
            a.setChecked(key == self._settings.theme_name)
            a.triggered.connect(lambda checked, k=key: self._switch_theme(k))
            view_menu.addAction(a)
            self._theme_actions[key] = a

        # Help
        help_menu = mb.addMenu("❓ Help")
        ab = QAction("About FocusCam", self)
        ab.triggered.connect(self._show_about)
        help_menu.addAction(ab)

        gd = QAction("How to Use", self)
        gd.triggered.connect(self._show_guide)
        help_menu.addAction(gd)

    # ── 中央布局 ──

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        # 左：视频 + 控制
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 4, 0)

        cam_row = QHBoxLayout()
        cam_row.addWidget(QLabel("Camera:"))
        self._cam_combo = QComboBox()
        self._available_cameras = get_available_cameras()
        for c in self._available_cameras:
            self._cam_combo.addItem(f"Camera {c}", c)
        saved_idx = self._cam_combo.findData(self._settings.camera_id)
        if saved_idx >= 0:
            self._cam_combo.setCurrentIndex(saved_idx)
        self._cam_combo.currentIndexChanged.connect(self._switch_camera)
        cam_row.addWidget(self._cam_combo)
        cam_row.addStretch()

        self._start_btn = QPushButton(" Start Detection")
        self._start_btn.setIcon(_icon("play", "#ffffff"))
        self._start_btn.setIconSize(QSize(16, 16))
        self._start_btn.clicked.connect(self._start_detection)
        cam_row.addWidget(self._start_btn)

        self._stop_btn = QPushButton(" Stop")
        self._stop_btn.setIcon(_icon("stop", "#ffffff"))
        self._stop_btn.setIconSize(QSize(16, 16))
        self._stop_btn.clicked.connect(self._stop_detection)
        self._stop_btn.setEnabled(False)
        cam_row.addWidget(self._stop_btn)

        self._settings_btn = QPushButton(" Settings")
        self._settings_btn.setIcon(_icon("settings", "#ffffff"))
        self._settings_btn.setIconSize(QSize(16, 16))
        self._settings_btn.clicked.connect(self._show_settings)
        cam_row.addWidget(self._settings_btn)

        left_layout.addLayout(cam_row)
        self._camera_widget = CameraWidget()
        left_layout.addWidget(self._camera_widget, stretch=1)

        self._distraction_banner = DistractionOverlay()
        self._distraction_banner.hide()
        left_layout.addWidget(self._distraction_banner)

        # 右：统计面板（可折叠、可拖拽）
        self._stats_widget = StatisticsWidget()
        self._stats_widget.setMinimumWidth(0)
        self._stats_widget.setMaximumWidth(400)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.addWidget(left_panel)
        self._splitter.addWidget(self._stats_widget)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setHandleWidth(4)
        main_layout.addWidget(self._splitter)

        if not self._side_visible:
            self._stats_widget.hide()

    # ── 状态栏 ──

    def _build_status_bar(self):
        self._status_bar = QStatusBar()
        self._status_bar.showMessage("Ready")
        self.setStatusBar(self._status_bar)

        self._user_icon = QLabel()
        self._user_icon.setPixmap(_icon("user").pixmap(16, 16))
        self._user_icon.setStyleSheet("padding-right: 2px;")
        self._status_bar.addPermanentWidget(self._user_icon)

        self._user_label = QLabel()
        self._update_user_label()
        self._user_label.setStyleSheet("padding-right: 8px;")
        self._status_bar.addPermanentWidget(self._user_label)

        self._sched_label = QLabel()
        self._sched_label.setStyleSheet("color: #6b7280; font-size: 8pt; padding-right: 6px;")
        self._status_bar.addPermanentWidget(self._sched_label)

    def _update_user_label(self):
        self._user_label.setText(f" {self._username}")

    # ── 按钮样式 ──

    def _apply_widget_styles(self):
        global _current_theme
        _current_theme = self._settings.theme_name
        t = _current_theme
        self._start_btn.setStyleSheet(make_button_style(get_btn_color(t, "start"), _lighten(get_btn_color(t, "start"))))
        self._stop_btn.setStyleSheet(make_button_style(get_btn_color(t, "stop"), _lighten(get_btn_color(t, "stop"))))
        self._settings_btn.setStyleSheet(make_button_style(get_btn_color(t, "settings"), _lighten(get_btn_color(t, "settings"))))
        if hasattr(self, "_camera_widget"):
            self._camera_widget.set_bg_color(get_camera_bg(t))
        self._start_btn.setIcon(_icon("play", "#ffffff"))
        self._stop_btn.setIcon(_icon("stop", "#ffffff"))
        self._settings_btn.setIcon(_icon("settings", "#ffffff"))
        if hasattr(self, "_user_icon"):
            self._user_icon.setPixmap(_icon("user").pixmap(16, 16))

    # ── 操作 ──

    def _start_detection(self):
        if not self._available_cameras:
            QMessageBox.critical(self, "Error", "No camera found.")
            return
        self._settings.camera_id = self._cam_combo.currentData()
        self._distraction_overlay = DistractionOverlay(self)

        self._camera_widget.start_detection(self._settings)
        worker = self._camera_widget.worker
        if worker:
            worker.status_update.connect(self._on_status_update)
            worker.distraction_alert.connect(self._on_distraction_alert)
            worker.distraction_start.connect(self._on_distraction_start)
            worker.distraction_end.connect(self._on_distraction_end)
            worker.thread_error.connect(self._on_worker_error)

        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._cam_combo.setEnabled(False)
        self._stats_widget.reset_session()
        self._set_sched_status("")

    def _stop_detection(self):
        self._camera_widget.stop_detection()
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._cam_combo.setEnabled(True)
        if self._distraction_banner:
            self._distraction_banner.hide()
        self._status_bar.showMessage("Detection stopped")

    def _switch_camera(self):
        if self._camera_widget and self._camera_widget.worker:
            self._settings.camera_id = self._cam_combo.currentData()
            self._camera_widget.worker.update_settings(self._settings)

    def _toggle_side_panel(self):
        self._side_visible = not self._side_visible
        self._settings.side_panel_visible = self._side_visible
        self._stats_widget.setVisible(self._side_visible)
        self._side_action.setChecked(self._side_visible)
        self._settings.save()

    # ── 用户 ──

    def _switch_user(self):
        name, ok = QInputDialog.getText(self, "Switch User", "Enter username:",
                                         QLineEdit.EchoMode.Normal, self._username)
        if ok and name and name.strip():
            self._set_username(name.strip())

    def _register_user(self):
        login = LoginDialog(self, self._cam_combo.currentData())
        if login.exec() == LoginDialog.DialogCode.Accepted:
            name = login.get_username()
            if name:
                self._set_username(name)

    def _set_username(self, name: str):
        self._username = name
        self._settings.last_username = name
        self._settings.save()
        self._update_user_label()

    # ── 设置与主题 ──

    def _show_settings(self):
        dialog = SettingsDialog(self._settings, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self._settings = dialog.get_settings()
            for key, a in self._theme_actions.items():
                a.setChecked(key == self._settings.theme_name)
            apply_theme(QApplication.instance(), self._settings.theme_name)
            self._apply_widget_styles()
            if self._camera_widget and self._camera_widget.worker:
                self._camera_widget.worker.update_settings(self._settings)

    def _show_automation(self):
        dialog = SchedulerDialog(self._settings, self)
        if dialog.exec() == SchedulerDialog.DialogCode.Accepted:
            self._settings = dialog.get_settings()

    def _switch_theme(self, theme_name: str):
        self._settings.theme_name = theme_name
        for key, a in self._theme_actions.items():
            a.setChecked(key == theme_name)
        apply_theme(QApplication.instance(), theme_name)
        self._apply_widget_styles()
        self._settings.save()

    # ── 自动化调度 ──

    def _set_sched_status(self, msg: str):
        self._sched_label.setText(msg)

    def _check_schedule(self):
        if not self._settings.schedule_enabled:
            return
        now = datetime.datetime.now()
        cur_min = now.hour * 60 + now.minute
        start_min = self._settings.schedule_start_hour * 60 + self._settings.schedule_start_minute
        end_min = self._settings.schedule_end_hour * 60 + self._settings.schedule_end_minute
        in_window = start_min <= cur_min <= end_min
        is_running = self._camera_widget and self._camera_widget.worker is not None

        if in_window and not is_running and self._start_btn.isEnabled():
            # 自动启动（用户没有手动停止的话）
            self._set_sched_status("⏰ Auto-start")
            self._start_detection()
        elif not in_window and is_running and not self._start_btn.isEnabled():
            # 自动停止
            self._set_sched_status("⏰ Auto-stop")
            self._stop_detection()

    # ── 帮助 ──

    def _show_about(self):
        QMessageBox.about(self, "About FocusCam",
            "FocusCam v2.0\n\n"
            "Real-time distraction detection using\n"
            "MediaPipe FaceMesh & OpenCV.\n\n"
            "Built with PyQt6 · Fusion Style\n"
            "Multi-theme · SVG Icons · Automation")

    def _show_guide(self):
        QMessageBox.information(self, "How to Use",
            "1. Select your camera\n"
            "2. Click Start Detection\n"
            "3. The app tracks your focus in real-time\n"
            "4. Get alerted when distracted\n\n"
            "User → Switch/Register users\n"
            "View → Toggle side panel / Theme\n"
            "Settings → Customize thresholds\n"
            "Automation → Schedule detection times\n\n"
            "Tip: Close eyes or look away to trigger alerts.")

    # ── 信号处理 ──

    def _on_status_update(self, text: str, color: str):
        self._stats_widget.update_state(text)

    def _on_distraction_alert(self, degree: float, duration: float):
        try:
            if self._distraction_banner:
                self._distraction_banner.show_alert(degree, duration)
            m = self._settings.alert_method
            if m in ("sound", "toast_and_sound"):
                self._play_alert_sound()
            if self._settings.log_to_csv:
                state = "eyes_closed" if self._stats_widget._state_cap.text().startswith("○") else "no_face"
                self._logger.log(f"Distraction: {state}", degree, duration)
        except Exception as e:
            import traceback
            print(f"[FocusCam] Alert error: {e}\n{traceback.format_exc()}")

    def _on_distraction_start(self, degree: float, duration: float):
        self._stats_widget.increment_distraction()
        self._stats_widget.log_event(f"Distraction started ({degree:.0f}%)")
        if self._settings.log_to_csv:
            self._logger.log("Distraction started", degree, duration)

    def _on_worker_error(self, msg: str):
        self._stop_detection()
        self._status_bar.showMessage("Detection stopped (error)")
        print(f"[FocusCam] Worker error: {msg}")

    def _on_distraction_end(self):
        pass

    def _play_alert_sound(self):
        try:
            import winsound
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "resources", "sounds", "alert.wav")
            if os.path.exists(path):
                winsound.PlaySound(path, winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            else:
                winsound.Beep(880, 120)
                winsound.Beep(660, 120)
        except Exception:
            pass

    def _sync_stats(self):
        if self._camera_widget and self._camera_widget.worker:
            self._stats_widget.update_degree(self._camera_widget.worker.distraction_degree)

    def closeEvent(self, event):
        self._settings.last_username = self._username or ""
        self._camera_widget.stop_detection()
        self._settings.save()
        event.accept()
