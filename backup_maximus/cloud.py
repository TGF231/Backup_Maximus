"""Envio do backup para armazenamento em nuvem, pela API do serviço.

Por que rclone em vez de falar com cada API diretamente
-------------------------------------------------------
Google Drive, OneDrive e Mega têm APIs incompatíveis entre si, cada uma com seu
fluxo OAuth, seu formato de token e sua renovação. Implementar as três significa
registrar um aplicativo em cada provedor, embutir os identificadores no
executável e manter três integrações que quebram em ritmos diferentes.

O rclone já faz exatamente isso, é um único executável, e conversa com a API de
verdade de cada serviço — não é pasta sincronizada. Encaixa na arquitetura que
já existe aqui: a aplicação localiza e chama ferramentas externas (7z, gbak,
sqlcmd, mysqldump) e lê o resultado.

A diferença prática em relação a apontar o destino para a pasta do OneDrive é
que aqui o envio é **confirmado**: o backup só é dado como concluído depois que
o arquivo chegou. Numa pasta sincronizada, o relatório diz "sucesso" assim que o
zip toca o disco, e o envio acontece depois, sem ninguém verificar.

Terabox não tem API pública nem suporte no rclone. Para ele, o caminho continua
sendo apontar o destino do conjunto para a pasta do cliente de sincronização.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field

from . import logger, util

#: Serviços que o rclone atende e que interessam aqui. O nome à esquerda é o
#: identificador do backend no rclone (`rclone config` pergunta por ele).
# ---------------------------------------------------------------- disponibilidade
#: O envio pela API está **suspenso**, e este é o interruptor único.
#:
#: Motivo: o Google exige que o domínio informado na tela de consentimento seja
#: verificado por registro DNS, o que só é possível com um domínio próprio. Sem
#: isso o aplicativo não sai de "Teste", e em "Teste" o Google expira a
#: credencial de renovação a cada 7 dias — o envio noturno pararia toda semana,
#: que é a pior forma de um backup falhar: silenciosa e tardia.
#:
#: Enquanto isso, o caminho para a nuvem é apontar o **destino do conjunto**
#: para a pasta de um cliente de sincronização instalado (OneDrive, Google
#: Drive, Dropbox, MEGA). Ver `util.cloud_folders`.
#:
#: Para reativar, basta trocar para True: nada foi removido, e os testes de
#: `cloud.py` e `cloud_setup.py` continuam cobrindo o código de envio.
ENVIO_POR_API = False

#: Frase única para a interface, para o motivo não ser reescrito em cada tela.
MOTIVO_INDISPONIVEL = (
    "O envio direto pela API do serviço está em desenvolvimento. Enquanto isso, "
    "aponte o destino do conjunto para a pasta de um cliente de sincronização "
    "instalado — o zip é enviado por ele."
)


KNOWN_PROVIDERS = {
    "drive": "Google Drive",
    "onedrive": "OneDrive",
    "mega": "MEGA",
    "dropbox": "Dropbox",
    "s3": "Amazon S3 / compatível",
    "b2": "Backblaze B2",
    "ftp": "FTP",
    "sftp": "SFTP",
    "webdav": "WebDAV",
}

#: Envio de arquivo grande por rede lenta leva tempo; o limite existe para não
#: pendurar o backup para sempre se a conexão morrer no meio.
UPLOAD_TIMEOUT = 3600.0


@dataclass
class RemoteFile:
    name: str
    size: int
    modified: str


@dataclass
class UploadResult:
    ok: bool = False
    message: str = ""
    elapsed: float = 0.0
    pruned: int = 0
    remote_files: list[RemoteFile] = field(default_factory=list)


def find_rclone(hint: str = "") -> str:
    """Localiza o rclone: informado, empacotado com o app, ou no sistema."""
    if hint and os.path.isfile(hint):
        return hint

    from .paths import find_vendor_tool
    bundled = find_vendor_tool("rclone.exe")
    if bundled:
        return bundled

    found = shutil.which("rclone")
    if found:
        return found
    for candidate in (r"C:\Program Files\rclone\rclone.exe",
                      r"C:\rclone\rclone.exe"):
        if os.path.isfile(candidate):
            return candidate
    return ""


def available(hint: str = "") -> bool:
    return bool(find_rclone(hint))


def version(hint: str = "") -> str:
    exe = find_rclone(hint)
    if not exe:
        return ""
    code, out = util.run_process([exe, "version"], timeout=30)
    if code != 0:
        return ""
    return out.splitlines()[0].strip() if out else "rclone"


def list_remotes(hint: str = "") -> list[str]:
    """Remotes já configurados, sem os dois-pontos finais."""
    exe = find_rclone(hint)
    if not exe:
        return []
    code, out = util.run_process([exe, "listremotes"], timeout=30)
    if code != 0:
        return []
    return [line.strip().rstrip(":") for line in out.splitlines() if line.strip()]


def remote_kind(name: str, hint: str = "") -> str:
    """Que serviço é um remote (drive, onedrive, mega...)."""
    exe = find_rclone(hint)
    if not exe:
        return ""
    code, out = util.run_process(
        [exe, "config", "show", name], timeout=30)
    if code != 0:
        return ""
    for line in out.splitlines():
        if line.strip().startswith("type"):
            _key, _sep, value = line.partition("=")
            return value.strip()
    return ""


def describe_remote(name: str, hint: str = "") -> str:
    kind = remote_kind(name, hint)
    return KNOWN_PROVIDERS.get(kind, kind or "desconhecido")


def open_config_wizard(hint: str = "") -> tuple[bool, str]:
    """Abre o assistente do rclone numa janela de console.

    A autenticação é interativa por natureza — o provedor abre o navegador e
    pede o consentimento. Não há como fazer isso dentro da nossa janela sem
    reimplementar o OAuth de cada serviço, que é justamente o que evitamos.
    """
    exe = find_rclone(hint)
    if not exe:
        return False, ("rclone não encontrado. Instale com "
                       "'winget install Rclone.Rclone' ou coloque o rclone.exe "
                       "em vendor\\rclone\\ ao lado do programa.")
    try:
        import subprocess
        subprocess.Popen([exe, "config"], creationflags=0x00000010)  # CREATE_NEW_CONSOLE
    except OSError as exc:
        return False, f"Não foi possível abrir o assistente: {exc}"
    return True, ("Assistente do rclone aberto numa janela de console. "
                  "Escolha 'n' para novo remote, dê um nome, escolha o serviço "
                  "e conclua o login no navegador.")


def _remote_target(remote: str, path: str) -> str:
    """monta remote:pasta/sub sem barras duplicadas."""
    clean = path.strip().strip("/\\").replace("\\", "/")
    return f"{remote}:{clean}" if clean else f"{remote}:"


def list_files(remote: str, path: str, hint: str = "") -> list[RemoteFile]:
    """Arquivos na pasta remota, do mais novo para o mais antigo."""
    exe = find_rclone(hint)
    if not exe or not remote:
        return []
    code, out = util.run_process(
        [exe, "lsjson", _remote_target(remote, path), "--files-only"],
        timeout=120)
    if code != 0:
        logger.warn(f"rclone lsjson falhou: {util.truncate(out, 300)}")
        return []
    try:
        entries = json.loads(out or "[]")
    except json.JSONDecodeError:
        return []

    files = [
        RemoteFile(name=e.get("Name", ""), size=int(e.get("Size", 0) or 0),
                   modified=e.get("ModTime", ""))
        for e in entries if not e.get("IsDir")
    ]
    files.sort(key=lambda f: f.modified, reverse=True)
    return files


def upload(
    local_file: str,
    remote: str,
    path: str,
    hint: str = "",
    on_progress=None,
) -> UploadResult:
    """Envia um arquivo para remote:path, conferindo a integridade."""
    import time
    result = UploadResult()
    started = time.monotonic()

    exe = find_rclone(hint)
    if not exe:
        result.message = ("rclone não encontrado — o envio à nuvem foi pulado. "
                          "Instale o rclone ou desmarque o envio no conjunto.")
        return result
    if not remote:
        result.message = "Nenhum remote de nuvem escolhido no conjunto."
        return result
    if not os.path.isfile(local_file):
        result.message = f"Arquivo não encontrado para envio: {local_file}"
        return result

    target = _remote_target(remote, path) + "/" + os.path.basename(local_file)
    size = os.path.getsize(local_file)
    if on_progress:
        on_progress(f"Enviando {util.format_bytes(size)} para {remote}…")

    logger.info(f"Enviando {os.path.basename(local_file)} "
                f"({util.format_bytes(size)}) para {target}")

    # copyto grava com o nome exato de destino. --checksum confirma que o que
    # chegou é o que saiu: é isso que diferencia um envio confirmado de um
    # "coloquei na pasta e torci".
    code, out = util.run_process(
        [exe, "copyto", local_file, target,
         "--checksum", "--retries", "3", "--low-level-retries", "5",
         "--stats-one-line", "--stats", "10s"],
        timeout=UPLOAD_TIMEOUT,
    )
    result.elapsed = time.monotonic() - started

    if code == -2:
        result.message = (f"Envio excedeu {int(UPLOAD_TIMEOUT / 60)} min e foi "
                          f"interrompido. O zip local está íntegro.")
        return result
    if code != 0:
        result.message = f"rclone retornou {code}: {util.truncate(out, 400)}"
        return result

    result.ok = True
    result.message = (f"Enviado em {util.format_seconds(result.elapsed)} "
                      f"({util.format_bytes(size)})")
    logger.info(f"Envio concluido: {result.message}")
    return result


def prune(remote: str, path: str, name_prefix: str, keep_last: int,
          hint: str = "") -> tuple[int, list[str]]:
    """Remove backups antigos da nuvem, preservando os N mais recentes.

    Só toca em arquivos que começam com o prefixo do conjunto e terminam em
    .zip — nada mais que esteja na pasta é candidato.
    """
    if keep_last <= 0:
        return 0, []
    exe = find_rclone(hint)
    if not exe or not remote:
        return 0, []

    prefix = name_prefix.lower()
    ours = [f for f in list_files(remote, path, hint)
            if f.name.lower().startswith(prefix) and f.name.lower().endswith(".zip")]
    victims = ours[keep_last:]
    if not victims:
        return 0, []

    removed = 0
    errors: list[str] = []
    base = _remote_target(remote, path)
    for victim in victims:
        code, out = util.run_process(
            [exe, "deletefile", f"{base}/{victim.name}"], timeout=120)
        if code == 0:
            removed += 1
            logger.info(f"Backup antigo removido da nuvem: {victim.name}")
        else:
            errors.append(f"{victim.name}: {util.truncate(out, 150)}")
    return removed, errors
