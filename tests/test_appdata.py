"""Onde ficam configuração, logs e relatórios.

A cascata de `paths.app_data_dir` decide isso, e errar aqui é caro de duas
formas opostas: mandar os dados para uma pasta protegida faz o programa abrir
como primeira execução e pedir senha nova; mudar de lugar sem motivo faz o
cliente perder de vista os conjuntos que já tinha configurado.

Nenhum teste aqui toca no disco de verdade além de um diretório temporário.
"""

import os
import tempfile
import unittest

from backup_maximus import paths


class CascataTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = self.tmp.name

        self._install_dir = paths.install_dir
        paths.install_dir = lambda: self.home
        self.addCleanup(self._restaurar)

        # O ambiente da máquina que roda a suíte não pode influenciar.
        self._ambiente = {k: os.environ.get(k) for k in ("BM_HOME", "LOCALAPPDATA")}
        os.environ.pop("BM_HOME", None)
        os.environ["LOCALAPPDATA"] = os.path.join(self.home, "_appdata")

    def _restaurar(self):
        paths.install_dir = self._install_dir
        for chave, valor in self._ambiente.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor

    def _marcar(self, nome: str):
        with open(os.path.join(self.home, nome), "w", encoding="utf-8") as fh:
            fh.write("teste")

    # ------------------------------------------------------------- prioridade
    def test_bm_home_vence_tudo(self):
        alvo = os.path.join(self.home, "dados-escolhidos")
        os.environ["BM_HOME"] = alvo
        self._marcar(paths.INSTALLED_MARKER)
        self.assertEqual(paths.app_data_dir(), os.path.abspath(alvo))

    def test_bm_home_cria_a_pasta(self):
        alvo = os.path.join(self.home, "ainda-nao-existe")
        os.environ["BM_HOME"] = alvo
        paths.app_data_dir()
        self.assertTrue(os.path.isdir(alvo))

    def test_portatil_vence_instalado(self):
        # Os dois marcadores presentes é situação de quem instalou e depois
        # decidiu levar a pasta num pen drive. A escolha explícita ganha.
        self._marcar(paths.INSTALLED_MARKER)
        self._marcar(paths.PORTABLE_MARKER)
        self.assertEqual(paths.app_data_dir(), self.home)

    def test_instalado_manda_para_o_appdata(self):
        self._marcar(paths.INSTALLED_MARKER)
        destino = paths.app_data_dir()
        self.assertNotEqual(destino, self.home)
        self.assertTrue(destino.endswith(paths.APPDATA_FOLDER))

    def test_sem_marcador_e_com_permissao_fica_ao_lado_do_exe(self):
        # O comportamento de sempre. Quem já usa a versão portátil hoje não
        # pode ver a configuração mudar de lugar numa atualização.
        self.assertEqual(paths.app_data_dir(), self.home)

    def test_pasta_sem_permissao_cai_no_appdata(self):
        paths.install_dir = lambda: os.path.join(self.home, "nao-existe", "fundo")
        destino = paths.app_data_dir()
        self.assertTrue(destino.endswith(paths.APPDATA_FOLDER))


class PermissaoTest(unittest.TestCase):
    """`_writable` testa gravando, porque `os.access` mente no Windows."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_pasta_gravavel(self):
        self.assertTrue(paths._writable(self.tmp.name))

    def test_pasta_inexistente_nao_e_gravavel(self):
        self.assertFalse(
            paths._writable(os.path.join(self.tmp.name, "nao", "existe")))

    def test_nao_deixa_lixo_para_tras(self):
        antes = set(os.listdir(self.tmp.name))
        paths._writable(self.tmp.name)
        self.assertEqual(set(os.listdir(self.tmp.name)), antes)


class AppDataTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self._antes = os.environ.get("LOCALAPPDATA")
        self.addCleanup(self._restaurar)

    def _restaurar(self):
        if self._antes is None:
            os.environ.pop("LOCALAPPDATA", None)
        else:
            os.environ["LOCALAPPDATA"] = self._antes

    def test_usa_localappdata_e_cria_a_pasta(self):
        os.environ["LOCALAPPDATA"] = self.tmp.name
        destino = paths.local_appdata_dir()
        self.assertEqual(destino,
                         os.path.join(self.tmp.name, paths.APPDATA_FOLDER))
        self.assertTrue(os.path.isdir(destino))

    def test_sem_a_variavel_recorre_ao_perfil_do_usuario(self):
        # Um agendamento mal configurado pode rodar sem LOCALAPPDATA definida;
        # ficar sem lugar para gravar seria pior do que deduzir o caminho.
        os.environ.pop("LOCALAPPDATA", None)
        destino = paths.local_appdata_dir()
        self.assertIn("AppData", destino)
        self.assertTrue(destino.endswith(paths.APPDATA_FOLDER))


if __name__ == "__main__":
    unittest.main()
