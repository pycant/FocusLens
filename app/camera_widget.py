"""摄像头画面显示组件 + 检测线程"""
import os
import traceback
import cv2
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap

# QPixmap 不是线程安全的，工作线程只传 QImage
# 主线程再转成 QPixmap

from core.detector import EyeDetector
from core.distraction_engine import DistractionEngine, FocusState
from core.camera_manager import CameraManager
from config.settings import FocusLensSettings

# 崩溃日志文件（用于捕获 C++ 层闪退）
_CRASH_LOG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "crash_debug.log",
)


def _log_debug(msg: str):
    """写入调试日志，捕获 Python 无法拦截的 C++ 崩溃"""
    try:
        with open(_CRASH_LOG, "a") as f:
            f.write(f"{msg}\n")
    except Exception:
        pass


class DetectionWorker(QThread):
    """后台检测线程 — 持续读取摄像头 + MediaPipe 处理"""

    frame_ready = pyqtSignal(QImage)  # QImage 线程安全，QPixmap 不是
    status_update = pyqtSignal(str, str)
    distraction_alert = pyqtSignal(float, float)
    distraction_start = pyqtSignal(float, float)
    distraction_end = pyqtSignal()
    thread_error = pyqtSignal(str)

    def __init__(self, settings: FocusLensSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._running = False
        self._detector = EyeDetector()
        self._camera = CameraManager(settings.camera_id)
        self._engine = DistractionEngine(settings)

        self._engine.on_distraction_start = self._on_distraction_start
        self._engine.on_distraction_end = self._on_distraction_end
        self._engine.on_alert = self._on_alert

    def _on_distraction_start(self, event):
        self.distraction_start.emit(event.degree, event.duration)

    def _on_distraction_end(self):
        self.distraction_end.emit()

    def _on_alert(self, event):
        # 警报限流由 DistractionEngine.alert_cooldown 控制
        self.distraction_alert.emit(event.degree, event.duration)

    def run(self):
        _log_debug("[WORKER] started")
        try:
            self._camera.open(self.settings.camera_id)
            self._running = True
            _log_debug("[WORKER] camera opened")

            while self._running:
                try:
                    if not self._camera.is_opened:
                        self.status_update.emit("Camera disconnected", "red")
                        self.msleep(100)
                        continue

                    ret, frame = self._camera.read()
                    if not ret or frame is None:
                        self.status_update.emit("Failed to grab frame", "red")
                        self.msleep(10)
                        continue

                    results = self._detector.process_frame(frame)
                    face_detected = False
                    eyes_open = False

                    if results and results.multi_face_landmarks:
                        face_detected = True
                        for face_landmarks in results.multi_face_landmarks:
                            self._detector.draw_landmarks(frame, face_landmarks)
                            eyes_open = self._detector.is_eyes_open(
                                face_landmarks, self.settings.eye_openness_threshold
                            )

                    state = self._engine.update(face_detected, eyes_open)

                    if self.settings.mirror_display:
                        frame = cv2.flip(frame, 1)

                    # UI 显示基于真实检测结果，不是引擎状态
                    if not face_detected:
                        self.status_update.emit("Status: No Face", "red")
                    elif not eyes_open:
                        self.status_update.emit(
                            f"Status: Eyes Closed ({self._engine.get_state_duration():.1f}s)",
                            "orange",
                        )
                    else:
                        self.status_update.emit("Status: Focused ✅", "green")

                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb.shape
                    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
                    self.frame_ready.emit(qimg.copy())  # copy() 确保数据独立

                    self.msleep(30)

                except Exception as e:
                    self.status_update.emit(f"Frame error", "red")
                    _log_debug(f"[WORKER] frame loop error: {e}")
                    self.msleep(100)

        except Exception as e:
            tb = traceback.format_exc()
            _log_debug(f"[WORKER] fatal error: {e}")
            self.thread_error.emit(f"Detection thread crashed:\n{tb}")
        finally:
            _log_debug("[WORKER] cleanup start")
            self._cleanup()
            _log_debug("[WORKER] cleanup done")

    def _cleanup(self):
        try:
            self._camera.close()
        except Exception:
            pass
        try:
            self._detector.close()
        except Exception:
            pass

    def stop(self):
        self._running = False
        if not self.wait(2000):
            self.terminate()

    def update_settings(self, settings: FocusLensSettings):
        self.settings = settings
        self._engine.settings = settings
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
        self._camera_bg = "#1e1e1e"
        self._video_label.setStyleSheet(f"background-color: {self._camera_bg}; border-radius: 8px;")
        self._video_label.setMinimumSize(640, 480)
        layout.addWidget(self._video_label)

    def start_detection(self, settings: FocusLensSettings):
        self.stop_detection()
        self._worker = DetectionWorker(settings)
        self._worker.frame_ready.connect(self._display_frame)
        self._worker.thread_error.connect(self._on_thread_error)
        self._worker.start()

    def stop_detection(self):
        if self._worker:
            w = self._worker
            self._worker = None
            if w.isRunning():
                w.stop()
        self._video_label.clear()

    def _on_thread_error(self, msg: str):
        print(f"[FocusLens Worker Error] {msg}")
        self.stop_detection()

    def _display_frame(self, qimg: QImage):
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self._video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._video_label.setPixmap(scaled)

    @property
    def worker(self) -> DetectionWorker | None:
        return self._worker

    def set_bg_color(self, color_hex: str):
        self._camera_bg = color_hex
        self._video_label.setStyleSheet(
            f"background-color: {color_hex}; border-radius: 8px;"
        )

    def closeEvent(self, event):
        self.stop_detection()
        super().closeEvent(event)
