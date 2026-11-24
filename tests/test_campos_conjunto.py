r"""Campos do conjunto e endereço do SQL Server.

"Manter últimos" foi relatado duas vezes como quebrado. As causas reais:
a caixa não tinha setas (parecia texto solto) e, no modo Incremental, voltava
a ficar editável por causa da ordem em que o painel era ligado — editável e
sem efeito, que é como "quebrado" se parece.

No SQL Server, o item vinha com a porta 1433 preenchida. Instância nomeada
e Express usam porta dinâmica, e a porta fixa fazia o logon expirar.
"""

import unittest

from backup_maximus import dbdump
from backup_maximus.config import BackupItem, ItemType, SetMode


class ManterUltimosTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            from PySide6.QtWidgets import QAbstractSpinBox, QApplication
        except ImportError:
            raise unittest.SkipTest("PySide6 nao instalado")
        cls.app = QApplication.instance() or QApplication([])
        cls.QAbstractSpinBox = QAbstractSpinBox

    def _janela(self, modo):
        from backup_maximus.ui import fitcheck
        from backup_maximus.ui.app import MainWindow
        cfg = fitcheck._sample_config()
        cfg.sets[0].mode = modo
        janela = MainWindow(cfg, "x.ini", ".")
        # Sem isso, fechar com alteração abre o "Salvar antes de sair?" modal.
        self.addCleanup(lambda: (setattr(janela, "dirty", False), janela.close()))
        return cfg, janela.tab_backups

    def test_tem_setas_para_escolher(self):
        _cfg, aba = self._janela(SetMode.FULL)
        self.assertNotEqual(aba.set_keep_last.buttonSymbols(),
                            self.QAbstractSpinBox.ButtonSymbols.NoButtons)

    def test_zero_se_le_como_todos(self):
        _cfg, aba = self._janela(SetMode.FULL)
        aba.set_keep_last.setValue(0)
        self.assertEqual(aba.set_keep_last.text(), "Todos")

    def test_completo_edita_e_grava(self):
        cfg, aba = self._janela(SetMode.FULL)
        self.assertTrue(aba.set_keep_last.isEnabled())
        aba.set_keep_last.setValue(5)
        self.assertEqual(cfg.sets[0].keep_last, 5)

    def test_incremental_fica_desligado_ao_carregar(self):
        _cfg, aba = self._janela(SetMode.INCREMENTAL)
        self.assertFalse(aba.set_keep_last.isEnabled())

    def test_trocar_para_completo_liga(self):
        _cfg, aba = self._janela(SetMode.INCREMENTAL)
        aba.set_mode.setCurrentIndex(1)
        self.assertTrue(aba.set_keep_last.isEnabled())


class EnderecoSqlServerTest(unittest.TestCase):

    def _item(self, host="localhost", port=""):
        item = BackupItem(name="x", type=ItemType.SQLSERVER, source="db")
        item.host, item.port = host, port
        return item

    def test_sem_porta_um_endereco(self):
        self.assertEqual(dbdump._servidores_sql(self._item()), ["localhost"])

    def test_com_porta_tenta_tambem_sem(self):
        self.assertEqual(dbdump._servidores_sql(self._item(port="1433")),
                         ["localhost,1433", "localhost"])

    def test_instancia_padrao_nao_leva_nome(self):
        self.assertEqual(dbdump.endereco_sql("MSSQLSERVER"), "localhost")
        self.assertEqual(dbdump.endereco_sql("SQLEXPRESS"), "localhost\\SQLEXPRESS")

    def test_cai_para_sem_porta_quando_a_porta_nao_responde(self):
        chamadas = []

        def falso(args, timeout=None, cwd=None):
            servidor = args[args.index("-S") + 1]
            chamadas.append(servidor)
            return (1, "Login timeout expired") if "," in servidor else (0, "")

        original, dbdump.util.run_process = dbdump.util.run_process, falso
        try:
            code, _out, usado = dbdump._sqlcmd(self._item(port="1433"),
                                               "sqlcmd.exe", "SELECT 1")
        finally:
            dbdump.util.run_process = original
        self.assertEqual((code, usado), (0, "localhost"))
        self.assertEqual(chamadas, ["localhost,1433", "localhost"])

    def test_item_novo_sem_porta_fixa(self):
        from backup_maximus.ui import tab_backups
        self.assertEqual(tab_backups._DEFAULT_CONNECTION[ItemType.SQLSERVER][1], "")


if __name__ == "__main__":
    unittest.main()
