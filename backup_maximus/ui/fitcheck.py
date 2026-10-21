"""Confere se as telas cabem sem cortar nem rolar.

Corte silencioso é o pior defeito de layout: nada avisa, e o campo simplesmente
não está lá. Este módulo mede, para o tamanho padrão e para o mínimo da janela,
quanto cada painel precisa e quanto tem.

    python -m backup_maximus.ui.fitcheck

Devolve 0 se tudo cabe, 1 se falta espaço em alguma configuração.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QScrollArea

from .. import logger
from ..config import BackupItem, BackupSet, Config, ItemType, NetCredential



#: Fontes em que o layout foi desenhado, na ordem em que o tema as pede.
#: A medição só vale numa delas: a largura de um campo é a largura do texto,
#: e um substituto genérico chega a ser o dobro.
FONTES_DO_PROJETO = ("Segoe UI", "Noto Sans")


def fonte_disponivel() -> str:
    """Qual das fontes do projeto existe aqui, ou string vazia.

    Sem nenhuma delas não dá para medir nada: a plataforma `offscreen`, por
    exemplo, não traz banco de fontes e substitui tudo por uma Sans Serif bem
    mais larga. Medir ali reprovaria um layout correto — e, pior, aprovaria um
    errado se o substituto fosse estreito.
    """
    from PySide6.QtGui import QFontDatabase
    familias = set(QFontDatabase.families())
    for nome in FONTES_DO_PROJETO:
        if nome in familias:
            return nome
    return ""


def _sample_config() -> Config:
    """Configuração cheia o bastante para o layout mostrar o pior caso."""
    cfg = Config()
    cfg.set_password("x")
    cfg.company_name = "Comércio Aurora Ltda"
    cfg.notify_email = "ti@aurora.com.br"
    cfg.smtp.host = "smtp.aurora.com.br"
    cfg.net_creds.append(NetCredential(unc_root=r"\\srv-nas\backups",
                                       user=r"AURORA\svc_backup"))
    bset = BackupSet(name="BKP_MAXIMUS", destination=r"C:\BACKUP\teste",
                     staging=r"C:\BACKUP", wait_for_path="U:\\", keep_last=3)
    bset.items = [
        BackupItem(
            name="PDV Expresso (banco)", type=ItemType.FIREBIRD,
            source=r"C:\Program Files (x86)\Eagle\Eagle Gestao\Data\2025.002.FDB",
            subfolder="PDVEXPRESSO", output_name="PDVEXPRESSO.FBK",
            host="LOCALHOST", port="3050", user="SYSDBA",
        ),
        BackupItem(name="XMLs destinatário", type=ItemType.FILES,
                   source=r"C:\Program Files (x86)\Eagle\PDVExpresso\Arquivos\Xml",
                   subfolder=r"PDVEXPRESSO\Arquivos\XmlDestinatario"),
    ]
    cfg.sets.append(bset)
    return cfg


def _measure(window, verbose: bool) -> bool:
    """Mede toda QScrollArea da janela. True se nada precisa rolar ou é cortado."""
    ok = True
    for scroll in window.findChildren(QScrollArea):
        contents = scroll.widget()
        if contents is None:
            continue
        need_w = contents.minimumSizeHint().width()
        have_w = scroll.viewport().width()
        need_h = contents.sizeHint().height()
        have_h = scroll.viewport().height()
        clipped = need_w > have_w
        scrolls = need_h > have_h
        ok = ok and not clipped and not scrolls
        if verbose:
            name = scroll.objectName() or "scroll"
            print(f"   {name}: largura precisa {need_w} tem {have_w}"
                  f" {'CORTA' if clipped else 'ok'} | "
                  f"altura precisa {need_h} tem {have_h}"
                  f" {'ROLA' if scrolls else 'ok'}")
    return ok


def check(verbose: bool = True) -> bool:
    app = QApplication.instance() or QApplication([])

    fonte = fonte_disponivel()
    if not fonte:
        # Não é aprovação nem reprovação: é a constatação de que aqui não há
        # como medir. Quem chama decide — o main avisa, o teste pula.
        if verbose:
            print("Nenhuma fonte do projeto disponivel "
                  f"({', '.join(FONTES_DO_PROJETO)}).")
            print("Sem elas a medicao usa um substituto de outra largura e nao")
            print("diz nada sobre o layout real. Rode numa sessao grafica.")
        return True
    from .app import MainWindow, apply_theme

    apply_theme(False)
    window = MainWindow(_sample_config(), "fitcheck.ini", ".")
    window.show()
    app.processEvents()

    results = []
    for label, size in (("tamanho padrão", None),
                        ("tamanho mínimo", (window.minimumWidth(),
                                            window.minimumHeight()))):
        if size:
            window.resize(*size)
        app.processEvents()
        if verbose:
            print(f"{label} — janela {window.width()}x{window.height()}")
        results.append(_measure(window, verbose))

    # Cada aba também é medida com ela mesma visível: uma aba escondida não
    # tem geometria confiável.
    for index in range(window.tabs.count()):
        window.tabs.setCurrentIndex(index)
        app.processEvents()
        title = window.tabs.tabText(index)
        if verbose:
            print(f"aba {title}")
        results.append(_measure(window, verbose))

    window.close()
    return all(results)


def main() -> int:
    logger.init(".")
    ok = check()
    print()
    print("OK — tudo visível sem rolar" if ok
          else "FALHOU — há corte ou rolagem")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
