from __future__ import annotations

import configparser
import json
from pathlib import Path


_SECTION_ORDER = [
    "general",
    "service",
    "paths",
    "ui",
    "station",
    "dashboard",
    "adif",
    "wsjt",
    "clublog",
    "qrz",
    "lotw",
    "misc",
]

_SECTION_COMMENTS = {
    "general": "Configuracao principal do PyCQLog",
    "service": "Modo servico, acesso remoto e autenticacao da API",
    "paths": "Diretorios de dados e logs",
    "ui": "Preferencias da interface grafica",
    "station": "Identificacao e operacao da estacao",
    "dashboard": "Preferencias visuais do dashboard",
    "adif": "Opcoes de importacao e exportacao ADIF",
    "wsjt": "Recepcao UDP de JTDX/WSJT-X e compatibilidade",
    "clublog": "Sincronizacao com Club Log",
    "qrz": "Integracao com QRZ.com",
    "lotw": "Configuracao do LoTW/TQSL",
    "misc": "Chaves nao mapeadas explicitamente",
}

_KEY_TO_SECTION = {
    "language": "ui",
    "theme": "ui",
    "data_dir": "paths",
    "log_dir": "paths",
    "operator_callsign": "station",
    "station_callsign": "station",
    "active_logbook_id": "station",
    "adif_export_prefix": "adif",
    "dashboard_use_band_colors": "dashboard",
    "dashboard_use_mode_colors": "dashboard",
    "dashboard_colorize_tables": "dashboard",
    "integration_wsjt_enabled": "wsjt",
    "integration_wsjt_debug": "wsjt",
    "integration_wsjt_host": "wsjt",
    "integration_wsjt_port": "wsjt",
    "integration_clublog_enabled": "clublog",
    "integration_clublog_upload_udp": "clublog",
    "integration_clublog_upload_manual": "clublog",
    "integration_clublog_email": "clublog",
    "integration_clublog_password": "clublog",
    "integration_clublog_callsign": "clublog",
    "integration_clublog_api_key": "clublog",
    "integration_clublog_endpoint": "clublog",
    "integration_clublog_delete_endpoint": "clublog",
    "integration_clublog_interval": "clublog",
    "integration_clublog_cooldown_until": "clublog",
    "integration_qrz_enabled": "qrz",
    "integration_qrz_upload_udp": "qrz",
    "integration_qrz_upload_manual": "qrz",
    "integration_qrz_username": "qrz",
    "integration_qrz_password": "qrz",
    "integration_qrz_api_key": "qrz",
    "integration_lotw_tqsl_path": "lotw",
    "integration_lotw_station_location": "lotw",
    "service_bind_host": "service",
    "service_bind_port": "service",
    "service_remote_enabled": "service",
    "service_remote_host": "service",
    "service_remote_port": "service",
    "service_auth_code": "service",
}

UI_SETTINGS_KEYS = {
    "language",
    "theme",
    "dashboard_use_band_colors",
    "dashboard_use_mode_colors",
    "dashboard_colorize_tables",
    "service_remote_enabled",
    "service_remote_host",
    "service_remote_port",
    "service_auth_code",
}


def filter_settings_for_profile(data: dict[str, str], profile: str) -> dict[str, str]:
    if profile == "ui":
        allowed = UI_SETTINGS_KEYS
        return {key: value for key, value in data.items() if key in allowed}
    if profile == "daemon":
        return {key: value for key, value in data.items() if key not in UI_SETTINGS_KEYS or key == "service_auth_code"}
    return dict(data)


def _section_for_key(key: str) -> str:
    return _KEY_TO_SECTION.get(key, "misc")


def _key_for_option(section: str, option: str) -> str:
    if section == "misc":
        return option
    return option


class JsonSettingsStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, object]:
        return self._load_flat()

    def save(self, data: dict[str, object]) -> None:
        flat = {key: str(value) for key, value in data.items()}
        self._write_flat(flat)

    def get_language(self, default: str) -> str:
        value = self.get_string("language", default)
        return value or default

    def set_language(self, language: str) -> None:
        self.set_string("language", language)

    def get_string(self, key: str, default: str = "") -> str:
        data = self._load_flat()
        value = data.get(key)
        return str(value) if isinstance(value, str) else default

    def set_string(self, key: str, value: str) -> None:
        data = self._load_flat()
        data[key] = value
        self._write_flat(data)

    def update_many(self, values: dict[str, str]) -> None:
        data = self._load_flat()
        data.update(values)
        self._write_flat(data)

    def _load_flat(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        try:
            raw = self._path.read_text(encoding="utf-8")
        except OSError:
            return {}
        stripped = raw.lstrip()
        if not stripped:
            return {}
        if stripped.startswith("{"):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return {}
            return {key: str(value) for key, value in data.items() if isinstance(key, str)}

        parser = configparser.ConfigParser(interpolation=None)
        try:
            parser.read_string(raw)
        except configparser.Error:
            return {}
        flat: dict[str, str] = {}
        for section in parser.sections():
            for option, value in parser.items(section):
                flat[_key_for_option(section, option)] = value
        return flat

    def _write_flat(self, data: dict[str, str]) -> None:
        sections: dict[str, dict[str, str]] = {section: {} for section in _SECTION_ORDER}
        for key, value in sorted(data.items()):
            section = _section_for_key(key)
            sections.setdefault(section, {})
            sections[section][key] = str(value)

        lines = [
            "# PyCQLog configuration file",
            "# Comentarios usam o prefixo #",
            "# Este arquivo e lido tanto pelo modo desktop quanto pelo modo servico",
            "",
        ]
        for section in _SECTION_ORDER:
            values = sections.get(section, {})
            if not values:
                continue
            comment = _SECTION_COMMENTS.get(section)
            if comment:
                lines.append(f"# {comment}")
            lines.append(f"[{section}]")
            for key, value in sorted(values.items()):
                lines.append(f"{key} = {value}")
            lines.append("")
        self._path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
