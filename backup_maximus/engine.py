"""Orquestração por conjunto.

Fluxo: aguarda unidade -> monta a árvore de staging -> cada item na sua
subpasta -> compacta a árvore inteira em UM zip -> relatório -> e-mail.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable

from . import (
    __version__, archive, cloud, dbdump, filecopy, logger, mailer, network,
    retention, sysinfo, util,
)
from .config import BackupItem, BackupSet, Config, ItemType, SetMode


class Phase(Enum):
    """Fase atual, para a interface reagir sem interpretar o texto da mensagem."""
    WORKING = auto()
    WAITING_DRIVE = auto()


#: progress(fase, percentual 0-100, mensagem) -> False cancela (só na espera).
ProgressFn = Callable[[Phase, int, str], bool] | None


@dataclass
class ItemResult:
    name: str = ""
    ok: bool = False
    detail: str = ""
    elapsed: float = 0.0


@dataclass
class SetResult:
    name: str = ""
    ok: bool = False
    zip_path: str = ""
    zip_bytes: int = 0
    message: str = ""
    elapsed: float = 0.0
    items: list[ItemResult] = field(default_factory=list)
    pruned: int = 0
    pruned_bytes: int = 0
    #: Envio à nuvem, quando o conjunto tem um remote configurado.
    cloud_ok: bool | None = None      # None = não configurado
    cloud_message: str = ""
    cloud_pruned: int = 0


@dataclass
class RunResult:
    all_ok: bool = False
    total_sets: int = 0
    succeeded_sets: int = 0
    elapsed: float = 0.0
    sets: list[SetResult] = field(default_factory=list)
    report_path: str = ""
    summary: str = ""


# --------------------------------------------------------------- relatório
def build_report(cfg: Config, run: RunResult, dev: sysinfo.DeviceInfo) -> str:
    def pct(value: float) -> str:
        return f"{value:.1f}".replace(".", ",")

    lines = [
        "=" * 42,
        f"  RELATORIO DE BACKUP - Backup Maximus {__version__}",
        "=" * 42,
        f"Empresa:      {cfg.company_name or '(nao configurada)'}",
        f"Data/hora:    {util.now_iso()}",
        f"Computador:   {dev.computer_name}",
        "",
        "--- Dispositivo ---",
        f"CPU:           {pct(dev.cpu_pct)}% em uso",
        f"Memoria:       {pct(dev.mem_pct)}% ({dev.mem_used_mb} MB de {dev.mem_total_mb} MB)",
        f"Armazenamento: {pct(dev.disk_pct)}% usado "
        f"({dev.disk_free_gb} GB livres de {dev.disk_total_gb} GB)",
        "",
        "--- Resultado ---",
        f"Conjuntos: {run.total_sets} | Sucesso: {run.succeeded_sets} | "
        f"Falhas: {run.total_sets - run.succeeded_sets}",
        f"Tempo total: {util.format_seconds(run.elapsed)}",
    ]

    for s in run.sets:
        lines.append("")
        lines.append(f"{'[OK]   ' if s.ok else '[FALHA]'} Conjunto: {s.name}  "
                     f"({util.format_seconds(s.elapsed)})")
        if s.zip_path:
            lines.append(f"        Arquivo: {s.zip_path}  ({util.format_bytes(s.zip_bytes)})")
        if s.pruned:
            lines.append(f"        Retenção: {s.pruned} backup(s) antigo(s) removido(s), "
                         f"{util.format_bytes(s.pruned_bytes)} liberados")
        # A linha aparece por haver mensagem, não por haver resultado: o
        # envio suspenso não é sucesso nem falha, mas o operador precisa saber
        # que o zip não foi para a nuvem.
        if s.cloud_message:
            mark = {True: "enviado", False: "FALHOU"}.get(s.cloud_ok, "nao enviado")
            lines.append(f"        Nuvem: {mark} — {s.cloud_message}")
            if s.cloud_pruned:
                lines.append(f"        Nuvem: {s.cloud_pruned} antigo(s) removido(s)")
        if s.message:
            lines.append(f"        {s.message}")
        for it in s.items:
            mark = "ok   " if it.ok else "FALHA"
            detail = f"  -  {it.detail}" if it.detail else ""
            lines.append(f"          {mark}  {it.name}{detail}")

    lines += ["", f"Log completo: {logger.current_path()}"]
    return "\n".join(lines)


def _write_report(app_dir: str, text: str) -> str:
    directory = os.path.join(app_dir, "reports")
    try:
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, f"relatorio_backup_{util.now_timestamp()}.txt")
        with open(path, "w", encoding="utf-8-sig", newline="\n") as fh:
            fh.write(text)
        return path
    except OSError as exc:
        logger.warn(f"Nao foi possivel gravar o relatorio: {exc}")
        return ""


# ------------------------------------------------------------------ um item
def _run_item(item: BackupItem, staging: str, cfg: Config) -> ItemResult:
    result = ItemResult(name=item.name)
    started = time.monotonic()

    target = os.path.join(staging, item.subfolder) if item.subfolder else staging

    if item.type.is_database:
        ok, dump_file, err = dbdump.dump_database(item, target)
        result.ok = ok
        if ok:
            try:
                result.detail = f"dump {util.format_bytes(os.path.getsize(dump_file))}"
            except OSError:
                result.detail = "dump gerado"
        else:
            result.detail = err
    else:
        net_ok, net_err = network.ensure_access(item.source, cfg.net_creds)
        if not net_ok:
            result.detail = net_err
        elif os.path.isfile(item.source):
            stats = filecopy.CopyStats()
            result.ok = filecopy.copy_one_file(item.source, target, stats)
            result.detail = (("copiado" if stats.copied else "ja atualizado")
                             if result.ok else stats.last_error)
        elif os.path.isdir(item.source):
            stats = filecopy.CopyStats()
            result.ok = filecopy.mirror_directory(item.source, target, item.mirror, stats)
            if result.ok:
                result.detail = stats.describe()
                if stats.bytes_copied:
                    result.detail += f" ({util.format_bytes(stats.bytes_copied)})"
            else:
                result.detail = stats.last_error
        else:
            result.detail = f"Origem nao encontrada: {item.source}"

    result.elapsed = time.monotonic() - started
    if result.ok:
        logger.info(f"  item '{item.name}': {result.detail}")
    else:
        logger.error(f"  item '{item.name}' FALHOU: {result.detail}")
    return result


# --------------------------------------------------------------- um conjunto
def _run_set(
    bset: BackupSet,
    cfg: Config,
    app_dir: str,
    archiver: archive.Archiver,
    base_pct: int,
    span_pct: int,
    progress: ProgressFn,
) -> SetResult:
    result = SetResult(name=bset.name)
    started = time.monotonic()
    staging = bset.staging_dir(app_dir)

    def report(local_pct: int, message: str, phase: Phase = Phase.WORKING) -> bool:
        if progress is None:
            return True
        return progress(phase, base_pct + local_pct * span_pct // 100, message)

    logger.info(f"--- Conjunto '{bset.name}' ({bset.mode.value}) | staging={staging} "
                f"| destino={bset.destination} ---")

    while True:  # bloco de saída única; `break` aborta o conjunto
        # 1) aguarda a unidade removível
        if bset.wait_for_path and not util.path_exists(bset.wait_for_path):
            logger.info(f"Aguardando unidade {bset.wait_for_path}...")
            cancelled = False

            def on_tick(elapsed: int) -> bool:
                nonlocal cancelled
                msg = (f"Aguardando unidade {bset.wait_for_path} — insira o pen drive "
                       f"ou HD externo ({elapsed}s)")
                if not report(2, msg, Phase.WAITING_DRIVE):
                    cancelled = True
                    return False
                return True

            if not util.wait_for_path(bset.wait_for_path, bset.wait_timeout_sec, on_tick):
                result.message = (
                    f"Espera pela unidade {bset.wait_for_path} cancelada pelo usuario."
                    if cancelled else
                    f"Unidade {bset.wait_for_path} nao ficou disponivel em "
                    f"{bset.wait_timeout_sec} s."
                )
                break
            logger.info(f"Unidade {bset.wait_for_path} detectada.")

        # 2) acesso ao destino
        net_ok, net_err = network.ensure_access(bset.destination, cfg.net_creds)
        if not net_ok:
            result.message = net_err
            break
        try:
            os.makedirs(bset.destination, exist_ok=True)
        except OSError as exc:
            result.message = f"Nao foi possivel criar/acessar o destino: {exc}"
            break

        # 3) monta a árvore
        if not bset.keep_staging:
            filecopy.remove_tree(staging)
        try:
            os.makedirs(staging, exist_ok=True)
        except OSError as exc:
            result.message = f"Nao foi possivel criar a arvore de montagem: {exc}"
            break

        # 4) cada item na sua subpasta
        active = bset.active_items
        if not active:
            result.message = "Conjunto sem itens habilitados."
            break

        failures = 0
        for index, item in enumerate(active):
            report(10 + index * 65 // len(active), f"[{bset.name}] {item.name}...")
            item_result = _run_item(item, staging, cfg)
            if not item_result.ok:
                failures += 1
            result.items.append(item_result)

        # 5) a árvore inteira vira UM zip
        max_compression = bset.mode is SetMode.FULL
        if max_compression:
            result.zip_path = os.path.join(
                bset.destination, f"{bset.name}{util.now_stamp_br()}.zip"
            )
        else:
            result.zip_path = os.path.join(bset.destination, f"{bset.name}.zip")

        tree_size = filecopy.directory_size(staging)
        available = util.free_space(bset.destination)
        # O zip raramente passa de 1/3 do original; abaixo disso o risco é real.
        if available and tree_size and available < tree_size // 3:
            logger.warn(f"Espaco livre em {bset.destination} "
                        f"({util.format_bytes(available)}) pode ser insuficiente para "
                        f"{util.format_bytes(tree_size)} de dados.")

        label = "maxima" if max_compression else "rapida"
        report(78, f"[{bset.name}] compactando {util.format_bytes(tree_size)} ({label})...")

        def zip_progress(pct: int, entry: str) -> None:
            report(78 + pct * 18 // 100, f"[{bset.name}] compactando... {entry}")

        ok, err = archiver.archive_tree(
            staging, result.zip_path, max_compression,
            update=(bset.mode is SetMode.INCREMENTAL),
            progress=zip_progress,
        )
        if not ok:
            result.message = err
            break

        try:
            result.zip_bytes = os.path.getsize(result.zip_path)
        except OSError:
            pass

        item_failures = failures
        if item_failures:
            result.message = (f"{item_failures} de {len(active)} itens falharam "
                              f"(o zip foi gerado com o restante).")

        # 6) expurgo dos antigos — só depois de o novo estar gravado, para nunca
        #    ficar sem backup nenhum se a compactação tivesse falhado.
        if bset.keep_last > 0 and bset.mode is SetMode.FULL:
            report(94, f"[{bset.name}] removendo backups antigos...")
            removed, freed, errors = retention.prune(bset)
            result.pruned = removed
            result.pruned_bytes = freed
            for err in errors:
                logger.warn(f"Expurgo: {err}")

        # 7) cópia na nuvem. Vem por último porque é a etapa mais lenta e a
        #    única que depende de rede: se falhar, o backup local continua
        #    válido e o relatório diz exatamente o que faltou.
        if bset.cloud_remote.strip() and not cloud.ENVIO_POR_API:
            # Configuração de uma versão anterior, com o envio por API agora
            # suspenso. Ignorar em silêncio seria pior: o operador continuaria
            # acreditando que o zip está indo para a nuvem.
            logger.warn(f"[{bset.name}] envio por API suspenso; "
                        f"'{bset.cloud_remote}' foi ignorado.")
            result.cloud_ok = None
            result.cloud_message = (
                "Envio pela API está em desenvolvimento — o zip ficou apenas "
                "no destino local.")
        elif bset.cloud_remote.strip():
            report(96, f"[{bset.name}] enviando para {bset.cloud_remote}...")
            upload = cloud.upload(
                result.zip_path, bset.cloud_remote, bset.cloud_path,
                cfg.rclone_path,
                on_progress=lambda msg: report(96, f"[{bset.name}] {msg}"),
            )
            result.cloud_ok = upload.ok
            result.cloud_message = upload.message
            if upload.ok:
                if bset.cloud_keep_last > 0:
                    removed, errors = cloud.prune(
                        bset.cloud_remote, bset.cloud_path, bset.name,
                        bset.cloud_keep_last, cfg.rclone_path)
                    result.cloud_pruned = removed
                    for err in errors:
                        logger.warn(f"Expurgo na nuvem: {err}")
            else:
                logger.error(f"Envio a nuvem falhou: {upload.message}")
                # O zip local está bom; o conjunto não é sucesso completo, mas
                # tampouco é perda de dados — a mensagem diz exatamente isso.
                extra = ("O zip local foi gravado; falhou apenas o envio à "
                         f"nuvem: {upload.message}")
                result.message = (f"{result.message} {extra}" if result.message
                                  else extra)

        # O conjunto só é sucesso se nenhum item falhou E a nuvem (quando
        # configurada) recebeu o arquivo.
        result.ok = (item_failures == 0) and (result.cloud_ok is not False)
        break

    result.elapsed = time.monotonic() - started
    if result.ok:
        logger.info(f"Conjunto '{bset.name}' OK em {util.format_seconds(result.elapsed)} "
                    f"-> {result.zip_path} ({util.format_bytes(result.zip_bytes)})")
    else:
        logger.error(f"Conjunto '{bset.name}' FALHOU: {result.message}")
    return result


# ------------------------------------------------------------------ execução
def run_backups(
    cfg: Config,
    cfg_path: str,
    app_dir: str,
    progress: ProgressFn = None,
) -> RunResult:
    run = RunResult()
    started = time.monotonic()

    def report(pct: int, message: str) -> None:
        if progress is not None:
            progress(Phase.WORKING, pct, message)

    archiver = archive.Archiver(cfg.sevenzip_path)
    logger.info(f"=== Iniciando execucao de backup ({archiver.tool_description}) ===")

    active = [s for s in cfg.sets if s.enabled]
    run.total_sets = len(active)

    if not active:
        run.summary = "Nenhum conjunto de backup habilitado. Abra as configuracoes."
        logger.warn(run.summary)
        report(100, run.summary)
        return run

    # 92% da barra para os conjuntos; o resto é relatório e e-mail.
    span = 92 // run.total_sets
    for index, bset in enumerate(active):
        result = _run_set(bset, cfg, app_dir, archiver, index * span, span, progress)
        if result.ok:
            run.succeeded_sets += 1
        run.sets.append(result)

    run.elapsed = time.monotonic() - started
    run.all_ok = run.succeeded_sets == run.total_sets

    report(94, "Gerando relatorio do dispositivo...")
    device = sysinfo.collect()
    report_text = build_report(cfg, run, device)
    run.report_path = _write_report(app_dir, report_text)

    cfg.last_run_unix = int(time.time())
    cfg.last_run_status = "ok" if run.all_ok else "error"
    cfg.save(cfg_path)

    # Config + relatório dentro de cada zip: se o INI local sumir, dá para
    # recuperar a configuração a partir de qualquer backup gerado.
    report(96, "Anexando configuracao e relatorio aos arquivos...")
    for result in run.sets:
        if not result.zip_path or not os.path.isfile(result.zip_path):
            continue
        if os.path.isfile(cfg_path):
            ok, err = archiver.add_file(result.zip_path, cfg_path)
            if not ok:
                logger.warn(f"Nao foi possivel embutir a config em {result.zip_path}: {err}")
        if run.report_path:
            archiver.add_file(result.zip_path, run.report_path)

    if cfg.send_report_email and cfg.notify_email and cfg.smtp.host:
        report(98, "Enviando relatorio por email...")
        subject = (f"[Backup Maximus] {cfg.company_name} - "
                   f"{'Backup OK' if run.all_ok else 'Backup com FALHAS'} "
                   f"({run.succeeded_sets}/{run.total_sets})")
        ok, err = mailer.send_email(
            cfg.smtp, cfg.notify_email, subject, report_text, run.report_path
        )
        if ok:
            logger.info(f"Relatorio enviado para {cfg.notify_email}")
        else:
            logger.warn(f"Envio de email falhou: {err}")

    network.disconnect_all()

    run.summary = (
        f"{'Backup concluido com sucesso' if run.all_ok else 'Backup concluido com falhas'} "
        f"({run.succeeded_sets}/{run.total_sets} conjuntos, {util.format_seconds(run.elapsed)})"
    )
    logger.info(f"=== {run.summary} ===")
    report(100, run.summary)
    return run


# ------------------------------------------------------------------ watchdog
def check_overdue(cfg: Config) -> tuple[bool, str]:
    """Devolve (disparou_alerta, mensagem)."""
    if cfg.alert_timeout_hours <= 0:
        return False, "Alerta de atraso desligado."

    age = int(time.time()) - cfg.last_run_unix
    limit = cfg.alert_timeout_hours * 3600
    overdue = (cfg.last_run_unix == 0 or age > limit or cfg.last_run_status == "error")

    if not overdue:
        return False, (f"Ultimo backup OK ha {age // 3600} h "
                       f"(limite {cfg.alert_timeout_hours} h).")

    if cfg.last_run_unix == 0:
        reason = "Nenhum backup foi executado ate agora."
    elif cfg.last_run_status == "error":
        reason = "A ultima execucao terminou com FALHAS."
    else:
        reason = (f"Ultimo backup concluido ha {age // 3600} horas — acima do limite "
                  f"de {cfg.alert_timeout_hours} horas.")

    message = f"ALERTA: {reason}"
    logger.error(message)

    if cfg.notify_email and cfg.smtp.host:
        body = (f"Empresa: {cfg.company_name}\n"
                f"Computador: {sysinfo.collect(0.05).computer_name}\n\n{reason}\n\n"
                f"Verifique a aplicacao Backup Maximus nesta maquina.")
        ok, err = mailer.send_email(
            cfg.smtp, cfg.notify_email,
            f"[Backup Maximus] ALERTA - backup atrasado ({cfg.company_name})", body,
        )
        if ok:
            logger.info(f"Alerta enviado para {cfg.notify_email}")
        else:
            logger.warn(f"Falha ao enviar alerta: {err}")

    return True, message


# ------------------------------------------------------- recuperar config
def recover_config_from_zip(search_dir: str, cfg_path: str) -> bool:
    """Extrai backup_maximus.ini do zip mais recente encontrado em search_dir."""
    if os.path.isfile(cfg_path) or not os.path.isdir(search_dir):
        return False

    zips = [os.path.join(search_dir, n) for n in os.listdir(search_dir)
            if n.lower().endswith(".zip")]
    if not zips:
        return False

    newest = max(zips, key=lambda p: os.path.getmtime(p))
    ok, err = archive.Archiver().extract_file(
        newest, "backup_maximus.ini", os.path.dirname(cfg_path)
    )
    if not ok:
        logger.warn(f"Recuperacao de config a partir de {newest} falhou: {err}")
        return False

    logger.info(f"Configuracao recuperada de {newest}")
    return os.path.isfile(cfg_path)
