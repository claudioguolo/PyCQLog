from __future__ import annotations

import hashlib
import json
import queue
import socket
import struct
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib import error, parse, request

from pycqlog.infrastructure.settings import JsonSettingsStore
from pycqlog.infrastructure.integrations_qrz import QrzUploader, QrzLogbookConfig, QrzUploadResult, QrzUploadJob


WSJTX_MAGIC = 0xADBCCBDA
WSJTX_MESSAGE_LOGGED_ADIF = 12


@dataclass(slots=True)
class LoggedAdifEvent:
    source_app: str
    adif_text: str


@dataclass(slots=True)
class ClubLogConfig:
    enabled: bool
    email: str
    password: str
    callsign: str
    api_key: str
    endpoint: str
    interval_seconds: int


@dataclass(slots=True)
class ClubLogUploadJob:
    job_id: str
    config: ClubLogConfig
    adif_text: str
    created_at: str
    signature: str


@dataclass(slots=True)
class ClubLogUploadResult:
    success: bool
    detail: str
    job_id: str = ""


class WsjtUdpListener:
    def __init__(self) -> None:
        self._host = "127.0.0.1"
        self._port = 2237
        self._enabled = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._events: queue.Queue[LoggedAdifEvent] = queue.Queue()
        self._socket: socket.socket | None = None
        self._seen_hashes: list[str] = []
        self._last_error = ""
        self._bound_label = ""

    def configure(self, enabled: bool, host: str, port: int) -> None:
        needs_restart = enabled != self._enabled or host != self._host or port != self._port
        self._enabled = enabled
        self._host = host
        self._port = port
        if needs_restart:
            self.stop()
            self.start()

    def start(self) -> None:
        if not self._enabled or self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="pycqlog-wsjtx-listener", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None

    def poll(self) -> list[LoggedAdifEvent]:
        items: list[LoggedAdifEvent] = []
        while True:
            try:
                items.append(self._events.get_nowait())
            except queue.Empty:
                break
        return items

    def inject(self, event: LoggedAdifEvent) -> None:
        self._events.put(event)

    def enabled(self) -> bool:
        return self._enabled

    def last_error(self) -> str:
        return self._last_error

    def status_label(self) -> str:
        if self._last_error:
            return self._last_error
        if self._enabled and self._bound_label:
            return self._bound_label
        return ""

    def _run(self) -> None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self._host, self._port))
            sock.settimeout(0.5)
            self._socket = sock
            self._last_error = ""
            self._bound_label = f"{self._host}:{self._port}"
        except OSError:
            self._last_error = f"Bind failed on {self._host}:{self._port}"
            self._bound_label = ""
            self._thread = None
            return

        while not self._stop_event.is_set():
            try:
                payload, _address = self._socket.recvfrom(65535)
            except TimeoutError:
                continue
            except OSError:
                break
            event = self._parse_datagram(payload)
            if event is None:
                continue
            digest = hashlib.sha1(event.adif_text.encode("utf-8", errors="ignore")).hexdigest()
            if digest in self._seen_hashes:
                continue
            self._seen_hashes.append(digest)
            self._seen_hashes = self._seen_hashes[-100:]
            self._events.put(event)

        self._socket = None
        if self._stop_event.is_set():
            self._bound_label = ""

    def _parse_datagram(self, payload: bytes) -> LoggedAdifEvent | None:
        if len(payload) < 16:
            return None
        magic, schema, message_type = struct.unpack(">III", payload[:12])
        if magic != WSJTX_MAGIC or schema <= 0 or message_type != WSJTX_MESSAGE_LOGGED_ADIF:
            return None
        offset = 12
        source_app, offset = _read_qt_utf8(payload, offset)
        adif_text, _offset = _read_qt_utf8(payload, offset)
        if not adif_text or "<EOR>" not in adif_text.upper():
            return None
        return LoggedAdifEvent(source_app=source_app or "WSJT-X", adif_text=adif_text)


