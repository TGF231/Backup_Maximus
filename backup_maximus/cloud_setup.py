"""Cadastro de serviços de nuvem sem passar pelo console.

O `rclone config` é um assistente de perguntas no terminal — funciona, mas pedir
a um operador de loja que responda a um questionário de texto numa janela preta
é um jeito de garantir que ninguém configure a nuvem.

Todo o fluxo tem equivalente não-interativo:

    rclone config providers          descreve cada serviço e seus campos, em JSON
    rclone authorize <tipo>          faz o OAuth e devolve o token
    rclone config create <nome> ...  cria o remote com os campos já preenchidos
    rclone config delete <nome>      remove

Com isso o formulário é montado a partir do próprio rclone (não há lista de
campos codificada aqui, que envelheceria a cada versão dele), e a única etapa
que continua fora da nossa janela é o consentimento no navegador — que é onde
ele tem de acontecer mesmo.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
from dataclasses import dataclass, field

from . import cloud, logger, oauth_app, util

#: Serviços oferecidos em primeiro plano, na ordem em que fazem sentido aqui.
#: O rclone atende 69 backends; listar todos só atrapalharia quem quer mandar
#: um zip para o Drive da loja.
FEATURED = ("drive", "onedrive", "dropbox", "mega", "sftp", "ftp", "webdav",
            "s3", "b2")

#: Quanto esperar o usuário concluir o consentimento no navegador.
AUTHORIZE_TIMEOUT = 300.0

_LINK_RE = re.compile(r"https?://127\.0\.0\.1:\d+/auth\?\S+")
#: O token vem entre marcadores; o JSON solto é o plano B se o formato mudar.
_TOKEN_BLOCK_RE = re.compile(r"--->\s*(\{.*?\})\s*<---", re.S)
_TOKEN_JSON_RE = re.compile(r"\{\s*\"access_token\".*?\}", re.S)


#: O rclone descreve os campos em inglês. Traduzir os poucos que aparecem de
#: fato — só os obrigatórios dos serviços em destaque — evita pedir "Pass" a
#: quem só quer mandar um zip para o Drive. O que não estiver aqui aparece com
#: o nome original, que é melhor do que uma tradução inventada.
_ROTULOS = {
    "user": "Usuário",
    "username": "Usuário",
    "pass": "Senha",
    "password": "Senha",
    "host": "Servidor",
    "port": "Porta",
    "url": "Endereço",
    "key_file": "Arquivo de chave",
    "account": "Conta",
    "region": "Região",
    "endpoint": "Endpoint",
    "provider": "Provedor",
    "bucket": "Bucket",
    "vendor": "Tipo de servidor",
    "access_key_id": "Chave de acesso",
    "secret_access_key": "Chave secreta",
    "client_id": "ID do cliente",
    "client_secret": "Segredo do cliente",
}

_AJUDAS = {
    "user": "Nome de usuário da conta.",
    "username": "Nome de usuário da conta.",
    "pass": "Senha da conta. Fica cifrada no arquivo do rclone.",
    "password": "Senha da conta. Fica cifrada no arquivo do rclone.",
    "host": "Endereço do servidor, sem o prefixo do protocolo.",
    "port": "Deixe em branco para usar a porta padrão do serviço.",
}


@dataclass
class ProviderOption:
    """Um campo que o serviço pede."""
    name: str
    help: str = ""
    required: bool = False
    is_password: bool = False
    sensitive: bool = False
    type: str = "string"
    default: str = ""
    examples: list[tuple[str, str]] = field(default_factory=list)

    @property
    def label(self) -> str:
        traduzido = _ROTULOS.get(self.name.lower())
        if traduzido:
            return traduzido
        return self.name.replace("_", " ").capitalize()

    @property
    def first_line(self) -> str:
        """Primeira linha da ajuda — o resto costuma ser um manual inteiro."""
        nossa = _AJUDAS.get(self.name.lower())
        if nossa:
            return nossa
        return (self.help or "").strip().splitlines()[0] if self.help else ""


@dataclass
class Provider:
    name: str
    description: str
    options: list[ProviderOption] = field(default_factory=list)
    uses_oauth: bool = False

    @property
    def label(self) -> str:
        """Nome para a lista de escolha.

        Alguns serviços descrevem a si mesmos com um parágrafo inteiro — o do
        S3 enumera cinquenta provedores compatíveis. Numa lista suspensa isso
        vira uma linha ilegível, então cortamos na primeira vírgula ou reticência.
        """
        short = self.description.split(",")[0].strip()
        if len(short) > 46:
            short = short[:45].rstrip() + "…"
        return f"{short} ({self.name})"

    def basic_options(self) -> list[ProviderOption]:
        """Só o que precisa ser preenchido para o serviço funcionar."""
        return [o for o in self.options if o.required]


def list_providers(hint: str = "") -> list[Provider]:
    """Serviços disponíveis, descritos pelo próprio rclone."""
    exe = cloud.find_rclone(hint)
    if not exe:
        return []
    code, out = util.run_process([exe, "config", "providers"], timeout=60)
    if code != 0:
        logger.warn(f"rclone config providers falhou: {util.truncate(out, 300)}")
        return []
    try:
        raw = json.loads(out)
    except json.JSONDecodeError:
        return []

    found: dict[str, Provider] = {}
    for entry in raw:
        name = entry.get("Name", "")
        options = []
        uses_oauth = False
        for opt in entry.get("Options") or []:
            if opt.get("Name") == "token":
                uses_oauth = True
            if opt.get("Advanced") or opt.get("Hide"):
                continue
            options.append(ProviderOption(
                name=opt.get("Name", ""),
                help=opt.get("Help", ""),
                required=bool(opt.get("Required")),
                is_password=bool(opt.get("IsPassword")),
                sensitive=bool(opt.get("Sensitive")),
                type=opt.get("Type", "string"),
                default=str(opt.get("DefaultStr", "") or ""),
                examples=[(e.get("Value", ""), e.get("Help", ""))
                          for e in (opt.get("Examples") or [])],
            ))
        found[name] = Provider(
            name=name,
            description=entry.get("Description", name),
            options=options,
            uses_oauth=uses_oauth,
        )

    # Os destacados primeiro, na ordem escolhida; o resto em ordem alfabética.
    ordered = [found[n] for n in FEATURED if n in found]
    ordered += sorted((p for n, p in found.items() if n not in FEATURED),
                      key=lambda p: p.description.lower())
    return ordered


class AuthorizeSession:
    """Uma sessão de `rclone authorize` acompanhada de fora.

    O rclone sobe um servidor em 127.0.0.1 e imprime o link que inicia o
    consentimento. Abrimos esse link no navegador padrão a partir da interface,
    então o usuário nunca vê um console.
    """

    def __init__(self, provider: str, hint: str = "",
                 client_id: str = "", client_secret: str = ""):
        self.provider = provider
        self.hint = hint
        # A chave tem de valer JÁ na autorização: o consentimento é dado a um
        # aplicativo específico, e um token obtido com outra chave não serve
        # para o remote que vamos criar depois.
        self.client_id = client_id
        self.client_secret = client_secret
        self.process: subprocess.Popen | None = None
        self.link: str = ""
        self.token: str = ""
        self.error: str = ""
        self._output: list[str] = []
        self._lock = threading.Lock()

    def start(self, on_link, on_finish) -> bool:
        """Inicia o processo. `on_link(url)` e `on_finish(ok, mensagem)`."""
        exe = cloud.find_rclone(self.hint)
        if not exe:
            self.error = "rclone não encontrado."
            return False

        args = [exe, "authorize", self.provider]
        if self.client_id:
            # O rclone aceita o par como argumentos posicionais; sem eles usaria
            # a chave compartilhada, que o Drive está aposentando.
            args += [self.client_id, self.client_secret]
        args += ["--auth-no-open-browser"]

        # O escopo não cabe nos argumentos do `authorize`, mas o rclone lê as
        # opções de backend do ambiente. Pedir o escopo certo aqui importa: o
        # consentimento é dado uma vez, e é ele que define o que o token pode.
        env = dict(os.environ)
        for key, value in oauth_app.defaults(self.provider).items():
            env[f"RCLONE_{self.provider.upper()}_{key.upper()}"] = value

        try:
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                env=env,
                creationflags=0x08000000,   # CREATE_NO_WINDOW
            )
        except OSError as exc:
            self.error = f"Não foi possível iniciar o rclone: {exc}"
            return False

        threading.Thread(target=self._pump, args=(on_link, on_finish),
                         daemon=True).start()
        return True

    def _pump(self, on_link, on_finish) -> None:
        """Lê a saída linha a linha, avisando quando o link aparece."""
        assert self.process is not None
        link_sent = False
        try:
            for line in self.process.stdout:  # type: ignore[union-attr]
                with self._lock:
                    self._output.append(line)
                if not link_sent:
                    match = _LINK_RE.search(line)
                    if match:
                        self.link = match.group(0)
                        link_sent = True
                        on_link(self.link)
        except Exception as exc:      # o processo pode ser morto no cancelamento
            logger.warn(f"Leitura da autorizacao interrompida: {exc}")

        self.process.wait()
        text = "".join(self._output)
        token = self._extract_token(text)

        if token:
            self.token = token
            on_finish(True, "Autorização concluída.")
        else:
            self.error = self._explain_failure(text)
            on_finish(False, self.error)

    @staticmethod
    def _extract_token(text: str) -> str:
        """Pega o JSON do token, entre os marcadores ou solto na saída."""
        match = _TOKEN_BLOCK_RE.search(text) or _TOKEN_JSON_RE.search(text)
        if not match:
            return ""
        candidate = match.group(1) if match.lastindex else match.group(0)
        try:
            json.loads(candidate)   # confirma que é JSON válido antes de usar
        except json.JSONDecodeError:
            return ""
        return candidate.strip()

    def _explain_failure(self, text: str) -> str:
        if self.process is not None and self.process.returncode is None:
            return "Autorização cancelada."
        for line in reversed(text.strip().splitlines()):
            clean = line.strip()
            # As linhas NOTICE são o roteiro normal, não o erro.
            if clean and "NOTICE:" not in clean:
                return util.truncate(clean, 300)
        return ("A autorização não foi concluída. Verifique se o consentimento "
                "foi dado no navegador.")

    def cancel(self) -> None:
        if self.process is not None and self.process.poll() is None:
            try:
                self.process.kill()
            except OSError:
                pass


def create_remote(name: str, provider: str, values: dict[str, str],
                  token: str = "", hint: str = "") -> tuple[bool, str]:
    """Cria o remote com os campos já respondidos, sem perguntar nada."""
    exe = cloud.find_rclone(hint)
    if not exe:
        return False, "rclone não encontrado."

    name = name.strip()
    if not name:
        return False, "Dê um nome ao serviço."
    if not re.fullmatch(r"[A-Za-z0-9_.\-]+", name):
        return False, ("O nome aceita apenas letras, números, ponto, hífen e "
                       "sublinhado — é assim que o rclone o identifica.")
    if name in cloud.list_remotes(hint):
        return False, f"Já existe um serviço chamado '{name}'."

    # O que o usuário digitou vence o nosso padrão, e o nosso padrão vence o
    # do rclone: quem informou uma chave própria não pode tê-la sobrescrita.
    campos = oauth_app.defaults(provider)
    client_id, client_secret = oauth_app.credentials(provider)
    if client_id:
        campos["client_id"] = client_id
        campos["client_secret"] = client_secret
    campos.update({k: v for k, v in values.items() if v != ""})
    values = campos

    args = [exe, "config", "create", name, provider, "--non-interactive"]
    for key, value in values.items():
        if value != "":
            args += [f"{key}={value}"]
    if token:
        args += [f"token={token}"]
    # --obscure faz o rclone cifrar as senhas no arquivo de configuração dele;
    # sem isso elas ficariam legíveis em rclone.conf.
    args += ["--obscure"]

    code, out = util.run_process(args, timeout=120)
    if code != 0:
        return False, util.truncate(out, 400) or f"rclone retornou {code}."

    logger.info(f"Servico de nuvem '{name}' ({provider}) cadastrado.")
    return True, f"Serviço '{name}' cadastrado."


def delete_remote(name: str, hint: str = "") -> tuple[bool, str]:
    exe = cloud.find_rclone(hint)
    if not exe:
        return False, "rclone não encontrado."
    code, out = util.run_process([exe, "config", "delete", name], timeout=60)
    if code != 0:
        return False, util.truncate(out, 300)
    logger.info(f"Servico de nuvem '{name}' removido.")
    return True, f"Serviço '{name}' removido."


def config_file_path(hint: str = "") -> str:
    """Onde o rclone guarda os remotes — útil para o usuário saber."""
    exe = cloud.find_rclone(hint)
    if not exe:
        return ""
    code, out = util.run_process([exe, "config", "file"], timeout=30)
    if code != 0:
        return ""
    for line in (out or "").splitlines():
        if os.path.sep in line or ":" in line:
            candidate = line.strip()
            if candidate.lower().endswith(".conf"):
                return candidate
    return ""
