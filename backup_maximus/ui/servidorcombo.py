r"""Campo "Servidor" que oferece o que existe nesta máquina.

O backup roda no próprio servidor, então o endereço quase sempre é uma
instância local — e digitar `localhost\SQL2019` de cabeça é onde o cadastro
erra. A lista é lida de novo a cada abertura (instância instalada com o
programa aberto aparece sem reiniciar). Continua editável: um servidor remoto
ainda pode ser digitado.

A interface é a de um QLineEdit (`text`, `setText`, `textChanged`,
`setPlaceholderText`) para o resto da aba tratá-lo como os outros campos.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox


class ServidorCombo(QComboBox):
    textChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._fonte: Callable[[], list[str]] = lambda: []
        self.editTextChanged.connect(self.textChanged)

    # ------------------------------------------------- interface de QLineEdit
    def text(self) -> str:
        return self.currentText()

    def setText(self, texto: str) -> None:
        self.setEditText(texto)

    def setPlaceholderText(self, texto: str) -> None:
        self.lineEdit().setPlaceholderText(texto)

    # -------------------------------------------------------------- opções
    def set_fonte(self, fonte: Callable[[], list[str]]) -> None:
        """Quem diz quais endereços existem; chamado a cada abertura."""
        self._fonte = fonte
        self._recarregar()

    def opcoes(self) -> list[str]:
        return [self.itemText(i) for i in range(self.count())]

    def _recarregar(self) -> None:
        atual = self.currentText()
        self.blockSignals(True)
        self.clear()
        try:
            self.addItems(self._fonte())
        except Exception:  # detecção nunca pode impedir a edição
            pass
        self.setEditText(atual)
        self.blockSignals(False)

    def showPopup(self) -> None:
        self._recarregar()
        super().showPopup()
