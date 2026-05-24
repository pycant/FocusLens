"""PyQt6 设置面板 — 所有可配置参数的可视化编辑"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QComboBox, QPushButton, QGroupBox,
    QCheckBox, QFormLayout, QWidget, QTabWidget,
    QSpinBox, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt

from config.settings import FocusCamSettings, ALERT_METHODS, FEEDBACK_ACTIONS


class SettingsDialog(QDialog):
    """设置对话框 — 自定义所有检测和提醒参数"""

    def __init__(self, settings: FocusCamSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FocusCam Settings")
        self.setMinimumWidth(520)
        self._original = settings
        self._settings = FocusCamSettings(
            **{k: v for k, v in vars(settings).items() if not k.startswith("_")}
        )
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # --- Tab 1: 分心检测 ---
        detection_tab = QWidget()
        det_layout = QFormLayout(detection_tab)

        # 分心时间阈值
        time_hbox = QHBoxLayout()
        self._time_spin = QDoubleSpinBox()
        self._time_spin.setRange(0.5, 10.0)
        self._time_spin.setSingleStep(0.5)
        self._time_spin.setValue(self._settings.distraction_time_threshold)
        self._time_spin.setSuffix(" 秒")
        time_hbox.addWidget(self._time_spin)
        time_hbox.addWidget(QLabel("闭眼/无人脸持续多久算分心"))
        det_layout.addRow("分心时间阈值:", time_hbox)

        # 眼睛敏感度
        eye_hbox = QHBoxLayout()
        self._eye_slider = QSlider(Qt.Orientation.Horizontal)
        self._eye_slider.setRange(5, 50)
        self._eye_slider.setValue(int(self._settings.eye_openness_threshold * 1000))
        self._eye_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._eye_slider.setTickInterval(5)
        self._eye_value_label = QLabel(f"{self._settings.eye_openness_threshold:.3f}")
        self._eye_slider.valueChanged.connect(
            lambda v: self._eye_value_label.setText(f"{v / 1000:.3f}")
        )
        eye_hbox.addWidget(self._eye_slider)
        eye_hbox.addWidget(self._eye_value_label)
        eye_hbox.addWidget(QLabel("(越大越敏感)"))
        det_layout.addRow("眼睛敏感度:", eye_hbox)

        # 分心程度阈值
        degree_hbox = QHBoxLayout()
        self._degree_slider = QSlider(Qt.Orientation.Horizontal)
        self._degree_slider.setRange(10, 100)
        self._degree_slider.setValue(int(self._settings.distraction_degree_threshold))
        self._degree_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._degree_slider.setTickInterval(10)
        self._degree_label = QLabel(f"{self._settings.distraction_degree_threshold:.0f}%")
        self._degree_slider.valueChanged.connect(
            lambda v: self._degree_label.setText(f"{v}%")
        )
        degree_hbox.addWidget(self._degree_slider)
        degree_hbox.addWidget(self._degree_label)
        det_layout.addRow("分心程度阈值:", degree_hbox)

        # 无人脸是否算分心
        self._no_face_cb = QCheckBox("No face detected counts as distraction")
        self._no_face_cb.setChecked(self._settings.no_face_is_distraction)
        det_layout.addRow("", self._no_face_cb)

        # 分心权重
        det_layout.addRow(
            "闭眼权重:",
            self._make_weight_spin("eyes_closed_weight", 0.1, 5.0),
        )
        det_layout.addRow(
            "无人脸权重:",
            self._make_weight_spin("no_face_weight", 0.1, 5.0),
        )
        det_layout.addRow(
            "衰减速度:",
            self._make_weight_spin("distraction_decay_rate", 0.1, 10.0),
        )
        tabs.addTab(detection_tab, "Detection")

        # --- Tab 2: 提醒设置 ---
        alert_tab = QWidget()
        alert_layout = QFormLayout(alert_tab)

        self._alert_method = QComboBox()
        for key, label in ALERT_METHODS.items():
            self._alert_method.addItem(label, key)
        idx = self._alert_method.findData(self._settings.alert_method)
        if idx >= 0:
            self._alert_method.setCurrentIndex(idx)
        alert_layout.addRow("提醒方式:", self._alert_method)

        # 冷却时间
        cooldown_hbox = QHBoxLayout()
        self._cooldown_spin = QDoubleSpinBox()
        self._cooldown_spin.setRange(1.0, 300.0)
        self._cooldown_spin.setSingleStep(1.0)
        self._cooldown_spin.setValue(self._settings.alert_cooldown)
        self._cooldown_spin.setSuffix(" 秒")
        cooldown_hbox.addWidget(self._cooldown_spin)
        cooldown_hbox.addWidget(QLabel("两次提醒之间的最短间隔"))
        alert_layout.addRow("提醒冷却:", cooldown_hbox)

        # 反馈行为
        self._feedback_combo = QComboBox()
        for key, label in FEEDBACK_ACTIONS.items():
            self._feedback_combo.addItem(label, key)
        idx = self._feedback_combo.findData(self._settings.feedback_action)
        if idx >= 0:
            self._feedback_combo.setCurrentIndex(idx)
        alert_layout.addRow("分心后行为:", self._feedback_combo)

        tabs.addTab(alert_tab, "Alert")

        # --- Tab 3: 杂项 ---
        misc_tab = QWidget()
        misc_layout = QFormLayout(misc_tab)

        self._mirror_cb = QCheckBox("Enable mirror display")
        self._mirror_cb.setChecked(self._settings.mirror_display)
        misc_layout.addRow("Display:", self._mirror_cb)

        self._log_csv_cb = QCheckBox("Log distractions to CSV")
        self._log_csv_cb.setChecked(self._settings.log_to_csv)
        misc_layout.addRow("Logging:", self._log_csv_cb)

        self._log_db_cb = QCheckBox("Log distractions to Database")
        self._log_db_cb.setChecked(self._settings.log_to_db)
        misc_layout.addRow("", self._log_db_cb)

        # 分隔线
        misc_layout.addRow(QLabel(""))

        # 暗色主题
        self._dark_mode_cb = QCheckBox("Enable dark mode")
        self._dark_mode_cb.setChecked(self._settings.dark_mode)
        misc_layout.addRow("Theme:", self._dark_mode_cb)

        tabs.addTab(misc_tab, "General")

        # --- 按钮 ---
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _make_weight_spin(self, attr: str, min_v: float, max_v: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(min_v, max_v)
        spin.setSingleStep(0.1)
        spin.setValue(getattr(self._settings, attr))
        spin.valueChanged.connect(lambda v: setattr(self._settings, attr, v))
        return spin

    def _save(self):
        self._settings.distraction_time_threshold = self._time_spin.value()
        self._settings.eye_openness_threshold = self._eye_slider.value() / 1000.0
        self._settings.distraction_degree_threshold = float(self._degree_slider.value())
        self._settings.no_face_is_distraction = self._no_face_cb.isChecked()
        self._settings.alert_method = self._alert_method.currentData()
        self._settings.alert_cooldown = self._cooldown_spin.value()
        self._settings.feedback_action = self._feedback_combo.currentData()
        self._settings.mirror_display = self._mirror_cb.isChecked()
        self._settings.log_to_csv = self._log_csv_cb.isChecked()
        self._settings.log_to_db = self._log_db_cb.isChecked()
        self._settings.dark_mode = self._dark_mode_cb.isChecked()
        self._settings.save()
        self.accept()

    def _reset_defaults(self):
        default = FocusCamSettings()
        self._time_spin.setValue(default.distraction_time_threshold)
        self._eye_slider.setValue(int(default.eye_openness_threshold * 1000))
        self._degree_slider.setValue(int(default.distraction_degree_threshold))
        self._no_face_cb.setChecked(default.no_face_is_distraction)
        idx = self._alert_method.findData(default.alert_method)
        if idx >= 0:
            self._alert_method.setCurrentIndex(idx)
        self._cooldown_spin.setValue(default.alert_cooldown)
        idx = self._feedback_combo.findData(default.feedback_action)
        if idx >= 0:
            self._feedback_combo.setCurrentIndex(idx)
        self._mirror_cb.setChecked(default.mirror_display)
        self._log_csv_cb.setChecked(default.log_to_csv)
        self._log_db_cb.setChecked(default.log_to_db)
        self._dark_mode_cb.setChecked(default.dark_mode)

    def get_settings(self) -> FocusCamSettings:
        return self._settings
