from __future__ import annotations

import json
from pathlib import Path


class JsonSettingsStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, object]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self, data: dict[str, object]) -> None:
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")

    def get_language(self, default: str) -> str:
        data = self.load()
        language = data.get("language")
        return str(language) if isinstance(language, str) else default

    def set_language(self, language: str) -> None:
        data = self.load()
        data["language"] = language
        self.save(data)

    def get_string(self, key: str, default: str = "") -> str:
        data = self.load()
        value = data.get(key)
        return str(value) if isinstance(value, str) else default

    def set_string(self, key: str, value: str) -> None:
        data = self.load()
        data[key] = value
        self.save(data)

    def update_many(self, values: dict[str, str]) -> None:
        data = self.load()
        data.update(values)
        self.save(data)
