"""Acesso direto a APIs do Windows via ctypes.

Mantém compatibilidade com a versão C++: as senhas continuam cifradas com DPAPI,
então um backup_maximus.ini gerado por qualquer uma das duas é lido pela outra.
"""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes
from typing import NamedTuple

# ---------------------------------------------------------------- bibliotecas
_crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_mpr = ctypes.WinDLL("mpr", use_last_error=True)


# ------------------------------------------------------------------- DPAPI
class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


_crypt32.CryptProtectData.argtypes = [
    ctypes.POINTER(_DataBlob), wintypes.LPCWSTR, ctypes.POINTER(_DataBlob),
    ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob),
]
_crypt32.CryptProtectData.restype = wintypes.BOOL
_crypt32.CryptUnprotectData.argtypes = [
    ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.POINTER(_DataBlob),
    ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob),
]
_crypt32.CryptUnprotectData.restype = wintypes.BOOL

_CRYPTPROTECT_UI_FORBIDDEN = 0x1
_DESCRIPTION = "BackupMaximus"


def _blob(data: bytes) -> _DataBlob:
    buf = ctypes.create_string_buffer(data, len(data))
    return _DataBlob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))


def _blob_bytes(blob: _DataBlob) -> bytes:
    return ctypes.string_at(blob.pbData, blob.cbData)


def dpapi_protect(plain: bytes) -> bytes | None:
    """Cifra com a chave do usuário+máquina. None em caso de falha."""
    if not plain:
        return b""
    src, out = _blob(plain), _DataBlob()
    ok = _crypt32.CryptProtectData(
        ctypes.byref(src), _DESCRIPTION, None, None, None,
        _CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(out),
    )
    if not ok:
        return None
    try:
        return _blob_bytes(out)
    finally:
        _kernel32.LocalFree(out.pbData)


def dpapi_unprotect(enc: bytes) -> bytes | None:
    if not enc:
        return b""
    src, out = _blob(enc), _DataBlob()
    ok = _crypt32.CryptUnprotectData(
        ctypes.byref(src), None, None, None, None,
        _CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(out),
    )
    if not ok:
        return None
    try:
        return _blob_bytes(out)
    finally:
        _kernel32.LocalFree(out.pbData)


# ------------------------------------------------------- métricas do sistema
class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class MemoryInfo(NamedTuple):
    load_pct: float
    total_mb: int
    used_mb: int


def memory_info() -> MemoryInfo:
    ms = _MemoryStatusEx()
    ms.dwLength = ctypes.sizeof(ms)
    if not _kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
        return MemoryInfo(0.0, 0, 0)
    mb = 1024 * 1024
    return MemoryInfo(
        float(ms.dwMemoryLoad),
        ms.ullTotalPhys // mb,
        (ms.ullTotalPhys - ms.ullAvailPhys) // mb,
    )


def _filetime_to_int(ft: wintypes.FILETIME) -> int:
    return (ft.dwHighDateTime << 32) | ft.dwLowDateTime


def cpu_sample() -> tuple[int, int]:
    """Devolve (ocupado, total) em unidades de 100 ns desde o boot."""
    idle, kern, user = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
    if not _kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user)):
        return (0, 0)
    i, k, u = _filetime_to_int(idle), _filetime_to_int(kern), _filetime_to_int(user)
    total = k + u  # o tempo de kernel já inclui o idle
    return (total - i, total)


class DiskInfo(NamedTuple):
    total_bytes: int
    free_bytes: int


def disk_info(path: str) -> DiskInfo:
    """Espaço do volume que contém `path`. Aceita raiz de unidade, pasta ou UNC."""
    free, total = ctypes.c_ulonglong(), ctypes.c_ulonglong()
    ok = _kernel32.GetDiskFreeSpaceExW(
        wintypes.LPCWSTR(path), ctypes.byref(free), ctypes.byref(total), None
    )
    if not ok:
        return DiskInfo(0, 0)
    return DiskInfo(total.value, free.value)


def computer_name() -> str:
    size = wintypes.DWORD(256)
    buf = ctypes.create_unicode_buffer(256)
    if _kernel32.GetComputerNameW(buf, ctypes.byref(size)):
        return buf.value
    return os.environ.get("COMPUTERNAME", "?")


def system_drive() -> str:
    buf = ctypes.create_unicode_buffer(260)
    if _kernel32.GetWindowsDirectoryW(buf, 260) and len(buf.value) > 1:
        return buf.value[0] + ":\\"
    return "C:\\"


# ----------------------------------------------------------- rede (UNC)
class _NetResource(ctypes.Structure):
    _fields_ = [
        ("dwScope", wintypes.DWORD), ("dwType", wintypes.DWORD),
        ("dwDisplayType", wintypes.DWORD), ("dwUsage", wintypes.DWORD),
        ("lpLocalName", wintypes.LPWSTR), ("lpRemoteName", wintypes.LPWSTR),
        ("lpComment", wintypes.LPWSTR), ("lpProvider", wintypes.LPWSTR),
    ]


NO_ERROR = 0
ERROR_SESSION_CREDENTIAL_CONFLICT = 1219
_RESOURCETYPE_DISK = 0x1


def net_connect(remote: str, user: str, password: str) -> int:
    """Conecta a um compartilhamento. Devolve o código de erro do Windows."""
    nr = _NetResource()
    nr.dwType = _RESOURCETYPE_DISK
    nr.lpRemoteName = remote
    return _mpr.WNetAddConnection2W(
        ctypes.byref(nr), password or None, user or None, 0
    )


def net_disconnect(remote: str) -> int:
    return _mpr.WNetCancelConnection2W(remote, 0, False)


# ------------------------------------------------------------------ console
_STD_OUTPUT_HANDLE = -11
_ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004


def enable_ansi() -> bool:
    """Liga o processamento de sequências ANSI no console (cores)."""
    try:
        h = _kernel32.GetStdHandle(_STD_OUTPUT_HANDLE)
        mode = wintypes.DWORD()
        if not _kernel32.GetConsoleMode(h, ctypes.byref(mode)):
            return False
        return bool(
            _kernel32.SetConsoleMode(h, mode.value | _ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        )
    except Exception:
        return False


def use_utf8_console() -> None:
    """Garante que os caracteres de desenho de caixa saiam corretos."""
    try:
        _kernel32.SetConsoleOutputCP(65001)
        _kernel32.SetConsoleCP(65001)
    except Exception:
        pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def set_console_title(title: str) -> None:
    try:
        _kernel32.SetConsoleTitleW(title)
    except Exception:
        pass
