# HuntOverlay

> English | [简体中文](README.zh-CN.md)

A lightweight, real-time Windows map overlay that displays Hunt: Showdown POI
markers on screen. It runs as a standalone window with click-through, per-category
POI configuration, and locally persisted settings, and never modifies game files.

This is a fork of [HuntOverlay-by-sKhaled](https://github.com/uzpj/HuntOverlay-by-sKhaled),
focused on Chinese localization, portable Windows builds, and ongoing feature and
logic improvements. The original author's documentation has been folded into this README.

---

## Safety Notice

The only official repository of the original Hunt Map Overlay by sKhaled is:

https://github.com/uzpj/HuntOverlay-by-sKhaled

The original author's official builds are published solely through that repository's
Releases page.

If you download an executable from an unknown source, it may contain modified or
unsafe code. Verify the source before running any executable. Treat any repository
distributing builds with external download links or modified binaries as untrusted
until verified.

## Disclaimer

This project is not affiliated with or endorsed by Crytek.

- Use at your own risk. No warranty is provided.
- This tool does not modify game files, nor read, inject into, or modify game memory.
- It is intended for informational and accessibility purposes only.

Always comply with the game's Terms of Service.

## Credits

- POI data provided by Kamille (https://github.com/waibcam) and the Discord community.
- The original implementation was created by sKhaled.

---

## Features

- Real-time on-screen map overlay
- Support for all Hunt: Showdown maps
- Configurable POI categories
- Enable or disable POIs per category
- Per-category color selection
- Global POI size scaling
- Click-through; does not block game input
- Hotkey-driven interaction
- Locally saved user configuration
- Per-category soft-hiding of specific POIs
- One-click select-all / deselect-all for POI categories
- Control panel anchored to the right edge, vertically centered, clear of the overlay
- Can be packaged as a portable single-file exe
- Localized Chinese UI

## How It Works

The tool loads map POI data from JSON files and projects markers into a configurable
on-screen rectangle. Coordinates are converted from Hunt: Showdown's 4096x4096 map grid
into normalized screen coordinates, then drawn as simple graphics balancing clarity and
performance.

It does not modify game files, inject into the game process, or hook the game. It is
simply a standalone layered window rendered above the game window.

## File Storage

On first launch the program creates the following directory:

```text
%LOCALAPPDATA%\HuntOverlay\
```

It contains:

- `data.json` — map POI coordinate data.
- `poiData.json` — POI style definitions, such as radius and default colors.
- `config.json` — user settings: enabled categories, colors, current map, hidden POIs, and global size scale.

Runtime changes to these files persist across restarts and updates.

## Hotkeys

Overlay controls:

| Hotkey | Action |
|--------|--------|
| Backtick `` ` `` (usually below Esc) | Toggle master switch |
| Tab | Show or hide the overlay |
| H | Hide the overlay |
| 1 2 3 4 | Switch maps (once enabled in the control panel) |
| Ctrl + Alt + Shift + Delete | Soft-hide the POI under the cursor |

About soft-hiding:

- Hides only that POI within its current category.
- Does not delete the POI from the JSON data files.
- The hidden state is saved to the config file.

## Control Panel

The control panel lets you:

- Enable or disable POI categories
- Select all / deselect all categories in one click
- Change category colors
- Switch maps manually
- Enable number-key map switching
- Adjust the global POI size scale
- View and modify hotkeys

The panel stays on top and does not interfere with gameplay.

## Global POI Scaling

The global size scale enlarges or shrinks all POIs without editing JSON files.

- Decrease/increase buttons adjust in steps
- A numeric field sets an exact scale value
- Scaling applies to all POI categories
- The value is saved to the config file

---

## Installation

### Option 1: Prebuilt Executable

1. Download the released executable
2. Run it
3. On first launch the program creates the files it needs
4. Start Hunt: Showdown and press a hotkey to open the overlay

### Option 2: Run from Source

Requirements:

- Python 3.10 – 3.13
- PySide6

Install dependencies and run:

```bash
pip install pyside6
python HuntOverlay.py
```

---

## Building an Executable

Build on a native Windows environment. Do not package a Windows exe from WSL.

The project ships a one-click build script, `build_windows.bat`. Double-click it to run
(no administrator rights required, but Python 3.10–3.13 must be installed first). The
script checks for required files, creates or reuses `.venv`, installs pinned versions of
`PySide6` and `pyinstaller`, then packages the app. It prefers an existing virtual
environment; otherwise it searches for a usable Python from 3.13 down to 3.10 (the Windows
`py` launcher or a mise-installed version).

### Usage

```bat
build_windows.bat                       :: onedir (default)
build_windows.bat onefile               :: single-file portable build
build_windows.bat both                  :: build both
build_windows.bat both clean            :: purge stale caches first
build_windows.bat onedir clean nopause  :: automation; skip the final pause
```

Optional flags:

- `clean` — remove `build\`, `dist\`, and `*.spec` before building, so PyInstaller does not reuse a stale cache.
- `nopause` — do not wait for a keypress at the end; useful for automation/CI.

### Output Paths

- Onedir: `dist\HuntOverlay\HuntOverlay.exe`
- Single-file: `dist\HuntOverlay-portable.exe`

> The onedir and single-file builds use distinct names, so `both` mode never overwrites
> one with the other. The single-file build unpacks to a temp directory on first launch,
> causing a few seconds of black screen — this is expected; prefer the onedir build for
> instant startup.

### Custom Python

If auto-discovery cannot find a suitable Python, point an environment variable at `python.exe`:

```powershell
$env:HUNTOVERLAY_PYTHON = "C:\Path\to\python.exe"
.\build_windows.bat
```

### Manual Build

Without the script, you can package the single-file build manually:

```powershell
py -m PyInstaller --noconfirm --onefile --windowed --name HuntOverlay-portable --icon myicon.ico --add-data "data.json;." --add-data "poiData.json;." --add-data "myicon.ico;." HuntOverlay.py
```

Output: `dist\HuntOverlay-portable.exe`.

## Windows SmartScreen Warning

Because the app is unsigned, Windows may show a SmartScreen warning on first run. This is
normal for unsigned executables. Click **More info** → **Run anyway**.

To remove the warning permanently, the executable must be code-signed with a trusted
certificate. This project does not currently provide code signing.

## License

MIT License. You may use, modify, redistribute, or integrate it into other projects,
provided you retain the original attribution and the license. See the `LICENSE` file for
full terms.

## Authors and Acknowledgments

- Original author: sKhaled ([HuntOverlay-by-sKhaled](https://github.com/uzpj/HuntOverlay-by-sKhaled))
- This fork: Chinese localization and feature extensions on top of the original project.

Contributions, improvements, and forks are welcome.
