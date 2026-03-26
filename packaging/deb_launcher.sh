#!/usr/bin/env bash

set -euo pipefail

APP_ROOT="/usr/lib/pycqlog"

export PYTHONPATH="${APP_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

if [[ -z "${QT_QPA_PLATFORM:-}" ]]; then
  if [[ "${XDG_SESSION_TYPE:-}" == "wayland" ]] && [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
    export QT_QPA_PLATFORM="wayland"
  elif [[ -n "${DISPLAY:-}" ]]; then
    export QT_QPA_PLATFORM="xcb"
  fi
fi

exec python3 -m pycqlog.main "$@"
