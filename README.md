# PyCQLog

Desktop logger for amateur radio built with Python and PyQt.

`PyCQLog` is a public open source application focused on practical radio operation, local-first data ownership, and an evolvable architecture for integrations such as ADIF, WSJT-X/JTDX, and Club Log.

## Why This Project Exists

`PyCQLog` was born from the need for a modern amateur radio logging application for Linux, written in a more accessible and current language, so more volunteers can join the development effort over time.

The project aims to combine practical daily operation with a codebase that is easier to understand, extend, review, and maintain collaboratively.

`PyCQLog` is open to everyone who wants to contribute, develop features, test the application, use it on the air, report bugs, suggest improvements, review code, improve documentation, or help shape its direction.

## Highlights

- manual QSO entry with CRUD
- local SQLite persistence
- multiple logbooks with active log selection
- reusable operator and station profiles
- ADIF import/export
- dashboard with operating statistics
- PT-BR and English interface
- light, dark, and system theme
- initial WSJT-X / JTDX UDP integration
- configurable realtime Club Log and QRZ.com queues
- LoTW (TQSL) automated ADIF export and signing
- QRZ.com Callbook automatic lookup

## Status

The project is under active development and already usable for early operation and validation.

## Current Scope

The current public version already includes:

- layered architecture
- local SQLite persistence
- PyQt6 desktop UI for QSO CRUD
- callsign history
- PT-BR and English support
- persistent settings
- operational dashboard
- multiple logbooks with active log selection
- reusable operator and station profiles
- improved local prefix resolution for DXCC, WAZ, and WPX
- `system`, `light`, and `dark` theme support
- ADIF import and export
- initial WSJT-X / JTDX UDP integration
- configurable realtime Club Log and QRZ.com queues for UDP and manual QSOs
- LoTW (TQSL) automated ADIF export and signing
- QRZ.com Callbook automatic lookup

## Documentacao

- Current project documentation: [docs/README.md](docs/README.md)
- Quick start in Portuguese: [docs/inicio_rapido_pt-BR.md](docs/inicio_rapido_pt-BR.md)
- Quick start in English: [docs/quick_start_en.md](docs/quick_start_en.md)
- User guide in Portuguese: [docs/guia_do_usuario_pt-BR.md](docs/guia_do_usuario_pt-BR.md)
- User guide in English: [docs/user_guide_en.md](docs/user_guide_en.md)
- FAQ in Portuguese: [docs/faq_pt-BR.md](docs/faq_pt-BR.md)
- FAQ in English: [docs/faq_en.md](docs/faq_en.md)

## Instalacao para desenvolvimento

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run

```bash
./pycqlog
```

Or via module:

```bash
PYTHONPATH=src python3 -m pycqlog.main
```

## Debian Package

To build a `.deb` package locally:

```bash
bash packaging/build_deb.sh
```

The package will be generated under `dist/deb/`.

To install it on another Linux computer:

```bash
sudo apt install ./dist/deb/pycqlog_<version>_all.deb
```

Using `apt` is recommended so the system can also install package dependencies such as `python3-pyqt6`.

## Linux Notes

If Qt fails with the `xcb` plugin, install:

```bash
sudo apt-get install -y \
  libxcb-cursor0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-render-util0
```

If your session uses Wayland, the `pycqlog` launcher already tries Wayland automatically.

## Testing

```bash
pytest
```

## Publicacao e colaboracao

- License: [MIT](LICENSE)
- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)
