"""摄像头画面显示组件 + 检测线程"""
import cv2 as cv
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap

from core.detector import EyeDetector
from core.distraction_engine import DistractionEngine, FocusState
from core.camera_manager import CameraManager
from config.settings import FocusCamSettings


class DetectionWorker(QThread):
    """后台检测线程 — 持续读取摄像头 + MediaPipe 处理"""

    frame_ready = pyqtSignal(object)  # QPixmap
    status_update = pyqtSignal(str, str)  # (status_text, color)
    distraction_alert = pyqtSignal(float, float)  # (degree, duration)
    distraction_start = pyqtSignal(float, float)  # (degree, duration)
    distraction_end = pyqtSignal()

    def __init__(self, settings: FocusCamSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._running = False
        self._detector = EyeDetector()
        self._camera = CameraManager(settings.camera_id)
        self._engine = DistractionEngine(settings)

        # Connect engine callbacks
        self._engine.on_distraction_start = self._on_distraction_start
        self._engine.on_distraction_end = self._on_distraction_end
        self._engine.on_alert = self._on_alert

    def _on_distraction_start(self, event):
        self.distraction_start.emit(event.degree, event.duration)

    def _on_distraction_end(self):
        self.distraction_end.emit()

    def _on_alert(self, event):
        self.distraction_alert.emit(event.degree, event.duration)

    def run(self):
        self._camera.open(self.settings.camera_id)
        self._running = True

        while self._running:
            if not self._camera.is_opened:
                self.status_update.emit("Camera disconnected", "red")
                self.msleep(100)
                continue

            ret, frame = self._camera.read()
            if not ret:
                self.status_update.emit("Failed to grab frame", "red")
                self.msleep(10)
                continue

            # --- 检测逻辑（原项目核心算法） ---
            results = self._detector.process_frame(frame)
            face_detected = False
            eyes_open = False

            if results.multi_face_landmarks:
                face_detected = True
                for face_landmarks in results.multi_face_landmarks:
                    self._detector.draw_landmarks(frame, face_landmarks)
                    eyes_open = self._detector.is_eyes_open(
                        face_landmarks, self.settings.eye_openness_threshold
                    )

            # 更新分心状态机
            state = self._engine.update(face_detected, eyes_open)

            # 镜像显示
            if self.settings.mirror_display:
                frame = cv.flip(frame, 1)

            # 状态标签
            if state == FocusState.FOCUSED:
                self.status_update.emit("Status: Focused ✅", "green")
            elif state == FocusState.EYES_CLOSED:
                self.status_update.emit(
                    f"Status: Eyes Closed ({self._engine.get_state_duration():.1f}s)",
                    "orange",
                )
            else:
                self.status_update.emit(
                    f"Status: No Face ({self._engine.get_state_duration():.1f}s)",
                    "red",
                )

            # 发送帧到 UI
            rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.frame_ready.emit(pixmap)

            self.msleep(30)  # ~33 FPS

        self._cleanup()

    def _cleanup(self):
        self._camera.close()
        self._detector.close()

    def stop(self):
        self._running = False
        self.wait(2000)

    def update_settings(self, settings: FocusCamSettings):
        self.settings = settings
        self._engine.settings = settings
        # 如果摄像头 ID 变了，重新连接
        if self._camera.camera_id != settings.camera_id:
            self._camera.open(settings.camera_id)

    @property
    def distraction_degree(self) -> float:
        return self._engine.distraction_degree

    @property
    def engine(self) -> DistractionEngine:
        return self._engine


class CameraWidget(QWidget):
    """摄像头画面显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: DetectionWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._video_label = QLabel()
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setStyleSheet("background-color: #1e1e1e; border-radius: 8px;")
        self._video_label.setMinimumSize(640, 480)
        layout.addWidget(self._video_label)

    def start_detection(self, settings: FocusCamSettings):
        self.stop_detection()
        self._worker = DetectionWorker(settings)
        self._worker.frame_ready.connect(self._display_frame)
        self._worker.start()

    def stop_detection(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker = None
        self._video_label.clear()

    def _display_frame(self, pixmap: QPixmap):
        scaled = pixmap.scaled(
            self._video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._video_label.setPixmap(scaled)

    @property
    def worker(self) -> DetectionWorker | None:
        return self._worker

    def closeEvent(self, event):
        self.stop_detection()
        super().closeEvent(event)
