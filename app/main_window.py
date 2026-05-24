"""FocusCam 主窗口 — PyQt6 桌面应用

整合摄像头画面、检测逻辑、设置面板、分心提醒、统计面板。
替代原项目 focuscam.py 的全部 tkinter UI。
"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QMessageBox,
    QStatusBar, QApplication, QSplitter,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont

from config.settings import FocusCamSettings
from core.camera_manager import get_available_cameras
from app.camera_widget import CameraWidget
from app.settings_dialog import SettingsDialog
from app.login_dialog import LoginDialog
from app.distraction_overlay import DistractionOverlay
from app.statistics_widget import StatisticsWidget
from app.theme import apply_theme
from utils.logger import DistractionLogger


class MainWindow(QMainWindow):
    """FocusCam 主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FocusCam")
        self.setMinimumSize(900, 620)

        # 配置和日志
        self._settings = FocusCamSettings.load()
        self._logger = DistractionLogger()
        self._username: str | None = None
        self._distraction_overlay: DistractionOverlay | None = None

        # 构建 UI
        self._build_menu_bar()
        self._build_central()
        self._build_status_bar()
        self._connect_signals()

        # 定时器：同步统计信息
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._sync_stats)
        self._stats_timer.start(500)

    # ────────────────── UI 构建 ──────────────────

    def _build_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        login_action = QAction("Login...", self)
        login_action.triggered.connect(self._show_login)
        file_menu.addAction(login_action)

        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        self._dark_mode_action = QAction("Toggle Dark Mode", self)
        self._dark_mode_action.setCheckable(True)
        self._dark_mode_action.setChecked(self._settings.dark_mode)
        self._dark_mode_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self._dark_mode_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # 左侧：视频 + 控制
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 4, 0)

        # 摄像头选择行
        cam_row = QHBoxLayout()
        cam_row.addWidget(QLabel("Camera:"))
        self._cam_combo = QComboBox()
        self._available_cameras = get_available_cameras()
        for c in self._available_cameras:
            self._cam_combo.addItem(f"Camera {c}", c)
        # 选中已保存的 camera_id
        saved_idx = self._cam_combo.findData(self._settings.camera_id)
        if saved_idx >= 0:
            self._cam_combo.setCurrentIndex(saved_idx)
        self._cam_combo.currentIndexChanged.connect(self._switch_camera)
        cam_row.addWidget(self._cam_combo)
        cam_row.addStretch()

        # 控制按钮
        self._start_btn = QPushButton("▶ Start Detection")
        self._start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b8a3e; color: white;
                border: none; border-radius: 6px; padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2f9e44; }
            QPushButton:disabled { background-color: #adb5bd; }
        """)
        self._start_btn.clicked.connect(self._start_detection)
        cam_row.addWidget(self._start_btn)

        self._stop_btn = QPushButton("■ Stop")
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8590c; color: white;
                border: none; border-radius: 6px; padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #f76707; }
            QPushButton:disabled { background-color: #adb5bd; }
        """)
        self._stop_btn.clicked.connect(self._stop_detection)
        self._stop_btn.setEnabled(False)
        cam_row.addWidget(self._stop_btn)

        self._settings_btn = QPushButton("⚙ Settings")
        self._settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c7cfa; color: white;
                border: none; border-radius: 6px; padding: 6px 12px;
            }
            QPushButton:hover { background-color: #748ffc; }
        """)
        self._settings_btn.clicked.connect(self._show_settings)
        cam_row.addWidget(self._settings_btn)

        left_layout.addLayout(cam_row)

        # 摄像头画面
        self._camera_widget = CameraWidget()
        left_layout.addWidget(self._camera_widget, stretch=1)

        # 右侧：统计面板
        self._stats_widget = StatisticsWidget()
        self._stats_widget.setFixedWidth(220)

        # 左右分割
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

        self._user_label = QLabel("Not logged in")
        self._user_label.setStyleSheet("color: #868e96; padding-right: 8px;")
        self._status_bar.addPermanentWidget(self._user_label)

    def _connect_signals(self):
        """连接检测线程的信号到 UI 处理"""
        pass  # 在 start_detection 时动态连接

    # ────────────────── 操作 ──────────────────

    def _start_detection(self):
        # 检查摄像头
        if not self._available_cameras:
            QMessageBox.critical(self, "Error", "No camera found.")
            return

        # 登录（如果还未登录）
        if not self._username:
            self._show_login()
            if not self._username:
                return

        # 更新 camera_id
        self._settings.camera_id = self._cam_combo.currentData()

        # 初始化分心提醒覆盖层
        self._distraction_overlay = DistractionOverlay(self)

        # 启动摄像头检测
        self._camera_widget.start_detection(self._settings)
        worker = self._camera_widget.worker
        if worker:
            worker.status_update.connect(self._on_status_update)
            worker.distraction_alert.connect(self._on_distraction_alert)
            worker.distraction_start.connect(self._on_distraction_start)
            worker.distraction_end.connect(self._on_distraction_end)

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
        if self._distraction_overlay:
            self._distraction_overlay.hide()
        self._status_bar.showMessage("Detection stopped")

    def _switch_camera(self):
        if hasattr(self, "_camera_widget") and self._camera_widget.worker:
            self._settings.camera_id = self._cam_combo.currentData()
            self._camera_widget.worker.update_settings(self._settings)

    def _show_login(self):
        login = LoginDialog(self, self._cam_combo.currentData())
        if login.exec() == LoginDialog.DialogCode.Accepted:
            self._username = login.get_username()
            self._user_label.setText(f"👤 {self._username}")
            self._user_label.setStyleSheet("color: #2b8a3e; padding-right: 8px;")

    def _show_settings(self):
        dialog = SettingsDialog(self._settings, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self._settings = dialog.get_settings()
            self._dark_mode_action.setChecked(self._settings.dark_mode)
            apply_theme(QApplication.instance(), self._settings.dark_mode)
            if self._camera_widget and self._camera_widget.worker:
                self._camera_widget.worker.update_settings(self._settings)

    def _toggle_theme(self):
        self._settings.dark_mode = self._dark_mode_action.isChecked()
        apply_theme(QApplication.instance(), self._settings.dark_mode)
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
        color_map = {
            "green": "#2b8a3e",
            "orange": "#e8590c",
            "red": "#c92a2a",
            "blue": "#1971c2",
        }
        html_color = color_map.get(color, "#333")
        self._stats_widget.update_state(text)

    def _on_distraction_alert(self, degree: float, duration: float):
        """分心提醒 — 非模态"""
        if self._distraction_overlay:
            self._distraction_overlay.show_alert(degree, duration)

        # 播放提示音
        method = self._settings.alert_method
        if method in ("sound", "toast_and_sound"):
            self._play_alert_sound()

        # 日志
        if self._settings.log_to_csv:
            state = "eyes_closed" if "Eyes" in self._stats_widget._state_label.text() else "no_face"
            self._logger.log(f"Distraction: {state}", degree, duration)

    def _on_distraction_start(self, degree: float, duration: float):
        self._stats_widget.increment_distraction()
        # 首次分心也记录日志
        if self._settings.log_to_csv:
            self._logger.log("Distraction started", degree, duration)

    def _on_distraction_end(self):
        pass

    def _play_alert_sound(self):
        """播放提示音（使用系统 bell 或 wav 文件）"""
        try:
            sound_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "resources", "sounds", "alert.wav",
            )
            if os.path.exists(sound_path):
                import winsound
                winsound.PlaySound(sound_path, winsound.SND_ASYNC)
            else:
                # 系统提示音
                QApplication.beep()
        except Exception:
            QApplication.beep()

    def _sync_stats(self):
        """定期同步统计信息"""
        if self._camera_widget and self._camera_widget.worker:
            self._stats_widget.update_degree(self._camera_widget.worker.distraction_degree)

    def closeEvent(self, event):
        self._camera_widget.stop_detection()
        self._settings.save()
        event.accept()
