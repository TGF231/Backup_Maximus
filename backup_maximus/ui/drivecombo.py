"""Seletor de unidade que continua aceitando o que ainda não existe.

O campo "Aguardar unidade" tem uma particularidade que descarta a lista
fechada: na hora de configurar, **o pen drive normalmente não está conectado**
— esperar por ele é justamente a função do campo. Uma lista só com o que o
Windows enxerga agora impediria o caso mais comum.

Daí o combo editável: oferece o que está montado, com rótulo e espaço livre
para a escolha ser informada, e aceita `U:\\` digitado mesmo que nenhum U:
exista. A lista é relida ao abrir, porque entre configurar e conferir o
usuário costuma justamente espetar o pen drive.
"""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox

from .. import util, winapi

#: Como cada tipo de unidade se chama para quem lê a tela.
_TIPOS = {
    winapi.DRIVE_REMOVABLE: "removível",
    winapi.DRIVE_FIXED: "fixo",
    winapi.DRIVE_REMOTE: "rede",
    winapi.DRIVE_CDROM: "CD/DVD",
    winapi.DRIVE_RAMDISK: "RAM",
}

#: Texto da primeira opção. Vazio no arquivo de configuração significa
#: "não espera", e a lista precisa dizer isso com todas as letras.
NAO_ESPERAR = "— não esperar —"


def describe(info: winapi.DriveInfo) -> str:
    """Uma linha por unidade, na ordem em que a pessoa decide.

    A letra vem primeiro porque é o que ela procura; o rótulo em seguida
    porque é como ela reconhece o pen drive certo entre dois espetados.
    """
    partes = [info.letter]
    if info.label:
        partes.append(info.label)
    detalhe = _TIPOS.get(info.kind, "?")
    if info.ready:
        detalhe += f", {util.format_bytes(info.free_bytes)} livres"
    else:
        # Leitor de cartão vazio, DVD sem disco: existe na lista e não responde.
        detalhe += ", sem mídia"
    partes.append(f"({detalhe})")
    return "  ".join(partes)


class DriveCombo(QComboBox):
    """Combo editável com as unidades montadas.

    O valor guardado é sempre a raiz (`U:\\`), nunca a linha descritiva: o
    `engine` usa isso como caminho, e um texto com rótulo e tamanho não
    existiria em disco nenhum.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.lineEdit().setPlaceholderText("vazio = não espera")
        self.activated.connect(self._on_activated)
        self.refresh()

    # ------------------------------------------------------------- conteúdo
    def refresh(self) -> None:
        """Relê as unidades, preservando o que estiver digitado."""
        atual = self.value()
        self.blockSignals(True)
        self.clear()
        self.addItem(NAO_ESPERAR, "")
        for info in winapi.drives():
            self.addItem(describe(info), info.letter)
            if not info.ready:
                indice = self.count() - 1
                self.setItemData(
                    indice,
                    "A unidade está montada mas não responde — leitor de cartão "
                    "vazio ou disco ausente.", 3)      # Qt.ToolTipRole
        self.blockSignals(False)
        self.setValue(atual)

    def showPopup(self) -> None:
        # Entre abrir a tela e abrir a lista, o usuário costuma espetar o pen
        # drive justamente para escolhê-lo aqui.
        self.refresh()
        super().showPopup()

    # ---------------------------------------------------------------- valor
    def value(self) -> str:
        texto = self.currentText().strip()
        if texto == NAO_ESPERAR:
            return ""
        # Se o texto é a linha descritiva de um item, devolve a raiz dele.
        indice = self.findText(texto)
        if indice >= 0:
            return self.itemData(indice) or ""
        return texto

    def setValue(self, valor: str) -> None:
        valor = (valor or "").strip()
        if not valor:
            self.setCurrentIndex(0)
            return
        for indice in range(self.count()):
            if (self.itemData(indice) or "").lower() == valor.lower():
                self.setCurrentIndex(indice)
                # A caixa mostra a raiz, não a linha inteira: é o valor real,
                # e o resto o usuário já leu ao escolher.
                self.setEditText(valor)
                return
        # Unidade ainda não conectada — é o caso normal ao configurar.
        self.setCurrentIndex(-1)
        self.setEditText(valor)

    def _on_activated(self, indice: int) -> None:
        self.setEditText(self.itemData(indice) or "")
