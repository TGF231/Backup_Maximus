"""Espaço no destino e expurgo de backups antigos.

No modo Completo cada execução gera um arquivo novo, então o destino enche —
tipicamente um pen drive, que enche rápido. Este módulo responde duas perguntas
que o operador faria olhando a pasta: quanto cabe ainda, e o que dá para apagar.

O expurgo é deliberadamente conservador: só remove arquivos que casam com o
padrão de nome daquele conjunto, nunca toca em nada mais que esteja no destino,
e sempre preserva os N mais recentes.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from . import logger, util
from .config import BackupSet, SetMode


@dataclass
class BackupFile:
    path: str
    name: str
    size: int
    mtime: float


@dataclass
class DestinationReport:
    """Retrato do destino de um conjunto."""
    destination: str = ""
    reachable: bool = False
    free_bytes: int = 0
    total_bytes: int = 0
    backups: list[BackupFile] = field(default_factory=list)
    #: os que o expurgo removeria com a política atual
    prunable: list[BackupFile] = field(default_factory=list)
    message: str = ""

    @property
    def used_bytes(self) -> int:
        return sum(b.size for b in self.backups)

    @property
    def prunable_bytes(self) -> int:
        return sum(b.size for b in self.prunable)

    @property
    def newest(self) -> BackupFile | None:
        return self.backups[0] if self.backups else None


def _name_pattern(set_name: str) -> re.Pattern[str]:
    """Casa <nome><DDMMYYYYHHMMSS>.zip e também <nome>.zip do modo incremental."""
    escaped = re.escape(set_name)
    return re.compile(rf"^{escaped}(\d{{14}})?\.zip$", re.IGNORECASE)


def list_backups(bset: BackupSet) -> list[BackupFile]:
    """Arquivos do destino que pertencem a este conjunto, do mais novo ao mais antigo."""
    destination = bset.destination.strip()
    if not destination or not os.path.isdir(destination):
        return []

    pattern = _name_pattern(bset.name)
    found: list[BackupFile] = []
    try:
        for entry in os.scandir(destination):
            if not entry.is_file(follow_symlinks=False):
                continue
            if not pattern.match(entry.name):
                continue
            try:
                stat = entry.stat()
            except OSError:
                continue
            found.append(BackupFile(entry.path, entry.name, stat.st_size, stat.st_mtime))
    except OSError as exc:
        logger.warn(f"Nao foi possivel listar {destination}: {exc}")
        return []

    found.sort(key=lambda b: b.mtime, reverse=True)
    return found


def inspect(bset: BackupSet) -> DestinationReport:
    """Espaço livre e lista de backups do conjunto, com o que seria expurgado."""
    report = DestinationReport(destination=bset.destination.strip())

    if not report.destination:
        report.message = "Conjunto sem destino configurado."
        return report

    if not os.path.isdir(report.destination):
        if util.is_unc(report.destination):
            report.message = (f"Sem acesso a {report.destination} agora — verifique "
                              f"a rede ou a credencial na aba Rede.")
        else:
            report.message = (f"A pasta {report.destination} ainda não existe; "
                              f"será criada no primeiro backup.")
        return report

    report.reachable = True
    disk = util.free_space(report.destination)
    report.free_bytes = disk
    from . import winapi
    report.total_bytes = winapi.disk_info(report.destination).total_bytes
    report.backups = list_backups(bset)
    report.prunable = _select_prunable(bset, report.backups)
    return report


def _select_prunable(bset: BackupSet, backups: list[BackupFile]) -> list[BackupFile]:
    """Quais arquivos sobram além da política de retenção."""
    # No modo incremental existe um arquivo só; não há o que expurgar.
    if bset.mode is not SetMode.FULL or bset.keep_last <= 0:
        return []
    return backups[bset.keep_last:]


def prune(bset: BackupSet, dry_run: bool = False) -> tuple[int, int, list[str]]:
    """Remove os backups além da retenção.

    Devolve (removidos, bytes liberados, erros). Com dry_run=True apenas calcula.
    """
    victims = _select_prunable(bset, list_backups(bset))
    if not victims:
        return 0, 0, []

    if dry_run:
        return len(victims), sum(v.size for v in victims), []

    removed = 0
    freed = 0
    errors: list[str] = []
    for victim in victims:
        try:
            os.unlink(victim.path)
            removed += 1
            freed += victim.size
            logger.info(f"Backup antigo removido: {victim.name} "
                        f"({util.format_bytes(victim.size)})")
        except OSError as exc:
            errors.append(f"{victim.name}: {exc}")
            logger.warn(f"Nao foi possivel remover {victim.path}: {exc}")

    return removed, freed, errors


def describe(report: DestinationReport) -> str:
    """Resumo de uma linha para a interface."""
    if not report.reachable:
        return report.message
    parts = [f"{util.format_bytes(report.free_bytes)} livres"]
    if report.backups:
        parts.append(f"{len(report.backups)} backup(s) ocupando "
                     f"{util.format_bytes(report.used_bytes)}")
        newest = report.newest
        if newest:
            parts.append(f"último: {util.format_bytes(newest.size)}")
    else:
        parts.append("nenhum backup deste conjunto ainda")
    return " · ".join(parts)
