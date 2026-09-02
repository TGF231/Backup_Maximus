"""Cadastro de nuvem sem console.

Nenhum teste aqui fala com a rede ou com um rclone de verdade: o que se
verifica é a leitura do que ele responde e as recusas antes de chamá-lo. Assim
a suíte roda igual na máquina de quem tem rclone instalado e na de quem não tem.
"""

import json
import unittest

from backup_maximus import cloud, cloud_setup, oauth_app


PROVIDERS_JSON = json.dumps([
    {
        "Name": "drive",
        "Description": "Google Drive",
        "Options": [
            {"Name": "client_id", "Help": "Google Application Client Id\nDeixe em branco normalmente.",
             "Type": "string"},
            {"Name": "token", "Help": "OAuth Access Token as a JSON blob.", "Type": "string"},
            {"Name": "chunk_size", "Help": "Upload chunk size.", "Advanced": True,
             "Type": "SizeSuffix"},
        ],
    },
    {
        "Name": "sftp",
        "Description": "SSH/SFTP",
        "Options": [
            {"Name": "host", "Help": "SSH host to connect to.", "Required": True,
             "Type": "string"},
            {"Name": "user", "Help": "SSH username.", "Required": True, "Type": "string"},
            {"Name": "pass", "Help": "SSH password.", "IsPassword": True, "Type": "string"},
            {"Name": "port", "Help": "SSH port.", "Type": "int", "DefaultStr": "22"},
            {"Name": "segredo", "Help": "interno", "Hide": 1, "Type": "string"},
        ],
    },
    {
        "Name": "s3",
        "Description": "Amazon S3 Compliant Storage Providers including AWS, "
                       "Alibaba, ArvanCloud, Ceph, ChinaMobile, Cloudflare",
        "Options": [
            {"Name": "provider", "Help": "Choose your S3 provider.", "Required": True,
             "Type": "string",
             "Examples": [{"Value": "AWS", "Help": "Amazon Web Services"},
                          {"Value": "Minio", "Help": ""}]},
        ],
    },
])


class FakeRclone:
    """Substitui as duas portas de saída do módulo: achar e executar o rclone."""

    def __init__(self, saida: str = PROVIDERS_JSON, code: int = 0):
        self.saida = saida
        self.code = code
        self.chamadas: list[list[str]] = []

    def find(self, hint=""):
        return r"C:\rclone\rclone.exe"

    def run(self, args, timeout=None, **kwargs):
        self.chamadas.append(list(args))
        return self.code, self.saida


class ListProvidersTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeRclone()
        self._find, cloud.find_rclone = cloud.find_rclone, self.fake.find
        self._run, cloud_setup.util.run_process = cloud_setup.util.run_process, self.fake.run

    def tearDown(self):
        cloud.find_rclone = self._find
        cloud_setup.util.run_process = self._run

    def test_le_a_lista_do_proprio_rclone(self):
        nomes = [p.name for p in cloud_setup.list_providers()]
        self.assertEqual(set(nomes), {"drive", "sftp", "s3"})

    def test_destacados_vem_primeiro_na_ordem_escolhida(self):
        nomes = [p.name for p in cloud_setup.list_providers()]
        self.assertEqual(nomes[:3], ["drive", "sftp", "s3"])

    def test_campo_token_marca_o_servico_como_oauth(self):
        por_nome = {p.name: p for p in cloud_setup.list_providers()}
        self.assertTrue(por_nome["drive"].uses_oauth)
        self.assertFalse(por_nome["sftp"].uses_oauth)

    def test_opcoes_avancadas_e_ocultas_ficam_de_fora(self):
        por_nome = {p.name: p for p in cloud_setup.list_providers()}
        nomes = [o.name for o in por_nome["sftp"].options]
        self.assertNotIn("segredo", nomes)
        nomes_drive = [o.name for o in por_nome["drive"].options]
        self.assertNotIn("chunk_size", nomes_drive)

    def test_formulario_pede_so_o_obrigatorio(self):
        por_nome = {p.name: p for p in cloud_setup.list_providers()}
        basicos = [o.name for o in por_nome["sftp"].basic_options()]
        self.assertEqual(basicos, ["host", "user"])

    def test_descricao_gigante_do_s3_nao_estoura_a_lista(self):
        por_nome = {p.name: p for p in cloud_setup.list_providers()}
        rotulo = por_nome["s3"].label
        self.assertLessEqual(len(rotulo), 60)
        self.assertTrue(rotulo.endswith("(s3)"))

    def test_json_invalido_nao_derruba_a_janela(self):
        self.fake.saida = "erro: comando desconhecido"
        self.assertEqual(cloud_setup.list_providers(), [])

    def test_rclone_com_erro_devolve_lista_vazia(self):
        self.fake.code = 1
        self.assertEqual(cloud_setup.list_providers(), [])

    def test_rotulos_comuns_saem_em_portugues(self):
        por_nome = {p.name: p for p in cloud_setup.list_providers()}
        rotulos = {o.name: o.label for o in por_nome["sftp"].options}
        self.assertEqual(rotulos["user"], "Usuário")
        self.assertEqual(rotulos["pass"], "Senha")
        self.assertEqual(rotulos["host"], "Servidor")

    def test_campo_sem_traducao_mantem_o_nome_do_rclone(self):
        por_nome = {p.name: p for p in cloud_setup.list_providers()}
        rotulos = {o.name: o.label for o in por_nome["drive"].options}
        # 'token' não está no glossário: melhor o nome original do rclone do
        # que uma tradução inventada que ninguém encontra na documentação dele.
        self.assertEqual(rotulos["token"], "Token")
        self.assertEqual(rotulos["client_id"], "ID do cliente")

    def test_ajuda_mostra_so_a_primeira_linha(self):
        por_nome = {p.name: p for p in cloud_setup.list_providers()}
        ajuda = {o.name: o.first_line for o in por_nome["drive"].options}["client_id"]
        self.assertEqual(ajuda, "Google Application Client Id")


class SemRcloneTest(unittest.TestCase):
    """Sem a ferramenta, tudo recua com uma frase — nada de exceção na cara."""

    def setUp(self):
        self._find = cloud.find_rclone
        cloud.find_rclone = lambda hint="": ""

    def tearDown(self):
        cloud.find_rclone = self._find

    def test_lista_vazia(self):
        self.assertEqual(cloud_setup.list_providers(), [])

    def test_criar_avisa(self):
        ok, msg = cloud_setup.create_remote("x", "drive", {})
        self.assertFalse(ok)
        self.assertIn("rclone", msg)

    def test_autorizar_avisa(self):
        sessao = cloud_setup.AuthorizeSession("drive")
        self.assertFalse(sessao.start(lambda _u: None, lambda _o, _m: None))
        self.assertIn("rclone", sessao.error)


class TokenTest(unittest.TestCase):
    """O token vem impresso na saída do `rclone authorize`, entre marcadores."""

    SAIDA = (
        "2026/08/26 10:00:00 NOTICE: Please go to the following link: "
        "http://127.0.0.1:53682/auth?state=abc\n"
        "2026/08/26 10:00:20 NOTICE: Got code\n"
        "Paste the following into your remote machine --->\n"
        '{"access_token":"ya29.aaa","token_type":"Bearer","expiry":"2026-08-26T11:00:00Z"}\n'
        "<---End paste\n"
    )

    def test_extrai_entre_os_marcadores(self):
        token = cloud_setup.AuthorizeSession._extract_token(self.SAIDA)
        self.assertEqual(json.loads(token)["access_token"], "ya29.aaa")

    def test_extrai_mesmo_sem_os_marcadores(self):
        solto = 'algo antes {"access_token":"zzz","expiry":"x"} algo depois'
        token = cloud_setup.AuthorizeSession._extract_token(solto)
        self.assertEqual(json.loads(token)["access_token"], "zzz")

    def test_saida_sem_token_nao_inventa_um(self):
        self.assertEqual(
            cloud_setup.AuthorizeSession._extract_token("Failed to get token"), "")

    def test_json_quebrado_nao_passa(self):
        quebrado = 'muito bem ---> {"access_token": <---'
        self.assertEqual(cloud_setup.AuthorizeSession._extract_token(quebrado), "")

    def test_link_local_e_reconhecido(self):
        achado = cloud_setup._LINK_RE.search(self.SAIDA)
        self.assertIsNotNone(achado)
        self.assertTrue(achado.group(0).startswith("http://127.0.0.1:"))


class CreateRemoteTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeRclone(saida="")
        self._find, cloud.find_rclone = cloud.find_rclone, self.fake.find
        self._run, cloud_setup.util.run_process = cloud_setup.util.run_process, self.fake.run
        self._remotes, cloud.list_remotes = cloud.list_remotes, lambda hint="": ["antigo"]

    def tearDown(self):
        cloud.find_rclone = self._find
        cloud_setup.util.run_process = self._run
        cloud.list_remotes = self._remotes

    def test_nome_vazio_e_recusado_antes_de_chamar_o_rclone(self):
        ok, _ = cloud_setup.create_remote("   ", "drive", {})
        self.assertFalse(ok)
        self.assertEqual(self.fake.chamadas, [])

    def test_nome_com_espaco_e_recusado(self):
        # O rclone identifica o remote por 'nome:', então espaço quebraria o
        # destino do envio — melhor barrar aqui do que falhar de madrugada.
        ok, msg = cloud_setup.create_remote("meu drive", "drive", {})
        self.assertFalse(ok)
        self.assertIn("letras", msg.lower())

    def test_nome_repetido_e_recusado(self):
        ok, msg = cloud_setup.create_remote("antigo", "drive", {})
        self.assertFalse(ok)
        self.assertIn("antigo", msg)

    def test_campos_vazios_nao_viram_argumento(self):
        cloud_setup.create_remote("novo", "sftp", {"host": "srv", "port": ""})
        args = self.fake.chamadas[0]
        self.assertIn("host=srv", args)
        self.assertNotIn("port=", args)

    def test_sempre_nao_interativo_e_com_senha_cifrada(self):
        cloud_setup.create_remote("novo", "sftp", {"host": "srv"})
        args = self.fake.chamadas[0]
        self.assertIn("--non-interactive", args)
        self.assertIn("--obscure", args)

    def test_token_entra_como_campo(self):
        cloud_setup.create_remote("novo", "drive", {}, token='{"access_token":"a"}')
        self.assertIn('token={"access_token":"a"}', self.fake.chamadas[0])

    def test_erro_do_rclone_chega_ao_usuario(self):
        self.fake.code = 1
        self.fake.saida = "Failed to configure: unknown provider"
        ok, msg = cloud_setup.create_remote("novo", "xyz", {})
        self.assertFalse(ok)
        self.assertIn("unknown provider", msg)


if __name__ == "__main__":
    unittest.main()


