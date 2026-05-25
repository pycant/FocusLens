import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CONFIG_DIR)
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "default_settings.json")
USER_CONFIG_PATH = os.path.join(PROJECT_DIR, "settings.json")

# 提醒方式枚举
ALERT_METHODS = {
    "toast": "悬浮提醒（非模态）",
    "sound": "提示音",
    "system_notification": "系统通知",
    "toast_and_sound": "悬浮提醒 + 提示音",
    "log_only": "仅记录到日志",
}

# 反馈行为枚举
FEEDBACK_ACTIONS = {
    "continue": "继续检测",
    "pause": "暂停检测",
    "minimize": "最小化到托盘",
}


@dataclass
class FocusLensSettings:
    # --- 分心检测参数 ---
    distraction_time_threshold: float = 2.0  # 闭眼/无人脸持续几秒算分心（1-10秒）
    eye_openness_threshold: float = 0.015    # 眼睛睁开敏感度（0.005-0.05）
    distraction_degree_threshold: float = 50.0  # 分心程度阈值(0-100)，超过此值触发提醒
    no_face_is_distraction: bool = True     # 无人脸是否算分心

    # --- 分心程度权重 ---
    eyes_closed_weight: float = 1.0     # 闭眼分心权重
    no_face_weight: float = 1.5         # 无人脸分心权重（离席更严重）
    distraction_decay_rate: float = 2.0  # 分心程度衰减速度（恢复到专注状态的速度）

    # --- 提醒设置 ---
    alert_method: str = "toast_and_sound"  # 提醒方式
    alert_cooldown: float = 10.0          # 两次提醒之间的最短间隔（秒）
    feedback_action: str = "continue"       # 分心后的反馈行为

    # --- 用户设置 ---
    last_username: str = ""

    # --- 摄像头设置 ---
    camera_id: int = 0
    mirror_display: bool = True

    # --- 日志设置 ---
    log_to_csv: bool = True
    log_to_db: bool = False

    # --- 自动化设置 ---
    auto_start_on_boot: bool = False
    schedule_enabled: bool = False
    schedule_start_hour: int = 9
    schedule_start_minute: int = 0
    schedule_end_hour: int = 17
    schedule_end_minute: int = 0
    schedule_work_minutes: int = 25
    schedule_break_minutes: int = 5

    # --- 显示设置 ---
    theme_name: str = "classic_light"
    side_panel_visible: bool = True

    @classmethod
    def load(cls) -> "FocusLensSettings":
        path = USER_CONFIG_PATH if os.path.exists(USER_CONFIG_PATH) else DEFAULT_CONFIG_PATH
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except (json.JSONDecodeError, TypeError, ValueError):
            return cls()

    def save(self):
        with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    def get_distraction_time_ms(self) -> int:
        return int(self.distraction_time_threshold * 1000)