class ClubLogUploader:
    def __init__(self, queue_path: Path) -> None:
        self._queue_path = queue_path
        self._queue_path.parent.mkdir(parents=True, exist_ok=True)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._queue: queue.Queue[ClubLogUploadJob] = queue.Queue()
        self._results: queue.Queue[ClubLogUploadResult] = queue.Queue()
        self._last_upload_at = 0.0
        self._pending_jobs: dict[str, ClubLogUploadJob] = self._load_pending_jobs()
        self._enqueued_ids: set[str] = set()
        self.retry_pending()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="pycqlog-clublog-uploader", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None

    def enqueue(self, config: ClubLogConfig, adif_text: str) -> ClubLogUploadJob | None:
        if not config.enabled:
            return None
        signature = hashlib.sha1(
            f"{config.callsign}|{config.endpoint}|{adif_text}".encode("utf-8", errors="ignore")
        ).hexdigest()
        for pending in self._pending_jobs.values():
            if pending.signature == signature:
                return pending
        job = ClubLogUploadJob(
            job_id=hashlib.sha1(f"{time.time()}:{adif_text}".encode("utf-8", errors="ignore")).hexdigest(),
            config=config,
            adif_text=adif_text,
            created_at=datetime.utcnow().isoformat(),
            signature=signature,
        )
        self._pending_jobs[job.job_id] = job
        self._save_pending_jobs()
        self._enqueue_runtime(job)
        self.start()
        return job

    def retry_pending(self) -> int:
        count = 0
        for job in self._pending_jobs.values():
            if job.job_id in self._enqueued_ids:
                continue
            self._enqueue_runtime(job)
            count += 1
        return count

    def pending_count(self) -> int:
        return len(self._pending_jobs)

    def poll_results(self) -> list[ClubLogUploadResult]:
        items: list[ClubLogUploadResult] = []
        while True:
            try:
                items.append(self._results.get_nowait())
            except queue.Empty:
                break
        return items

    def _enqueue_runtime(self, job: ClubLogUploadJob) -> None:
        self._queue.put(job)
        self._enqueued_ids.add(job.job_id)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                job = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            wait_seconds = max(0.0, job.config.interval_seconds - (time.time() - self._last_upload_at))
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            result = self._upload(job)
            self._last_upload_at = time.time()
            self._enqueued_ids.discard(job.job_id)
            if result.success:
                self._pending_jobs.pop(job.job_id, None)
                self._save_pending_jobs()
            self._results.put(result)

    def _upload(self, job: ClubLogUploadJob) -> ClubLogUploadResult:
        payload = {
            "email": job.config.email,
            "password": job.config.password,
            "callsign": job.config.callsign,
            "api": job.config.api_key,
            "adif": job.adif_text,
        }
        encoded = parse.urlencode(payload).encode("utf-8")
        req = request.Request(job.config.endpoint, data=encoded, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("User-Agent", "PyCQLog/0.1.0")
        try:
            with request.urlopen(req, timeout=20) as response:
                status_code = getattr(response, "status", 200)
                body = response.read().decode("utf-8", errors="ignore").strip()
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore").strip()
            return ClubLogUploadResult(
                success=False,
                detail=f"HTTP {exc.code}: {detail[:200] or exc.reason}",
                job_id=job.job_id,
            )
        except error.URLError as exc:
            return ClubLogUploadResult(success=False, detail=str(exc), job_id=job.job_id)

        body_upper = body.upper()
        looks_failed = any(token in body_upper for token in ("ERROR", "INVALID", "FAILED"))
        success = 200 <= status_code < 300 and not looks_failed
        detail = f"HTTP {status_code}: {body[:200] or 'OK'}"
        return ClubLogUploadResult(success=success, detail=detail, job_id=job.job_id)

    def _load_pending_jobs(self) -> dict[str, ClubLogUploadJob]:
        if not self._queue_path.exists():
            return {}
        try:
            raw = json.loads(self._queue_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        jobs: dict[str, ClubLogUploadJob] = {}
        for item in raw if isinstance(raw, list) else []:
            try:
                config_raw = item["config"]
                job = ClubLogUploadJob(
                    job_id=str(item["job_id"]),
                    config=ClubLogConfig(
                        enabled=bool(config_raw["enabled"]),
                        email=str(config_raw["email"]),
                        password=str(config_raw["password"]),
                        callsign=str(config_raw["callsign"]),
                        api_key=str(config_raw["api_key"]),
                        endpoint=str(config_raw["endpoint"]),
                        interval_seconds=int(config_raw["interval_seconds"]),
                    ),
                    adif_text=str(item["adif_text"]),
                    created_at=str(item["created_at"]),
                    signature=str(item.get("signature") or ""),
                )
            except (KeyError, TypeError, ValueError):
                continue
            if not job.signature:
                job = ClubLogUploadJob(
                    job_id=job.job_id,
                    config=job.config,
                    adif_text=job.adif_text,
                    created_at=job.created_at,
                    signature=hashlib.sha1(
                        f"{job.config.callsign}|{job.config.endpoint}|{job.adif_text}".encode(
                            "utf-8", errors="ignore"
                        )
                    ).hexdigest(),
                )
            jobs[job.job_id] = job
        return jobs

    def _save_pending_jobs(self) -> None:
        serialized = [
            {
                "job_id": job.job_id,
                "config": asdict(job.config),
                "adif_text": job.adif_text,
                "created_at": job.created_at,
                "signature": job.signature,
            }
            for job in self._pending_jobs.values()
        ]
        self._queue_path.write_text(json.dumps(serialized, indent=2, ensure_ascii=True), encoding="utf-8")


class IntegrationManager:
    def __init__(self, settings_store: JsonSettingsStore, queue_path: Path) -> None:
        self._settings_store = settings_store
        self._listener = WsjtUdpListener()
        self._uploader = ClubLogUploader(queue_path)
        self._qrz_uploader = QrzUploader(queue_path.parent / "qrz_queue.json")

    def start(self) -> None:
        self.reconfigure()
        self._uploader.start()
        self._qrz_uploader.start()

    def stop(self) -> None:
        self._listener.stop()
        self._uploader.stop()
        self._qrz_uploader.stop()

    def reconfigure(self) -> None:
        self._listener.configure(
            enabled=self._settings_store.get_string("integration_wsjt_enabled", "false") == "true",
            host=self._settings_store.get_string("integration_wsjt_host", "127.0.0.1") or "127.0.0.1",
            port=int(self._settings_store.get_string("integration_wsjt_port", "2237") or "2237"),
        )

    def listener_enabled(self) -> bool:
        return self._listener.enabled()

    def listener_status(self) -> tuple[bool, str]:
        if self._listener.last_error():
            return False, self._listener.last_error()
        if self._listener.enabled():
            return True, self._listener.status_label()
        return False, ""

    def clublog_enabled(self) -> bool:
        return self._settings_store.get_string("integration_clublog_enabled", "false") == "true"

    def clublog_status(self) -> tuple[bool, str]:
        config = self._clublog_config()
        if not config.enabled:
            return False, ""
        ready, detail = self.validate_clublog_config()
        return ready, "" if ready else detail

    def pending_upload_count(self) -> int:
        return self._uploader.pending_count() + self._qrz_uploader.pending_count()

    def poll_logged_qsos(self) -> list[LoggedAdifEvent]:
        return self._listener.poll()

    def poll_upload_results(self) -> list[tuple[str, bool, str]]:
        # Returns a list of (Service_Name, Success, Detail)
        items = []
        for res in self._uploader.poll_results():
            items.append(("Club Log", res.success, res.detail))
        for res in self._qrz_uploader.poll_results():
            items.append(("QRZ", res.success, res.detail))
        return items

    def enqueue_uploads(self, adif_text: str, source: str) -> list[str]:
        queued = []
        if self._enqueue_clublog_upload(adif_text, source):
            queued.append("Club Log")
        if self._enqueue_qrz_upload(adif_text, source):
            queued.append("QRZ")
        return queued

    def _enqueue_clublog_upload(self, adif_text: str, source: str) -> ClubLogUploadJob | None:
        config = self._clublog_config()
        if not self.should_upload_source(source):
            return None
        if not (config.enabled and config.email and config.password and config.callsign and config.api_key):
            return None
        return self._uploader.enqueue(config, adif_text)

    def _enqueue_qrz_upload(self, adif_text: str, source: str) -> QrzUploadJob | None:
        normalized = source.strip().lower()
        if normalized == "manual":
            should_upload = self._settings_store.get_string("integration_qrz_upload_manual", "false") == "true"
        elif normalized in {"udp", "wsjtx_udp", "jtdx_udp", "udp_integration"}:
            should_upload = self._settings_store.get_string("integration_qrz_upload_udp", "true") == "true"
        else:
            should_upload = False

        if not should_upload:
            return None

        enabled = self._settings_store.get_string("integration_qrz_enabled", "false") == "true"
        api_key = self._settings_store.get_string("integration_qrz_api_key", "")
        if not (enabled and api_key):
            return None

        config = QrzLogbookConfig(enabled=enabled, api_key=api_key)
        return self._qrz_uploader.enqueue(config, adif_text)

    def retry_pending_uploads(self) -> int:
        self._uploader.start()
        self._qrz_uploader.start()
        return self._uploader.retry_pending() + self._qrz_uploader.retry_pending()

    def inject_test_logged_qso(self, callsign: str = "PY0TEST") -> None:
        adif = (
            f"<CALL:{len(callsign)}>{callsign}"
            "<QSO_DATE:8>20260326"
            "<TIME_ON:6>123000"
            "<FREQ:6>14.074"
            "<MODE:3>FT8"
            "<COMMENT:20>PyCQLog UDP monitor"
            "<EOR>"
        )
        self._listener.inject(LoggedAdifEvent(source_app="PyCQLog Test", adif_text=adif))

    def enqueue_test_clublog_upload(self) -> tuple[bool, str]:
        ready, detail = self.validate_clublog_config()
        if not ready:
            return False, detail
        config = self._clublog_config()
        adif = (
            f"<CALL:{len(config.callsign)}>{config.callsign}"
            "<QSO_DATE:8>20260326"
            "<TIME_ON:6>123500"
            "<FREQ:5>7.040"
            "<MODE:2>CW"
            "<COMMENT:24>PyCQLog Club Log test"
            "<EOR>"
        )
        self._uploader.enqueue(config, adif)
        return True, "Club Log test job queued."

    def should_upload_source(self, source: str) -> bool:
        normalized = source.strip().lower()
        if normalized == "manual":
            return self._settings_store.get_string("integration_clublog_upload_manual", "false") == "true"
        if normalized in {"udp", "wsjtx_udp", "jtdx_udp", "udp_integration"}:
            return self._settings_store.get_string("integration_clublog_upload_udp", "true") == "true"
        return False

    def validate_clublog_config(self) -> tuple[bool, str]:
        config = self._clublog_config()
        if not config.enabled:
            return False, "Club Log disabled."
        if not config.endpoint.startswith(("https://", "http://")):
            return False, "Club Log endpoint must start with http:// or https://."
        if not config.email:
            return False, "Club Log email is required."
        if not config.password:
            return False, "Club Log app password is required."
        if not config.callsign:
            return False, "Club Log callsign is required."
        if not config.api_key:
            return False, "Club Log API key is required."
        return True, "Club Log ready"

    def _clublog_config(self) -> ClubLogConfig:
        return ClubLogConfig(
            enabled=self._settings_store.get_string("integration_clublog_enabled", "false") == "true",
            email=self._settings_store.get_string("integration_clublog_email", ""),
            password=self._settings_store.get_string("integration_clublog_password", ""),
            callsign=self._settings_store.get_string("integration_clublog_callsign", ""),
            api_key=self._settings_store.get_string("integration_clublog_api_key", ""),
            endpoint=self._settings_store.get_string("integration_clublog_endpoint", "https://clublog.org/realtime.php"),
            interval_seconds=max(5, int(self._settings_store.get_string("integration_clublog_interval", "30") or "30")),
        )


def _read_qt_utf8(payload: bytes, offset: int) -> tuple[str, int]:
    if offset + 4 > len(payload):
        return "", len(payload)
    (size,) = struct.unpack(">I", payload[offset : offset + 4])
    offset += 4
    if size == 0xFFFFFFFF:
        return "", offset
    end = min(len(payload), offset + size)
    value = payload[offset:end].decode("utf-8", errors="ignore")
    return value, end
