"""Seletor de unidade do campo "Aguardar unidade".

A regra que governa este widget não é óbvia e é fácil de quebrar numa refatoração:
**ele precisa aceitar uma unidade que não existe**. Ao configurar o backup, o
pen drive normalmente não está espetado — esperar por ele é a função do campo.
Um seletor que só admitisse o que o Windows enxerga agora inviabilizaria o caso
mais comum, e o defeito só apareceria com o cliente.
"""

import os
import unittest


def _sem_qt() -> str:
    try:
        import PySide6.QtWidgets  # noqa: F401
    except ImportError:
        return "PySide6 nao instalado"
    if not os.environ.get("DISPLAY") and os.name != "nt":
        return "sem servidor grafico"
    return ""


@unittest.skipIf(_sem_qt(), _sem_qt() or "sem Qt")
class DriveComboTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from backup_maximus import winapi
        from backup_maximus.ui import drivecombo
        self.drivecombo = drivecombo
        self.winapi = winapi

        # Unidades fixas, para o teste não depender do que está espetado na
        # máquina de quem roda a suíte.
        self.falsas = [
            winapi.DriveInfo("C:\\", winapi.DRIVE_FIXED, "", "NTFS",
                             500_000_000_000, 240_000_000_000),
            winapi.DriveInfo("E:\\", winapi.DRIVE_REMOVABLE, "PENDRIVE", "FAT32",
                             16_000_000_000, 14_900_000_000),
            winapi.DriveInfo("F:\\", winapi.DRIVE_CDROM, "", "", 0, 0),
        ]
        self._orig = drivecombo.winapi.drives
        drivecombo.winapi.drives = lambda: list(self.falsas)

    def tearDown(self):
        self.drivecombo.winapi.drives = self._orig

    def _combo(self):
        return self.drivecombo.DriveCombo()

    # ------------------------------------------------------------- conteúdo
    def test_lista_as_unidades_montadas(self):
        combo = self._combo()
        valores = [combo.itemData(i) for i in range(combo.count())]
        self.assertEqual(valores, ["", "C:\\", "E:\\", "F:\\"])

    def test_primeira_opcao_desliga_a_espera(self):
        combo = self._combo()
        self.assertEqual(combo.itemData(0), "")
        self.assertEqual(combo.itemText(0), self.drivecombo.NAO_ESPERAR)

    def test_rotulo_e_espaco_livre_ajudam_a_reconhecer_o_pendrive(self):
        combo = self._combo()
        texto = combo.itemText(2)
        self.assertIn("E:\\", texto)
        self.assertIn("PENDRIVE", texto)
        self.assertIn("removível", texto)
        self.assertIn("GB", texto)

    def test_unidade_sem_midia_e_anunciada_como_tal(self):
        # Leitor de cartão vazio ou DVD sem disco aparece na lista do Windows
        # e não responde. Oferecê-lo como destino pronto seria mentira.
        combo = self._combo()
        self.assertIn("sem mídia", combo.itemText(3))

    # ---------------------------------------------------------------- valor
    def test_aceita_unidade_que_ainda_nao_existe(self):
        # O caso central: configura-se com o pen drive fora.
        combo = self._combo()
        combo.setValue("U:\\")
        self.assertEqual(combo.value(), "U:\\")

    def test_guarda_a_raiz_e_nao_a_linha_descritiva(self):
        # O engine usa este valor como caminho: "E:\  PENDRIVE  (removível…)"
        # não existiria em disco nenhum.
        combo = self._combo()
        combo.setValue("E:\\")
        self.assertEqual(combo.value(), "E:\\")
        self.assertNotIn("PENDRIVE", combo.currentText())

    def test_escolher_na_lista_deixa_so_a_raiz_na_caixa(self):
        combo = self._combo()
        combo._on_activated(2)
        self.assertEqual(combo.value(), "E:\\")

    def test_vazio_significa_nao_esperar(self):
        combo = self._combo()
        combo.setValue("")
        self.assertEqual(combo.value(), "")

    def test_caminho_de_rede_digitado_e_preservado(self):
        # wait_for_path é um caminho qualquer, não só letra de unidade.
        combo = self._combo()
        combo.setEditText(r"\\servidor\backup")
        self.assertEqual(combo.value(), r"\\servidor\backup")

    def test_espaco_em_volta_nao_vira_caminho_invalido(self):
        combo = self._combo()
        combo.setEditText("  U:\\  ")
        self.assertEqual(combo.value(), "U:\\")

    def test_maiuscula_e_minuscula_casam_com_a_unidade(self):
        combo = self._combo()
        combo.setValue("e:\\")
        self.assertEqual(combo.value(), "e:\\")
        self.assertGreaterEqual(combo.currentIndex(), 0)

    # -------------------------------------------------------------- releitura
    def test_releitura_preserva_o_que_estava_digitado(self):
        combo = self._combo()
        combo.setValue("U:\\")
        self.falsas.append(self.winapi.DriveInfo(
            "U:\\", self.winapi.DRIVE_REMOVABLE, "BACKUP", "exFAT",
            32_000_000_000, 31_000_000_000))
        combo.refresh()
        self.assertEqual(combo.value(), "U:\\")

    def test_unidade_que_sumiu_nao_apaga_a_configuracao(self):
        # O pen drive foi retirado entre abrir a tela e abrir a lista: o
        # conjunto continua configurado para esperar por ele.
        combo = self._combo()
        combo.setValue("E:\\")
        self.falsas[:] = [d for d in self.falsas if d.letter != "E:\\"]
        combo.refresh()
        self.assertEqual(combo.value(), "E:\\")


if __name__ == "__main__":
    unittest.main()
