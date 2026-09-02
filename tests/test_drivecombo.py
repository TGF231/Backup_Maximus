"""Seletor de unidade do campo "Aguardar unidade".

É uma lista fechada: não se digita nada. Duas regras a sustentam, e ambas são
fáceis de quebrar sem perceber numa refatoração.

1. **A unidade configurada continua na lista mesmo ausente.** Ao abrir a tela,
   o pen drive normalmente não está espetado — esperar por ele é a função do
   campo. Se a lista mostrasse só o que está montado, abrir a tela apagaria a
   configuração do conjunto em silêncio.

2. **Caminhos UNC vêm da aba Rede.** Sem digitação, é por lá que um
   compartilhamento entra — e é o certo: esperar por um caminho de rede sem
   ter a credencial dele só produziria falha na hora do backup.
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

    def _valores(self, combo):
        return [combo.itemData(i) for i in range(combo.count())]

    # -------------------------------------------------------- lista fechada
    def test_nao_aceita_digitacao(self):
        self.assertFalse(self._combo().isEditable())

    def test_lista_as_unidades_montadas(self):
        self.assertEqual(self._valores(self._combo()), ["", "C:\\", "E:\\", "F:\\"])

    def test_primeira_opcao_desliga_a_espera(self):
        combo = self._combo()
        self.assertEqual(combo.itemData(0), "")
        self.assertEqual(combo.itemText(0), self.drivecombo.NAO_ESPERAR)

    def test_rotulo_e_espaco_livre_ajudam_a_reconhecer_o_pendrive(self):
        # Com dois pen drives espetados, a letra sozinha não diz qual é qual.
        texto = self._combo().itemText(2)
        self.assertIn("E:\\", texto)
        self.assertIn("PENDRIVE", texto)
        self.assertIn("removível", texto)
        self.assertIn("GB", texto)

    def test_unidade_sem_midia_e_anunciada_como_tal(self):
        # Leitor de cartão vazio ou DVD sem disco aparece na lista do Windows
        # e não responde. Oferecê-lo como destino pronto seria mentira.
        self.assertIn("sem mídia", self._combo().itemText(3))

    # ---------------------------------------------------------------- valor
    def test_guarda_a_raiz_e_nao_a_linha_descritiva(self):
        # O engine usa este valor como caminho: "E:\  PENDRIVE  (removível…)"
        # não existiria em disco nenhum.
        combo = self._combo()
        combo.setValue("E:\\")
        self.assertEqual(combo.value(), "E:\\")

    def test_vazio_significa_nao_esperar(self):
        combo = self._combo()
        combo.setValue("E:\\")
        combo.setValue("")
        self.assertEqual(combo.value(), "")
        self.assertEqual(combo.currentIndex(), 0)

    def test_letra_minuscula_no_ini_casa_com_a_unidade(self):
        # Configuração antiga pode ter "e:\"; o seletor normaliza para a raiz
        # como o Windows a reporta.
        combo = self._combo()
        combo.setValue("e:\\")
        self.assertEqual(combo.value(), "E:\\")

    # --------------------------------------------- unidade não conectada
    def test_unidade_ausente_continua_na_lista(self):
        # A regra central: configurar com o pen drive fora é o caso normal.
        combo = self._combo()
        combo.setValue("U:\\")
        self.assertEqual(combo.value(), "U:\\")
        self.assertIn("U:\\", self._valores(combo))

    def test_unidade_ausente_e_identificada_como_tal(self):
        combo = self._combo()
        combo.setValue("U:\\")
        self.assertIn("não conectada", combo.currentText())

    def test_abrir_a_tela_nao_apaga_a_configuracao(self):
        # Sem isto, carregar o conjunto zeraria wait_for_path em silêncio e o
        # backup deixaria de esperar pelo pen drive.
        combo = self._combo()
        combo.setValue("U:\\")
        combo.refresh()
        self.assertEqual(combo.value(), "U:\\")

    def test_unidade_que_reaparece_deixa_de_ser_marcada_como_ausente(self):
        combo = self._combo()
        combo.setValue("U:\\")
        self.falsas.append(self.winapi.DriveInfo(
            "U:\\", self.winapi.DRIVE_REMOVABLE, "BACKUP", "exFAT",
            32_000_000_000, 31_000_000_000))
        combo.refresh()
        self.assertEqual(combo.value(), "U:\\")
        self.assertIn("BACKUP", combo.currentText())
        self.assertNotIn("não conectada", combo.currentText())

    def test_unidade_retirada_nao_apaga_a_escolha(self):
        combo = self._combo()
        combo.setValue("E:\\")
        self.falsas[:] = [d for d in self.falsas if d.letter != "E:\\"]
        combo.refresh()
        self.assertEqual(combo.value(), "E:\\")

    # ------------------------------------------------------------ rede/UNC
    def test_unc_cadastrado_na_aba_rede_aparece_na_lista(self):
        combo = self._combo()
        combo.set_network_paths([r"\\servidor\backup"])
        self.assertIn(r"\\servidor\backup", self._valores(combo))

    def test_unc_pode_ser_escolhido(self):
        combo = self._combo()
        combo.set_network_paths([r"\\servidor\backup"])
        combo.setValue(r"\\servidor\backup")
        self.assertEqual(combo.value(), r"\\servidor\backup")
        self.assertNotIn("não conectada", combo.currentText())

    def test_unc_configurado_sem_cadastro_na_rede_nao_se_perde(self):
        # Configuração vinda de uma versão anterior, quando se digitava: o
        # valor tem de sobreviver até alguém cadastrá-lo na aba Rede.
        combo = self._combo()
        combo.setValue(r"\\antigo\compartilhamento")
        self.assertEqual(combo.value(), r"\\antigo\compartilhamento")

    def test_lista_de_rede_vazia_nao_acrescenta_nada(self):
        combo = self._combo()
        combo.set_network_paths([])
        self.assertEqual(self._valores(combo), ["", "C:\\", "E:\\", "F:\\"])

    def test_entradas_em_branco_da_aba_rede_sao_ignoradas(self):
        combo = self._combo()
        combo.set_network_paths(["", "   ", r"\\servidor\backup"])
        self.assertEqual(self._valores(combo),
                         ["", "C:\\", "E:\\", "F:\\", r"\\servidor\backup"])


if __name__ == "__main__":
    unittest.main()
