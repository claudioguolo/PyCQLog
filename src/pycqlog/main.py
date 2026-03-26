from pycqlog.bootstrap import build_desktop_app


def main() -> int:
    app = build_desktop_app()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
