# Quick Start - en

## Purpose

This guide helps you get `PyCQLog` running in a few minutes.

## In 5 minutes

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the application:

```bash
pip install -e .
```

3. Start the app:

```bash
./pycqlog
```

If you already have a `.deb` package, you can also install it with:

```bash
sudo apt install ./pycqlog_<version>_all.deb
```

4. Review these settings:

- `Settings > Language`
- `Settings > Theme`
- `Settings > Directories`
- `Settings > ADIF`

5. Create or select a `Logbook`.

6. Save a manual QSO or import an `ADIF` file.

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

## Dashboard

Menu:

```text
Dashboard > Open Dashboard
```

Use it to follow:

- QSO volume
- active bands and modes
- operating hours
- top callsigns
- estimated DXCC, CQ, and WPX indicators

## JTDX or WSJT-X integration

Menu:

```text
Settings > Integrations > JTDX / Club Log
```

To begin:

1. enable the `UDP` listener
2. set `host` and `port`
3. configure `JTDX` or `WSJT-X` to send `Logged ADIF`
4. monitor results in `Settings > Integrations > Monitor`

## Where to go next

- full guide: [user_guide_en.md](user_guide_en.md)
- FAQ: [faq_en.md](faq_en.md)
- integrations: [integracoes.md](integracoes.md)
- ADIF import: [importacao_adif.md](importacao_adif.md)
