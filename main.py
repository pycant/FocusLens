"""FocusCam — 专注力检测桌面应用

基于 OpenCV, MediaPipe, PyQt6 构建。
替代原 tkinter 版本，提供可配置的分心检测参数和非模态提醒。
"""
import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config.settings import FocusCamSettings
from app.main_window import MainWindow
from app.theme import apply_theme


def main():
    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("FocusCam")
    app.setOrganizationName("FocusCam")

    # 全局字体
    font = QFont("Microsoft YaHei UI", 9)
    app.setFont(font)

    # 加载已保存的主题设置
    settings = FocusCamSettings.load()
    apply_theme(app, settings.theme_name)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
