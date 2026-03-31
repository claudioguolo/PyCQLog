from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


_APP_LOGGER_NAME = "pycqlog"
_CURRENT_LOG_FILE: Path | None = None
_LOG_MAX_BYTES = 2_000_000
_LOG_BACKUP_COUNT = 5
_LOG_FILE_MAP = {
    "pycqlog.bootstrap": "bootstrap.log",
    "pycqlog.repositories": "repositories.log",
    "pycqlog.integrations": "integrations.log",
    "pycqlog.ui.main_window": "ui_main_window.log",
    "pycqlog.jtdx_contacts": "jtdx_contacts.log",
    "pycqlog.clublog_uploads": "clublog_uploads.log",
    "pycqlog.station_service": "station_service.log",
    "pycqlog.service_api": "service_api.log",
    "pycqlog.sync.clublog": "sync_clublog.log",
    "pycqlog.sync.qrz": "sync_qrz.log",
}
_CURRENT_LOGS_DIR: Path | None = None


class _PrefixFilter(logging.Filter):
    def __init__(self, prefix: str) -> None:
        super().__init__()
        self._prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name == self._prefix or record.name.startswith(f"{self._prefix}.")


def _root_logger() -> logging.Logger:
    logger = logging.getLogger(_APP_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger


def configure_app_logging(base_dir: str | Path) -> Path:
    global _CURRENT_LOG_FILE, _CURRENT_LOGS_DIR

    resolved_base_dir = Path(base_dir).expanduser()
    logs_dir = resolved_base_dir if resolved_base_dir.name == "logs" else resolved_base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "pycqlog.log"

    logger = _root_logger()
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=_LOG_MAX_BYTES,
        backupCount=_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    for logger_name, filename in _LOG_FILE_MAP.items():
        scoped_handler = RotatingFileHandler(
            logs_dir / filename,
            maxBytes=_LOG_MAX_BYTES,
            backupCount=_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        scoped_handler.setLevel(logging.DEBUG)
        scoped_handler.setFormatter(formatter)
        scoped_handler.addFilter(_PrefixFilter(logger_name))
        logger.addHandler(scoped_handler)

    _CURRENT_LOG_FILE = log_file
    _CURRENT_LOGS_DIR = logs_dir
    logger.info("Logging configured. log_file=%s", log_file)
    return log_file


def get_logger(name: str | None = None) -> logging.Logger:
    if not name:
        return _root_logger()
    normalized = name if name.startswith(f"{_APP_LOGGER_NAME}.") else f"{_APP_LOGGER_NAME}.{name}"
    return logging.getLogger(normalized)


def current_log_file() -> Path | None:
    return _CURRENT_LOG_FILE


def register_logger_file(logger_name: str, filename: str) -> None:
    _LOG_FILE_MAP.setdefault(logger_name, filename)
    logs_dir = _CURRENT_LOGS_DIR
    if logs_dir is None:
        return
    root = _root_logger()
    for handler in root.handlers:
        if isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == logs_dir / filename:
            return
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    scoped_handler = RotatingFileHandler(
        logs_dir / filename,
        maxBytes=_LOG_MAX_BYTES,
        backupCount=_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    scoped_handler.setLevel(logging.DEBUG)
    scoped_handler.setFormatter(formatter)
    scoped_handler.addFilter(_PrefixFilter(logger_name))
    root.addHandler(scoped_handler)
