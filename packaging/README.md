# Debian Packaging

This directory contains the files used to build a `.deb` package for `PyCQLog`.

## Build

From the project root:

```bash
bash packaging/build_deb.sh
```

The generated package will be placed in:

```text
dist/deb/
```

## Install on another computer

Recommended:

```bash
sudo apt install ./dist/deb/pycqlog_<version>_all.deb
```

Using `apt` is preferred because it can also resolve system dependencies such as `python3-pyqt6`.

## Package contents

The package installs:

- application source under `/usr/lib/pycqlog`
- launcher under `/usr/bin/pycqlog`
- desktop entry under `/usr/share/applications/pycqlog.desktop`
- icon under `/usr/share/icons/hicolor/scalable/apps/pycqlog.svg`
