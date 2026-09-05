r"""Exportação, importação e conjuntos modelo.

A regra que sustenta o módulo, e que uma refatoração desatenta desfaz: **nenhum
segredo sai num perfil**. Não é só cautela — as senhas são cifradas com DPAPI,
que usa a chave do usuário e da máquina, então elas não decifrariam no destino
de qualquer forma. Exportá-las entregaria campos preenchidos que não funcionam,
e o técnico só descobriria na primeira madrugada.
"""

import os
import tempfile
import unittest

from backup_maximus import profiles
from backup_maximus.config import (
    BackupItem, BackupSet, Config, ItemType, NetCredential, SetMode,
)


def _config_completa() -> Config:
    cfg = Config()
    cfg.company_name = "Loja Teste"
    cfg.notify_email = "ti@loja.com.br"
    cfg.alert_timeout_hours = 30
    cfg.smtp.host = "smtp.loja.com.br"
    cfg.smtp.port = 587
    cfg.smtp.user = "backup@loja.com.br"
    cfg.smtp.password_enc = "SEGREDO-SMTP"
    cfg.set_password("senha-da-interface")
    cfg.net_creds.append(NetCredential(unc_root=r"\\servidor\dados",
                                       user="rede", password_enc="SEGREDO-REDE"))
    cfg.sets.append(BackupSet(
        name="PRINCIPAL",
        destination=r"U:\ ".strip(),
        items=[
            BackupItem(name="Banco", type=ItemType.FIREBIRD, source="MEUBANCO",
                       subfolder="BD", user="SYSDBA",
                       password_enc="SEGREDO-BANCO"),
            BackupItem(name="XMLs", type=ItemType.FILES, source=r"C:\xml",
                       subfolder="XML", mirror=True),
        ],
    ))
    return cfg


class SemSegredosTest(unittest.TestCase):

    def setUp(self):
        self.cfg = _config_completa()
        self.limpa = profiles.sem_segredos(self.cfg)

    def test_senha_do_smtp_nao_viaja(self):
        self.assertEqual(self.limpa.smtp.password_enc, "")

    def test_senha_de_rede_nao_viaja(self):
        self.assertEqual(self.limpa.net_creds[0].password_enc, "")

    def test_senha_de_banco_nao_viaja(self):
        self.assertEqual(self.limpa.sets[0].items[0].password_enc, "")

    def test_senha_da_interface_nao_viaja(self):
        # Importar um perfil não pode trocar a senha de quem já usa a máquina.
        self.assertEqual(self.limpa.ui_password_hash, "")
        self.assertEqual(self.limpa.ui_password_salt, "")

    def test_o_original_permanece_intacto(self):
        # A limpeza trabalha numa cópia: quem exporta não pode perder as
        # próprias senhas por ter clicado em exportar.
        self.assertEqual(self.cfg.smtp.password_enc, "SEGREDO-SMTP")
        self.assertEqual(self.cfg.sets[0].items[0].password_enc, "SEGREDO-BANCO")
        self.assertTrue(self.cfg.has_password)

    def test_o_resto_da_configuracao_sobrevive(self):
        self.assertEqual(self.limpa.company_name, "Loja Teste")
        self.assertEqual(self.limpa.smtp.host, "smtp.loja.com.br")
        self.assertEqual(self.limpa.smtp.user, "backup@loja.com.br")
        self.assertEqual(self.limpa.sets[0].items[0].source, "MEUBANCO")


class PendenciasTest(unittest.TestCase):
    """O perfil precisa dizer o que ficou faltando, não só omitir."""

    def test_lista_as_senhas_que_terao_de_ser_digitadas(self):
        pendencias = profiles.campos_pendentes(_config_completa())
        texto = " | ".join(pendencias)
        self.assertIn("e-mail", texto)
        self.assertIn("rede", texto)
        self.assertIn("banco", texto.lower())

    def test_configuracao_sem_senhas_nao_gera_pendencia(self):
        cfg = Config()
        cfg.sets.append(BackupSet(name="X", items=[
            BackupItem(name="Pasta", type=ItemType.FILES, source=r"C:\x")]))
        self.assertEqual(profiles.campos_pendentes(cfg), [])


class ExportarLerTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cfg = _config_completa()

    def _caminho(self, nome="perfil.ini") -> str:
        return os.path.join(self.tmp.name, nome)

    def test_exporta_e_le_de_volta(self):
        destino = self._caminho()
        ok, _ = profiles.exportar(self.cfg, destino)
        self.assertTrue(ok)
        lido = profiles.ler(destino)
        self.assertIsNotNone(lido)
        self.assertEqual([s.name for s in lido.sets], ["PRINCIPAL"])

    def test_o_arquivo_exportado_nao_contem_os_segredos(self):
        # A verificação é sobre o conteúdo em disco, não sobre o objeto: é o
        # arquivo que viaja por e-mail e pen drive.
        destino = self._caminho()
        profiles.exportar(self.cfg, destino)
        with open(destino, encoding="utf-8-sig") as fh:
            bruto = fh.read()
        for segredo in ("SEGREDO-SMTP", "SEGREDO-REDE", "SEGREDO-BANCO"):
            self.assertNotIn(segredo, bruto)

    def test_apenas_conjuntos_descarta_dados_da_loja(self):
        # Um modelo não pode carregar a empresa nem o SMTP de quem o criou.
        destino = self._caminho("modelo.ini")
        profiles.exportar(self.cfg, destino, apenas_conjuntos=True)
        lido = profiles.ler(destino)
        self.assertEqual(lido.company_name, "")
        self.assertEqual(lido.smtp.host, "")
        self.assertEqual(len(lido.sets), 1)

    def test_exportar_um_conjunto_escolhido(self):
        self.cfg.sets.append(BackupSet(name="SECUNDARIO"))
        destino = self._caminho()
        profiles.exportar(self.cfg, destino, nomes=["SECUNDARIO"])
        lido = profiles.ler(destino)
        self.assertEqual([s.name for s in lido.sets], ["SECUNDARIO"])

    def test_nome_inexistente_recusa_em_vez_de_gravar_vazio(self):
        ok, mensagem = profiles.exportar(self.cfg, self._caminho(),
                                         nomes=["NAO_EXISTE"])
        self.assertFalse(ok)
        self.assertIn("Nenhum", mensagem)
        self.assertFalse(os.path.exists(self._caminho()))

    def test_cria_a_pasta_de_destino(self):
        destino = os.path.join(self.tmp.name, "nova", "pasta", "perfil.ini")
        ok, _ = profiles.exportar(self.cfg, destino)
        self.assertTrue(ok)
        self.assertTrue(os.path.isfile(destino))

    def test_arquivo_inexistente_devolve_none(self):
        self.assertIsNone(profiles.ler(self._caminho("nao-existe.ini")))

    def test_ini_qualquer_nao_passa_por_perfil(self):
        # Um .ini de outro programa carrega sem erro e vem vazio; aceitá-lo
        # apagaria os conjuntos do usuário no modo Substituir.
        estranho = self._caminho("outro.ini")
        with open(estranho, "w", encoding="utf-8") as fh:
            fh.write("[qualquer]\nchave=valor\n")
        self.assertIsNone(profiles.ler(estranho))


class ImportarConjuntosTest(unittest.TestCase):

    def setUp(self):
        self.destino = Config()
        self.destino.sets = [BackupSet(name="ANTIGO"), BackupSet(name="COMUM")]
        self.perfil = Config()
        self.perfil.sets = [BackupSet(name="COMUM", destination=r"D:\novo"),
                            BackupSet(name="NOVO")]

    def _nomes(self):
        return [s.name for s in self.destino.sets]

    def test_substituir_descarta_os_atuais(self):
        profiles.importar_conjuntos(self.destino, self.perfil,
                                    profiles.ImportMode.SUBSTITUIR)
        self.assertEqual(self._nomes(), ["COMUM", "NOVO"])

    def test_mesclar_atualiza_o_de_mesmo_nome_sem_duplicar(self):
        acrescentados, atualizados = profiles.importar_conjuntos(
            self.destino, self.perfil, profiles.ImportMode.MESCLAR)
        self.assertEqual(self._nomes(), ["ANTIGO", "COMUM", "NOVO"])
        self.assertEqual((acrescentados, atualizados), (1, 1))

    def test_mesclar_preserva_a_ordem_de_quem_ja_estava(self):
        profiles.importar_conjuntos(self.destino, self.perfil,
                                    profiles.ImportMode.MESCLAR)
        self.assertEqual(self.destino.sets[1].name, "COMUM")
        self.assertEqual(self.destino.sets[1].destination, r"D:\novo")

    def test_acrescentar_renomeia_a_colisao(self):
        profiles.importar_conjuntos(self.destino, self.perfil,
                                    profiles.ImportMode.ACRESCENTAR)
        self.assertEqual(self._nomes(), ["ANTIGO", "COMUM", "COMUM (2)", "NOVO"])

    def test_importar_nao_liga_os_conjuntos_ao_perfil_de_origem(self):
        # Cópia profunda: editar o conjunto importado não pode alterar o
        # perfil, que pode ser importado de novo noutro lugar.
        profiles.importar_conjuntos(self.destino, self.perfil,
                                    profiles.ImportMode.SUBSTITUIR)
        self.destino.sets[0].name = "RENOMEADO"
        self.assertEqual(self.perfil.sets[0].name, "COMUM")


