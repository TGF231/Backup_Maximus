r"""Senha gravada por outro usuário do Windows.

O DPAPI cifra no escopo do usuário. Uma senha salva com o programa aberto como
Administrador — o que acontece quando alguém mexe em Program Files — não é
decifrável pelo usuário que executa o backup à noite.

Antes desta correção os dois lados mentiam juntos: a tela dizia "•••••• (gravada)"
e o `gbak` recebia `masterkey` no lugar da senha real. O backup falhava por
autenticação e o relatório culpava o banco, sem ninguém relacionar o problema à
conta do Windows.
"""

import base64
import os
import unittest

from backup_maximus import config, dbdump
from backup_maximus.config import BackupItem, ItemType


def _blob_de_outra_conta() -> str:
    """Base64 válido que o DPAPI desta conta recusa — é como chega na prática."""
    return base64.b64encode(b"\x01\x00\x00\x00" + os.urandom(180)).decode()


class SegredoIlegivelTest(unittest.TestCase):

    def test_campo_vazio_nao_e_ilegivel(self):
        # Vazio é uma escolha ("usar o padrão"); ilegível é um defeito.
        self.assertFalse(config.secret_ilegivel(""))

    def test_senha_desta_conta_e_legivel(self):
        self.assertFalse(config.secret_ilegivel(config.protect_secret("abc")))

    def test_senha_de_outra_conta_e_ilegivel(self):
        self.assertTrue(config.secret_ilegivel(_blob_de_outra_conta()))

    def test_lixo_que_nem_e_base64_tambem_conta(self):
        self.assertTrue(config.secret_ilegivel("isso nao e base64 ###"))


class AvisoNoFirebirdTest(unittest.TestCase):

    def _item(self, enc: str) -> BackupItem:
        item = BackupItem(name="PDV", type=ItemType.FIREBIRD, source="BD")
        item.user = "SYSDBA"
        item.password_enc = enc
        return item

    def test_sem_senha_nao_avisa(self):
        self.assertEqual(dbdump.senha_ilegivel(self._item("")), "")

    def test_senha_propria_nao_avisa(self):
        item = self._item(config.protect_secret("minhasenha"))
        self.assertEqual(dbdump.senha_ilegivel(item), "")

    def test_senha_de_outra_conta_avisa_e_diz_o_que_fazer(self):
        aviso = dbdump.senha_ilegivel(self._item(_blob_de_outra_conta()))
        self.assertIn("outro usuario do Windows", aviso)
        self.assertIn("PDV", aviso)
        self.assertIn("de novo", aviso)

    def test_o_backup_recusa_em_vez_de_tentar_com_masterkey(self):
        # Tentar com a senha padrão produziria um erro de autenticação que
        # aponta para o banco, escondendo a causa real.
        item = self._item(_blob_de_outra_conta())
        chamou = []

        def nao_deveria(*args, **kwargs):
            chamou.append(args)
            return 0, ""

        original = dbdump.util.run_process
        achar = dbdump.find_tool
        dbdump.util.run_process = nao_deveria
        dbdump.find_tool = lambda _item: "gbak.exe"   # finge que a ferramenta existe
        try:
            ok, detalhe = dbdump._firebird(item, "C:\\saida.fbk")
        finally:
            dbdump.util.run_process = original
            dbdump.find_tool = achar

        self.assertFalse(ok)
        self.assertIn("outro usuario do Windows", detalhe)
        self.assertEqual(chamou, [], "chamou o gbak apesar da senha ilegivel")


class SenhaPadraoTest(unittest.TestCase):
    """O padrão `masterkey` continua valendo para campo realmente vazio."""

    def test_campos_vazios(self):
        item = BackupItem(name="x", type=ItemType.FIREBIRD, source="BD")
        self.assertEqual(dbdump.firebird_credenciais(item),
                         ("SYSDBA", "masterkey"))

    def test_usuario_proprio_mantem_masterkey(self):
        item = BackupItem(name="x", type=ItemType.FIREBIRD, source="BD")
        item.user = "OUTRO"
        self.assertEqual(dbdump.firebird_credenciais(item),
                         ("OUTRO", "masterkey"))

    def test_senha_propria_vence_o_padrao(self):
        item = BackupItem(name="x", type=ItemType.FIREBIRD, source="BD")
        item.password_enc = config.protect_secret("minhasenha")
        self.assertEqual(dbdump.firebird_credenciais(item)[1], "minhasenha")


if __name__ == "__main__":
    unittest.main()
