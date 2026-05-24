"""FocusCam 主题系统 — 亮色/暗色主题切换

通过 QPalette + 全局 QSS 实现完整的暗色主题适配。
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor


# ── 暗色主题配色变量 ──────────────────────────────────

DARK_COLORS = {
    "window": QColor(35, 39, 43),
    "window_text": QColor(220, 220, 220),
    "base": QColor(43, 48, 53),
    "alternate_base": QColor(38, 43, 48),
    "tooltip_base": QColor(50, 55, 60),
    "tooltip_text": QColor(220, 220, 220),
    "text": QColor(220, 220, 220),
    "button": QColor(55, 60, 65),
    "button_text": QColor(220, 220, 220),
    "bright_text": QColor(255, 255, 255),
    "link": QColor(80, 160, 255),
    "highlight": QColor(60, 120, 220),
    "highlighted_text": QColor(255, 255, 255),
    "disabled_text": QColor(120, 125, 130),
    "disabled_button": QColor(45, 50, 55),
    "disabled_button_text": QColor(100, 105, 110),
    "mid": QColor(65, 70, 75),
    "midlight": QColor(75, 80, 85),
    "dark": QColor(25, 28, 32),
    "shadow": QColor(15, 18, 22),
}

LIGHT_COLORS = {}


def _build_palette(is_dark: bool) -> QPalette:
    """根据主题构建 QPalette"""
    colors = DARK_COLORS if is_dark else LIGHT_COLORS

    p = QPalette()

    if is_dark:
        p.setColor(QPalette.ColorRole.Window, colors["window"])
        p.setColor(QPalette.ColorRole.WindowText, colors["window_text"])
        p.setColor(QPalette.ColorRole.Base, colors["base"])
        p.setColor(QPalette.ColorRole.AlternateBase, colors["alternate_base"])
        p.setColor(QPalette.ColorRole.ToolTipBase, colors["tooltip_base"])
        p.setColor(QPalette.ColorRole.ToolTipText, colors["tooltip_text"])
        p.setColor(QPalette.ColorRole.Text, colors["text"])
        p.setColor(QPalette.ColorRole.Button, colors["button"])
        p.setColor(QPalette.ColorRole.ButtonText, colors["button_text"])
        p.setColor(QPalette.ColorRole.BrightText, colors["bright_text"])
        p.setColor(QPalette.ColorRole.Link, colors["link"])
        p.setColor(QPalette.ColorRole.Highlight, colors["highlight"])
        p.setColor(QPalette.ColorRole.HighlightedText, colors["highlighted_text"])
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, colors["disabled_text"])
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, colors["disabled_text"])
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, colors["disabled_button_text"])
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, colors["disabled_button"])
        p.setColor(QPalette.ColorRole.Mid, colors["mid"])
        p.setColor(QPalette.ColorRole.Midlight, colors["midlight"])
        p.setColor(QPalette.ColorRole.Dark, colors["dark"])
        p.setColor(QPalette.ColorRole.Shadow, colors["shadow"])

    return p


def _qss(is_dark: bool) -> str:
    """主题相关的全局 QSS 样式"""
    if not is_dark:
        return ""

    return """
        QMenuBar {
            background-color: #272b30;
            color: #dcdcdc;
            border-bottom: 1px solid #1c1f23;
        }
        QMenuBar::item:selected {
            background-color: #3c3f44;
        }
        QMenu {
            background-color: #2b3035;
            color: #dcdcdc;
            border: 1px solid #3c3f44;
        }
        QMenu::item:selected {
            background-color: #3c78d8;
            color: white;
        }
        QMenu::separator {
            height: 1px;
            background: #3c3f44;
            margin: 4px 8px;
        }
        QStatusBar {
            background-color: #23272b;
            color: #9a9ea3;
            border-top: 1px solid #1c1f23;
        }
        QToolTip {
            background-color: #32373c;
            color: #dcdcdc;
            border: 1px solid #4a4f55;
            padding: 4px;
        }
        QTabWidget::pane {
            border: 1px solid #3c3f44;
            background-color: #2b3035;
        }
        QTabBar::tab {
            background-color: #23272b;
            color: #9a9ea3;
            padding: 6px 16px;
            border: 1px solid #3c3f44;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #2b3035;
            color: #dcdcdc;
        }
        QTabBar::tab:hover:!selected {
            background-color: #2f3338;
        }
        QGroupBox {
            border: 1px solid #3c3f44;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 12px;
            color: #dcdcdc;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }
        QProgressBar {
            background: #34383d;
            border: 1px solid #3c3f44;
            border-radius: 4px;
            color: #dcdcdc;
        }
        QSplitter::handle {
            background-color: #3c3f44;
        }
        QComboBox {
            background-color: #34383d;
            color: #dcdcdc;
            border: 1px solid #4a4f55;
            border-radius: 4px;
            padding: 3px 8px;
        }
        QComboBox::drop-down {
            background-color: #3c3f44;
            border: none;
            width: 20px;
        }
        QComboBox QAbstractItemView {
            background-color: #2b3035;
            color: #dcdcdc;
            selection-background-color: #3c78d8;
            border: 1px solid #4a4f55;
        }
        QDoubleSpinBox, QSpinBox {
            background-color: #34383d;
            color: #dcdcdc;
            border: 1px solid #4a4f55;
            border-radius: 4px;
            padding: 3px;
        }
        QCheckBox {
            color: #dcdcdc;
        }
        QCheckBox::indicator:unchecked {
            border: 1px solid #5a5f65;
            background: #34383d;
            border-radius: 3px;
        }
        QCheckBox::indicator:checked {
            border: 1px solid #3c78d8;
            background: #3c78d8;
            border-radius: 3px;
        }
        QSlider::groove:horizontal {
            background: #34383d;
            height: 6px;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #5a7fb5;
            width: 14px;
            height: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }
        QSlider::sub-page:horizontal {
            background: #3c78d8;
            border-radius: 3px;
        }
    """


def apply_theme(app: QApplication, is_dark: bool):
    """应用主题到整个应用"""
    palette = _build_palette(is_dark)
    app.setPalette(palette)
    app.setStyleSheet(_qss(is_dark))
