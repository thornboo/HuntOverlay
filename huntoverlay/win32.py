"""Windows window-layer helpers.

SAFETY: this module only operates on *our own* window (click-through,
always-on-top) and reads global key state for hotkeys. It never reads or
writes another process's memory, and never touches the game process.

ctypes/user32 is bound lazily so this module imports cleanly on non-Windows
platforms (e.g. for static checks and unit-test collection); the actual
calls only run on Windows.
"""

import ctypes

_user32 = None
_kernel32 = None
# Held mutex handle for the single-instance lock (kept alive for the process
# lifetime; the OS releases it on exit).
_instance_mutex = None


def _u32():
    global _user32
    if _user32 is None:
        _user32 = ctypes.windll.user32  # only resolvable on Windows
    return _user32


def _k32():
    global _kernel32
    if _kernel32 is None:
        _kernel32 = ctypes.windll.kernel32
    return _kernel32


def key(vk: int) -> bool:
    """True if the given virtual-key is currently pressed."""
    return (_u32().GetAsyncKeyState(vk) & 0x8000) != 0


def topmost(hwnd: int) -> None:
    try:
        _u32().SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x1 | 0x2 | 0x10 | 0x40)
    except Exception:
        pass


def click_through(hwnd: int) -> None:
    try:
        style = _u32().GetWindowLongW(hwnd, -20)
        _u32().SetWindowLongW(hwnd, -20, style | 0x80000 | 0x80 | 0x8000000 | 0x20)
    except Exception:
        pass


# WS_EX_TRANSPARENT — the bit that makes mouse clicks pass through.
_WS_EX_TRANSPARENT = 0x20


def set_mouse_transparent(hwnd: int, transparent: bool) -> None:
    """Toggle only the click-through bit, leaving the other extended styles
    (layered / toolwindow / noactivate) intact.

    transparent=True restores normal pass-through; False lets the overlay
    receive mouse events (used by the POI pick mode), then it is flipped
    back to True when picking ends.
    """
    try:
        style = _u32().GetWindowLongW(hwnd, -20)
        if transparent:
            style |= _WS_EX_TRANSPARENT
        else:
            style &= ~_WS_EX_TRANSPARENT
        _u32().SetWindowLongW(hwnd, -20, style)
    except Exception:
        pass


_ERROR_ALREADY_EXISTS = 183


def acquire_single_instance(name: str = "HuntOverlay_SingleInstance") -> bool:
    """Try to claim a process-wide single-instance lock via a named mutex.

    Returns True if this is the first/only instance (lock acquired), or False
    if another instance already holds it. The mutex handle is kept for the
    process lifetime; Windows releases it automatically on exit. On any error
    (or non-Windows), returns True so the app still launches.
    """
    global _instance_mutex
    try:
        handle = _k32().CreateMutexW(None, False, name)
        if not handle:
            return True
        if _k32().GetLastError() == _ERROR_ALREADY_EXISTS:
            return False
        _instance_mutex = handle  # keep alive
        return True
    except Exception:
        return True
