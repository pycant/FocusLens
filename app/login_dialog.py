"""PyQt6 登录对话框 — 用户名输入 + 人脸拍照"""
import cv2 as cv
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QMessageBox,
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap

from core.camera_manager import get_available_cameras
from utils.database import save_face_image, save_user_to_db


class LoginDialog(QDialog):
    def __init__(self, parent=None, camera_id: int = 0):
        super().__init__(parent)
        self.setWindowTitle("Login - Face Capture")
        self.setMinimumSize(480, 420)
        self.setModal(True)

        self._result_username: str | None = None
        self._camera_id = camera_id
        self._cap = cv.VideoCapture(camera_id)
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_frame)

        self._build_ui()
        self._timer.start(30)

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Username input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Username:"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Enter your username")
        name_layout.addWidget(self._name_input)
        layout.addLayout(name_layout)

        # Camera selector
        cam_layout = QHBoxLayout()
        cam_layout.addWidget(QLabel("Camera:"))
        self._cam_combo = QComboBox()
        cameras = get_available_cameras()
        for c in cameras:
            self._cam_combo.addItem(f"Camera {c}", c)
        if self._camera_id in cameras:
            self._cam_combo.setCurrentIndex(cameras.index(self._camera_id))
        self._cam_combo.currentIndexChanged.connect(self._switch_camera)
        cam_layout.addWidget(self._cam_combo)
        cam_layout.addStretch()
        layout.addLayout(cam_layout)

        # Video display
        self._video_label = QLabel()
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setMinimumHeight(280)
        layout.addWidget(self._video_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self._capture_btn = QPushButton("📸 Capture & Login")
        self._capture_btn.clicked.connect(self._capture)
        btn_layout.addWidget(self._capture_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)
        layout.addLayout(btn_layout)

    def _switch_camera(self):
        idx = self._cam_combo.currentIndex()
        new_id = self._cam_combo.itemData(idx)
        if new_id is not None and new_id != self._camera_id:
            self._camera_id = new_id
            self._timer.stop()
            self._cap.release()
            self._cap = cv.VideoCapture(new_id)
            self._timer.start(30)

    def _update_frame(self):
        if self._cap is None or not self._cap.isOpened():
            return
        ret, frame = self._cap.read()
        if ret:
            rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self._video_label.setPixmap(
                QPixmap.fromImage(qimg).scaled(
                    460, 280, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def _capture(self):
        username = self._name_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Warning", "Username cannot be empty.")
            return

        ret, frame = self._cap.read()
        if not ret:
            QMessageBox.critical(self, "Error", "Failed to capture image.")
            return

        image_path = save_face_image(username, frame)
        ok = save_user_to_db(username, image_path)
        if ok:
            QMessageBox.information(
                self, "Success",
                f"User '{username}' registered.\nImage: {image_path}",
            )
        else:
            QMessageBox.warning(
                self, "Warning",
                f"User '{username}' saved locally, but DB save failed.",
            )

        self._result_username = username
        self.accept()

    def get_username(self) -> str | None:
        return self._result_username

    def closeEvent(self, event):
        self._timer.stop()
        if self._cap:
            self._cap.release()
        super().closeEvent(event)
