"""Conexão autenticada a compartilhamentos de rede (UNC)."""

from __future__ import annotations

from . import logger, util, winapi
from .config import NetCredential

_connected: set[str] = set()


def ensure_access(path: str, creds: list[NetCredential]) -> tuple[bool, str]:
    """Garante acesso ao caminho UNC. Caminho local devolve (True, "")."""
    root = util.unc_root(path)
    if not root:
        return True, ""
    if root.lower() in _connected:
        return True, ""

    # Sessão já existente ou compartilhamento aberto: nada a fazer.
    if util.path_exists(root) or util.path_exists(path):
        _connected.add(root.lower())
        return True, ""

    cred = next(
        (c for c in creds if util.unc_root(c.unc_root).lower() == root.lower()), None
    )
    if cred is None:
        return False, (f"Sem acesso a {root} e nenhuma credencial configurada "
                       f"para este compartilhamento.")

    code = winapi.net_connect(root, cred.user, cred.password)
    if code in (winapi.NO_ERROR, winapi.ERROR_SESSION_CREDENTIAL_CONFLICT):
        # Conflito de credencial significa que já há sessão válida com o servidor.
        _connected.add(root.lower())
        logger.info(f"Conectado ao compartilhamento {root}")
        return True, ""

    hint = ""
    if code == 1326:
        hint = " (usuario ou senha incorretos)"
    elif code == 53:
        hint = " (servidor nao encontrado na rede)"
    return False, f"Falha ao conectar em {root}: erro {code}{hint}"


def disconnect_all() -> None:
    for root in list(_connected):
        winapi.net_disconnect(root)
    _connected.clear()
