from __future__ import annotations

import argparse
import sys

from pycqlog.bootstrap import build_desktop_app
from pycqlog.service_main import main as service_main


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pycqlog", add_help=True)
    parser.add_argument(
        "--service",
        action="store_true",
        help="Run only the background service when used alone.",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Run only the desktop UI when used alone.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_argv = argv or sys.argv[1:]
    parser = _build_parser()
    args, qt_args = parser.parse_known_args(raw_argv)

    if args.service and not args.ui:
        return service_main()

    desktop_app = build_desktop_app()
    return desktop_app.run([sys.argv[0], *qt_args])


if __name__ == "__main__":
    raise SystemExit(main())
