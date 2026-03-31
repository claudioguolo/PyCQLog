# Quick Start - en

## Purpose

This guide gets `PyCQLog` running quickly, with a focus on ease of use.

The project is designed so you can:

- open the UI and log a QSO in a few minutes
- import or export ADIF without too many steps
- integrate with JTDX or WSJT-X
- later grow into a remote daemon setup if your station needs it

## Operating styles

`PyCQLog` can be used in three ways:

1. Local desktop, when everything runs on the same machine.
2. Daemon only, for a small server or Raspberry Pi.
3. Remote UI, when the desktop connects to a daemon on another host.

## In a few minutes

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the application:

```bash
pip install -e .
```

3. Start the mode you need:

Full local desktop:

```bash
pycqlog
```

Daemon only:

```bash
pycqlog --service
```

UI only:

```bash
pycqlog --ui
```

If you already have a `.deb` package, you can also install it with:

```bash
sudo apt install ./pycqlog_<version>_all.deb
```

## First configuration

Review these items:

- `Settings > Language`
- `Settings > Theme`
- `Settings > Directories`
- `Settings > ADIF`
- `Integrations > Remotes`

If the UI will connect to a remote daemon, configure in `Integrations > Remotes`:

- daemon IP or host
- port
- authentication code

## First manual QSO

In the main window:

1. enter `callsign`
2. adjust `date` and `time`
3. enter `frequency`
4. choose `mode`
5. click `Save QSO`

The application will:

- validate the key fields
- resolve the band from frequency when possible
- save the QSO in the active logbook

## Import ADIF

Menu:

```text
Settings > ADIF > Import ADIF
```

Flow:

1. choose an `.adi` or `.adif` file
2. review the preview
3. select or unselect records
4. edit fields if needed
5. confirm the import

## Export ADIF

Menu:

```text
Settings > ADIF > Export ADIF
```

You can export:

- the whole active logbook
- by callsign
- by date range
- by band
- by mode

## JTDX or WSJT-X integration

Menu:

```text
Integrations > Remotes
```

For local capture:

1. enable the `UDP` listener
2. set `host` and `port`
3. configure `JTDX` or `WSJT-X` to send `Logged ADIF`
4. monitor results in `Integrations > Integration Monitor`

## Remote mode

Files used:

- UI: `~/.config/pycqlog/pycqlog_ui.conf`
- daemon: `~/.config/pycqlog/pycqlog_daemon.conf`

Example:

- on the server, run `pycqlog --service`
- on the client, set `service_remote_enabled = true`
- open the UI with `pycqlog --ui`

## Where to go next

- full guide: [user_guide_en.md](user_guide_en.md)
- FAQ: [faq_en.md](faq_en.md)
- integrations: [integracoes.md](integracoes.md)
- ADIF import: [importacao_adif.md](importacao_adif.md)
