"""Seletor das unidades do computador, sem digitação.

A lista é reconstruída toda vez que é aberta: entre configurar o conjunto e
escolher a unidade, o usuário costuma justamente espetar o pen drive.

Há um caso que a lista precisa cobrir para não destruir configuração: o
conjunto pode estar apontado para uma unidade que **não está conectada agora**
— é a situação normal, já que esperar pelo pen drive é a função do campo. Essa
unidade continua na lista, marcada como não conectada, para que abrir a tela
não apague silenciosamente o que já estava configurado.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
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

#: Primeira opção. Vazio no arquivo de configuração significa "não espera", e a
#: lista precisa dizer isso com todas as letras em vez de deixar em branco.
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
    """Lista fechada das unidades montadas.

    O valor é sempre a raiz (`U:\\`), nunca a linha descritiva: o `engine` usa
    isso como caminho, e um texto com rótulo e tamanho não existiria em disco.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # O valor configurado que não corresponde a nenhuma unidade montada.
        # Preservá-lo é o que impede a tela de apagar a configuração ao abrir.
        self._ausente = ""
        #: Caminhos UNC cadastrados na aba Rede. Sem digitação, é por lá que
        #: um compartilhamento entra — e faz sentido: esperar por um caminho
        #: de rede sem ter as credenciais dele só produziria falha na hora do
        #: backup. `set_network_paths` é chamado pela aba de conjuntos.
        self._unc: list[str] = []
        self.refresh()

    def set_network_paths(self, caminhos) -> None:
        """Compartilhamentos vindos da aba Rede, na ordem em que estão lá."""
        novos = [c.strip() for c in caminhos if c and c.strip()]
        if novos == self._unc:
            return
        self._unc = novos
        self.refresh()

    # ------------------------------------------------------------- conteúdo
    def refresh(self, manter: str = "") -> None:
        """Relê as unidades, sem perder o que está escolhido.

        `manter` força um valor que ainda não está na lista — é o caminho por
        onde a configuração de um conjunto chega antes de a unidade existir.
        """
        escolhido = manter or self.value()
        self.blockSignals(True)
        self.clear()
        self.addItem(NAO_ESPERAR, "")

        montadas = winapi.drives()
        for info in montadas:
            self.addItem(describe(info), info.letter)
            if not info.ready:
                self.setItemData(
                    self.count() - 1,
                    "A unidade está montada mas não responde — leitor de cartão "
                    "vazio ou disco ausente.", Qt.ToolTipRole)

        # Compartilhamentos de rede vêm da aba Rede, onde já têm credencial.
        for unc in self._unc:
            self.addItem(f"{unc}  (rede, cadastrado)", unc)

        # O que estava configurado e não está montado agora continua na lista.
        conhecidos = {i.letter.lower() for i in montadas}
        conhecidos |= {u.lower() for u in self._unc}
        if escolhido and escolhido.lower() not in conhecidos:
            self._ausente = escolhido
            self.addItem(f"{escolhido}  (não conectada agora)", escolhido)
            self.setItemData(
                self.count() - 1,
                "Configurada neste conjunto, mas ausente no momento. É o "
                "esperado: o backup aguarda esta unidade aparecer.",
                Qt.ToolTipRole)

        self.blockSignals(False)
        self._selecionar(escolhido)

    def showPopup(self) -> None:
        # Reconstrói a cada abertura, como pedido: entre abrir a tela e abrir a
        # lista, o pen drive costuma ser espetado justamente para escolhê-lo.
        self.refresh()
        super().showPopup()

    # ---------------------------------------------------------------- valor
    def value(self) -> str:
        dado = self.currentData()
        return dado if dado else ""

    def setValue(self, valor: str) -> None:
        valor = (valor or "").strip()
        self._ausente = ""
        if valor and self._indice_de(valor) < 0:
            # Vem da configuração e a unidade não está conectada. É o caso
            # normal: espera-se que o pen drive apareça depois.
            self.refresh(manter=valor)
            return
        self._selecionar(valor)

    def _indice_de(self, valor: str) -> int:
        for indice in range(self.count()):
            if (self.itemData(indice) or "").lower() == valor.lower():
                return indice
        return -1

    def _selecionar(self, valor: str) -> None:
        indice = self._indice_de(valor) if valor else 0
        self.setCurrentIndex(indice if indice >= 0 else 0)
