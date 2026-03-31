#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_ROOT="${PROJECT_ROOT}/build/deb"
DIST_ROOT="${PROJECT_ROOT}/dist/deb"
PKG_ROOT="${BUILD_ROOT}/pkg"

readarray -t METADATA < <(
  PROJECT_ROOT="${PROJECT_ROOT}" python3 -c '
from pathlib import Path
import os
import tomllib
project_root = Path(os.environ["PROJECT_ROOT"])
data = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
project = data["project"]
print(project["name"])
print(project["version"])
print(project["description"])
'
)

PACKAGE_NAME="${METADATA[0]}"
PACKAGE_VERSION="${METADATA[1]}"
PACKAGE_DESCRIPTION="${METADATA[2]}"
ARCHITECTURE="all"
OUTPUT_PACKAGE="${DIST_ROOT}/${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCHITECTURE}.deb"

rm -rf "${PKG_ROOT}"
mkdir -p \
  "${PKG_ROOT}/DEBIAN" \
  "${PKG_ROOT}/usr/bin" \
  "${PKG_ROOT}/usr/lib/${PACKAGE_NAME}/src" \
  "${PKG_ROOT}/usr/share/applications" \
  "${PKG_ROOT}/usr/share/icons/hicolor/scalable/apps" \
  "${DIST_ROOT}"

cat > "${PKG_ROOT}/DEBIAN/control" <<EOF
Package: ${PACKAGE_NAME}
Version: ${PACKAGE_VERSION}
Section: hamradio
Priority: optional
Architecture: ${ARCHITECTURE}
Maintainer: Claudio - PY9MT
Depends: python3 (>= 3.11), python3-pyqt6, libxcb-cursor0 | libxcb-cursor0t64, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-render-util0
Description: ${PACKAGE_DESCRIPTION}
 Desktop logger for amateur radio built with Python and PyQt.
 Includes local logging, ADIF workflows, dashboard, and initial
 integrations for WSJT-X / JTDX and Club Log.
EOF

cp -R "${PROJECT_ROOT}/src/pycqlog" "${PKG_ROOT}/usr/lib/${PACKAGE_NAME}/src/"
cp "${PROJECT_ROOT}/LICENSE" "${PKG_ROOT}/usr/lib/${PACKAGE_NAME}/LICENSE"
cp "${PROJECT_ROOT}/README.md" "${PKG_ROOT}/usr/lib/${PACKAGE_NAME}/README.md"
cp "${PROJECT_ROOT}/packaging/deb_launcher.sh" "${PKG_ROOT}/usr/bin/${PACKAGE_NAME}"
cp "${PROJECT_ROOT}/packaging/pycqlog.desktop" "${PKG_ROOT}/usr/share/applications/${PACKAGE_NAME}.desktop"
cp "${PROJECT_ROOT}/packaging/pycqlog.svg" "${PKG_ROOT}/usr/share/icons/hicolor/scalable/apps/${PACKAGE_NAME}.svg"

chmod 0755 "${PKG_ROOT}/usr/bin/${PACKAGE_NAME}"
find "${PKG_ROOT}/usr/lib/${PACKAGE_NAME}" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "${PKG_ROOT}/usr/lib/${PACKAGE_NAME}" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
find "${PKG_ROOT}/usr/lib/${PACKAGE_NAME}" -type d -exec chmod 0755 {} +
find "${PKG_ROOT}/usr/lib/${PACKAGE_NAME}" -type f -exec chmod 0644 {} +

dpkg-deb --build --root-owner-group "${PKG_ROOT}" "${OUTPUT_PACKAGE}"

echo "Built package: ${OUTPUT_PACKAGE}"