class ImportarGeraisTest(unittest.TestCase):

    def setUp(self):
        self.destino = Config()
        self.destino.set_password("senha-local")
        self.perfil = _config_completa()
        self.perfil = profiles.sem_segredos(self.perfil)

    def test_traz_empresa_e_email(self):
        profiles.importar_gerais(self.destino, self.perfil)
        self.assertEqual(self.destino.company_name, "Loja Teste")
        self.assertEqual(self.destino.notify_email, "ti@loja.com.br")

    def test_traz_o_servidor_de_email_sem_a_senha(self):
        profiles.importar_gerais(self.destino, self.perfil)
        self.assertEqual(self.destino.smtp.host, "smtp.loja.com.br")
        self.assertEqual(self.destino.smtp.password_enc, "")

    def test_nao_troca_a_senha_da_interface(self):
        # A senha protege esta máquina. Um perfil vindo de fora não a define.
        profiles.importar_gerais(self.destino, self.perfil)
        self.assertTrue(self.destino.check_password("senha-local"))

    def test_caminho_de_rede_repetido_nao_duplica(self):
        self.destino.net_creds.append(
            NetCredential(unc_root=r"\\SERVIDOR\DADOS", user="ja-existe"))
        profiles.importar_gerais(self.destino, self.perfil)
        self.assertEqual(len(self.destino.net_creds), 1)

    def test_relata_o_que_mudou(self):
        mudou = profiles.importar_gerais(self.destino, self.perfil)
        self.assertTrue(any("empresa" in m for m in mudou))
        self.assertTrue(any("e-mail" in m for m in mudou))

    def test_perfil_vazio_nao_apaga_o_que_existe(self):
        self.destino.company_name = "Minha Loja"
        profiles.importar_gerais(self.destino, Config())
        self.assertEqual(self.destino.company_name, "Minha Loja")


class ModelosTest(unittest.TestCase):
    """Os modelos que acompanham o programa precisam carregar de verdade."""

    def test_ha_modelos_distribuidos(self):
        modelos = profiles.listar_modelos()
        self.assertGreater(len(modelos), 0,
                           "nenhum modelo em modelos/ — rode gerar_modelos.py")

    def test_todo_modelo_tem_conjunto_e_item(self):
        for modelo in profiles.listar_modelos():
            with self.subTest(modelo=modelo.nome):
                self.assertTrue(modelo.info.sets)
                self.assertGreater(modelo.info.items, 0)

    def test_modelo_nao_carrega_dados_de_nenhuma_loja(self):
        # Um modelo que trouxesse empresa ou SMTP sobrescreveria o que o
        # técnico acabou de digitar na loja onde está instalando.
        for modelo in profiles.listar_modelos():
            with self.subTest(modelo=modelo.nome):
                cfg = profiles.ler(modelo.caminho)
                self.assertEqual(cfg.company_name, "")
                self.assertEqual(cfg.smtp.host, "")

    def test_modelo_nao_carrega_segredo(self):
        for modelo in profiles.listar_modelos():
            with self.subTest(modelo=modelo.nome):
                with open(modelo.caminho, encoding="utf-8-sig") as fh:
                    bruto = fh.read()
                for linha in bruto.splitlines():
                    if linha.startswith("password_enc="):
                        self.assertEqual(linha.strip(), "password_enc=")


if __name__ == "__main__":
    unittest.main()
