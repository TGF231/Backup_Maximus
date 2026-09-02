"""Cópia incremental para a árvore de montagem, com semântica de ROBOCOPY /MIR.

Só recopia o que mudou (tamanho ou data de modificação) e, quando espelhando,
apaga do destino o que sumiu da origem.
"""

from __future__ import annotations

import os
import shutil
import stat
from dataclasses import dataclass, field

from . import logger

#: Pen drives em FAT32 gravam a hora com resolução de 2 s — sem essa tolerância
#: todo arquivo pareceria alterado a cada execução.
_MTIME_TOLERANCE = 2.0


@dataclass
class CopyStats:
    copied: int = 0
    skipped: int = 0
    deleted: int = 0
    errors: int = 0
    bytes_copied: int = 0
    last_error: str = ""

    def describe(self) -> str:
        parts = [f"{self.copied} copiados", f"{self.skipped} iguais"]
        if self.deleted:
            parts.append(f"{self.deleted} removidos")
        if self.errors:
            parts.append(f"{self.errors} com erro")
        return ", ".join(parts)


def _same_file(src_stat: os.stat_result, dest_path: str) -> bool:
    try:
        dst = os.stat(dest_path)
    except OSError:
        return False
    if src_stat.st_size != dst.st_size:
        return False
    return abs(src_stat.st_mtime - dst.st_mtime) <= _MTIME_TOLERANCE


def _clear_readonly(path: str) -> None:
    try:
        mode = os.stat(path).st_mode
        if not mode & stat.S_IWRITE:
            os.chmod(path, mode | stat.S_IWRITE)
    except OSError:
        pass


def _copy_file(src: str, dest: str, src_stat: os.stat_result, stats: CopyStats) -> None:
    try:
        _clear_readonly(dest)
    except OSError:
        pass
    try:
        # copy2 preserva mtime, que é o que torna a próxima execução incremental.
        shutil.copy2(src, dest)
        stats.copied += 1
        stats.bytes_copied += src_stat.st_size
    except OSError as exc:
        # Arquivo em uso não aborta o backup: registra e segue com o resto.
        stats.errors += 1
        stats.last_error = f"Falha ao copiar {src}: {exc}"
        logger.warn(stats.last_error)


def copy_one_file(src_file: str, dest_dir: str, stats: CopyStats) -> bool:
    """Copia um arquivo avulso para dest_dir, preservando o nome."""
    try:
        src_stat = os.stat(src_file)
    except OSError:
        stats.errors += 1
        stats.last_error = f"Origem nao encontrada: {src_file}"
        return False

    try:
        os.makedirs(dest_dir, exist_ok=True)
    except OSError as exc:
        stats.errors += 1
        stats.last_error = f"Nao foi possivel criar {dest_dir}: {exc}"
        return False

    dest = os.path.join(dest_dir, os.path.basename(src_file))
    if _same_file(src_stat, dest):
        stats.skipped += 1
        return True

    before = stats.errors
    _copy_file(src_file, dest, src_stat, stats)
    return stats.errors == before


def mirror_directory(src_dir: str, dest_dir: str, mirror: bool, stats: CopyStats) -> bool:
    """Copia src_dir recursivamente para dest_dir.

    mirror=True remove do destino o que não existe mais na origem (/MIR).
    """
    if not os.path.isdir(src_dir):
        stats.errors += 1
        stats.last_error = f"Pasta de origem nao encontrada: {src_dir}"
        return False

    try:
        os.makedirs(dest_dir, exist_ok=True)
    except OSError as exc:
        stats.errors += 1
        stats.last_error = f"Nao foi possivel criar {dest_dir}: {exc}"
        return False

    seen: set[str] = set()
    try:
        entries = list(os.scandir(src_dir))
    except OSError as exc:
        stats.errors += 1
        stats.last_error = f"Nao foi possivel ler {src_dir}: {exc}"
        return False

    for entry in entries:
        seen.add(entry.name.lower())
        dest = os.path.join(dest_dir, entry.name)
        try:
            if entry.is_dir(follow_symlinks=False):
                # Não seguir junction/symlink evita laço infinito.
                mirror_directory(entry.path, dest, mirror, stats)
            elif entry.is_file(follow_symlinks=False):
                src_stat = entry.stat()
                if _same_file(src_stat, dest):
                    stats.skipped += 1
                else:
                    _copy_file(entry.path, dest, src_stat, stats)
        except OSError as exc:
            stats.errors += 1
            stats.last_error = f"Falha em {entry.path}: {exc}"
            logger.warn(stats.last_error)

    if not mirror:
        return True

    try:
        for entry in list(os.scandir(dest_dir)):
            if entry.name.lower() in seen:
                continue
            if entry.is_dir(follow_symlinks=False):
                if remove_tree(entry.path):
                    stats.deleted += 1
            else:
                _clear_readonly(entry.path)
                try:
                    os.unlink(entry.path)
                    stats.deleted += 1
                except OSError as exc:
                    stats.errors += 1
                    stats.last_error = f"Falha ao remover {entry.path}: {exc}"
    except OSError as exc:
        stats.errors += 1
        stats.last_error = f"Falha ao espelhar {dest_dir}: {exc}"

    return True


def remove_tree(path: str) -> bool:
    if not os.path.isdir(path):
        return True

    def on_error(func, target, exc_info):
        _clear_readonly(target)
        try:
            func(target)
        except OSError:
            pass

    try:
        shutil.rmtree(path, onexc=on_error)
    except TypeError:  # Python < 3.12 usa onerror
        shutil.rmtree(path, onerror=on_error)
    except OSError:
        return False
    return not os.path.exists(path)


def directory_size(path: str) -> int:
    total = 0
    if not os.path.isdir(path):
        return 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total
