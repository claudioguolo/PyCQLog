# User Guide - en

## Purpose

This guide is for people who want to use `PyCQLog` in practice. It covers installation, first-time setup, daily operation, ADIF workflows, dashboard usage, and integrations.

## What PyCQLog does today

`PyCQLog` is a desktop application for amateur radio focused on local-first operation and operator-controlled data.

Current highlights:

- manual QSO entry
- QSO edit and delete
- callsign search
- callsign history
- multiple logbooks
- operator and station profiles
- ADIF import
- ADIF export
- operating dashboard
- initial `WSJT-X / JTDX` integration
- configurable `Club Log` queue
- `pt-BR` and `en` interface

## Requirements

- Linux with a graphical desktop session
- Python `3.11` or newer
- `PyQt6`

If Qt fails because of the `xcb` plugin, install:

```bash
sudo apt-get install -y \
  libxcb-cursor0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-render-util0
```

## Local installation

Inside the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Starting the application

Recommended:

```bash
./pycqlog
```

Alternative:

```bash
PYTHONPATH=src python3 -m pycqlog.main
```

## First run checklist

Review these items on first launch:

1. interface language
2. visual theme
3. data directory
4. default logs directory
5. active logbook

## Main window layout

The main window includes:

- manual QSO form
- active logbook selector
- recent QSO list
- quick band and mode filters
- callsign history panel
- menu bar for settings, dashboard, and help

## Logbooks

A `logbook` is the main operating context. It can represent:

- your main log
- a contest log
- a portable operation
- an expedition
- a secondary station

### Changing the active logbook

Use the selector at the top of the main window.

When the active logbook changes:

- the QSO list is reloaded
- callsign history follows the selected logbook
- the dashboard switches to that logbook
- operator and station defaults may change

### Managing logbooks

Menu:

```text
Settings > Logbooks
```

In the logbook dialog you can:

- create a new logbook
- edit name and description
- assign an operator profile
- assign a station profile
- delete a logbook

## Operator and station profiles

Profiles are reusable operating presets.

### Supported fields

- profile name
- type
- callsign
- QTH
- locator
- power
- antenna
- notes

### Where to manage them

Menu:

```text
Settings > Profiles
```

### Why use them

- to reuse operator and station defaults
- to standardize data across logbooks
- to reduce repeated typing

## Manual QSO entry

The form supports:

- callsign
- date
- time
- frequency in MHz
- mode
- sent RST
- received RST
- operator
- station
- notes

### Saving a QSO

1. fill in the required fields
2. click `Save QSO`

The application:

- normalizes the callsign
- normalizes the mode
- tries to resolve the band from frequency
- validates required fields
- saves the QSO in the active logbook

### Editing a QSO

1. select a row in the table
2. click `Edit Selected`
3. change the fields
4. click `Update QSO`

### Deleting a QSO

1. select a row in the table
2. click `Delete Selected`
3. confirm the action

## Search and quick filters

### Callsign search

Use the search field above the main table.

### Quick filters

Above the table there are clickable filters for:

- band
- mode

You can combine them and clear everything with `Clear filters`.

## Callsign history

When you type or select a callsign, the side panel shows previous QSOs with that exact callsign inside the active logbook.

This helps you review:

- date
- time
- band
- mode
- RST

## Dashboard

Menu:

```text
Dashboard > Open Dashboard
```

The dashboard reflects the active logbook.
Award counters now use a curated local prefix reference with better handling for slash calls, although they are still not a full official awards database.

### Current summary cards

- total QSOs
- unique callsigns
- active bands
- active modes
- DXCC based on the local prefix reference
- CQ zones
- WPX prefixes

### Current charts

- QSOs by band
- QSOs by mode
- QSOs by day
- monthly trend
- QSOs by hour
- top callsigns

### Time filters

You can switch between:

- whole log
- last 7 days
- last 30 days
- last 12 months

## Language and theme

### Language

Menu:

```text
Settings > Language
```

Current languages:

- `pt-BR`
- `en`

### Theme

Menu:

```text
Settings > Theme
```

Available modes:

- `system`
- `light`
- `dark`

## Directories

Menu:

```text
Settings > Directories
```

### Data directory

Used for:

- SQLite database
- local application data

### Default logs directory

Used as the default location for:

- ADIF import
- ADIF export

## ADIF preferences

Menu:

```text
Settings > ADIF > ADIF Preferences
```

You can define:

- default operator callsign
- default station callsign
- default export filename prefix

## ADIF import

Menu:

```text
Settings > ADIF > Import ADIF
```

### Workflow

1. select an `.adi` or `.adif` file
2. review the preview dialog
3. filter by status if needed
4. select or unselect records
5. edit key fields if required
6. confirm the import

### Preview information

- total records
- ready
- skipped
- failed

### Editable preview fields

- callsign
- date
- time
- frequency
- mode

## ADIF export

Menu:

```text
Settings > ADIF > Export ADIF
```

### Available filters

- callsign
- start date
- end date
- band
- mode

The export filename uses the configured ADIF export prefix.

## WSJT-X / JTDX integration

Menu:

```text
Settings > Integrations > JTDX / Club Log
```

### What exists today

- UDP listener for `Logged ADIF`
- automatic save into the active logbook
- Club Log upload queue
- upload controls for UDP-based QSOs and manually saved QSOs

### Main settings

- enable UDP capture
- local host
- UDP port

### Practical tip

Configure the same UDP port in both `WSJT-X / JTDX` and `PyCQLog`.

## Club Log integration

In the same integration dialog you can configure:

- email
- app password
- primary callsign
- API key
- endpoint
- minimum interval between uploads

### Notes

- uploads run asynchronously
- pending uploads are kept in a local queue
- pending work can be resumed after restarting the app

## Integration monitor

Menu:

```text
Settings > Integrations > Monitor
```

The monitor shows:

- UDP listener status
- Club Log status
- packets received
- QSOs saved
- completed uploads
- failures
- pending jobs
- event history

### Available actions

- `Test UDP`
- `Test Club Log`
- `Retry pending`
- `Clear history`

## Where data is stored

By default:

- config: `~/.config/pycqlog`
- data: `~/.local/share/pycqlog`

If changed by the user, those locations may be different.

## Common problems

### The UI does not open

Check:

- whether `PyQt6` is installed
- whether the required Qt `xcb` libraries are installed

### A JTDX QSO is not saved automatically

Check:

- whether UDP capture is enabled
- whether host and port match the external application
- whether the integration monitor shows received packets

### Club Log is not uploading

Check:

- email
- app password
- primary callsign
- API key
- network connectivity
- configured endpoint

### The dashboard looks empty

Check:

- whether the active logbook is the expected one
- whether the current time filter is too restrictive

## Good usage practices

- separate different operating contexts into different logbooks
- use profiles to standardize operator and station data
- confirm the active logbook before logging QSOs
- review ADIF imports before confirming
- keep the integration monitor open while testing external integrations

## Quick start summary

If you want the shortest path to using the app:

1. open `PyCQLog`
2. create or choose the correct logbook
3. configure language, theme, and directories
4. adjust ADIF defaults and profiles
5. log manually or import ADIF
6. open the dashboard to follow progress
7. if you use digital modes, enable `WSJT-X / JTDX` integration
