"""Tela "Sobre": versão, licenças e diagnóstico.

Não é enfeite. A LGPLv3 da PySide6/Qt exige **aviso visível** de que o programa
usa a biblioteca e sob qual licença; um arquivo de texto na pasta de instalação
cumpre a letra, mas uma tela que o usuário alcança em um clique cumpre a
intenção. A aba de diagnóstico existe pelo motivo prático de sempre: é o
primeiro conjunto de dados que o suporte pede, e digitá-lo à mão dá erro.
"""

from __future__ import annotations

import os
import platform
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QDialog

from .. import __version__, cloud, paths
from . import forms

#: Identificação do fornecedor, num lugar só. A mesma informação está nos
#: documentos em docs/ e nas propriedades do executável (BackupMaximus.spec);
#: ao mudar aqui, confira os três.
EMPRESA = "WALYTECH SOLUÇÕES TECNOLÓGICAS LTDA"
CNPJ = "50.449.577/0001-53"
EMAIL = "tgf231.dev@gmail.com"
SITE = "https://github.com/TGF231/backup-maximus-docs"
SITE_CURTO = "github.com/TGF231/backup-maximus-docs"


def _licenses_dir() -> str:
    """Pasta com os textos completos, dentro do pacote ou do código-fonte."""
    return os.path.join(paths.resource_dir(), "licenses")


def _texto_aplicativo() -> str:
    return f"""
<p><b>Backup Maximus {__version__}</b></p>
<p>Agente de backup para Windows. Copia bancos de dados e arquivos para uma
árvore de pastas, compacta tudo em um único .zip e, opcionalmente, envia para
um serviço de armazenamento em nuvem.</p>
<p>© 2026 {EMPRESA} — CNPJ {CNPJ}.<br>Todos os direitos reservados.</p>
<p><b>Privacidade em uma linha:</b> o programa roda inteiramente nesta máquina.
Não há telemetria, e nada é enviado ao desenvolvedor.</p>
<p>Política de privacidade e termos de serviço acompanham a instalação e estão
publicados em <a href="{SITE}">{SITE_CURTO}</a>.</p>
<p>Suporte: <a href="mailto:{EMAIL}">{EMAIL}</a></p>
"""


def _texto_terceiros() -> str:
    """O aviso que a LGPL exige, mais o crédito de quem não exige nada."""
    return """
<p><b>PySide6 / Qt 6</b> — GNU Lesser General Public License, versão 3.</p>
<p>Este programa usa a biblioteca PySide6 (Qt for Python), da The Qt Company,
distribuída sob a LGPLv3. O texto completo da licença, e o da GPLv3 à qual ela
se refere, acompanham a instalação — botão <i>Ver licenças</i> abaixo.</p>
<p>A LGPLv3 assegura a você o direito de <b>substituir</b> a biblioteca Qt por
outra versão compatível. Para isso, distribuímos também uma versão do programa
em pasta, com as bibliotecas do Qt separadas e substituíveis. Solicite-a pelo
canal de suporte, ou obtenha-a na página de versões do projeto.</p>
<p>Código-fonte do Qt: <a href="https://download.qt.io/official_releases/qt/">download.qt.io</a></p>
<hr>
<p><b>rclone</b> — licença MIT. Copyright © 2012 Nick Craig-Wood e
colaboradores. Usado para o envio aos serviços de nuvem.
<a href="https://rclone.org/">rclone.org</a></p>
<p><b>7-Zip</b> — GNU LGPL. Copyright © 1999-2026 Igor Pavlov. Usado para
compactar. <a href="https://www.7-zip.org/">7-zip.org</a></p>
<p>Ambos são executados como programas independentes, e não são vinculados a
este aplicativo.</p>
<hr>
<p><b>Python</b> — Python Software Foundation License.
<a href="https://www.python.org/">python.org</a></p>
<p>As ferramentas de banco de dados (<code>gbak</code>, <code>sqlcmd</code>,
<code>mysqldump</code>) não são distribuídas com este programa: ele usa as que
já estão instaladas nesta máquina.</p>
"""


def diagnostico(app_dir: str = "") -> str:
    """Texto puro, para o usuário copiar e colar num e-mail de suporte."""
    rclone = cloud.version(hint="") or "não encontrado"
    seven = paths.find_vendor_tool("7za.exe", "7z.exe") or "não encontrado"
    linhas = [
        f"Backup Maximus  : {__version__}",
        f"Windows         : {platform.platform()}",
        f"Arquitetura     : {platform.machine()}",
        f"Python          : {platform.python_version()}",
        f"Empacotado      : {'sim' if getattr(sys, 'frozen', False) else 'não (código-fonte)'}",
        f"Pasta do app    : {app_dir or paths.install_dir()}",
        f"7-Zip           : {seven}",
        f"rclone          : {rclone.splitlines()[0] if rclone else 'não encontrado'}",
    ]
    try:
        from PySide6 import __version__ as pyside_version
        linhas.insert(4, f"PySide6         : {pyside_version}")
    except ImportError:      # não deveria acontecer: a interface já está de pé
        pass
    return "\n".join(linhas)


class AboutDialog(QDialog):
    def __init__(self, app_dir: str = "", parent=None):
        super().__init__(parent)
        self.app_dir = app_dir

        self.ui = forms.load("dialog_about")()
        self.ui.setupUi(self)

        self.ui.lblVersion.setText(
            f"Versão {__version__} · "
            f"{'executável' if getattr(sys, 'frozen', False) else 'código-fonte'}")
        self.ui.textApp.setHtml(_texto_aplicativo())
        self.ui.textThird.setHtml(_texto_terceiros())

        self._diagnostico = diagnostico(app_dir)
        self.ui.textSystem.setPlainText(self._diagnostico)

        self.ui.btnLicenses.clicked.connect(self._abrir_licencas)
        self.ui.btnCopy.clicked.connect(self._copiar)
        self.ui.btnClose.clicked.connect(self.accept)

        pasta = _licenses_dir()
        self.ui.btnLicenses.setEnabled(os.path.isdir(pasta))
        if not os.path.isdir(pasta):
            self.ui.btnLicenses.setToolTip(
                f"Os textos das licenças não foram encontrados em {pasta}.")

    def _abrir_licencas(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(_licenses_dir()))

    def _copiar(self) -> None:
        QApplication.clipboard().setText(self._diagnostico)
        self.ui.btnCopy.setText("Copiado")
        self.ui.btnCopy.setEnabled(False)


def show(app_dir: str = "", parent=None) -> None:
    AboutDialog(app_dir, parent).exec()
