"""HuntOverlay — an extended Hunt: Showdown map overlay.

Package layout:
  constants  — static data and label lookups (pure)
  geometry   — aspect/rect/coordinate math (pure)
  mapdata    — POI data + style JSON parsing (pure)
  paths      — filesystem paths and JSON I/O
  config     — config schema, defaults, merge, load/migrate

UI and platform layers (Qt widgets, Win32 window calls) live alongside
these but are imported only by the front ends, never by the pure core.
"""
