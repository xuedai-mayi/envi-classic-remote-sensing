from __future__ import annotations

import ctypes
import os
import re
import time
from ctypes import wintypes
from dataclasses import dataclass
from typing import Callable

from .models import MenuItem, WindowInfo


if os.name == "nt":
    user32 = ctypes.WinDLL("user32", use_last_error=True)
else:
    user32 = None


def _enable_dpi_awareness() -> None:
    """Keep Win32 window rectangles, cursor positions, and captured pixels aligned."""
    if user32 is None:
        return
    try:
        setter = user32.SetProcessDpiAwarenessContext
        setter.argtypes = [ctypes.c_void_p]
        setter.restype = wintypes.BOOL
        if setter(ctypes.c_void_p(-4)):
            return
    except (AttributeError, OSError):
        pass
    try:
        user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


_enable_dpi_awareness()


WM_COMMAND = 0x0111
WM_CLOSE = 0x0010
SMTO_ABORTIFHUNG = 0x0002
MF_BYPOSITION = 0x00000400
MFS_DISABLED = 0x00000003
SW_RESTORE = 9
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
INPUT_KEYBOARD = 1


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)


def _require_windows() -> None:
    if user32 is None:
        raise RuntimeError("ENVI Classic GUI 自动化仅支持 Windows。")


if os.name == "nt":
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.GetMenu.argtypes = [wintypes.HWND]
    user32.GetMenu.restype = wintypes.HMENU
    user32.GetMenuItemCount.argtypes = [wintypes.HMENU]
    user32.GetMenuItemCount.restype = ctypes.c_int
    user32.GetSubMenu.argtypes = [wintypes.HMENU, ctypes.c_int]
    user32.GetSubMenu.restype = wintypes.HMENU
    user32.GetMenuItemID.argtypes = [wintypes.HMENU, ctypes.c_int]
    user32.GetMenuItemID.restype = wintypes.UINT
    user32.GetMenuStringW.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.LPWSTR, ctypes.c_int, wintypes.UINT]
    user32.GetMenuStringW.restype = ctypes.c_int
    user32.GetMenuState.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.UINT]
    user32.GetMenuState.restype = wintypes.UINT
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SendMessageTimeoutW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
        wintypes.UINT,
        wintypes.UINT,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    user32.SendMessageTimeoutW.restype = ctypes.c_size_t


def window_title(handle: int) -> str:
    _require_windows()
    length = user32.GetWindowTextLengthW(handle)
    buffer = ctypes.create_unicode_buffer(max(1, length + 1))
    user32.GetWindowTextW(handle, buffer, len(buffer))
    return buffer.value


def window_class(handle: int) -> str:
    _require_windows()
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(handle, buffer, len(buffer))
    return buffer.value


def window_rect(handle: int) -> Rect:
    _require_windows()
    raw = wintypes.RECT()
    if not user32.GetWindowRect(handle, ctypes.byref(raw)):
        raise ctypes.WinError(ctypes.get_last_error())
    return Rect(raw.left, raw.top, raw.right, raw.bottom)


def enum_windows_for_pid(process_id: int, visible_only: bool = True) -> list[WindowInfo]:
    _require_windows()
    windows: list[WindowInfo] = []

    @WNDENUMPROC
    def callback(handle: int, _lparam: int) -> bool:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(handle, ctypes.byref(pid))
        if pid.value != process_id:
            return True
        visible = bool(user32.IsWindowVisible(handle))
        if visible_only and not visible:
            return True
        title = window_title(handle)
        rect = window_rect(handle)
        if rect.width <= 0 or rect.height <= 0:
            return True
        windows.append(
            WindowInfo(
                handle=int(handle),
                title=title,
                class_name=window_class(handle),
                left=rect.left,
                top=rect.top,
                right=rect.right,
                bottom=rect.bottom,
                width=rect.width,
                height=rect.height,
                visible=visible,
            )
        )
        return True

    if not user32.EnumWindows(callback, 0):
        error = ctypes.get_last_error()
        if error:
            raise ctypes.WinError(error)
    return sorted(windows, key=lambda item: (item.title != "ENVI Classic", -item.width * item.height, item.title))


def wait_for_window(process_id: int, title_contains: str, timeout_seconds: float = 15.0) -> WindowInfo:
    deadline = time.monotonic() + timeout_seconds
    needle = title_contains.casefold()
    while time.monotonic() < deadline:
        for item in enum_windows_for_pid(process_id):
            if needle in item.title.casefold():
                return item
        time.sleep(0.15)
    available = [item.title for item in enum_windows_for_pid(process_id)]
    raise TimeoutError(f"等待 ENVI 窗口超时：{title_contains!r}；当前窗口：{available}")


def find_window(process_id: int, title_contains: str | None = None) -> WindowInfo:
    windows = enum_windows_for_pid(process_id)
    if not windows:
        raise RuntimeError("该 ENVI 会话当前没有可见窗口。")
    if title_contains is None:
        return max(windows, key=lambda item: item.width * item.height)
    needle = title_contains.casefold()
    matches = [item for item in windows if needle in item.title.casefold()]
    if not matches:
        raise ValueError(f"未找到标题包含 {title_contains!r} 的 ENVI 窗口。")
    return max(matches, key=lambda item: item.width * item.height)


def focus_window(handle: int) -> None:
    _require_windows()
    user32.ShowWindow(handle, SW_RESTORE)
    user32.SetForegroundWindow(handle)
    time.sleep(0.12)
    if int(user32.GetForegroundWindow() or 0) != int(handle):
        raise RuntimeError("无法确认目标 ENVI 窗口位于前台；已取消点击或键盘动作以保护其他应用。")


