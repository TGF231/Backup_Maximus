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


#: Credenciais padrão do Firebird. SYSDBA/masterkey é o par que vem de fábrica
#: e que a esmagadora maioria das instalações mantém — inclusive o PDV que
#: este programa nasceu para copiar. Exigir que fossem digitadas significava
#: um backup que falha na madrugada por um campo em branco, e o campo em
#: branco já era a intenção de "usar o padrão".
FIREBIRD_USER_PADRAO = "SYSDBA"
FIREBIRD_SENHA_PADRAO = "masterkey"


def firebird_credenciais(item) -> tuple[str, str]:
    """(usuário, senha) do item, completados com o padrão do Firebird."""
    return (item.user or FIREBIRD_USER_PADRAO,
            item.password or FIREBIRD_SENHA_PADRAO)


def senha_ilegivel(item) -> str:
    """Aviso quando há senha gravada que esta conta não decifra, ou ''.

    Substituir por `masterkey` nesse caso seria o pior dos mundos: o backup
    falharia por autenticação e o relatório culparia o banco, quando o
    problema é a conta do Windows que gravou a senha.
    """
    from .config import secret_ilegivel
    if not secret_ilegivel(item.password_enc):
        return ""
    return (f"A senha gravada para '{item.name}' foi cifrada por outro "
            f"usuario do Windows e nao pode ser lida por este. Reabra as "
            f"configuracoes com o mesmo usuario que executa o backup e "
            f"digite a senha de novo.")


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

    aviso = senha_ilegivel(item)
    if aviso:
        return False, aviso
    usuario, senha = firebird_credenciais(item)
    args = [gbak, "-b", "-g", "-t", conn, out_file,
            "-user", usuario, "-password", senha]

    code, out = util.run_process(args)
    if code != 0 or not os.path.isfile(out_file):
        return False, f"gbak falhou (rc={code}): {util.truncate(out)}"
    return True, ""


# ------------------------------------------------------------- SQL Server
def instancias_sql_locais() -> list[str]:
    r"""Instâncias do SQL Server instaladas neste computador, pelo registro.

    "MSSQLSERVER" é a instância padrão (endereço só `localhost`); as outras são
    nomeadas (`localhost\NOME`). Lê as duas visões do registro porque um
    SQL Server de 32 bits num Windows de 64 grava na outra.
    """
    try:
        import winreg
    except ImportError:
        return []
    achadas: list[str] = []
    chave = r"SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL"
    for visao in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, chave, 0,
                                winreg.KEY_READ | visao) as k:
                i = 0
                while True:
                    try:
                        nome = winreg.EnumValue(k, i)[0]
                    except OSError:
                        break
                    if nome not in achadas:
                        achadas.append(nome)
                    i += 1
        except OSError:
            continue
    return achadas


def endereco_sql(nome_instancia: str, host: str = "localhost") -> str:
    """Como o sqlcmd chama a instância: a padrão não leva o nome."""
    if nome_instancia.upper() == "MSSQLSERVER":
        return host
    return host + "\\" + nome_instancia


def _servidores_sql(item: BackupItem) -> list[str]:
    """Endereços a tentar, na ordem.

    Com porta, o sqlcmd vai direto por TCP naquela porta. O SQL Server Express
    e as instâncias nomeadas usam porta dinâmica — ou nem têm TCP ligado — e
    aí a tentativa só expira ("O tempo limite do logon expirou"). Por isso,
    se houver porta, tenta-se também sem ela: o cliente do SQL Server resolve
    a instância pelo SQL Browser ou por memória compartilhada.
    """
    base = item.host.strip() or "localhost"
    if item.port.strip():
        return [f"{base},{item.port.strip()}", base]
    return [base]


def _sqlcmd(item: BackupItem, tool: str, query: str,
            timeout: float | None = None) -> tuple[int, str, str]:
    """Roda a consulta tentando cada endereço. Devolve (código, saída, endereço)."""
    code, out, usado = 1, "", ""
    for servidor in _servidores_sql(item):
        args = [tool, "-S", servidor, "-b", "-l", "15", "-Q", query]
        args += (["-U", item.user, "-P", item.password] if item.user else ["-E"])
        code, out = util.run_process(args, timeout=timeout)
        usado = servidor
        if code == 0:
            break
    return code, out, usado


def _dica_sql(item: BackupItem, usado: str) -> str:
    """O que fazer quando nenhum endereço respondeu."""
    partes = []
    if item.port.strip():
        partes.append(f"Tentado com a porta {item.port.strip()} e sem ela.")
    locais = instancias_sql_locais()
    host = (item.host.strip() or "localhost")
    local = host.split("\\")[0].lower() in ("localhost", ".", "(local)", "127.0.0.1")
    if local and locais:
        nomes = ", ".join(endereco_sql(n) for n in locais)
        partes.append(f"Instâncias neste computador: {nomes}. Use uma delas em Servidor.")
    else:
        partes.append("Confira o nome da instância (ex.: SERVIDOR\\SQLEXPRESS) e se o "
                      "serviço SQL Server está em execução.")
    return " ".join(partes)


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

    code, out, usado = _sqlcmd(item, sqlcmd, query)
    if code != 0 or not os.path.isfile(out_file):
        return False, (f"sqlcmd/BACKUP DATABASE falhou em {usado} (rc={code}): "
                       f"{util.truncate(out)} {_dica_sql(item, usado)}").strip()
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
            usuario, senha = firebird_credenciais(item)
            args = [gstat, "-h", conn, "-user", usuario, "-password", senha]
            code, out = util.run_process(args, timeout=30)
            return (code == 0), ("Conexao OK" if code == 0 else util.truncate(out, 300))
        return True, "gstat.exe nao encontrado; gbak localizado em " + tool

    if item.type is ItemType.SQLSERVER:
        code, out, usado = _sqlcmd(item, tool, "SELECT 1", timeout=30)
        if code == 0:
            if item.port.strip() and usado != _servidores_sql(item)[0]:
                return True, (f"Conexão OK em {usado}, sem a porta {item.port.strip()}: "
                              "nessa porta o servidor não responde. Apague a porta "
                              "do item para o backup não perder tempo com ela.")
            return True, f"Conexão OK em {usado}."
        # A dica vem primeiro: a caixa de mensagem corta o texto longo, e a
        # saída do sqlcmd é longa e genérica.
        return False, (_dica_sql(item, usado) + "\n\n"
                       + util.truncate(out, 300)).strip()

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
