# FAQ - en

## Is `PyCQLog` already usable for daily operation?

Yes. The application already supports local operation with manual logging, ADIF import and export, multiple logbooks, a dashboard, and initial `WSJT-X / JTDX` integration.

## Where is my data stored?

QSOs are stored in a local `SQLite` database. The database location depends on the configured `Data directory` in `Settings > Directories`.

## Can I use more than one log?

Yes. The system supports multiple `logbooks`, with one active log at a time.

## Can I switch the interface language?

Yes. The app currently supports `pt-BR` and `en`, and the translation structure is ready for more languages.

## Can I use a dark theme?

Yes. The app supports `system`, `light`, and `dark`.

## Can the application import large ADIF files?

Yes. The import flow already supports preview, individual record selection, field editing, and basic deduplication.

## Does ADIF export support filters?

Yes. You can export by `callsign`, `date range`, `band`, and `mode`.

## Can `JTDX` or `WSJT-X` already send QSOs automatically?

Yes, through the initial `UDP Logged ADIF` integration. It is best to validate with the integration monitor open first.

## Is `Club Log` upload already available?

There is initial support with a persistent queue and monitoring. In real operation, you should validate credentials, endpoint configuration, and queue behavior carefully.

## Are the award counters in the dashboard accurate?

They are more reliable than in the early versions because they now use a curated local prefix reference and more conservative matching. They are still not a full official awards database and should not be treated as a definitive confirmation source.

## Is there already a `.deb` package?

Not yet in the current codebase. The application is already in a good position for that as a next distribution step.

## What if the UI does not start because of a Qt error?

On Linux systems using `xcb`, install:

```bash
sudo apt-get install -y \
  libxcb-cursor0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-render-util0
```

## Where should I start for a quick test?

Start with:

- [quick_start_en.md](quick_start_en.md)
- [user_guide_en.md](user_guide_en.md)
