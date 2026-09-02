"""O registro de formulários não pode divergir da pasta do Designer.

Um `.ui` criado e esquecido no registro não é compilado, e a falha só aparece
quando alguém abre aquela tela — em produção, na máquina do cliente. Foi o que
aconteceu ao acrescentar a tela "Sobre": o build informou sucesso, compilou 11
dos 12 formulários e ninguém notou.
"""

import os
import re
import unittest

from backup_maximus.ui import forms

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGNER = os.path.join(RAIZ, "designer")


def _arquivos_ui() -> set[str]:
    return {n[:-3] for n in os.listdir(DESIGNER) if n.endswith(".ui")}


class RegistroDeFormulariosTest(unittest.TestCase):
    def test_todo_ui_esta_registrado(self):
        faltando = _arquivos_ui() - set(forms.FORMS)
        self.assertEqual(faltando, set(),
                         f"formulários sem registro em forms.FORMS: {sorted(faltando)}")

    def test_todo_registro_tem_arquivo(self):
        sobrando = set(forms.FORMS) - _arquivos_ui()
        self.assertEqual(sobrando, set(),
                         f"registrados sem .ui correspondente: {sorted(sobrando)}")

    def test_nome_da_classe_bate_com_o_declarado_no_ui(self):
        # O uic gera `Ui_<class>`; se o registro disser outro nome, o load()
        # falha com AttributeError só na hora de abrir a tela.
        for nome, classe in sorted(forms.FORMS.items()):
            caminho = os.path.join(DESIGNER, f"{nome}.ui")
            with self.subTest(formulario=nome):
                with open(caminho, encoding="utf-8") as fh:
                    texto = fh.read()
                declarada = re.search(r"<class>([^<]+)</class>", texto).group(1)
                self.assertEqual(classe, f"Ui_{declarada}")


if __name__ == "__main__":
    unittest.main()
