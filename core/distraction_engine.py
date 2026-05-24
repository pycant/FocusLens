"""可配置的分心状态机

替代原项目 handle_distraction_status() 的硬编码逻辑，
支持：
- 自定义分心持续时间阈值
- 分心程度量化计算（连续值而非二元判断）
- 可配置的分心程度阈值
- 提醒冷却机制
"""
import time
from enum import Enum
from typing import Optional, Callable

from config.settings import FocusCamSettings


class FocusState(Enum):
    FOCUSED = "focused"
    EYES_CLOSED = "eyes_closed"
    NO_FACE = "no_face"


class DistractionEvent:
    """一次分心事件的数据"""

    def __init__(self, degree: float, duration: float, state: FocusState):
        self.degree = degree
        self.duration = duration
        self.state = state
        self.timestamp = time.time()


class DistractionEngine:
    """分心状态机 — 替代原项目的 handle_distraction_status

    状态转换:
        FOCUSED  → (闭眼)   → EYES_CLOSED
        FOCUSED  → (无人脸)  → NO_FACE
        EYES_CLOSED/NO_FACE → (恢复) → FOCUSED
    """

    def __init__(self, settings: FocusCamSettings):
        self.settings = settings

        # 状态
        self.current_state: FocusState = FocusState.FOCUSED
        self.state_start_time: Optional[float] = None
        self.is_distracted = False

        # 分心程度累计
        self._distraction_degree: float = 0.0
        self._last_update_time: float = time.time()

        # 冷却机制
        self._last_alert_time: float = 0.0

        # 回调
        self.on_distraction_start: Optional[Callable[[DistractionEvent], None]] = None
        self.on_distraction_end: Optional[Callable[[], None]] = None
        self.on_alert: Optional[Callable[[DistractionEvent], None]] = None
        self._event: Optional[DistractionEvent] = None

    @property
    def distraction_degree(self) -> float:
        """当前分心程度 (0.0 ~ 100.0)"""
        return min(self._distraction_degree, 100.0)

    def update(self, face_detected: bool, eyes_open: bool) -> FocusState:
        """每帧调用，更新状态和分心程度

        Args:
            face_detected: 是否检测到人脸
            eyes_open: 眼睛是否睁开

        Returns:
            当前专注状态
        """
        now = time.time()
        dt = now - self._last_update_time
        self._last_update_time = now

        previous_state = self.current_state

        # 1. 状态转换
        if not face_detected:
            if self.settings.no_face_is_distraction:
                self.current_state = FocusState.NO_FACE
            # else: 无人脸不算分心 → 保持当前状态不变
        elif not eyes_open:
            self.current_state = FocusState.EYES_CLOSED
        else:
            self.current_state = FocusState.FOCUSED

        # 2. 状态计时
        if self.current_state != previous_state:
            self.state_start_time = now
            # 从不专注 → 专注：分心结束
            if self.current_state == FocusState.FOCUSED and self.is_distracted:
                self.is_distracted = False
                if self.on_distraction_end:
                    self.on_distraction_end()
        elif self.state_start_time is None:
            self.state_start_time = now

        # 3. 计算分心程度
        elapsed = now - self.state_start_time if self.state_start_time else 0

        if self.current_state == FocusState.FOCUSED:
            # 专注状态：分心程度衰减（程度越高衰减越快）
            level = self._distraction_degree / 100.0
            decay = self.settings.distraction_decay_rate * (1.0 + level) * dt
            self._distraction_degree = max(0.0, self._distraction_degree - decay * 5)
            return FocusState.FOCUSED

        # 分心状态：累积分心程度
        if self.current_state == FocusState.EYES_CLOSED:
            weight = self.settings.eyes_closed_weight
        else:  # NO_FACE
            weight = self.settings.no_face_weight

        # 分心程度 = 权重 × 持续时间，上限 100
        self._distraction_degree = min(100.0, self._distraction_degree + weight * dt * 5)

        # 4. 触发分心事件
        if not self.is_distracted and elapsed >= self.settings.distraction_time_threshold:
            self.is_distracted = True
            self._event = DistractionEvent(
                degree=self.distraction_degree,
                duration=elapsed,
                state=self.current_state,
            )
            if self.on_distraction_start:
                self.on_distraction_start(self._event)

        # 5. 判断是否触发提醒（分心程度达标 + 冷却期已过）
        if self.is_distracted:
            can_alert = (now - self._last_alert_time) >= self.settings.alert_cooldown
            degree_ok = self.distraction_degree >= self.settings.distraction_degree_threshold
            if can_alert and degree_ok and self.on_alert:
                self.on_alert(self._event or DistractionEvent(
                    degree=self.distraction_degree,
                    duration=elapsed,
                    state=self.current_state,
                ))
                self._last_alert_time = now

        return self.current_state

    def get_state_duration(self) -> float:
        """当前状态的持续时间（秒）"""
        if self.state_start_time is None:
            return 0.0
        return time.time() - self.state_start_time

    def reset(self):
        """重置所有状态"""
        self.current_state = FocusState.FOCUSED
        self.state_start_time = None
        self.is_distracted = False
        self._distraction_degree = 0.0
        self._event = None
