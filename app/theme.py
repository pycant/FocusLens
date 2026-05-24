"""FocusCam 多主题系统 — 每个主题含 QPalette + QSS"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

# ── 主题定义 ──────────────────────────────────────────

THEMES = {
    "classic_light": {
        "label": "☀️ Classic Light",
        "dark": False,
        "qss": "",
    },
    "dark": {
        "label": "🌙 Dark",
        "dark": True,
    },
    "midnight": {
        "label": "🌌 Midnight Blue",
        "dark": True,
    },
    "forest": {
        "label": "🌲 Forest",
        "dark": True,
    },
    "charcoal": {
        "label": "🖤 Charcoal",
        "dark": True,
    },
}


# ── 各主题配色 ──────────────────────────────────────────

_COLORS = {
    "dark": {
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
        "accent": QColor(60, 120, 220),
        "surface": QColor(43, 48, 53),
    },
    "midnight": {
        "window": QColor(22, 28, 43),
        "window_text": QColor(210, 215, 230),
        "base": QColor(28, 35, 55),
        "alternate_base": QColor(24, 30, 48),
        "tooltip_base": QColor(35, 42, 65),
        "tooltip_text": QColor(210, 215, 230),
        "text": QColor(210, 215, 230),
        "button": QColor(35, 45, 70),
        "button_text": QColor(210, 215, 230),
        "bright_text": QColor(255, 255, 255),
        "link": QColor(100, 180, 255),
        "highlight": QColor(50, 100, 200),
        "highlighted_text": QColor(255, 255, 255),
        "disabled_text": QColor(100, 108, 125),
        "disabled_button": QColor(30, 38, 58),
        "disabled_button_text": QColor(80, 88, 105),
        "mid": QColor(50, 60, 85),
        "midlight": QColor(60, 70, 95),
        "dark": QColor(16, 20, 32),
        "shadow": QColor(10, 14, 22),
        "accent": QColor(60, 140, 240),
        "surface": QColor(28, 35, 55),
    },
    "forest": {
        "window": QColor(30, 38, 30),
        "window_text": QColor(210, 220, 205),
        "base": QColor(38, 48, 38),
        "alternate_base": QColor(33, 42, 33),
        "tooltip_base": QColor(45, 58, 45),
        "tooltip_text": QColor(210, 220, 205),
        "text": QColor(210, 220, 205),
        "button": QColor(48, 60, 46),
        "button_text": QColor(210, 220, 205),
        "bright_text": QColor(255, 255, 255),
        "link": QColor(100, 200, 120),
        "highlight": QColor(50, 140, 60),
        "highlighted_text": QColor(255, 255, 255),
        "disabled_text": QColor(110, 120, 105),
        "disabled_button": QColor(38, 48, 36),
        "disabled_button_text": QColor(85, 95, 80),
        "mid": QColor(60, 72, 56),
        "midlight": QColor(70, 82, 66),
        "dark": QColor(20, 28, 20),
        "shadow": QColor(12, 18, 12),
        "accent": QColor(60, 180, 80),
        "surface": QColor(38, 48, 38),
    },
    "charcoal": {
        "window": QColor(25, 25, 25),
        "window_text": QColor(240, 240, 240),
        "base": QColor(33, 33, 33),
        "alternate_base": QColor(28, 28, 28),
        "tooltip_base": QColor(45, 45, 45),
        "tooltip_text": QColor(240, 240, 240),
        "text": QColor(240, 240, 240),
        "button": QColor(50, 50, 50),
        "button_text": QColor(240, 240, 240),
        "bright_text": QColor(255, 255, 255),
        "link": QColor(80, 180, 255),
        "highlight": QColor(220, 220, 220),
        "highlighted_text": QColor(25, 25, 25),
        "disabled_text": QColor(110, 110, 110),
        "disabled_button": QColor(40, 40, 40),
        "disabled_button_text": QColor(75, 75, 75),
        "mid": QColor(58, 58, 58),
        "midlight": QColor(68, 68, 68),
        "dark": QColor(15, 15, 15),
        "shadow": QColor(8, 8, 8),
        "accent": QColor(200, 200, 200),
        "surface": QColor(33, 33, 33),
    },
}


def _build_palette(name: str) -> QPalette:
    c = _COLORS.get(name)
    if not c:
        return QPalette()

    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, c["window"])
    p.setColor(QPalette.ColorRole.WindowText, c["window_text"])
    p.setColor(QPalette.ColorRole.Base, c["base"])
    p.setColor(QPalette.ColorRole.AlternateBase, c["alternate_base"])
    p.setColor(QPalette.ColorRole.ToolTipBase, c["tooltip_base"])
    p.setColor(QPalette.ColorRole.ToolTipText, c["tooltip_text"])
    p.setColor(QPalette.ColorRole.Text, c["text"])
    p.setColor(QPalette.ColorRole.Button, c["button"])
    p.setColor(QPalette.ColorRole.ButtonText, c["button_text"])
    p.setColor(QPalette.ColorRole.BrightText, c["bright_text"])
    p.setColor(QPalette.ColorRole.Link, c["link"])
    p.setColor(QPalette.ColorRole.Highlight, c["highlight"])
    p.setColor(QPalette.ColorRole.HighlightedText, c["highlighted_text"])
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, c["disabled_text"])
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, c["disabled_text"])
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, c["disabled_button_text"])
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, c["disabled_button"])
    p.setColor(QPalette.ColorRole.Mid, c["mid"])
    p.setColor(QPalette.ColorRole.Midlight, c["midlight"])
    p.setColor(QPalette.ColorRole.Dark, c["dark"])
    p.setColor(QPalette.ColorRole.Shadow, c["shadow"])
    return p


def _qss(name: str) -> str:
    """各主题的 QSS 微调"""
    if name == "classic_light":
        return ""

    c = _COLORS.get(name)
    if not c:
        return ""

    bg = c["window"].name()
    surface = c["surface"].name()
    text = c["text"].name()
    disabled = c["disabled_text"].name()
    border = c["mid"].name()
    accent = c["accent"].name()
    hl_bg = c["highlight"].name()
    hl_text = c["highlighted_text"].name()

    return f"""
        QMenuBar {{
            background-color: {c["dark"].name()};
            color: {text};
            border-bottom: 1px solid {border};
        }}
        QMenuBar::item:selected {{
            background-color: {c["midlight"].name()};
        }}
        QMenu {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
        }}
        QMenu::item:selected {{
            background-color: {accent};
            color: white;
        }}
        QMenu::separator {{
            height: 1px;
            background: {border};
            margin: 4px 8px;
        }}
        QStatusBar {{
            background-color: {bg};
            color: {disabled};
            border-top: 1px solid {c["shadow"].name()};
        }}
        QToolTip {{
            background-color: {c["tooltip_base"].name()};
            color: {text};
            border: 1px solid {c["midlight"].name()};
            padding: 4px;
        }}
        QTabWidget::pane {{
            border: 1px solid {border};
            background-color: {surface};
        }}
        QTabBar::tab {{
            background-color: {c["dark"].name()};
            color: {disabled};
            padding: 6px 16px;
            border: 1px solid {border};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QTabBar::tab:selected {{
            background-color: {surface};
            color: {text};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {c["alternate_base"].name()};
        }}
        QGroupBox {{
            border: 1px solid {border};
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 12px;
            color: {text};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }}
        QProgressBar {{
            background: {c["dark"].name()};
            border: 1px solid {border};
            border-radius: 4px;
            color: {text};
        }}
        QSplitter::handle {{
            background-color: {border};
        }}
        QComboBox {{
            background-color: {c["base"].name()};
            color: {text};
            border: 1px solid {c["midlight"].name()};
            border-radius: 4px;
            padding: 3px 8px;
        }}
        QComboBox::drop-down {{
            background-color: {border};
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {surface};
            color: {text};
            selection-background-color: {accent};
            border: 1px solid {c["midlight"].name()};
        }}
        QDoubleSpinBox, QSpinBox {{
            background-color: {c["base"].name()};
            color: {text};
            border: 1px solid {c["midlight"].name()};
            border-radius: 4px;
            padding: 3px;
        }}
        QCheckBox {{ color: {text}; }}
        QSlider::groove:horizontal {{
            background: {c["dark"].name()};
            height: 6px;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {c["midlight"].name()};
            width: 14px;
            height: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }}
        QSlider::sub-page:horizontal {{
            background: {accent};
            border-radius: 3px;
        }}
    """


# ── 公开 API ──────────────────────────────────────────

def get_theme_names() -> list:
    return list(THEMES.keys())


def get_theme_label(name: str) -> str:
    return THEMES.get(name, {}).get("label", name)


def apply_theme(app: QApplication, theme_name: str):
    meta = THEMES.get(theme_name, THEMES["classic_light"])
    app.setPalette(_build_palette(theme_name))
    app.setStyleSheet(_qss(theme_name))
