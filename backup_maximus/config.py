"""Modelo de configuração e persistência em INI.

Modelo Conjunto -> Itens: um CONJUNTO produz exatamente um .zip; cada ITEM
coloca seu conteúdo numa subpasta da árvore de montagem, e a árvore inteira
vira esse zip.

O formato do INI é o mesmo da versão C++ — os arquivos são intercambiáveis.
"""

from __future__ import annotations

import base64
import configparser
import hashlib
import os
import secrets
from dataclasses import dataclass, field
from enum import Enum

from . import winapi


# ------------------------------------------------------------------ enums
class ItemType(str, Enum):
    FIREBIRD = "firebird"
    SQLSERVER = "sqlserver"
    MYSQL = "mysql"
    DBF = "dbf"
    FILES = "files"

    @property
    def is_database(self) -> bool:
        return self in (ItemType.FIREBIRD, ItemType.SQLSERVER, ItemType.MYSQL)

    @property
    def dump_ext(self) -> str:
        return {
            ItemType.FIREBIRD: ".fbk",
            ItemType.SQLSERVER: ".bak",
            ItemType.MYSQL: ".sql",
        }.get(self, "")

    @property
    def label(self) -> str:
        return {
            ItemType.FIREBIRD: "Firebird",
            ItemType.SQLSERVER: "SQL Server",
            ItemType.MYSQL: "MySQL",
            ItemType.DBF: "DBF",
            ItemType.FILES: "Arquivo/Pasta",
        }[self]


class SetMode(str, Enum):
    INCREMENTAL = "incremental"
    FULL = "full"

    @property
    def label(self) -> str:
        return ("Incremental (1 zip fixo)" if self is SetMode.INCREMENTAL
                else "Completo (zip por execução)")


def parse_enum(cls, raw: str, default):
    try:
        return cls((raw or "").strip().lower())
    except ValueError:
        return default


# ------------------------------------------------------------- segredos
def protect_secret(plain: str) -> str:
    """Cifra com DPAPI e devolve Base64. String vazia continua vazia."""
    if not plain:
        return ""
    enc = winapi.dpapi_protect(plain.encode("utf-8"))
    return base64.b64encode(enc).decode("ascii") if enc else ""


def unprotect_secret(enc_b64: str) -> str:
    if not enc_b64:
        return ""
    try:
        raw = base64.b64decode(enc_b64, validate=True)
    except Exception:
        return ""
    plain = winapi.dpapi_unprotect(raw)
    return plain.decode("utf-8", "replace") if plain else ""


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# ------------------------------------------------------------- estruturas
@dataclass
class BackupItem:
    name: str = ""
    type: ItemType = ItemType.FILES
    #: Firebird: alias ou .fdb | SQL/MySQL: nome do banco | Files/DBF: arquivo ou pasta
    source: str = ""
    #: caminho relativo DENTRO do zip (ex.: "PDVEXPRESSO\\Arquivos\\Log")
    subfolder: str = ""
    #: nome do arquivo de dump; vazio = <name> + extensão padrão do tipo
    output_name: str = ""
    #: espelha a origem (remove o que sumiu) — equivale ao ROBOCOPY /MIR
    mirror: bool = True
    host: str = ""
    port: str = ""
    user: str = ""
    password_enc: str = ""
    tool_path: str = ""
    enabled: bool = True

    @property
    def password(self) -> str:
        return unprotect_secret(self.password_enc)

    def set_password(self, plain: str) -> None:
        self.password_enc = protect_secret(plain)

    def dump_filename(self) -> str:
        return self.output_name.strip() or f"{self.name}{self.type.dump_ext}"


@dataclass
class BackupSet:
    name: str = "BKP_MAXIMUS"
    #: árvore de montagem; vazio = <pasta do app>/staging/<name>
    staging: str = ""
    #: onde o zip final é gravado (ex.: "U:\\")
    destination: str = ""
    mode: SetMode = SetMode.FULL
    #: aguarda esse caminho ficar acessível antes de começar (ex.: "U:\\")
    wait_for_path: str = ""
    wait_timeout_sec: int = 300
    #: manter a árvore entre execuções acelera muito as próximas
    keep_staging: bool = True
    #: Quantos .zip manter no destino (modo Completo). 0 = manter todos.
    #: No modo Incremental não se aplica: existe um arquivo só.
    keep_last: int = 0

    #: Envio para nuvem pela API do serviço (via rclone). Vazio = não envia.
    #: `cloud_remote` é o nome do remote configurado no rclone.
    cloud_remote: str = ""
    cloud_path: str = ""
    #: Retenção na nuvem, independente da local: a nuvem costuma ter mais
    #: espaço que o pen drive, e faz sentido guardar mais tempo lá.
    cloud_keep_last: int = 0
    enabled: bool = True
    items: list[BackupItem] = field(default_factory=list)

    def staging_dir(self, app_dir: str) -> str:
        return self.staging.strip() or os.path.join(app_dir, "staging", self.name)

    @property
    def active_items(self) -> list[BackupItem]:
        return [i for i in self.items if i.enabled]


