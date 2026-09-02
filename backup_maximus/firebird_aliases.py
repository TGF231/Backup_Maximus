"""Descoberta de aliases do Firebird.

Digitar o caminho do .fdb à mão é a parte mais chata e mais sujeita a erro de
configurar um backup — ainda mais quando o servidor já tem os bancos
registrados por alias. Este módulo lê essa lista direto do servidor.

Formatos, ambos `nome = caminho`:

    Firebird 2.5   aliases.conf      2025.002 = C:\\dados\\2025.002.FDB
    Firebird 3+    databases.conf    DADOS = C:\\UpSystem\\Dados\\DADOS.FDB
                                     {
                                     DefaultDBCachePages = 312144
                                     }

O bloco entre chaves do Firebird 3+ traz parâmetros por banco e é ignorado.
Entradas internas do servidor (com macro `$(...)`, como a base de segurança)
também ficam de fora: não são dados de cliente.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from . import logger

#: Entradas que o próprio servidor registra e não interessam a um backup.
_SYSTEM_ENTRIES = {"security.db", "security3.db", "security4.db", "security5.db"}

_ALIAS_LINE = re.compile(r"^\s*([^#=\s{}][^=]*?)\s*=\s*(.+?)\s*$")


@dataclass
class FirebirdInstance:
    """Uma instalação do Firebird encontrada na máquina."""
    root: str                 # C:\Program Files\Firebird\Firebird_2_5
    version: str              # "2.5", "5.0" ou "?"
    config_file: str          # aliases.conf ou databases.conf
    gbak: str = ""            # caminho do gbak.exe, se achado

    @property
    def label(self) -> str:
        return f"Firebird {self.version}"


@dataclass
class FirebirdAlias:
    """Um banco registrado no servidor."""
    name: str
    path: str
    instance: FirebirdInstance
    exists: bool = False
    size: int = 0

    @property
    def status(self) -> str:
        if not self.exists:
            return "arquivo não encontrado"
        from . import util
        return util.format_bytes(self.size)


# ------------------------------------------------------------ instalações
def _version_from_path(root: str) -> str:
    """Firebird_2_5 -> 2.5 ; Firebird_5_0 -> 5.0"""
    match = re.search(r"Firebird[_\- ]?(\d+)[_\-.](\d+)", os.path.basename(root),
                      re.IGNORECASE)
    return f"{match.group(1)}.{match.group(2)}" if match else "?"


def _registry_roots() -> list[str]:
    """Instâncias registradas — é onde o servidor realmente diz onde está."""
    roots: list[str] = []
    try:
        import winreg
    except ImportError:
        return roots

    key_path = r"SOFTWARE\Firebird Project\Firebird Server\Instances"
    for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0,
                                winreg.KEY_READ | view) as key:
                index = 0
                while True:
                    try:
                        _name, value, _kind = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    if isinstance(value, str) and value.strip():
                        roots.append(os.path.normpath(value.strip()))
                    index += 1
        except OSError:
            continue
    return roots


def _glob_roots() -> list[str]:
    """Instalações fora do registro (cópia manual, servidor embarcado)."""
    import glob
    found: list[str] = []
    for pattern in (r"C:\Program Files\Firebird\*",
                    r"C:\Program Files (x86)\Firebird\*"):
        found.extend(p for p in glob.glob(pattern) if os.path.isdir(p))
    return found


def find_instances() -> list[FirebirdInstance]:
    """Instalações do Firebird com arquivo de aliases legível."""
    instances: list[FirebirdInstance] = []
    seen: set[str] = set()

    for root in _registry_roots() + _glob_roots():
        key = os.path.normpath(root).rstrip("\\").lower()
        if key in seen:
            continue
        seen.add(key)

        # 2.5 usa aliases.conf; 3+ usa databases.conf. Procuramos os dois
        # porque uma instalação atualizada no lugar pode ter ambos.
        for filename in ("aliases.conf", "databases.conf"):
            config = os.path.join(root, filename)
            if not os.path.isfile(config):
                continue
            gbak = ""
            for candidate in (os.path.join(root, "bin", "gbak.exe"),
                              os.path.join(root, "gbak.exe")):
                if os.path.isfile(candidate):
                    gbak = candidate
                    break
            instances.append(FirebirdInstance(
                root=root, version=_version_from_path(root),
                config_file=config, gbak=gbak,
            ))
            break

    instances.sort(key=lambda i: i.version, reverse=True)
    return instances


# ------------------------------------------------------------------ aliases
def parse_alias_file(text: str) -> list[tuple[str, str]]:
    """Extrai (nome, caminho) do conteúdo de um aliases.conf/databases.conf."""
    aliases: list[tuple[str, str]] = []
    depth = 0

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue

        # O bloco { } do Firebird 3+ traz parâmetros do banco anterior.
        if depth or line.startswith("{"):
            depth += line.count("{") - line.count("}")
            depth = max(depth, 0)
            continue

        match = _ALIAS_LINE.match(line)
        if not match:
            continue

        name, path = match.group(1).strip(), match.group(2).strip()
        # A chave de abertura pode vir na mesma linha do caminho.
        if path.endswith("{"):
            path = path[:-1].strip()
            depth += 1
        if not name or not path:
            continue
        if name.lower() in _SYSTEM_ENTRIES:
            continue
        # Macros do próprio servidor: $(dir_secDb), $(root) etc.
        if "$(" in path:
            continue
        aliases.append((name, os.path.normpath(path)))

    return aliases


def read_aliases(instance: FirebirdInstance) -> list[FirebirdAlias]:
    """Lê os aliases de uma instalação, já com o estado de cada arquivo."""
    try:
        with open(instance.config_file, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        logger.warn(f"Nao foi possivel ler {instance.config_file}: {exc}")
        return []

    result: list[FirebirdAlias] = []
    for name, path in parse_alias_file(text):
        alias = FirebirdAlias(name=name, path=path, instance=instance)
        try:
            alias.size = os.path.getsize(path)
            alias.exists = True
        except OSError:
            # O alias pode apontar para um banco em outra máquina ou desmontado;
            # continua sendo um alias válido para o gbak resolver no servidor.
            alias.exists = False
        result.append(alias)
    return result


def discover() -> list[FirebirdAlias]:
    """Todos os aliases de todas as instalações encontradas."""
    aliases: list[FirebirdAlias] = []
    for instance in find_instances():
        found = read_aliases(instance)
        logger.info(f"Firebird {instance.version}: {len(found)} alias(es) em "
                    f"{instance.config_file}")
        aliases.extend(found)
    return aliases
