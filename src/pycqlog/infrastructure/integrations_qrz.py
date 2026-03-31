from __future__ import annotations

import hashlib
import json
import queue
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib import error, parse, request

from pycqlog.infrastructure.sync_audit import audit_sync_event, parse_adif_summary


@dataclass(slots=True)
class QrzLogbookConfig:
    enabled: bool
    api_key: str


@dataclass(slots=True)
class QrzUploadJob:
    job_id: str
    config: QrzLogbookConfig
    adif_text: str
    created_at: str
    signature: str


@dataclass(slots=True)
class QrzUploadResult:
    success: bool
    detail: str
    job_id: str = ""


class QrzUploader:
    def __init__(self, queue_path: Path) -> None:
        self._queue_path = queue_path
        self._queue_path.parent.mkdir(parents=True, exist_ok=True)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._queue: queue.Queue[QrzUploadJob] = queue.Queue()
        self._results: queue.Queue[QrzUploadResult] = queue.Queue()
        self._last_upload_at = 0.0
        self._pending_jobs: dict[str, QrzUploadJob] = self._load_pending_jobs()
        self._enqueued_ids: set[str] = set()
        self.retry_pending()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="pycqlog-qrz-uploader", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None

    def enqueue(self, config: QrzLogbookConfig, adif_text: str) -> QrzUploadJob | None:
        if not config.enabled:
            return None
        signature = hashlib.sha1(
            f"{config.api_key}|{adif_text}".encode("utf-8", errors="ignore")
        ).hexdigest()
        for pending in self._pending_jobs.values():
            if pending.signature == signature:
                return pending
        job = QrzUploadJob(
            job_id=hashlib.sha1(f"qrz:{time.time()}:{adif_text}".encode("utf-8", errors="ignore")).hexdigest(),
            config=config,
            adif_text=adif_text,
            created_at=datetime.utcnow().isoformat(),
            signature=signature,
        )
        self._pending_jobs[job.job_id] = job
        self._save_pending_jobs()
        self._enqueue_runtime(job)
        self.start()
        audit_sync_event(
            "qrz",
            state="queued",
            job_id=job.job_id,
            action="insert",
            adif_text=adif_text,
            detail="Queued for QRZ upload",
            attempts=0,
        )
        return job

    def retry_pending(self) -> int:
        count = 0
        for job in self._pending_jobs.values():
            if job.job_id in self._enqueued_ids:
                continue
            self._enqueue_runtime(job)
            count += 1
            audit_sync_event(
                "qrz",
                state="pending",
                job_id=job.job_id,
                action="insert",
                adif_text=job.adif_text,
                detail="Pending QRZ job moved back to runtime queue",
            )
        return count

    def pending_count(self) -> int:
        return len(self._pending_jobs)

    def poll_results(self) -> list[QrzUploadResult]:
        items: list[QrzUploadResult] = []
        while True:
            try:
                items.append(self._results.get_nowait())
            except queue.Empty:
                break
        return items

    def _enqueue_runtime(self, job: QrzUploadJob) -> None:
        self._queue.put(job)
        self._enqueued_ids.add(job.job_id)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                job = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            # QRZ API shouldn't be hammered too fast, applying a 5 second throttle
            wait_seconds = max(0.0, 5.0 - (time.time() - self._last_upload_at))
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            result = self._upload(job)
            self._last_upload_at = time.time()
            self._enqueued_ids.discard(job.job_id)
            if result.success:
                self._pending_jobs.pop(job.job_id, None)
                self._save_pending_jobs()
                audit_sync_event(
                    "qrz",
                    state="success",
                    job_id=job.job_id,
                    action="insert",
                    adif_text=job.adif_text,
                    detail=result.detail,
                )
            else:
                audit_sync_event(
                    "qrz",
                    state="failed",
                    job_id=job.job_id,
                    action="insert",
                    adif_text=job.adif_text,
                    detail=result.detail,
                )
            self._results.put(result)

    def _upload(self, job: QrzUploadJob) -> QrzUploadResult:
        summary = parse_adif_summary(job.adif_text)
        audit_sync_event(
            "qrz",
            state="attempt",
            job_id=job.job_id,
            action="insert",
            adif_text=job.adif_text,
            callsign=summary["callsign"],
            qso_date=summary["qso_date"],
            time_on=summary["time_on"],
            band=summary["band"],
            mode=summary["mode"],
            endpoint="https://logbook.qrz.com/api",
            detail="Posting QRZ logbook job",
        )
        payload = {
            "KEY": job.config.api_key,
            "ACTION": "INSERT",
            "ADIF": job.adif_text,
        }
        encoded = parse.urlencode(payload).encode("utf-8")
        req = request.Request("https://logbook.qrz.com/api", data=encoded, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("User-Agent", "PyCQLog/1.0")
        try:
            with request.urlopen(req, timeout=20) as response:
                status_code = getattr(response, "status", 200)
                body = response.read().decode("utf-8", errors="ignore").strip()
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore").strip()
            return QrzUploadResult(
                success=False,
                detail=f"QRZ HTTP {exc.code}: {detail[:200] or exc.reason}",
                job_id=job.job_id,
            )
        except error.URLError as exc:
            return QrzUploadResult(success=False, detail=str(exc), job_id=job.job_id)

        # QRZ returns RESULT=OK or RESULT=FAIL
        body_upper = body.upper()
        if "RESULT=FAIL" in body_upper or "REASON=" in body_upper:
            return QrzUploadResult(success=False, detail=f"QRZ API Error: {body[:200]}", job_id=job.job_id)
        
        success = 200 <= status_code < 300
        detail = f"QRZ OK: {body[:100]}"
        return QrzUploadResult(success=success, detail=detail, job_id=job.job_id)

    def _load_pending_jobs(self) -> dict[str, QrzUploadJob]:
        if not self._queue_path.exists():
            return {}
        try:
            raw = json.loads(self._queue_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        jobs: dict[str, QrzUploadJob] = {}
        for item in raw if isinstance(raw, list) else []:
            try:
                config_raw = item["config"]
                job = QrzUploadJob(
                    job_id=str(item["job_id"]),
                    config=QrzLogbookConfig(
                        enabled=bool(config_raw["enabled"]),
                        api_key=str(config_raw["api_key"]),
                    ),
                    adif_text=str(item["adif_text"]),
                    created_at=str(item["created_at"]),
                    signature=str(item.get("signature") or ""),
                )
            except (KeyError, TypeError, ValueError):
                continue
            if not job.signature:
                job.signature = hashlib.sha1(
                    f"{job.config.api_key}|{job.adif_text}".encode("utf-8", errors="ignore")
                ).hexdigest()
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
