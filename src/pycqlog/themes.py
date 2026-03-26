from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


THEME_CHOICES = ["system", "light", "dark"]


@dataclass(frozen=True)
class ThemePalette:
    window_bg: str
    panel_bg: str
    panel_alt_bg: str
    text: str
    muted_text: str
    border: str
    gridline: str
    button_bg: str
    button_hover: str
    button_text: str


LIGHT_THEME = ThemePalette(
    window_bg="#f7f1e8",
    panel_bg="#fffdf8",
    panel_alt_bg="#fdf7ef",
    text="#213547",
    muted_text="#475b6b",
    border="#d6c7af",
    gridline="#eadfcd",
    button_bg="#b55233",
    button_hover="#963f25",
    button_text="#ffffff",
)

DARK_THEME = ThemePalette(
    window_bg="#161a20",
    panel_bg="#1f252d",
    panel_alt_bg="#252d37",
    text="#edf2f7",
    muted_text="#b8c4d1",
    border="#3b4654",
    gridline="#313b47",
    button_bg="#d97757",
    button_hover="#e38b69",
    button_text="#0f1419",
)


def detect_system_theme(app: QApplication) -> str:
    palette = app.palette()
    color = palette.color(QPalette.ColorRole.Window)
    return "dark" if _is_dark(color) else "light"


def resolve_theme(theme_name: str, app: QApplication) -> tuple[str, ThemePalette]:
    resolved = theme_name if theme_name in THEME_CHOICES else "system"
    if resolved == "system":
        resolved = detect_system_theme(app)
    palette = DARK_THEME if resolved == "dark" else LIGHT_THEME
    return resolved, palette


def build_stylesheet(theme: ThemePalette) -> str:
    return f"""
    QMainWindow, QDialog, QMessageBox {{
        background: {theme.window_bg};
    }}
    QMenuBar, QMenu {{
        background: {theme.panel_bg};
        color: {theme.text};
    }}
    QMenuBar::item:selected, QMenu::item:selected {{
        background: {theme.panel_alt_bg};
    }}
    QLabel#headerLabel {{
        font-size: 26px;
        font-weight: 700;
        color: {theme.text};
    }}
    QLabel#sectionLabel {{
        font-size: 20px;
        font-weight: 700;
        color: {theme.text};
    }}
    QLabel#filterLabel {{
        font-size: 15px;
        font-weight: 700;
        color: {theme.text};
    }}
    QWidget#dashboardCard {{
        background: {theme.panel_bg};
        border: 1px solid {theme.border};
        border-radius: 12px;
    }}
    QLabel#dashboardCardTitle {{
        color: {theme.muted_text};
        font-size: 13px;
        font-weight: 600;
    }}
    QLabel#dashboardCardValue {{
        color: {theme.text};
        font-size: 28px;
        font-weight: 700;
    }}
    QLabel {{
        color: {theme.text};
    }}
    QLineEdit, QTextEdit, QTableWidget, QComboBox, QMessageBox {{
        background: {theme.panel_bg};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 8px;
        color: {theme.text};
        selection-background-color: {theme.button_bg};
    }}
    QTextEdit, QTableWidget, QMessageBox {{
        border-radius: 10px;
    }}
    QHeaderView::section {{
        background: {theme.panel_alt_bg};
        color: {theme.text};
        border: 1px solid {theme.border};
        padding: 6px;
    }}
    QPushButton {{
        background: {theme.button_bg};
        color: {theme.button_text};
        border: none;
        border-radius: 8px;
        padding: 10px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background: {theme.button_hover};
    }}
    QPushButton:disabled {{
        background: {theme.border};
        color: {theme.muted_text};
    }}
    QPushButton#quickFilterChip {{
        background: {theme.panel_alt_bg};
        color: {theme.text};
        border: 1px solid {theme.border};
        padding: 6px 12px;
    }}
    QPushButton#quickFilterChip:hover {{
        background: {theme.panel_bg};
    }}
    QPushButton#quickFilterChip:checked {{
        background: {theme.button_bg};
        color: {theme.button_text};
        border: 1px solid {theme.button_bg};
    }}
    QTableWidget {{
        gridline-color: {theme.gridline};
    }}
    """


def _is_dark(color: QColor) -> bool:
    return color.lightness() < 128