class ChaveEmbutidaTest(unittest.TestCase):
    """A identidade do aplicativo, e como ela chega ao rclone."""

    def setUp(self):
        self.fake = FakeRclone(saida="")
        self._find, cloud.find_rclone = cloud.find_rclone, self.fake.find
        self._run, cloud_setup.util.run_process = cloud_setup.util.run_process, self.fake.run
        self._remotes, cloud.list_remotes = cloud.list_remotes, lambda hint="": []
        self._keys = dict(oauth_app.APP_KEYS)

    def tearDown(self):
        cloud.find_rclone = self._find
        cloud_setup.util.run_process = self._run
        cloud.list_remotes = self._remotes
        oauth_app.APP_KEYS.clear()
        oauth_app.APP_KEYS.update(self._keys)

    def test_chave_do_aplicativo_entra_no_remote(self):
        oauth_app.APP_KEYS["drive"] = ("meu-id", "meu-secret")
        cloud_setup.create_remote("d", "drive", {}, token='{"access_token":"a"}')
        args = self.fake.chamadas[0]
        self.assertIn("client_id=meu-id", args)
        self.assertIn("client_secret=meu-secret", args)

    def test_escopo_restrito_e_o_padrao_do_drive(self):
        # drive.file dá acesso só ao que o próprio programa criou — é o que
        # dispensa a verificação de segurança que o Google exige do escopo
        # 'drive' completo.
        cloud_setup.create_remote("d", "drive", {}, token='{"access_token":"a"}')
        self.assertIn("scope=drive.file", self.fake.chamadas[0])

    def test_chave_digitada_vence_a_embutida(self):
        oauth_app.APP_KEYS["drive"] = ("embutida", "s1")
        cloud_setup.create_remote("d", "drive", {"client_id": "minha",
                                                 "client_secret": "s2"})
        args = self.fake.chamadas[0]
        self.assertIn("client_id=minha", args)
        self.assertNotIn("client_id=embutida", args)

    def test_escopo_escolhido_vence_o_nosso_padrao(self):
        cloud_setup.create_remote("d", "drive", {"scope": "drive"})
        args = self.fake.chamadas[0]
        self.assertIn("scope=drive", args)
        self.assertNotIn("scope=drive.file", args)

    def test_servico_sem_chave_nossa_nao_ganha_campos_extras(self):
        cloud_setup.create_remote("m", "mega", {"user": "a", "pass": "b"})
        args = self.fake.chamadas[0]
        self.assertFalse([a for a in args if a.startswith("client_id=")])
        self.assertFalse([a for a in args if a.startswith("scope=")])

    def test_sem_chave_embutida_o_rclone_usa_a_dele(self):
        oauth_app.APP_KEYS["drive"] = ("", "")
        cloud_setup.create_remote("d", "drive", {}, token='{"access_token":"a"}')
        args = self.fake.chamadas[0]
        self.assertFalse([a for a in args if a.startswith("client_id=")])

    def test_so_o_drive_exige_chave_propria(self):
        # OneDrive e Dropbox descrevem a chave como "deixe em branco
        # normalmente"; só o Drive avisa que aposenta a compartilhada.
        self.assertTrue(oauth_app.needs_own_key("drive"))
        self.assertFalse(oauth_app.needs_own_key("onedrive"))
        self.assertFalse(oauth_app.needs_own_key("dropbox"))

    def test_credenciais_ignoram_espaco_colado_por_engano(self):
        oauth_app.APP_KEYS["drive"] = ("  id  ", "  seg  ")
        self.assertEqual(oauth_app.credentials("drive"), ("id", "seg"))


class AutorizacaoUsaAChaveTest(unittest.TestCase):
    """O consentimento pertence ao aplicativo que o pediu.

    Se autorizássemos com a chave compartilhada e gravássemos a nossa no
    remote, o token nasceria recusado — e o erro só apareceria no envio.
    """

    def setUp(self):
        self.args: list[str] = []
        self.env: dict = {}
        self._find, cloud.find_rclone = cloud.find_rclone, lambda hint="": "rclone.exe"

        def fake_popen(args, **kwargs):
            self.args = list(args)
            self.env = kwargs.get("env") or {}
            raise OSError("não executa de verdade no teste")

        self._popen = cloud_setup.subprocess.Popen
        cloud_setup.subprocess.Popen = fake_popen

    def tearDown(self):
        cloud.find_rclone = self._find
        cloud_setup.subprocess.Popen = self._popen

    def test_chave_vai_como_argumento_posicional(self):
        sessao = cloud_setup.AuthorizeSession("drive", "", "meu-id", "meu-seg")
        sessao.start(lambda _u: None, lambda _o, _m: None)
        self.assertEqual(self.args[:5],
                         ["rclone.exe", "authorize", "drive", "meu-id", "meu-seg"])

    def test_sem_chave_nao_sobra_argumento_vazio(self):
        sessao = cloud_setup.AuthorizeSession("mega")
        sessao.start(lambda _u: None, lambda _o, _m: None)
        self.assertEqual(self.args, ["rclone.exe", "authorize", "mega",
                                     "--auth-no-open-browser"])

    def test_escopo_vai_pelo_ambiente(self):
        # O `authorize` não aceita o escopo como argumento, mas o rclone lê as
        # opções de backend do ambiente.
        sessao = cloud_setup.AuthorizeSession("drive", "", "id", "seg")
        sessao.start(lambda _u: None, lambda _o, _m: None)
        self.assertEqual(self.env.get("RCLONE_DRIVE_SCOPE"), "drive.file")
