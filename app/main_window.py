"""FocusCam 主窗口 — PyQt6 桌面应用"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QMessageBox,
    QStatusBar, QApplication, QSplitter, QInputDialog,
    QLineEdit,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont, QIcon

from config.settings import FocusCamSettings
from core.camera_manager import get_available_cameras
from app.camera_widget import CameraWidget
from app.settings_dialog import SettingsDialog
from app.login_dialog import LoginDialog
from app.distraction_overlay import DistractionOverlay
from app.statistics_widget import StatisticsWidget
from app.theme import apply_theme, THEMES, get_camera_bg, make_button_style
from utils.logger import DistractionLogger

DEFAULT_USER = "Default User"
ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icons")


def _icon(name: str) -> QIcon:
    return QIcon(os.path.join(ICONS_DIR, f"{name}.svg"))


class MainWindow(QMainWindow):
    """FocusCam 主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FocusCam")
        self.setWindowIcon(_icon("focus"))
        self.setMinimumSize(900, 620)

        # 配置和日志
        self._settings = FocusCamSettings.load()
        self._logger = DistractionLogger()

        # 自动使用上次登录用户（无需弹登录框）
        self._username = self._settings.last_username or DEFAULT_USER

        # 构建 UI
        self._build_menu_bar()
        self._build_central()
        self._build_status_bar()

        # 应用按钮配色
        self._apply_widget_styles()

        # 定时器：同步统计信息
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._sync_stats)
        self._stats_timer.start(500)

    # ────────────────── UI 构建 ──────────────────

    def _build_menu_bar(self):
        menubar = self.menuBar()

        user_menu = menubar.addMenu("User")
        switch_action = QAction("Switch User...", self)
        switch_action.setIcon(_icon("user"))
        switch_action.triggered.connect(self._switch_user)
        user_menu.addAction(switch_action)

        register_action = QAction("Register New User (Face Capture)...", self)
        register_action.setIcon(_icon("user"))
        register_action.triggered.connect(self._register_user)
        user_menu.addAction(register_action)
        user_menu.addSeparator()

        settings_action = QAction("Settings...", self)
        settings_action.setIcon(_icon("settings"))
        settings_action.triggered.connect(self._show_settings)
        user_menu.addAction(settings_action)
        user_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setIcon(_icon("stop"))
        exit_action.triggered.connect(self.close)
        user_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        self._theme_actions = {}
        for key, meta in THEMES.items():
            a = QAction(meta["label"], self)
            a.setCheckable(True)
            a.setChecked(key == self._settings.theme_name)
            a.triggered.connect(lambda checked, k=key: self._switch_theme(k))
            view_menu.addAction(a)
            self._theme_actions[key] = a

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 4, 0)

        # 顶部控制栏
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
        self._start_btn.setIcon(_icon("play"))
        self._start_btn.setIconSize(Qt.QSize(16, 16))
        self._start_btn.clicked.connect(self._start_detection)
        cam_row.addWidget(self._start_btn)

        self._stop_btn = QPushButton(" Stop")
        self._stop_btn.setIcon(_icon("stop"))
        self._stop_btn.setIconSize(Qt.QSize(16, 16))
        self._stop_btn.clicked.connect(self._stop_detection)
        self._stop_btn.setEnabled(False)
        cam_row.addWidget(self._stop_btn)

        self._settings_btn = QPushButton(" Settings")
        self._settings_btn.setIcon(_icon("settings"))
        self._settings_btn.setIconSize(Qt.QSize(16, 16))
        self._settings_btn.clicked.connect(self._show_settings)
        cam_row.addWidget(self._settings_btn)

        left_layout.addLayout(cam_row)

        # 摄像头画面
        self._camera_widget = CameraWidget()
        left_layout.addWidget(self._camera_widget, stretch=1)

        # 分心提醒横幅（嵌入主窗口，不开新窗口）
        self._distraction_banner = DistractionOverlay()
        self._distraction_banner.hide()
        left_layout.addWidget(self._distraction_banner)

        # 右侧统计面板
        self._stats_widget = StatisticsWidget()
        self._stats_widget.setFixedWidth(220)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self._stats_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

    def _build_status_bar(self):
        self._status_bar = QStatusBar()
        self._status_bar.showMessage("Ready — click Start Detection to begin")
        self.setStatusBar(self._status_bar)

        self._user_icon = QLabel()
        self._user_icon.setPixmap(_icon("user").pixmap(16, 16))
        self._user_icon.setStyleSheet("padding-right: 2px;")
        self._status_bar.addPermanentWidget(self._user_icon)

        self._user_label = QLabel()
        self._update_user_label()
        self._user_label.setStyleSheet("padding-right: 8px;")
        self._status_bar.addPermanentWidget(self._user_label)

    def _apply_widget_styles(self):
        """根据当前主题更新按钮和摄像头背景色"""
        theme = self._settings.theme_name
        self._start_btn.setStyleSheet(make_button_style("#2b8a3e", "#2f9e44"))
        self._stop_btn.setStyleSheet(make_button_style("#e8590c", "#f76707"))
        self._settings_btn.setStyleSheet(make_button_style("#5c7cfa", "#748ffc"))
        # 摄像头背景
        if hasattr(self, "_camera_widget"):
            self._camera_widget.set_bg_color(get_camera_bg(theme))

    def _update_user_label(self):
        name = self._username or DEFAULT_USER
        self._user_label.setText(f" {name}")

    # ────────────────── 操作 ──────────────────

    def _start_detection(self):
        if not self._available_cameras:
            QMessageBox.critical(self, "Error", "No camera found.")
            return

        self._settings.camera_id = self._cam_combo.currentData()

        # overlay now embedded as self._distraction_banner in _build_central

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
        self._status_bar.showMessage(f"Detection running — User: {self._username}")

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

    # ──────────── 用户管理 ────────────

    def _switch_user(self):
        """简易切换用户：只输用户名，不弹摄像头"""
        name, ok = QInputDialog.getText(
            self, "Switch User", "Enter username:",
            QLineEdit.EchoMode.Normal, self._username,
        )
        if ok and name and name.strip():
            self._set_username(name.strip())

    def _register_user(self):
        """注册新用户：带摄像头人脸拍照"""
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
        self._status_bar.showMessage(f"User: {self._username}")

    # ──────────── 设置与主题 ────────────

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

    def _switch_theme(self, theme_name: str):
        self._settings.theme_name = theme_name
        for key, a in self._theme_actions.items():
            a.setChecked(key == theme_name)
        apply_theme(QApplication.instance(), theme_name)
        self._apply_widget_styles()
        apply_theme(QApplication.instance(), theme_name)
        self._settings.save()

    def _show_about(self):
        QMessageBox.about(
            self, "About FocusCam",
            "FocusCam v2.0\n\n"
            "Real-time distraction detection using\n"
            "MediaPipe FaceMesh & OpenCV.\n\n"
            "Built with PyQt6",
        )

    # ────────────────── 信号处理 ──────────────────

    def _on_status_update(self, text: str, color: str):
        self._stats_widget.update_state(text)

    def _on_distraction_alert(self, degree: float, duration: float):
        try:
            if self._distraction_banner:
                self._distraction_banner.show_alert(degree, duration)

            method = self._settings.alert_method
            if method in ("sound", "toast_and_sound"):
                self._play_alert_sound()

            if self._settings.log_to_csv:
                state = "eyes_closed" if self._stats_widget.is_eyes_closed_state() else "no_face"
                self._logger.log(f"Distraction: {state}", degree, duration)
        except Exception as e:
            import traceback
            print(f"[FocusCam] Alert error: {e}\n{traceback.format_exc()}")

    def _on_distraction_start(self, degree: float, duration: float):
        self._stats_widget.increment_distraction()
        if self._settings.log_to_csv:
            self._logger.log("Distraction started", degree, duration)

    def _on_worker_error(self, msg: str):
        """检测线程崩溃时，自动停止并提示用户"""
        self._stop_detection()
        self._status_bar.showMessage("Detection stopped (thread error)")
        print(f"[FocusCam] Worker error: {msg}")

    def _on_distraction_end(self):
        pass

    def _play_alert_sound(self):
        """播放提示音 — WAV → Beep 回退"""
        try:
            import winsound
            path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "resources", "sounds", "alert.wav",
            )
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
        # 保存最后使用的用户名
        self._settings.last_username = self._username or ""
        self._camera_widget.stop_detection()
        self._settings.save()
        event.accept()
