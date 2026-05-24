"""摄像头管理模块 — 从原项目移植并改进"""
import cv2 as cv
from typing import List, Optional


def get_available_cameras(max_test: int = 5) -> List[int]:
    """枚举可用的摄像头索引"""
    cameras = []
    for i in range(max_test):
        cap = cv.VideoCapture(i)
        if cap.isOpened():
            cameras.append(i)
            cap.release()
    return cameras if cameras else [0]


class CameraManager:
    """摄像头管理器 — 支持打开、切换、释放"""

    def __init__(self, camera_id: int = 0):
        self._camera_id = camera_id
        self._cap: Optional[cv.VideoCapture] = None

    @property
    def camera_id(self) -> int:
        return self._camera_id

    def open(self, camera_id: Optional[int] = None):
        if camera_id is not None:
            self._camera_id = camera_id
        self.close()
        self._cap = cv.VideoCapture(self._camera_id)

    def read(self):
        if self._cap is None or not self._cap.isOpened():
            return False, None
        return self._cap.read()

    def switch(self, new_id: int):
        if new_id != self._camera_id:
            self.open(new_id)

    def close(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    @property
    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()
