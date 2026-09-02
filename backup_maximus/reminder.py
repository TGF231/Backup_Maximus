"""Lembrete de backup em horário definido.

Por que o Agendador do Windows e não um processo residente
----------------------------------------------------------
Um lembrete precisa disparar mesmo se ninguém abriu o programa, e continuar
funcionando depois de reiniciar a máquina. Deixar um processo na bandeja o dia
inteiro resolve isso mal: some quando o usuário fecha, não sobrevive ao boot sem
mais configuração, e consome memória sem fazer nada 23 horas por dia.

O Agendador já resolve tudo isso. A aplicação registra uma tarefa que executa
`BackupMaximus.exe /remind` no horário escolhido; esse processo mostra a
notificação e morre.

O lembrete é silencioso quando o backup do dia já rodou: avisar sobre algo que
já foi feito treina a pessoa a ignorar o aviso.
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass

from . import logger, util
from .config import Config

#: Nome da tarefa no Agendador. Fixo, para conseguirmos localizar e remover.
TASK_NAME = "Backup Maximus - Lembrete"

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def valid_time(text: str) -> bool:
    return bool(_TIME_RE.match(text.strip()))


def normalize_time(text: str) -> str:
    """'7:5' -> '07:05'. Devolve '' se não for hora válida."""
    match = _TIME_RE.match(text.strip())
    if not match:
        return ""
    return f"{int(match.group(1)):02d}:{match.group(2)}"


@dataclass
class ReminderState:
    """Por que (ou por que não) o lembrete deve aparecer agora."""
    should_notify: bool
    headline: str
    detail: str


def evaluate(cfg: Config) -> ReminderState:
    """Decide se há motivo para incomodar o usuário neste momento."""
    if not cfg.reminder_enabled:
        return ReminderState(False, "", "Lembrete desligado nas configurações.")

    if not cfg.sets:
        return ReminderState(
            True, "Backup Maximus não está configurado",
            "Nenhum conjunto de backup foi criado ainda. Abra o programa para "
            "configurar."
        )

    if cfg.last_run_unix == 0:
        return ReminderState(
            True, "Hora do backup",
            "Nenhum backup foi executado até agora nesta máquina."
        )

    age_hours = (time.time() - cfg.last_run_unix) / 3600.0
    last = time.strftime("%d/%m às %H:%M", time.localtime(cfg.last_run_unix))

    if cfg.last_run_status == "error":
        return ReminderState(
            True, "O último backup falhou",
            f"A execução de {last} terminou com falhas. Vale rodar de novo e "
            f"conferir o relatório."
        )

    # Rodou hoje e deu certo: não há o que lembrar. Avisar assim mesmo ensina a
    # pessoa a fechar o aviso sem ler.
    if age_hours < 12:
        return ReminderState(
            False, "", f"Backup de {last} concluído há {age_hours:.0f} h."
        )

    return ReminderState(
        True, "Hora do backup",
        f"O último backup foi {last}, há {age_hours:.0f} horas."
    )


# ------------------------------------------------------- tarefa agendada
def _executable_command() -> str:
    """Linha de comando que o Agendador deve executar."""
    from .paths import frozen, install_dir
    if frozen():
        return f'"{sys.executable}" /remind'
    launcher = os.path.join(install_dir(), "BackupMaximus.pyw")
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    if os.path.isfile(launcher):
        return f'"{pythonw}" "{launcher}" /remind'
    return f'"{pythonw}" -m backup_maximus /remind'


def task_installed() -> bool:
    code, _out = util.run_process(
        ["schtasks", "/Query", "/TN", TASK_NAME], timeout=30)
    return code == 0


def install_task(hhmm: str) -> tuple[bool, str]:
    """Registra (ou reescreve) a tarefa diária do lembrete."""
    when = normalize_time(hhmm)
    if not when:
        return False, f"Horário inválido: '{hhmm}'. Use HH:MM, como 22:00."

    code, out = util.run_process(
        ["schtasks", "/Create", "/TN", TASK_NAME,
         "/TR", _executable_command(),
         "/SC", "DAILY", "/ST", when, "/F"],
        timeout=60,
    )
    if code != 0:
        detail = util.truncate(out, 300)
        if "Acesso negado" in detail or "Access is denied" in detail:
            detail += (" — abra o Backup Maximus como administrador para "
                       "registrar a tarefa.")
        return False, detail or "O Agendador recusou a criação da tarefa."

    logger.info(f"Lembrete diario agendado para {when}.")
    return True, f"Lembrete diário registrado para {when}."


def remove_task() -> tuple[bool, str]:
    if not task_installed():
        return True, "Nenhum lembrete estava agendado."
    code, out = util.run_process(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], timeout=60)
    if code != 0:
        return False, util.truncate(out, 300)
    logger.info("Lembrete diario removido.")
    return True, "Lembrete removido do Agendador."


def sync_task(cfg: Config) -> tuple[bool, str]:
    """Alinha o Agendador com o que está configurado."""
    if cfg.reminder_enabled:
        return install_task(cfg.reminder_time)
    return remove_task()


# ------------------------------------------------------------ notificação
def notify(cfg: Config) -> int:
    """Mostra o lembrete. Devolve o código de saída do modo /remind."""
    state = evaluate(cfg)
    if not state.should_notify:
        logger.info(f"Lembrete dispensado: {state.detail}")
        return 0

    logger.info(f"Lembrete exibido: {state.headline}")
    from .ui import reminder_window
    return reminder_window.show(cfg, state.headline, state.detail)
