"""眼睛检测核心算法 — 从原 FocusLens 移植

保留原始的 MediaPipe FaceMesh 检测逻辑，
支持可配置的眼睛睁开敏感度阈值。
"""
import cv2 as cv
import mediapipe as mp


class EyeDetector:
    """使用 MediaPipe FaceMesh 检测人脸和眼睛状态"""

    # MediaPipe 面部特征点索引（原项目使用）
    LEFT_EYE_TOP = 159
    LEFT_EYE_BOTTOM = 145
    RIGHT_EYE_TOP = 386
    RIGHT_EYE_BOTTOM = 374

    def __init__(self):
        mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)
        self.mp_face_mesh = mp_face_mesh
        self.mp_drawing = mp.solutions.drawing_utils

    def process_frame(self, frame_bgr):
        """处理 BGR 帧，返回检测结果"""
        frame_rgb = cv.cvtColor(frame_bgr, cv.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)
        return results

    def draw_landmarks(self, frame, face_landmarks):
        """在帧上绘制面部网格"""
        self.mp_drawing.draw_landmarks(
            image=frame,
            landmark_list=face_landmarks,
            connections=self.mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=self.mp_drawing.DrawingSpec(
                color=(0, 255, 0), thickness=1, circle_radius=1
            ),
        )

    def is_eyes_open(self, face_landmarks, threshold: float = 0.015) -> bool:
        """检测眼睛是否睁开

        基于原项目逻辑：通过上下眼睑特征点的 y 坐标差值判断。
        threshold 越小越敏感（更容易判定为睁眼）。

        Args:
            face_landmarks: MediaPipe 面部特征点
            threshold: 眼睛睁开阈值（原项目硬编码 0.015）

        Returns:
            True 表示双眼睁开
        """
        left_openness = abs(
            face_landmarks.landmark[self.LEFT_EYE_TOP].y
            - face_landmarks.landmark[self.LEFT_EYE_BOTTOM].y
        )
        right_openness = abs(
            face_landmarks.landmark[self.RIGHT_EYE_TOP].y
            - face_landmarks.landmark[self.RIGHT_EYE_BOTTOM].y
        )
        return left_openness > threshold and right_openness > threshold

    def get_eye_openness_score(self, face_landmarks) -> float:
        """返回眼睛睁开程度评分 (0.0 ~ 1.0)，用于计算分心程度"""
        left = abs(
            face_landmarks.landmark[self.LEFT_EYE_TOP].y
            - face_landmarks.landmark[self.LEFT_EYE_BOTTOM].y
        )
        right = abs(
            face_landmarks.landmark[self.RIGHT_EYE_TOP].y
            - face_landmarks.landmark[self.RIGHT_EYE_BOTTOM].y
        )
        avg = (left + right) / 2.0
        # 映射到 0-1 范围，0.03 大约对应完全睁眼
        return min(avg / 0.03, 1.0)

    def close(self):
        if self.face_mesh:
            self.face_mesh.close()