def _clean_menu_text(value: str) -> str:
    value = value.split("\t", 1)[0]
    return value.replace("&&", "\0").replace("&", "").replace("\0", "&").strip()


def _menu_text(menu: int, position: int) -> str:
    buffer = ctypes.create_unicode_buffer(512)
    user32.GetMenuStringW(menu, position, buffer, len(buffer), MF_BYPOSITION)
    return _clean_menu_text(buffer.value)


def list_menu_items(handle: int) -> list[MenuItem]:
    _require_windows()
    root_menu = user32.GetMenu(handle)
    if not root_menu:
        raise RuntimeError("目标窗口没有原生 Win32 菜单。")

    items: list[MenuItem] = []

    def walk(menu: int, parent: list[str]) -> None:
        count = user32.GetMenuItemCount(menu)
        for position in range(count):
            title = _menu_text(menu, position)
            if not title or title == "-":
                continue
            path = [*parent, title]
            submenu = user32.GetSubMenu(menu, position)
            state = user32.GetMenuState(menu, position, MF_BYPOSITION)
            enabled = (state & MFS_DISABLED) == 0
            raw_command_id = int(user32.GetMenuItemID(menu, position))
            command_id = None if raw_command_id == 0xFFFFFFFF else raw_command_id
            items.append(
                MenuItem(
                    path=path,
                    command_id=command_id,
                    enabled=enabled,
                    has_submenu=bool(submenu),
                )
            )
            if submenu:
                walk(submenu, path)

    walk(root_menu, [])
    return items


def _normalize_menu_segment(value: str) -> str:
    return re.sub(r"\s+", " ", _clean_menu_text(value)).casefold()


def invoke_menu_path(handle: int, path: list[str]) -> int:
    if not path:
        raise ValueError("菜单路径不能为空。")
    wanted = [_normalize_menu_segment(segment) for segment in path]
    exact: list[MenuItem] = []
    for item in list_menu_items(handle):
        normalized = [_normalize_menu_segment(segment) for segment in item.path]
        if normalized == wanted:
            exact.append(item)
    if not exact:
        raise ValueError(f"未找到菜单路径：{' -> '.join(path)}")
    item = exact[0]
    if item.command_id is None:
        raise ValueError(f"菜单路径不是可执行叶节点：{' -> '.join(path)}")
    if not item.enabled:
        raise RuntimeError(f"菜单项当前不可用：{' -> '.join(path)}")
    focus_window(handle)
    message_result = ctypes.c_size_t()
    delivered = user32.SendMessageTimeoutW(
        handle,
        WM_COMMAND,
        item.command_id,
        0,
        SMTO_ABORTIFHUNG,
        5000,
        ctypes.byref(message_result),
    )
    if not delivered:
        raise ctypes.WinError(ctypes.get_last_error())
    return item.command_id


def _point_inside(window: WindowInfo, x_ratio: float, y_ratio: float) -> tuple[int, int]:
    x = window.left + round((window.width - 1) * x_ratio)
    y = window.top + round((window.height - 1) * y_ratio)
    if not (window.left <= x < window.right and window.top <= y < window.bottom):
        raise ValueError("计算出的点击位置超出目标 ENVI 窗口。")
    return x, y


def click_window(window: WindowInfo, x_ratio: float, y_ratio: float, double: bool = False) -> tuple[int, int]:
    _require_windows()
    focus_window(window.handle)
    x, y = _point_inside(window, x_ratio, y_ratio)
    if not user32.SetCursorPos(x, y):
        raise ctypes.WinError(ctypes.get_last_error())
    count = 2 if double else 1
    for _ in range(count):
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        if double:
            time.sleep(0.08)
    return x, y


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUTUNION)]


if os.name == "nt":
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT


def _send_inputs(inputs: list[INPUT]) -> None:
    _require_windows()
    array = (INPUT * len(inputs))(*inputs)
    sent = user32.SendInput(len(inputs), array, ctypes.sizeof(INPUT))
    if sent != len(inputs):
        raise ctypes.WinError(ctypes.get_last_error())


def type_text(window: WindowInfo, text: str) -> None:
    focus_window(window.handle)
    inputs: list[INPUT] = []
    for character in text:
        scan = ord(character)
        inputs.append(INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, scan, KEYEVENTF_UNICODE, 0, 0)))
        inputs.append(INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, scan, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)))
    if inputs:
        _send_inputs(inputs)


VK_CODES = {
    "BACKSPACE": 0x08,
    "TAB": 0x09,
    "ENTER": 0x0D,
    "SHIFT": 0x10,
    "CTRL": 0x11,
    "ALT": 0x12,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "SPACE": 0x20,
    "PAGEUP": 0x21,
    "PAGEDOWN": 0x22,
    "END": 0x23,
    "HOME": 0x24,
    "LEFT": 0x25,
    "UP": 0x26,
    "RIGHT": 0x27,
    "DOWN": 0x28,
    "DELETE": 0x2E,
}
VK_CODES.update({f"F{number}": 0x6F + number for number in range(1, 13)})


def _vk(value: str) -> int:
    normalized = value.strip().upper()
    if normalized in VK_CODES:
        return VK_CODES[normalized]
    if len(normalized) == 1 and normalized.isascii() and normalized.isalnum():
        return ord(normalized)
    raise ValueError(f"不支持的按键：{value!r}")


def press_key(window: WindowInfo, key_spec: str) -> None:
    focus_window(window.handle)
    keys = [_vk(part) for part in key_spec.split("+") if part.strip()]
    if not keys:
        raise ValueError("按键不能为空。")
    for key in keys:
        user32.keybd_event(key, 0, 0, 0)
    for key in reversed(keys):
        user32.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)


def close_window(handle: int) -> None:
    _require_windows()
    user32.PostMessageW(handle, WM_CLOSE, 0, 0)
