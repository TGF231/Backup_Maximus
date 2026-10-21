"""Versão e notas que alimentam a release automática.

O workflow decide publicar a partir daqui. Um erro neste módulo produz uma
release sem notas, com a tag errada, ou release nenhuma — e a falha aparece
no GitHub Actions, longe de quem escreveu o commit.
"""

import os
import re
import tempfile
import unittest

import release_info


class VersaoTest(unittest.TestCase):
    def test_le_a_versao_do_codigo(self):
        self.assertRegex(release_info.versao(), r"^\d+\.\d+\.\d+$")

    def test_tag_leva_v_e_a_versao_nao(self):
        # Convenção do Git de um lado, do Python do outro; confundir as duas
        # faria a tag virar "vv2.1.0" ou a versão do .exe virar "v2.1.0".
        self.assertEqual(f"v{release_info.versao()}",
                         release_info.versao() and f"v{release_info.versao()}")
        self.assertFalse(release_info.versao().startswith("v"))


class NotasTest(unittest.TestCase):
    def setUp(self):
        self._changelog = release_info.CHANGELOG

    def tearDown(self):
        release_info.CHANGELOG = self._changelog

    def _com_changelog(self, texto: str):
        arq = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                          encoding="utf-8")
        arq.write(texto)
        arq.close()
        self.addCleanup(os.unlink, arq.name)
        release_info.CHANGELOG = arq.name

    def test_extrai_a_secao_da_versao(self):
        self._com_changelog(
            "# Histórico\n\n"
            "## [Não lançado]\n\nNada ainda.\n\n"
            "## [2.1.0] — 2026-09-01\n\n### Adicionado\n\n- Coisa nova.\n\n"
            "## [2.0.0] — interno\n\nOutra coisa.\n")
        notas = release_info.notas("2.1.0")
        self.assertIn("Coisa nova", notas)
        self.assertNotIn("Outra coisa", notas)
        self.assertNotIn("Nada ainda", notas)

    def test_nao_inclui_o_cabecalho_da_propria_secao(self):
        self._com_changelog("## [2.1.0] — hoje\n\nTexto.\n")
        self.assertNotIn("[2.1.0]", release_info.notas("2.1.0"))

    def test_versao_sem_secao_devolve_vazio(self):
        self._com_changelog("## [1.0.0]\n\nAntiga.\n")
        self.assertEqual(release_info.notas("9.9.9"), "")

    def test_regua_entre_secoes_nao_vaza_para_as_notas(self):
        self._com_changelog("## [2.1.0] — hoje\n\nTexto.\n\n---\n\n## [2.0.0]\n\nX\n")
        self.assertNotIn("---", release_info.notas("2.1.0"))

    def test_versao_com_ponto_nao_casa_por_engano(self):
        # "2.1.0" não pode casar com a seção de "2X1Y0" por causa do ponto
        # solto de uma expressão regular mal escapada.
        self._com_changelog("## [2X1Y0]\n\nErrada.\n")
        self.assertEqual(release_info.notas("2.1.0"), "")


class ConferirTest(unittest.TestCase):
    def setUp(self):
        self._changelog = release_info.CHANGELOG
        self._init = release_info.INIT

    def tearDown(self):
        release_info.CHANGELOG = self._changelog
        release_info.INIT = self._init

    def _montar(self, versao: str, changelog: str):
        for conteudo, sufixo, atributo in (
            (f'__version__ = "{versao}"\n', ".py", "INIT"),
            (changelog, ".md", "CHANGELOG"),
        ):
            arq = tempfile.NamedTemporaryFile("w", suffix=sufixo, delete=False,
                                              encoding="utf-8")
            arq.write(conteudo)
            arq.close()
            self.addCleanup(os.unlink, arq.name)
            setattr(release_info, atributo, arq.name)

    def test_aprova_versao_com_notas(self):
        self._montar("2.1.0", "## [Não lançado]\n\nNada ainda.\n\n"
                              "## [2.1.0]\n\n- Uma mudança descrita com "
                              "detalhe suficiente para avaliar.\n")
        self.assertEqual(release_info.conferir(), [])

    def test_regua_entre_secoes_nao_conta_como_conteudo(self):
        # A "---" que separa as secoes entra na captura. Sem desconta-la, a
        # verificacao reprovaria todo CHANGELOG bem formado, e um guarda que
        # grita sempre deixa de ser lido.
        self._montar("2.1.0",
                     "## [Não lançado]\n\nNada ainda.\n\n---\n\n"
                     "## [2.1.0]\n\n- Uma mudança descrita com detalhe "
                     "suficiente para avaliar.\n")
        self.assertEqual(release_info.conferir(), [])

    def test_reprova_sem_secao_no_changelog(self):
        self._montar("3.0.0", "## [2.1.0]\n\n- Velha.\n")
        problemas = release_info.conferir()
        self.assertTrue(any("3.0.0" in p for p in problemas))

    def test_reprova_conteudo_esquecido_em_nao_lancado(self):
        # O erro mais provável na prática: subir a versão e esquecer de mover
        # o que estava em "Não lançado". As notas sairiam sem as novidades.
        self._montar("2.2.0",
                     "## [Não lançado]\n\n- Recurso que ninguém moveu.\n\n"
                     "## [2.2.0]\n\n- Uma mudança descrita com detalhe "
                     "suficiente para avaliar.\n")
        problemas = release_info.conferir()
        self.assertTrue(any("Não lançado" in p for p in problemas))

    def test_reprova_versao_fora_do_formato(self):
        self._montar("2.1", "## [2.1]\n\n- Uma mudança descrita com detalhe "
                            "suficiente para avaliar.\n")
        problemas = release_info.conferir()
        self.assertTrue(any("MAIOR.MENOR" in p for p in problemas))


class WorkflowTest(unittest.TestCase):
    """O YAML precisa continuar chamando o que este módulo oferece."""

    CAMINHO = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), ".github", "workflows", "release.yml")

    def setUp(self):
        if not os.path.isfile(self.CAMINHO):
            self.skipTest("workflow ausente")
        with open(self.CAMINHO, encoding="utf-8") as fh:
            self.texto = fh.read()

    def test_usa_o_utilitario_em_vez_de_repetir_a_versao(self):
        self.assertIn("release_info.py --versao", self.texto)
        self.assertIn("release_info.py --tag", self.texto)

    def test_nao_traz_a_versao_escrita_no_yaml(self):
        # Uma terceira cópia da versão divergiria das outras duas. O que
        # importa é o YAML executável: um comentário pode citar uma versão ao
        # explicar por que um passo existe, e isso não entra no build.
        util = []
        for linha in self.texto.splitlines():
            sem_comentario = re.sub(r"(^|\s)#.*$", "", linha)
            util.append(re.sub(r"python-version: '[^']+'", "", sem_comentario))
        self.assertIsNone(re.search(r"\bv?\d+\.\d+\.\d+\b", "\n".join(util)))

    def test_confere_o_changelog_antes_de_empacotar(self):
        self.assertIn("release_info.py --conferir", self.texto)

    def test_audita_o_pacote_antes_de_publicar(self):
        # Sem isso, uma biblioteca GPL poderia entrar num produto fechado.
        self.assertIn("auditar_pacote.py", self.texto)

    def test_publica_tambem_a_build_em_pasta(self):
        # Exigência da LGPLv3 da PySide6/Qt.
        self.assertIn("Compress-Archive", self.texto)

    def test_roda_os_testes_antes_de_publicar(self):
        self.assertIn("unittest discover", self.texto)


if __name__ == "__main__":
    unittest.main()
