"""Generate a neon QSS stylesheet from a VUNJA LUTI palette."""

from __future__ import annotations

from .. import themes


def qss(theme_name: str, font_family: str = "JetBrainsMono Nerd Font") -> str:
    p = themes.palette(theme_name)
    return f"""
* {{
    font-family: "{font_family}", "JetBrains Mono", monospace;
    font-size: 13px;
    color: {p['text']};
    selection-background-color: {p['accent']};
    selection-color: {p['base']};
}}
QMainWindow, QWidget#root {{
    background-color: {p['base']};
}}
QLabel#title {{
    font-size: 22px;
    font-weight: 700;
    color: {p['accent']};
}}
QLabel#subtitle {{ color: {p['subtext']}; font-size: 12px; }}
QLabel#statValue {{ font-size: 20px; font-weight: 700; color: {p['text']}; }}
QLabel#statKey   {{ color: {p['subtext']}; font-size: 11px; text-transform: uppercase; }}

QFrame.card {{
    background-color: {p['surface']};
    border: 1px solid {p['overlay']};
    border-radius: 14px;
}}
QFrame#accentCard {{
    background-color: {p['surface']};
    border: 1px solid {p['accent']};
    border-radius: 14px;
}}

QTabWidget::pane {{ border: none; }}
QTabBar::tab {{
    background: transparent;
    color: {p['subtext']};
    padding: 10px 18px;
    margin-right: 4px;
    border-radius: 10px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    color: {p['base']};
    background: {p['accent']};
}}
QTabBar::tab:hover:!selected {{ color: {p['text']}; background: {p['overlay']}; }}

QPushButton {{
    background-color: {p['overlay']};
    color: {p['text']};
    border: 1px solid {p['overlay']};
    border-radius: 10px;
    padding: 9px 16px;
    font-weight: 600;
}}
QPushButton:hover {{ border: 1px solid {p['accent']}; color: {p['accent']}; }}
QPushButton:pressed {{ background-color: {p['accent']}; color: {p['base']}; }}
QPushButton#primary {{
    background-color: {p['good']}; color: {p['base']}; border: none;
}}
QPushButton#primary:hover {{ background-color: {p['accent']}; }}
QPushButton#danger {{ background-color: {p['bad']}; color: {p['base']}; border: none; }}
QPushButton#ghost {{ background: transparent; border: 1px solid {p['overlay']}; }}

QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextEdit {{
    background-color: {p['base']};
    border: 1px solid {p['overlay']};
    border-radius: 8px;
    padding: 7px 10px;
    color: {p['text']};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {p['accent']}; }}
QComboBox QAbstractItemView {{
    background: {p['surface']};
    border: 1px solid {p['overlay']};
    selection-background-color: {p['accent']};
    selection-color: {p['base']};
}}

QProgressBar {{
    background-color: {p['base']};
    border: 1px solid {p['overlay']};
    border-radius: 8px;
    text-align: center;
    color: {p['subtext']};
    height: 16px;
}}
QProgressBar::chunk {{
    background-color: {p['accent']};
    border-radius: 7px;
}}

QPlainTextEdit#console, QTextEdit#console {{
    background-color: {p['base']};
    border: 1px solid {p['overlay']};
    color: {p['good']};
    font-size: 12px;
}}

QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 38px; height: 20px; border-radius: 10px;
    background: {p['overlay']};
}}
QCheckBox::indicator:checked {{ background: {p['good']}; }}

QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {p['overlay']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {p['accent']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

QStatusBar {{ color: {p['subtext']}; }}
"""


def accent(theme_name: str, role: str = "accent") -> str:
    return themes.palette(theme_name)[role]
