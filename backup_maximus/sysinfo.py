"""Métricas do dispositivo para o relatório de backup.

A coleta é leve de propósito: duas leituras de GetSystemTimes separadas por um
intervalo curto, e chamadas diretas de API para memória e disco. Roda depois do
backup, para não competir por CPU e disco durante a cópia.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from . import winapi


@dataclass
class DeviceInfo:
    computer_name: str = ""
    cpu_pct: float = 0.0
    mem_pct: float = 0.0
    mem_total_mb: int = 0
    mem_used_mb: int = 0
    disk_total_gb: int = 0
    disk_free_gb: int = 0
    disk_pct: float = 0.0


def collect(sample_seconds: float = 0.4) -> DeviceInfo:
    info = DeviceInfo(computer_name=winapi.computer_name())

    busy1, total1 = winapi.cpu_sample()
    time.sleep(sample_seconds)
    busy2, total2 = winapi.cpu_sample()
    delta_total = total2 - total1
    if delta_total > 0:
        info.cpu_pct = max(0.0, min(100.0, 100.0 * (busy2 - busy1) / delta_total))

    mem = winapi.memory_info()
    info.mem_pct = mem.load_pct
    info.mem_total_mb = mem.total_mb
    info.mem_used_mb = mem.used_mb

    gb = 1024 ** 3
    disk = winapi.disk_info(winapi.system_drive())
    info.disk_total_gb = disk.total_bytes // gb
    info.disk_free_gb = disk.free_bytes // gb
    if disk.total_bytes > 0:
        info.disk_pct = 100.0 * (disk.total_bytes - disk.free_bytes) / disk.total_bytes

    return info
