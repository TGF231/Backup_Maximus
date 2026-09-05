"""Campo de caminho: aceita arrastar-e-soltar e valida depois da digitação.

Duas decisões que valem explicar:

*Por que validar com atraso.* Validar a cada tecla acusaria erro em todo caminho
pela metade — `C:\\Prog` não existe, mas está a caminho de existir. O campo só
julga depois que a digitação para, então o aviso aparece quando ele é útil.

*Por que aviso e não bloqueio.* Um destino que ainda não existe é legítimo (o
programa cria a pasta), e um servidor de rede pode estar fora do ar na hora de
configurar. O campo informa; quem decide é quem configura.
"""

from __future__ import annotations

import os
from enum import Enum

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QLineEdit

from .. import util

#: Tempo de silêncio antes de validar.
DEBOUNCE_MS = 2000


class PathKind(str, Enum):
    FILE = "file"          # precisa existir e ser arquivo
    DIR = "dir"            # precisa existir e ser pasta
    ANY = "any"            # arquivo ou pasta
    DESTINATION = "dest"   # pasta de saída: criada se faltar, precisa ser gravável
    #: Aceita caminho OU nome simples. É o caso do Firebird, onde a origem tanto
    #: pode ser C:\dados\ERP.FDB quanto o alias PDVEXPRESSO registrado no
    #: aliases.conf — cobrar caminho acusaria erro em toda configuração por alias.
    PATH_OR_NAME = "path_or_name"
    NONE = "none"          # sem validação (o campo não é um caminho neste tipo)


def looks_like_path(value: str) -> bool:
    """Distingue um caminho de um nome simples (alias, nome de banco)."""
    value = value.strip()
    if not value:
        return False
    if "\\" in value or "/" in value:
        return True
    if len(value) >= 2 and value[1] == ":":       # C:algo
        return True
    return os.path.splitext(value)[1].lower() in (".fdb", ".gdb", ".dbf")


class PathState(str, Enum):
    NEUTRAL = ""
    OK = "ok"
    WARN = "warn"
    BAD = "bad"


def _cloud_destination(provider: str, space: str) -> tuple[PathState, str]:
    """Como anunciar um destino que um cliente de sincronização já espelha.

    Enquanto o envio pela API está suspenso (`cloud.ENVIO_POR_API`), esta é a
    via **recomendada** para levar o backup à nuvem — e não mais o plano B que
    era quando a API funcionava.

    Duas verdades competem aqui, e a escolha entre elas é de produto:

    - É o caminho certo, e o operador acaba de fazer o que a tela pediu.
    - A garantia é menor: o backup é dado como concluído quando o zip toca o
      disco, e quem envia é o cliente de sincronização, depois, sem ninguém
      conferir se chegou.

    `space` já vem pronto (ex.: "12,4 GB livres no destino.") e pode ser
    vazio; concatene com cuidado para não sobrar espaço solto.

    Por ora fica no âmbar que já existia, para preservar a distinção entre
    "gravado" e "chegou na nuvem". A escolha entre âmbar e verde é de produto e
    segue em aberto — trocar aqui muda a tela inteira, e só aqui.
    """
    return PathState.WARN, (
        f"Pasta do {provider} — é assim que o backup vai para a nuvem hoje. "
        f"O backup conclui ao gravar o arquivo; o envio é feito depois pelo "
        f"{provider}, então confirme lá que subiu. {space}"
    ).strip()


def validate(path: str, kind: PathKind) -> tuple[PathState, str]:
    """Avalia um caminho. Devolve (estado, mensagem para o usuário)."""
    path = path.strip()
    if not path or kind is PathKind.NONE:
        return PathState.NEUTRAL, ""

    if kind is PathKind.PATH_OR_NAME:
        if not looks_like_path(path):
            return PathState.NEUTRAL, "Tratado como alias registrado no servidor."
        kind = PathKind.ANY

    if util.is_unc(path) and not util.path_exists(path):
        # Compartilhamento pode exigir credencial da aba Rede, ou estar fora do
        # ar agora e disponível na hora do backup. Nunca é erro definitivo.
        return PathState.WARN, (
            f"Sem acesso a {util.unc_root(path)} agora. Se precisar de "
            f"credencial, cadastre na aba Rede."
        )

    exists = util.path_exists(path)

    if kind is PathKind.DESTINATION:
        if exists:
            if not os.path.isdir(path):
                return PathState.BAD, "Existe um arquivo com esse nome; informe uma pasta."
            if not os.access(path, os.W_OK):
                return PathState.BAD, "A pasta existe, mas não aceita gravação."

            provider = util.cloud_provider(path)
            free = util.free_space(path)
            space = f"{util.format_bytes(free)} livres no destino." if free else ""
            if provider:
                return _cloud_destination(provider, space)
            return (PathState.OK, space) if space else (PathState.OK, "")
        parent = os.path.dirname(os.path.normpath(path)) or path
        if os.path.isdir(parent):
            return PathState.WARN, "A pasta ainda não existe; será criada no backup."
        return PathState.BAD, f"Caminho inacessível: {parent}"

    if not exists:
        return PathState.BAD, "Caminho não encontrado."
    if kind is PathKind.FILE and not os.path.isfile(path):
        return PathState.BAD, "Isto é uma pasta; informe um arquivo."
    if kind is PathKind.DIR and not os.path.isdir(path):
        return PathState.BAD, "Isto é um arquivo; informe uma pasta."

    if os.path.isdir(path):
        return PathState.OK, "Pasta encontrada."
    try:
        return PathState.OK, f"Arquivo encontrado ({util.format_bytes(os.path.getsize(path))})."
    except OSError:
        return PathState.OK, "Arquivo encontrado."


