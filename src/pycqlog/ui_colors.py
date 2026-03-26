from __future__ import annotations

from PyQt6.QtGui import QColor


BAND_COLORS = {
    "160m": "#8b5e3c",
    "80m": "#b35c44",
    "40m": "#d97757",
    "20m": "#f4a261",
    "15m": "#e9c46a",
    "10m": "#2a9d8f",
    "6m": "#3a86ff",
}

MODE_COLORS = {
    "FT8": "#3a86ff",
    "CW": "#e9c46a",
    "SSB": "#d97757",
    "AM": "#f4a261",
    "FM": "#2a9d8f",
    "RTTY": "#9b5de5",
}

DEFAULT_SERIES_COLORS = ["#d97757", "#e9c46a", "#2a9d8f", "#3a86ff", "#9b5de5", "#f4a261"]


def color_for_band(label: str, index: int = 0) -> str:
    return BAND_COLORS.get(label, DEFAULT_SERIES_COLORS[index % len(DEFAULT_SERIES_COLORS)])


def color_for_mode(label: str, index: int = 0) -> str:
    return MODE_COLORS.get(label.upper(), DEFAULT_SERIES_COLORS[index % len(DEFAULT_SERIES_COLORS)])


def contrasting_text_color(hex_color: str) -> str:
    return "#0f1419" if QColor(hex_color).lightness() > 150 else "#edf2f7"
