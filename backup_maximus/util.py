"""Utilitários compartilhados: formatação, caminhos e espera por unidade."""

from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime
from typing import Callable

from . import winapi

#: Sinalizadores para rodar processos sem piscar janela de console.
_NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW


def now_stamp_br() -> str:
    """DDMMYYYYHHMMSS — o mesmo padrão do -ag do WinRAR."""
    return f"{datetime.now():%d%m%Y%H%M%S}"


def now_timestamp() -> str:
    return f"{datetime.now():%Y-%m-%d_%H%M%S}"


def now_iso() -> str:
    return f"{datetime.now():%Y-%m-%d %H:%M:%S}"


def format_bytes(n: int) -> str:
    """Tamanho legível no padrão brasileiro (vírgula decimal)."""
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(n)
    idx = 0
    while value >= 1024 and idx < len(units) - 1:
        value /= 1024
        idx += 1
    text = f"{value:.0f}" if idx == 0 else f"{value:.1f}"
    return f"{text.replace('.', ',')} {units[idx]}"


def format_seconds(sec: float) -> str:
    if sec < 60:
        return f"{sec:.1f}".replace(".", ",") + " s"
    minutes, seconds = divmod(int(sec), 60)
    return f"{minutes} min {seconds} s"


def is_unc(path: str) -> bool:
    return path.startswith("\\\\")


def unc_root(path: str) -> str:
    """\\\\servidor\\share a partir de um caminho UNC completo."""
    if not is_unc(path):
        return ""
    parts = path[2:].split("\\")
    if len(parts) < 2:
        return path
    return "\\\\" + parts[0] + "\\" + parts[1]


def path_exists(path: str) -> bool:
    try:
        return os.path.exists(path)
    except OSError:
        return False


def wait_for_path(
    path: str,
    timeout_sec: int,
    on_tick: Callable[[int], bool] | None = None,
    poll_seconds: float = 1.0,
) -> bool:
    """Aguarda o caminho ficar acessível (pen drive, HD externo).

    on_tick(segundos) é chamado a cada intervalo; devolver False cancela.
    timeout_sec = 0 espera indefinidamente. Retorna True se ficou disponível.
    """
    if not path:
        return True
    start = time.monotonic()
    while True:
        if path_exists(path):
            return True
        elapsed = int(time.monotonic() - start)
        if timeout_sec > 0 and elapsed >= timeout_sec:
            return False
        if on_tick is not None and not on_tick(elapsed):
            return False
        time.sleep(poll_seconds)


def free_space(path: str) -> int:
    return winapi.disk_info(path).free_bytes


def run_process(
    args: list[str],
    timeout: float | None = None,
    cwd: str | None = None,
) -> tuple[int, str]:
    """Executa um comando capturando stdout+stderr. Devolve (código, saída).

    Código -1 = não foi possível iniciar; -2 = estourou o tempo limite.
    """
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            timeout=timeout,
            cwd=cwd,
            creationflags=_NO_WINDOW,
        )
    except FileNotFoundError:
        return -1, "programa nao encontrado"
    except subprocess.TimeoutExpired:
        return -2, "tempo limite excedido"
    except OSError as exc:
        return -1, str(exc)

    raw = (proc.stdout or b"") + (proc.stderr or b"")
    # Ferramentas de console costumam usar a codepage OEM; UTF-8 primeiro.
    for encoding in ("utf-8", "cp850", "cp1252"):
        try:
            return proc.returncode, raw.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return proc.returncode, raw.decode("utf-8", "replace").strip()


def truncate(text: str, limit: int = 500) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


# ------------------------------------------------------ pastas de nuvem
def cloud_folders() -> dict[str, str]:
    """Pastas de sincronização de nuvem presentes nesta máquina.

    Gravar o zip numa dessas pastas é a forma mais simples de mandar o backup
    para a nuvem: o cliente de sincronização faz o envio. Detectamos para poder
    avisar o que isso implica — ver `cloud_provider`.
    """
    found: dict[str, str] = {}
    for var, label in (("OneDrive", "OneDrive"),
                       ("OneDriveCommercial", "OneDrive corporativo"),
                       ("OneDriveConsumer", "OneDrive pessoal")):
        value = os.environ.get(var, "").strip()
        if value and os.path.isdir(value):
            found.setdefault(os.path.normpath(value).lower(), label)

    home = os.path.expanduser("~")
    for candidate, label in (
        (os.path.join(home, "Google Drive"), "Google Drive"),
        (os.path.join(home, "MEGAsync"), "MEGA"),
        (os.path.join(home, "MEGA"), "MEGA"),
        (os.path.join(home, "Dropbox"), "Dropbox"),
    ):
        if os.path.isdir(candidate):
            found.setdefault(os.path.normpath(candidate).lower(), label)

    # O Google Drive para Desktop monta uma unidade própria (normalmente G:).
    for letter in "GHIJKLMNOPQRSTUVWXY":
        root = f"{letter}:\\"
        marker = os.path.join(root, "Meu Drive")
        alt = os.path.join(root, "My Drive")
        if os.path.isdir(marker) or os.path.isdir(alt):
            found.setdefault(root.lower(), "Google Drive")

    return found


def cloud_provider(path: str) -> str:
    """Nome do serviço de nuvem que sincroniza esse caminho, ou string vazia."""
    if not path:
        return ""
    try:
        normalized = os.path.normpath(os.path.abspath(path)).lower()
    except (OSError, ValueError):
        return ""
    for folder, label in cloud_folders().items():
        if normalized == folder or normalized.startswith(folder.rstrip("\\") + "\\"):
            return label
    return ""