@dataclass
class NetCredential:
    unc_root: str = ""
    user: str = ""
    password_enc: str = ""

    @property
    def password(self) -> str:
        return unprotect_secret(self.password_enc)


@dataclass
class SmtpConfig:
    host: str = ""
    port: int = 587
    use_ssl: bool = True
    user: str = ""
    password_enc: str = ""
    sender: str = ""

    @property
    def password(self) -> str:
        return unprotect_secret(self.password_enc)


@dataclass
class Config:
    company_name: str = ""
    notify_email: str = ""
    alert_timeout_hours: int = 26
    send_report_email: bool = False
    ui_password_hash: str = ""
    ui_password_salt: str = ""
    sevenzip_path: str = ""
    #: Caminho do rclone.exe (vazio = empacotado com o app, ou do sistema).
    rclone_path: str = ""
    #: Preferência de aparência, lembrada entre execuções.
    dark_theme: bool = False

    #: Lembrete diário. O horário é registrado no Agendador do Windows; a
    #: aplicação não precisa ficar rodando.
    reminder_enabled: bool = False
    reminder_time: str = "22:00"

    smtp: SmtpConfig = field(default_factory=SmtpConfig)
    net_creds: list[NetCredential] = field(default_factory=list)
    sets: list[BackupSet] = field(default_factory=list)

    last_run_unix: int = 0
    last_run_status: str = ""

    # ---------------------------------------------------------- senha da UI
    @property
    def has_password(self) -> bool:
        return bool(self.ui_password_hash)

    def set_password(self, plain: str) -> None:
        self.ui_password_salt = secrets.token_hex(16)
        self.ui_password_hash = sha256_hex(self.ui_password_salt + plain)

    def check_password(self, plain: str) -> bool:
        if not self.ui_password_hash:
            return True
        # compare_digest evita vazar informação pelo tempo de comparação
        return secrets.compare_digest(
            sha256_hex(self.ui_password_salt + plain), self.ui_password_hash
        )

    def total_items(self) -> int:
        return sum(len(s.items) for s in self.sets)

    # ------------------------------------------------------------------ INI
    @staticmethod
    def default_path(app_dir: str) -> str:
        return os.path.join(app_dir, "backup_maximus.ini")

    @classmethod
    def load(cls, path: str) -> "Config | None":
        if not os.path.isfile(path):
            return None
        parser = configparser.ConfigParser(interpolation=None)
        # allow_no_value + leitura tolerante: um INI editado à mão não pode
        # derrubar o backup por causa de uma linha estranha.
        try:
            with open(path, "r", encoding="utf-8-sig") as fh:
                parser.read_file(fh)
        except (OSError, configparser.Error):
            return None

        def get(section: str, key: str, default: str = "") -> str:
            return parser.get(section, key, fallback=default).strip()

        def get_int(section: str, key: str, default: int) -> int:
            try:
                return int(get(section, key, str(default)) or default)
            except ValueError:
                return default

        def get_bool(section: str, key: str, default: bool) -> bool:
            raw = get(section, key, "")
            return default if raw == "" else raw == "1"

        cfg = cls()
        cfg.company_name = get("general", "company")
        cfg.notify_email = get("general", "notify_email")
        cfg.alert_timeout_hours = get_int("general", "alert_timeout_hours", 26)
        cfg.send_report_email = get_bool("general", "send_report_email", False)
        cfg.ui_password_hash = get("general", "ui_password_hash")
        cfg.ui_password_salt = get("general", "ui_password_salt")
        cfg.sevenzip_path = get("general", "sevenzip_path")
        cfg.rclone_path = get("general", "rclone_path")
        cfg.dark_theme = get_bool("general", "dark_theme", False)
        cfg.reminder_enabled = get_bool("general", "reminder_enabled", False)
        cfg.reminder_time = get("general", "reminder_time", "22:00") or "22:00"

        cfg.smtp = SmtpConfig(
            host=get("smtp", "host"),
            port=get_int("smtp", "port", 587),
            use_ssl=get_bool("smtp", "ssl", True),
            user=get("smtp", "user"),
            password_enc=get("smtp", "password_enc"),
            sender=get("smtp", "from"),
        )

        cfg.last_run_unix = get_int("state", "last_run_unix", 0)
        cfg.last_run_status = get("state", "last_run_status")

        i = 1
        while parser.has_section(f"netcred.{i}"):
            sec = f"netcred.{i}"
            unc = get(sec, "unc")
            if unc:
                cfg.net_creds.append(NetCredential(
                    unc_root=unc, user=get(sec, "user"),
                    password_enc=get(sec, "password_enc"),
                ))
            i += 1

        s = 1
        while parser.has_section(f"set.{s}"):
            sec = f"set.{s}"
            bs = BackupSet(
                name=get(sec, "name", f"conjunto{s}"),
                staging=get(sec, "staging"),
                destination=get(sec, "destination"),
                mode=parse_enum(SetMode, get(sec, "mode", "full"), SetMode.FULL),
                wait_for_path=get(sec, "wait_for_path"),
                wait_timeout_sec=get_int(sec, "wait_timeout_sec", 300),
                keep_staging=get_bool(sec, "keep_staging", True),
                keep_last=get_int(sec, "keep_last", 0),
                cloud_remote=get(sec, "cloud_remote"),
                cloud_path=get(sec, "cloud_path"),
                cloud_keep_last=get_int(sec, "cloud_keep_last", 0),
                enabled=get_bool(sec, "enabled", True),
            )
            k = 1
            while parser.has_section(f"item.{s}.{k}"):
                isec = f"item.{s}.{k}"
                bs.items.append(BackupItem(
                    name=get(isec, "name", f"item{k}"),
                    type=parse_enum(ItemType, get(isec, "type", "files"), ItemType.FILES),
                    source=get(isec, "source"),
                    subfolder=get(isec, "subfolder"),
                    output_name=get(isec, "output_name"),
                    mirror=get_bool(isec, "mirror", True),
                    host=get(isec, "host"),
                    port=get(isec, "port"),
                    user=get(isec, "user"),
                    password_enc=get(isec, "password_enc"),
                    tool_path=get(isec, "tool_path"),
                    enabled=get_bool(isec, "enabled", True),
                ))
                k += 1
            cfg.sets.append(bs)
            s += 1

        return cfg

    def save(self, path: str) -> bool:
        lines: list[str] = [
            "; Backup Maximus - arquivo de configuracao",
            "; Um [set.N] produz UM arquivo .zip. Cada [item.N.M] coloca seu conteudo",
            "; na subpasta indicada dentro da arvore de montagem, e a arvore inteira",
            "; vira esse zip. Senhas sao cifradas com DPAPI (validas so nesta maquina).",
            "",
            "[general]",
            f"company={self.company_name}",
            f"notify_email={self.notify_email}",
            f"alert_timeout_hours={self.alert_timeout_hours}",
            f"send_report_email={1 if self.send_report_email else 0}",
            f"ui_password_hash={self.ui_password_hash}",
            f"ui_password_salt={self.ui_password_salt}",
            f"sevenzip_path={self.sevenzip_path}",
            f"rclone_path={self.rclone_path}",
            f"dark_theme={1 if self.dark_theme else 0}",
            f"reminder_enabled={1 if self.reminder_enabled else 0}",
            f"reminder_time={self.reminder_time}",
            "",
            "[smtp]",
            f"host={self.smtp.host}",
            f"port={self.smtp.port}",
            f"ssl={1 if self.smtp.use_ssl else 0}",
            f"user={self.smtp.user}",
            f"password_enc={self.smtp.password_enc}",
            f"from={self.smtp.sender}",
            "",
            "[state]",
            f"last_run_unix={self.last_run_unix}",
            f"last_run_status={self.last_run_status}",
            "",
        ]

        for n, nc in enumerate(self.net_creds, 1):
            lines += [f"[netcred.{n}]", f"unc={nc.unc_root}", f"user={nc.user}",
                      f"password_enc={nc.password_enc}", ""]

        for si, bs in enumerate(self.sets, 1):
            lines += [
                f"[set.{si}]",
                f"name={bs.name}",
                f"staging={bs.staging}",
                f"destination={bs.destination}",
                f"mode={bs.mode.value}",
                f"wait_for_path={bs.wait_for_path}",
                f"wait_timeout_sec={bs.wait_timeout_sec}",
                f"keep_staging={1 if bs.keep_staging else 0}",
                f"keep_last={bs.keep_last}",
                f"cloud_remote={bs.cloud_remote}",
                f"cloud_path={bs.cloud_path}",
                f"cloud_keep_last={bs.cloud_keep_last}",
                f"enabled={1 if bs.enabled else 0}",
                "",
            ]
            for ii, it in enumerate(bs.items, 1):
                lines += [
                    f"[item.{si}.{ii}]",
                    f"name={it.name}",
                    f"type={it.type.value}",
                    f"source={it.source}",
                    f"subfolder={it.subfolder}",
                    f"output_name={it.output_name}",
                    f"mirror={1 if it.mirror else 0}",
                    f"host={it.host}",
                    f"port={it.port}",
                    f"user={it.user}",
                    f"password_enc={it.password_enc}",
                    f"tool_path={it.tool_path}",
                    f"enabled={1 if it.enabled else 0}",
                    "",
                ]

        text = "\n".join(lines)
        tmp = path + ".tmp"
        try:
            # Grava num temporário e troca: uma queda no meio da escrita não
            # deixa a configuração pela metade.
            with open(tmp, "w", encoding="utf-8-sig", newline="\n") as fh:
                fh.write(text)
            os.replace(tmp, path)
            return True
        except OSError:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            return False