class PathEdit(QLineEdit):
    """QLineEdit que aceita soltar arquivos/pastas e se valida sozinho.

    O construtor recebe apenas `parent` porque a classe é promovida no Qt
    Designer, e o código gerado pelo uic sempre chama `PathEdit(pai)`. A regra
    de validação vem da propriedade dinâmica `pathKind` declarada no .ui — ou
    seja, o layout diz o que o campo significa — e pode ser trocada em tempo de
    execução com `set_kind` quando o tipo do item muda.
    """

    #: (estado, mensagem) sempre que a validação roda
    validated = Signal(object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._kind: PathKind | None = None
        self.setAcceptDrops(True)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(DEBOUNCE_MS)
        self._timer.timeout.connect(self.validate_now)
        self.textChanged.connect(self._on_text_changed)

    # ------------------------------------------------------------ validação
    @property
    def kind(self) -> PathKind:
        """Regra do campo, lida do .ui na primeira consulta.

        A leitura é adiada porque o uic define as propriedades dinâmicas depois
        de construir o widget — no __init__ elas ainda não existem.
        """
        if self._kind is None:
            raw = self.property("pathKind")
            try:
                self._kind = PathKind(raw) if raw else PathKind.ANY
            except ValueError:
                self._kind = PathKind.ANY
        return self._kind

    @kind.setter
    def kind(self, value: PathKind) -> None:
        self._kind = value

    def set_kind(self, kind: PathKind) -> None:
        """Troca a regra (o tipo do item mudou o significado do campo)."""
        if kind is self.kind:
            return
        self._kind = kind
        self._timer.stop()
        self.validate_now()

    def _on_text_changed(self, _text: str) -> None:
        # Enquanto digita o campo volta ao neutro: manter um erro antigo na tela
        # enquanto o texto já mudou é pior do que não mostrar nada.
        self._set_state(PathState.NEUTRAL)
        self._timer.start()

    def validate_now(self) -> tuple[PathState, str]:
        state, message = validate(self.text(), self.kind)
        self._set_state(state)
        self.validated.emit(state, message)
        return state, message

    def _set_state(self, state: PathState) -> None:
        if self.property("state") == state.value:
            return
        self.setProperty("state", state.value)
        self.style().unpolish(self)
        self.style().polish(self)

    # -------------------------------------------------------- arrastar/soltar
    @staticmethod
    def _dropped_path(event) -> str:
        mime = event.mimeData()
        if not mime.hasUrls():
            return ""
        for url in mime.urls():
            if url.isLocalFile():
                return os.path.normpath(url.toLocalFile())
        return ""

    def _accepts(self, path: str) -> bool:
        if not path:
            return False
        if self.kind is PathKind.FILE:
            return os.path.isfile(path)
        if self.kind in (PathKind.DIR, PathKind.DESTINATION):
            return os.path.isdir(path)
        return True

    def _set_dragover(self, on: bool) -> None:
        self.setProperty("dragover", "true" if on else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event) -> None:
        if self.isEnabled() and self._accepts(self._dropped_path(event)):
            event.acceptProposedAction()
            self._set_dragover(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if self.isEnabled() and self._accepts(self._dropped_path(event)):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._set_dragover(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self._set_dragover(False)
        path = self._dropped_path(event)
        if not self._accepts(path):
            event.ignore()
            return
        # Soltar uma pasta num campo que quer arquivo, ou vice-versa, já foi
        # barrado em _accepts; aqui é só aceitar.
        self.setText(path)
        self._timer.stop()
        self.validate_now()
        event.acceptProposedAction()
        self.setFocus()
