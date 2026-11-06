r"""As regras do MegUI que dá para conferir sem olhar a tela.

Cada teste corresponde a um jeito conhecido de a assinatura se perder aos
poucos: uma cor literal que sobrevive à troca de tema, um segundo botão de
acento, um peso 600 que a fonte não tem, um canto de 8px.
"""

import glob
import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI = os.path.join(RAIZ, "backup_maximus", "ui")
DESIGNER = os.path.join(RAIZ, "designer")

HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")


def _ler(caminho: str) -> str:
    with open(caminho, encoding="utf-8") as fh:
        return fh.read()


def _acentos(ui: str) -> int:
    return len(re.findall(r'name="role"[^>]*>\s*<string[^>]*>accent<', _ler(ui)))


class SemCorLiteralTest(unittest.TestCase):

    def test_nenhuma_cor_fora_dos_tokens(self):
        # Cor literal é exatamente o que fica ilegível quando o tema muda.
        achados = []
        for caminho in glob.glob(os.path.join(UI, "*.py")):
            if os.path.basename(caminho) == "megui_tokens.py":
                continue
            for n, linha in enumerate(_ler(caminho).splitlines(), 1):
                if HEX.search(linha):
                    achados.append(f"{os.path.basename(caminho)}:{n}")
        self.assertEqual(achados, [])

    def test_nenhum_estilo_local(self):
        # setStyleSheet num widget ganha da folha global e escapa do tema.
        achados = []
        for caminho in glob.glob(os.path.join(UI, "*.py")):
            for n, linha in enumerate(_ler(caminho).splitlines(), 1):
                if ".setStyleSheet(" in linha and "theme.stylesheet()" not in linha:
                    achados.append(f"{os.path.basename(caminho)}:{n}")
        self.assertEqual(achados, [])

    def test_ui_sem_stylesheet_embutido(self):
        achados = [os.path.basename(u)
                   for u in glob.glob(os.path.join(DESIGNER, "*.ui"))
                   if 'name="styleSheet"' in _ler(u)]
        self.assertEqual(achados, [])


class UmAcentoPorTelaTest(unittest.TestCase):

    def test_cada_formulario_tem_no_maximo_um(self):
        for ui in glob.glob(os.path.join(DESIGNER, "*.ui")):
            with self.subTest(ui=os.path.basename(ui)):
                self.assertLessEqual(_acentos(ui), 1)

    def test_janela_principal_com_a_aba_de_backups(self):
        # A aba Backups vive dentro da janela principal: as duas somam uma tela.
        total = (_acentos(os.path.join(DESIGNER, "main_window.ui"))
                 + _acentos(os.path.join(DESIGNER, "tab_backups.ui")))
        self.assertEqual(total, 1)


class FolhaDeEstiloTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError:
            raise unittest.SkipTest("PySide6 nao instalado")
        cls.app = QApplication.instance() or QApplication([])
        from backup_maximus.ui import theme
        cls.theme = theme
        cls.folhas = []
        for escuro in (False, True):
            theme.set_dark(escuro)
            cls.folhas.append(theme.stylesheet())
        theme.set_dark(False)

    def test_dois_pesos(self):
        for folha in self.folhas:
            pesos = set(re.findall(r"font-weight:\s*(\w+)", folha))
            self.assertLessEqual(pesos, {"400", "700"})

    def test_raio_maximo_4px(self):
        for folha in self.folhas:
            raios = [int(r) for r in re.findall(r"radius:\s*(\d+)px", folha)]
            self.assertTrue(raios)
            self.assertLessEqual(max(raios), 4)

    def test_sem_sombra_nem_gradiente(self):
        for folha in self.folhas:
            self.assertNotIn("gradient", folha)
            self.assertNotIn("shadow", folha)

    def test_acento_puro_so_como_fundo_da_acao_primaria(self):
        # No escuro o acento puro como linha dá 1,5:1; linha usa accent_linha.
        from backup_maximus.ui.megui_tokens import ESCURO
        usos = [linha.strip() for linha in self.folhas[1].splitlines()
                if ESCURO.accent in linha]
        self.assertTrue(usos)
        for linha in usos:
            self.assertTrue(linha.startswith("background:"), linha)

    def test_fontes_embarcadas_carregam(self):
        from PySide6.QtGui import QFontDatabase
        self.assertTrue(self.theme.carregar_fontes())
        familias = set(QFontDatabase.families())
        self.assertIn(self.theme.FAMILIA_UI, familias)
        self.assertIn(self.theme.FAMILIA_MONO, familias)


if __name__ == "__main__":
    unittest.main()
