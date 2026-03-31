from __future__ import annotations

import os
import signal
import threading
from contextlib import suppress

from pycqlog.bootstrap import build_app_context
from pycqlog.infrastructure.app_logging import get_logger
from pycqlog.infrastructure.service_api import ServiceApiServer
from pycqlog.infrastructure.station_service import StationService


logger = get_logger("service_main")


def main() -> int:
    context = build_app_context(allow_remote=False)
    service = StationService(
        settings_store=context.settings_store,
        save_qso_use_case=context.save_qso,
        get_active_logbook_use_case=context.get_active_logbook,
        queue_path=context.config_dir / "clublog_queue.json",
    )
    stop_event = threading.Event()
    api_host = os.environ.get(
        "PYCQLOG_SERVICE_HOST",
        context.settings_store.get_string("service_bind_host", "127.0.0.1") or "127.0.0.1",
    )
    api_port = int(
        os.environ.get(
            "PYCQLOG_SERVICE_PORT",
            context.settings_store.get_string("service_bind_port", "8746") or "8746",
        )
        or "8746"
    )
    auth_code = context.settings_store.get_string("service_auth_code", "")
    api_server = ServiceApiServer((api_host, api_port), service, context, auth_code)
    api_thread = threading.Thread(target=api_server.serve_forever, name="pycqlog-service-api", daemon=True)

    def _request_stop(signum: int, _frame) -> None:
        logger.info("Signal received. signum=%s", signum)
        stop_event.set()
        api_server.shutdown()

    for signum in (signal.SIGINT, signal.SIGTERM):
        with suppress(ValueError):
            signal.signal(signum, _request_stop)

    logger.info(
        "Starting PyCQLog service. api_host=%s api_port=%s auth_enabled=%s",
        api_host,
        api_port,
        bool(auth_code.strip()),
    )
    api_thread.start()
    try:
        service.run_forever(stop_event=stop_event)
    finally:
        api_server.server_close()
        logger.info("PyCQLog service stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
