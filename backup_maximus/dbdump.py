"""Dumps de banco pelas ferramentas nativas de cada SGBD.

Firebird  -> gbak -b -g -t
SQLServer -> sqlcmd + BACKUP DATABASE ... WITH COPY_ONLY
MySQL     -> mysqldump --single-transaction

Usar a ferramenta nativa é intencional: garante integridade transacional do
dump, que uma cópia bruta dos arquivos de dados não daria.
"""

from __future__ import annotations

import glob
import os
import shutil

from .config import BackupItem, ItemType
from . import util


def _search_tool(exe: str, extra_dirs: list[str]) -> str:
    for directory in extra_dirs:
        candidate = os.path.join(directory, exe)
        if os.path.isfile(candidate):
            return candidate
    return shutil.which(exe) or ""


def find_tool(item: BackupItem) -> str:
    """Localiza a ferramenta do tipo, respeitando item.tool_path."""
    if item.tool_path and os.path.isfile(item.tool_path):
        return item.tool_path

    if item.type is ItemType.FIREBIRD:
        roots = glob.glob(r"C:\Program Files\Firebird\*") + \
                glob.glob(r"C:\Program Files (x86)\Firebird\*")
        # Firebird 2.5 mantém o gbak em <raiz>\bin; 3.0+ também na raiz.
        dirs = [os.path.join(r, "bin") for r in roots] + roots
        return _search_tool("gbak.exe", dirs)

    if item.type is ItemType.SQLSERVER:
        roots = glob.glob(r"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\*") + \
                glob.glob(r"C:\Program Files\Microsoft SQL Server\*")
        dirs = [os.path.join(r, "Tools", "Binn") for r in roots]
        return _search_tool("sqlcmd.exe", dirs)

    if item.type is ItemType.MYSQL:
        roots = glob.glob(r"C:\Program Files\MySQL\*") + glob.glob(r"C:\Program Files\MariaDB*")
        return _search_tool("mysqldump.exe", [os.path.join(r, "bin") for r in roots])

    return ""


def _firebird(item: BackupItem, out_file: str) -> tuple[bool, str]:
    gbak = find_tool(item)
    if not gbak:
        return False, "gbak.exe nao encontrado. Informe o caminho no campo 'Ferramenta' do item."

    # Conexão HOST[/porta]:ALIAS — o mesmo LOCALHOST:PDVEXPRESSO do script antigo.
    conn = item.source
    if item.host:
        conn = item.host + (f"/{item.port}" if item.port else "") + f":{item.source}"

    if os.path.isfile(out_file):
        try:
            os.unlink(out_file)
        except OSError:
            pass

    args = [gbak, "-b", "-g", "-t", conn, out_file, "-user", item.user or "SYSDBA"]
    password = item.password
    if password:
        args += ["-password", password]

    code, out = util.run_process(args)
    if code != 0 or not os.path.isfile(out_file):
        return False, f"gbak falhou (rc={code}): {util.truncate(out)}"
    return True, ""


def _sqlserver(item: BackupItem, out_file: str) -> tuple[bool, str]:
    sqlcmd = find_tool(item)
    if not sqlcmd:
        return False, ("sqlcmd.exe nao encontrado. Instale as SQL Server Command Line "
                       "Utilities ou informe o caminho no item.")

    # O BACKUP roda dentro do serviço do SQL Server: a conta de serviço precisa
    # enxergar e escrever em out_file. Para instância local isso é o caso normal.
    database = item.source.replace("]", "]]")
    target = out_file.replace("'", "''")
    query = (f"BACKUP DATABASE [{database}] TO DISK=N'{target}' "
             f"WITH COPY_ONLY, INIT, CHECKSUM")

    server = item.host or "localhost"
    if item.port:
        server += f",{item.port}"

    args = [sqlcmd, "-S", server, "-b", "-Q", query]
    if item.user:
        args += ["-U", item.user, "-P", item.password]
    else:
        args += ["-E"]  # autenticação Windows

    code, out = util.run_process(args)
    if code != 0 or not os.path.isfile(out_file):
        return False, f"sqlcmd/BACKUP DATABASE falhou (rc={code}): {util.truncate(out)}"
    return True, ""


def _mysql(item: BackupItem, out_file: str) -> tuple[bool, str]:
    mysqldump = find_tool(item)
    if not mysqldump:
        return False, "mysqldump.exe nao encontrado. Informe o caminho no item."

    args = [mysqldump, "--single-transaction", "--routines", "--triggers", "--events",
            f"--result-file={out_file}"]
    if item.host:
        args += ["-h", item.host]
    if item.port:
        args += ["-P", item.port]
    if item.user:
        args += ["-u", item.user]
    password = item.password
    if password:
        args.append(f"--password={password}")
    args.append(item.source)

    code, out = util.run_process(args)
    if code != 0 or not os.path.isfile(out_file):
        return False, f"mysqldump falhou (rc={code}): {util.truncate(out)}"
    return True, ""


def dump_database(item: BackupItem, target_dir: str) -> tuple[bool, str, str]:
    """Gera o dump em target_dir. Devolve (ok, caminho_do_arquivo, erro)."""
    try:
        os.makedirs(target_dir, exist_ok=True)
    except OSError as exc:
        return False, "", f"Nao foi possivel criar {target_dir}: {exc}"

    out_file = os.path.join(target_dir, item.dump_filename())
    handler = {
        ItemType.FIREBIRD: _firebird,
        ItemType.SQLSERVER: _sqlserver,
        ItemType.MYSQL: _mysql,
    }.get(item.type)

    if handler is None:
        return False, "", "dump_database chamado para um tipo que nao e banco de dados."

    ok, err = handler(item, out_file)
    return ok, (out_file if ok else ""), err


def test_connection(item: BackupItem) -> tuple[bool, str]:
    """Valida credenciais sem gerar dump — para o botão 'Testar conexão'."""
    tool = find_tool(item)
    if not tool:
        return False, f"Ferramenta do tipo {item.type.label} nao encontrada."

    if item.type is ItemType.FIREBIRD:
        conn = item.source
        if item.host:
            conn = item.host + (f"/{item.port}" if item.port else "") + f":{item.source}"
        # gstat -h lê apenas o cabeçalho do banco: autentica sem tocar nos dados.
        gstat = os.path.join(os.path.dirname(tool), "gstat.exe")
        if os.path.isfile(gstat):
            args = [gstat, "-h", conn, "-user", item.user or "SYSDBA"]
            if item.password:
                args += ["-password", item.password]
            code, out = util.run_process(args, timeout=30)
            return (code == 0), ("Conexao OK" if code == 0 else util.truncate(out, 300))
        return True, "gstat.exe nao encontrado; gbak localizado em " + tool

    if item.type is ItemType.SQLSERVER:
        server = item.host or "localhost"
        if item.port:
            server += f",{item.port}"
        args = [tool, "-S", server, "-b", "-Q", "SELECT 1"]
        args += (["-U", item.user, "-P", item.password] if item.user else ["-E"])
        code, out = util.run_process(args, timeout=30)
        return (code == 0), ("Conexao OK" if code == 0 else util.truncate(out, 300))

    if item.type is ItemType.MYSQL:
        args = [tool, "--no-data", "--result-file=NUL"]
        if item.host:
            args += ["-h", item.host]
        if item.port:
            args += ["-P", item.port]
        if item.user:
            args += ["-u", item.user]
        if item.password:
            args.append(f"--password={item.password}")
        args.append(item.source)
        code, out = util.run_process(args, timeout=30)
        return (code == 0), ("Conexao OK" if code == 0 else util.truncate(out, 300))

    return False, "Tipo sem teste de conexao."
