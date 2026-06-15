# HuntOverlay.py — thin entry shim.
#
# The implementation now lives in the `huntoverlay` package. This file is
# kept as the entry point so the PyInstaller build (and `python HuntOverlay.py`)
# keeps working unchanged.
#
# Project overview
# This app is a click through, always on top overlay that draws POIs (points of
# interest) inside a user defined rectangle on the screen.
#
# Runtime folder
#   %LOCALAPPDATA%\HuntOverlay
#
# Seeded files on first run
#   data.json     POI coordinate dataset
#   poiData.json  style definitions for POI types
#   config.json   user settings, per map rect ratios, keybinds, hidden POIs
#
# Core behavior
#   Loads data.json and poiData.json from %LOCALAPPDATA%\HuntOverlay
#   Applies a screen rectangle per map based on detected aspect ratio
#   Draws POIs using normalized coordinates derived from a 4096x4096 grid
#
# Package layout (see huntoverlay/):
#   constants, geometry, mapdata, paths, config, data_source  — pure core
#   win32, qt_adapters, runtime                                — platform/Qt glue
#   widgets/dialogs.py, widgets/panel.py, overlay.py           — Qt UI
#   __main__.py                                                — entry point

from huntoverlay.__main__ import main

if __name__ == "__main__":
    main()
