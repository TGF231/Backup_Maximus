"""Testes do núcleo do Backup Maximus (sem interface).

Executar:  python -m unittest discover -s tests -v
      ou:  run_tests.bat
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backup_maximus import (  # noqa: E402
    archive, engine, filecopy, logger, retention, sysinfo, util,
)
from backup_maximus.config import (  # noqa: E402
    BackupItem, BackupSet, Config, ItemType, NetCredential, SetMode,
    protect_secret, sha256_hex, unprotect_secret,
)


class ScratchCase(unittest.TestCase):
    """Base que dá a cada teste uma pasta temporária isolada."""

    def setUp(self) -> None:
        self.scratch = tempfile.mkdtemp(prefix="bm_test_")

    def tearDown(self) -> None:
        filecopy.remove_tree(self.scratch)

    def path(self, *parts: str) -> str:
        return os.path.join(self.scratch, *parts)

    def write(self, rel: str, text: str) -> str:
        full = self.path(rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(text)
        return full


# ---------------------------------------------------------------- utilidades
class TestUtil(unittest.TestCase):
    def test_format_bytes_usa_virgula_decimal(self):
        self.assertEqual(util.format_bytes(500), "500 B")
        self.assertEqual(util.format_bytes(1536), "1,5 KB")
        self.assertEqual(util.format_bytes(1024 ** 3), "1,0 GB")

    def test_format_seconds(self):
        self.assertEqual(util.format_seconds(5.25), "5,2 s")
        self.assertEqual(util.format_seconds(125), "2 min 5 s")

    def test_carimbo_no_padrao_do_winrar(self):
        stamp = util.now_stamp_br()
        self.assertEqual(len(stamp), 14)
        self.assertTrue(stamp.isdigit())

    def test_unc_root(self):
        self.assertEqual(util.unc_root(r"\\srv\share\a\b"), r"\\srv\share")
        self.assertEqual(util.unc_root(r"\\srv\share"), r"\\srv\share")
        self.assertEqual(util.unc_root(r"C:\local\path"), "")
        self.assertTrue(util.is_unc(r"\\srv\x"))
        self.assertFalse(util.is_unc(r"C:\x"))

    def test_truncate(self):
        self.assertEqual(util.truncate("a  b\n c"), "a b c")
        self.assertTrue(util.truncate("x" * 900).endswith("..."))
        self.assertLessEqual(len(util.truncate("x" * 900)), 503)

    def test_run_process_programa_inexistente(self):
        code, out = util.run_process(["programa_que_nao_existe_xyz.exe"])
        self.assertEqual(code, -1)
        self.assertIn("nao encontrado", out)


class TestFlagParsing(unittest.TestCase):
    """As flags precisam sobreviver a como cada shell as entrega."""

    def test_barra_traco_e_traco_duplo(self):
        from backup_maximus.__main__ import parse_flags
        for form in (["/silent"], ["-silent"], ["--silent"], ["/SILENT"]):
            self.assertIn("silent", parse_flags(form), form)

    def test_argumento_mangleado_por_shell_posix(self):
        # Git Bash/MSYS convertem '/check' em 'C:/Program Files/Git/check'
        from backup_maximus.__main__ import parse_flags
        flags = parse_flags([r"C:/Program Files/Git/check", "/quiet"])
        self.assertIn("check", flags)
        self.assertIn("quiet", flags)

    def test_varias_flags(self):
        from backup_maximus.__main__ import parse_flags
        self.assertEqual(parse_flags(["/check", "/quiet"]), {"check", "quiet"})

    def test_sem_argumentos(self):
        from backup_maximus.__main__ import parse_flags
        self.assertEqual(parse_flags([]), set())
        self.assertEqual(parse_flags(["", "   "]), set())


class TestWaitForPath(ScratchCase):
    def test_retorna_imediato_quando_ja_existe(self):
        started = time.monotonic()
        self.assertTrue(util.wait_for_path(self.scratch, 5))
        self.assertLess(time.monotonic() - started, 1.0)

    def test_expira_quando_nao_aparece(self):
        started = time.monotonic()
        ok = util.wait_for_path(self.path("nao_existe"), 2, poll_seconds=0.2)
        self.assertFalse(ok)
        self.assertGreaterEqual(time.monotonic() - started, 1.9)

    def test_detecta_unidade_que_aparece_durante_a_espera(self):
        alvo = self.path("pendrive")

        def on_tick(elapsed: int) -> bool:
            if elapsed >= 1:
                os.makedirs(alvo, exist_ok=True)
            return True

        self.assertTrue(util.wait_for_path(alvo, 10, on_tick, poll_seconds=0.3))

    def test_cancelamento_interrompe_a_espera(self):
        ok = util.wait_for_path(
            self.path("nunca"), 30, lambda _e: False, poll_seconds=0.1
        )
        self.assertFalse(ok)

    def test_caminho_vazio_nao_espera(self):
        self.assertTrue(util.wait_for_path("", 5))


# ------------------------------------------------------------- criptografia
class TestSecrets(unittest.TestCase):
    def test_ciclo_dpapi(self):
        plain = "S3nh@-Forte-ção"
        enc = protect_secret(plain)
        self.assertTrue(enc)
        self.assertNotEqual(enc, plain)
        self.assertEqual(unprotect_secret(enc), plain)

    def test_vazio_continua_vazio(self):
        self.assertEqual(protect_secret(""), "")
        self.assertEqual(unprotect_secret(""), "")

    def test_entrada_invalida_nao_quebra(self):
        self.assertEqual(unprotect_secret("isto-nao-e-base64!!"), "")
        self.assertEqual(unprotect_secret("YWJjZGVm"), "")

    def test_sha256_bate_com_vetor_conhecido(self):
        self.assertEqual(
            sha256_hex("abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )


class TestPassword(unittest.TestCase):
    def test_config_nova_nao_tem_senha(self):
        cfg = Config()
        self.assertFalse(cfg.has_password)
        self.assertTrue(cfg.check_password("qualquer"))

    def test_senha_nao_fica_em_texto_plano(self):
        cfg = Config()
        cfg.set_password("minha-senha")
        self.assertTrue(cfg.has_password)
        self.assertNotIn("minha-senha", cfg.ui_password_hash)
        self.assertTrue(cfg.ui_password_salt)

    def test_verificacao(self):
        cfg = Config()
        cfg.set_password("minha-senha")
        self.assertTrue(cfg.check_password("minha-senha"))
        self.assertFalse(cfg.check_password("minha-senh"))
        self.assertFalse(cfg.check_password(""))

    def test_salt_torna_hashes_diferentes(self):
        a, b = Config(), Config()
        a.set_password("igual")
        b.set_password("igual")
        self.assertNotEqual(a.ui_password_salt, b.ui_password_salt)
        self.assertNotEqual(a.ui_password_hash, b.ui_password_hash)


# -------------------------------------------------------------------- enums
class TestEnums(unittest.TestCase):
    def test_tipos(self):
        self.assertTrue(ItemType.FIREBIRD.is_database)
        self.assertFalse(ItemType.FILES.is_database)
        self.assertEqual(ItemType.FIREBIRD.dump_ext, ".fbk")
        self.assertEqual(ItemType.SQLSERVER.dump_ext, ".bak")
        self.assertEqual(ItemType.MYSQL.dump_ext, ".sql")
        self.assertEqual(ItemType.FILES.dump_ext, "")

    def test_nome_do_dump(self):
        item = BackupItem(name="erp", type=ItemType.FIREBIRD)
        self.assertEqual(item.dump_filename(), "erp.fbk")
        item.output_name = "PDVEXPRESSO.FBK"
        self.assertEqual(item.dump_filename(), "PDVEXPRESSO.FBK")


# ------------------------------------------------------------------- config
class TestConfigRoundTrip(ScratchCase):
    def _sample(self) -> Config:
        cfg = Config()
        cfg.company_name = "Comércio Aurora Ltda"
        cfg.notify_email = "ti@aurora.com.br"
        cfg.alert_timeout_hours = 12
        cfg.send_report_email = True
        cfg.set_password("admin123")
        cfg.smtp.host = "smtp.aurora.com.br"
        cfg.smtp.port = 465
        cfg.smtp.password_enc = protect_secret("smtp-secreta")
        cfg.last_run_unix = 1756200000
        cfg.last_run_status = "ok"
        cfg.net_creds.append(NetCredential(
            unc_root=r"\\servidor\backups", user=r"DOMINIO\svc_backup",
            password_enc=protect_secret("rede-secreta"),
        ))

        bset = BackupSet(
            name="BKP_MAXIMUS", staging=r"C:\BACKUP", destination="U:\\",
            mode=SetMode.FULL, wait_for_path="U:\\", wait_timeout_sec=600,
        )
        bset.items.append(BackupItem(
            name="PDV Expresso (banco)", type=ItemType.FIREBIRD,
            source="PDVEXPRESSO", subfolder="PDVEXPRESSO",
            output_name="PDVEXPRESSO.FBK", host="LOCALHOST", user="SYSDBA",
            password_enc=protect_secret("masterkey"),
        ))
        bset.items.append(BackupItem(
            name="Config NFC-e", type=ItemType.FILES,
            source=r"C:\Program Files (x86)\Eagle\PDVExpresso\nfceConfig.ini",
            subfolder="PDVEXPRESSO",
        ))
        bset.items.append(BackupItem(
            name="XMLs destinatário", type=ItemType.FILES,
            source=r"C:\Program Files (x86)\Eagle\PDVExpresso\Arquivos\XmlDestinatario",
            subfolder=r"PDVEXPRESSO\Arquivos\XmlDestinatario",
            mirror=True, enabled=False,
        ))
        cfg.sets.append(bset)
        return cfg

    def test_round_trip_preserva_tudo(self):
        path = self.path("cfg.ini")
        original = self._sample()
        self.assertEqual(original.total_items(), 3)
        self.assertTrue(original.save(path))

        loaded = Config.load(path)
        self.assertIsNotNone(loaded)

        self.assertEqual(loaded.company_name, "Comércio Aurora Ltda")
        self.assertEqual(loaded.alert_timeout_hours, 12)
        self.assertTrue(loaded.send_report_email)
        self.assertTrue(loaded.check_password("admin123"))
        self.assertFalse(loaded.check_password("errada"))
        self.assertEqual(loaded.smtp.port, 465)
        self.assertEqual(unprotect_secret(loaded.smtp.password_enc), "smtp-secreta")
        self.assertEqual(loaded.last_run_unix, 1756200000)
        self.assertEqual(loaded.last_run_status, "ok")

        self.assertEqual(len(loaded.net_creds), 1)
        self.assertEqual(loaded.net_creds[0].password, "rede-secreta")

        self.assertEqual(len(loaded.sets), 1)
        bset = loaded.sets[0]
        self.assertEqual(bset.name, "BKP_MAXIMUS")
        self.assertEqual(bset.staging, r"C:\BACKUP")
        self.assertEqual(bset.destination, "U:\\")
        self.assertIs(bset.mode, SetMode.FULL)
        self.assertEqual(bset.wait_for_path, "U:\\")
        self.assertEqual(bset.wait_timeout_sec, 600)
        self.assertTrue(bset.keep_staging)

        self.assertEqual(len(bset.items), 3)
        self.assertIs(bset.items[0].type, ItemType.FIREBIRD)
        self.assertEqual(bset.items[0].source, "PDVEXPRESSO")
        self.assertEqual(bset.items[0].output_name, "PDVEXPRESSO.FBK")
        self.assertEqual(bset.items[0].password, "masterkey")
        self.assertEqual(bset.items[2].subfolder,
                         r"PDVEXPRESSO\Arquivos\XmlDestinatario")
        self.assertTrue(bset.items[2].mirror)
        self.assertFalse(bset.items[2].enabled)
        self.assertEqual(len(bset.active_items), 2)

    def test_sobrescrita(self):
        path = self.path("cfg.ini")
        cfg = self._sample()
        cfg.save(path)
        cfg.company_name = "Outro Nome"
        self.assertTrue(cfg.save(path))
        self.assertEqual(Config.load(path).company_name, "Outro Nome")

    def test_arquivo_ausente(self):
        self.assertIsNone(Config.load(self.path("nao_existe.ini")))

    def test_ini_corrompido_nao_derruba(self):
        path = self.write("ruim.ini", "isto nao e um ini valido\n[[[\n")
        self.assertIsNone(Config.load(path))

    def test_valores_invalidos_caem_no_padrao(self):
        path = self.write("estranho.ini",
                          "[general]\nalert_timeout_hours=abc\n"
                          "[set.1]\nname=X\nmode=diferencial\n")
        cfg = Config.load(path)
        self.assertEqual(cfg.alert_timeout_hours, 26)
        self.assertIs(cfg.sets[0].mode, SetMode.FULL)

    def test_staging_padrao(self):
        bset = BackupSet(name="MEU")
        self.assertTrue(bset.staging_dir(r"C:\app").endswith(r"staging\MEU"))
        bset.staging = r"C:\BACKUP"
        self.assertEqual(bset.staging_dir(r"C:\app"), r"C:\BACKUP")


# --------------------------------------------------------------- métricas
class TestSysInfo(unittest.TestCase):
    def test_faixas_validas(self):
        info = sysinfo.collect(0.15)
        self.assertTrue(info.computer_name)
        self.assertGreaterEqual(info.cpu_pct, 0.0)
        self.assertLessEqual(info.cpu_pct, 100.0)
        self.assertGreater(info.mem_pct, 0.0)
        self.assertLessEqual(info.mem_pct, 100.0)
        self.assertGreater(info.mem_total_mb, 0)
        self.assertLessEqual(info.mem_used_mb, info.mem_total_mb)
        self.assertGreater(info.disk_total_gb, 0)
        self.assertLessEqual(info.disk_free_gb, info.disk_total_gb)


# ------------------------------------------------------ cópia e espelhamento
class TestFileCopy(ScratchCase):
    def setUp(self) -> None:
        super().setUp()
        self.src = self.path("src")
        self.dst = self.path("dst")
        self.write("src/a.txt", "conteudo A")
        self.write("src/b.txt", "conteudo B")
        self.write("src/sub/c.txt", "conteudo C")

    def test_primeira_copia(self):
        stats = filecopy.CopyStats()
        self.assertTrue(filecopy.mirror_directory(self.src, self.dst, True, stats))
        self.assertEqual(stats.copied, 3)
        self.assertEqual(stats.errors, 0)
        self.assertTrue(os.path.isfile(self.path("dst/sub/c.txt")))

    def test_segunda_passada_nao_recopia(self):
        stats = filecopy.CopyStats()
        filecopy.mirror_directory(self.src, self.dst, True, stats)
        again = filecopy.CopyStats()
        filecopy.mirror_directory(self.src, self.dst, True, again)
        self.assertEqual(again.copied, 0)
        self.assertEqual(again.skipped, 3)

    def test_somente_o_alterado_e_recopiado(self):
        filecopy.mirror_directory(self.src, self.dst, True, filecopy.CopyStats())
        time.sleep(1.1)  # supera a tolerância de mtime de 2 s do FAT32
        self.write("src/b.txt", "conteudo B MODIFICADO e bem maior que antes")
        stats = filecopy.CopyStats()
        filecopy.mirror_directory(self.src, self.dst, True, stats)
        self.assertEqual(stats.copied, 1)
        with open(self.path("dst/b.txt"), encoding="utf-8") as fh:
            self.assertIn("MODIFICADO", fh.read())

    def test_espelhamento_remove_o_que_sumiu(self):
        filecopy.mirror_directory(self.src, self.dst, True, filecopy.CopyStats())
        os.unlink(self.path("src/a.txt"))
        stats = filecopy.CopyStats()
        filecopy.mirror_directory(self.src, self.dst, True, stats)
        self.assertEqual(stats.deleted, 1)
        self.assertFalse(os.path.exists(self.path("dst/a.txt")))
        self.assertTrue(os.path.isfile(self.path("dst/b.txt")))

    def test_sem_espelhamento_preserva(self):
        filecopy.mirror_directory(self.src, self.dst, False, filecopy.CopyStats())
        os.unlink(self.path("src/a.txt"))
        stats = filecopy.CopyStats()
        filecopy.mirror_directory(self.src, self.dst, False, stats)
        self.assertEqual(stats.deleted, 0)
        self.assertTrue(os.path.isfile(self.path("dst/a.txt")))

    def test_espelhamento_remove_subpasta_inteira(self):
        filecopy.mirror_directory(self.src, self.dst, True, filecopy.CopyStats())
        filecopy.remove_tree(self.path("src/sub"))
        stats = filecopy.CopyStats()
        filecopy.mirror_directory(self.src, self.dst, True, stats)
        self.assertFalse(os.path.exists(self.path("dst/sub")))

    def test_arquivo_unico(self):
        stats = filecopy.CopyStats()
        alvo = self.path("um")
        self.assertTrue(filecopy.copy_one_file(self.path("src/a.txt"), alvo, stats))
        self.assertTrue(os.path.isfile(os.path.join(alvo, "a.txt")))
        de_novo = filecopy.CopyStats()
        filecopy.copy_one_file(self.path("src/a.txt"), alvo, de_novo)
        self.assertEqual(de_novo.skipped, 1)

    def test_origem_inexistente(self):
        stats = filecopy.CopyStats()
        self.assertFalse(filecopy.mirror_directory(
            self.path("nao_existe"), self.dst, True, stats))
        self.assertIn("nao encontrada", stats.last_error)

    def test_directory_size(self):
        self.assertGreater(filecopy.directory_size(self.src), 0)
        self.assertEqual(filecopy.directory_size(self.path("nada")), 0)

    def test_descricao_das_estatisticas(self):
        stats = filecopy.CopyStats(copied=2, skipped=5, deleted=1)
        self.assertEqual(stats.describe(), "2 copiados, 5 iguais, 1 removidos")


# ------------------------------------------------------------------- zip
class TestArchive(ScratchCase):
    def setUp(self) -> None:
        super().setUp()
        # Árvore no mesmo formato que o conjunto monta
        self.tree = self.path("BACKUP")
        self.write("BACKUP/PDVEXPRESSO/PDVEXPRESSO.FBK", "F" * 5000)
        self.write("BACKUP/PDVEXPRESSO/nfceConfig.ini", "[nfce]\nambiente=1\n")
        self.write("BACKUP/PDVEXPRESSO/Arquivos/XmlDestinatario/nota1.xml", "<nfe>1</nfe>")
        self.write("BACKUP/PDVEXPRESSO/Arquivos/Log/envio.log", "log de envio")
        self.arch = archive.Archiver()

    def test_arvore_inteira_em_um_zip(self):
        alvo = self.path("BKP_MAXIMUS26082026170000.zip")
        ok, err = self.arch.archive_tree(self.tree, alvo, True, False)
        self.assertTrue(ok, err)
        with zipfile.ZipFile(alvo) as zf:
            names = zf.namelist()
        # O 7-Zip grava também entradas de diretório; o zipfile, só arquivos.
        # A comparação é sobre os arquivos, que é o que importa no backup.
        arquivos = [n for n in names if not n.endswith("/")]
        # A pasta raiz é preservada, como o WinRAR fazia com C:\BACKUP
        self.assertTrue(all(n.startswith("BACKUP") for n in names), names)
        self.assertEqual(len(arquivos), 4, arquivos)
        self.assertTrue(any("XmlDestinatario" in n and n.endswith("nota1.xml")
                            for n in arquivos))

    def test_config_embutida_e_recuperada(self):
        alvo = self.path("saida.zip")
        self.arch.archive_tree(self.tree, alvo, False, False)

        ini = self.path("backup_maximus.ini")
        cfg = Config()
        cfg.company_name = "Empresa Embutida"
        cfg.alert_timeout_hours = 33
        cfg.save(ini)

        ok, err = self.arch.add_file(alvo, ini)
        self.assertTrue(ok, err)

        destino = self.path("extraido")
        ok, err = self.arch.extract_file(alvo, "backup_maximus.ini", destino)
        self.assertTrue(ok, err)

        recuperada = Config.load(os.path.join(destino, "backup_maximus.ini"))
        self.assertEqual(recuperada.company_name, "Empresa Embutida")
        self.assertEqual(recuperada.alert_timeout_hours, 33)

    def test_entrada_ausente(self):
        alvo = self.path("saida.zip")
        self.arch.archive_tree(self.tree, alvo, False, False)
        ok, err = self.arch.extract_file(alvo, "nao_existe.ini", self.path("out"))
        self.assertFalse(ok)
        self.assertIn("nao encontrado", err)

    def test_arvore_inexistente(self):
        ok, err = self.arch.archive_tree(
            self.path("nada"), self.path("x.zip"), True, False)
        self.assertFalse(ok)
        self.assertIn("nao encontrada", err)

    def test_progresso_e_reportado(self):
        vistos: list[int] = []
        self.arch.sevenzip = ""  # força o caminho do zipfile, que reporta progresso
        self.arch.archive_tree(self.tree, self.path("p.zip"), False, False,
                               progress=lambda pct, _e: vistos.append(pct))
        self.assertTrue(vistos)
        self.assertEqual(vistos[-1], 100)


# ---------------------------------------------------------------- watchdog
class TestWatchdog(unittest.TestCase):
    def _cfg(self, age_hours: float, status: str) -> Config:
        cfg = Config()
        cfg.alert_timeout_hours = 26
        cfg.last_run_unix = int(time.time() - age_hours * 3600) if age_hours >= 0 else 0
        cfg.last_run_status = status
        return cfg

    def test_dentro_do_prazo_nao_alerta(self):
        alerted, msg = engine.check_overdue(self._cfg(2, "ok"))
        self.assertFalse(alerted)
        self.assertIn("Ultimo backup OK", msg)

    def test_atrasado_alerta(self):
        alerted, msg = engine.check_overdue(self._cfg(40, "ok"))
        self.assertTrue(alerted)
        self.assertIn("acima do limite", msg)

    def test_ultima_execucao_falhou_alerta(self):
        alerted, msg = engine.check_overdue(self._cfg(1, "error"))
        self.assertTrue(alerted)
        self.assertIn("FALHAS", msg)

    def test_nunca_rodou_alerta(self):
        alerted, msg = engine.check_overdue(self._cfg(-1, ""))
        self.assertTrue(alerted)
        self.assertIn("Nenhum backup", msg)

    def test_alerta_desligado(self):
        cfg = self._cfg(999, "error")
        cfg.alert_timeout_hours = 0
        alerted, _msg = engine.check_overdue(cfg)
        self.assertFalse(alerted)


# ------------------------------------------------------- execução completa
class TestEngineEndToEnd(ScratchCase):
    """Reproduz o cenário do PDV Expresso: 4 origens -> 1 zip."""

    def setUp(self) -> None:
        super().setUp()
        logger.init(self.scratch)

        self.write("origem/PDVEXPRESSO.FDB", "F" * 20000)
        self.write("origem/nfceConfig.ini", "[nfce]\nambiente=1\n")
        for n in (1, 2, 3):
            self.write(f"origem/XmlDestinatario/nota{n}.xml", f"<nfe>{n}</nfe>")
        self.write("origem/Log/envio.log", "envio ok")

        self.destino = self.path("U_drive")
        os.makedirs(self.destino, exist_ok=True)

        bset = BackupSet(
            name="BKP_MAXIMUS",
            staging=self.path("BACKUP"),
            destination=self.destino,
            mode=SetMode.FULL,
        )
        bset.items = [
            BackupItem(name="PDV Expresso (banco)", type=ItemType.FILES,
                       source=self.path("origem/PDVEXPRESSO.FDB"),
                       subfolder="PDVEXPRESSO"),
            BackupItem(name="Config NFC-e", type=ItemType.FILES,
                       source=self.path("origem/nfceConfig.ini"),
                       subfolder="PDVEXPRESSO"),
            BackupItem(name="XMLs destinatário", type=ItemType.FILES,
                       source=self.path("origem/XmlDestinatario"),
                       subfolder=r"PDVEXPRESSO\Arquivos\XmlDestinatario",
                       mirror=True),
            BackupItem(name="Logs de transmissão", type=ItemType.FILES,
                       source=self.path("origem/Log"),
                       subfolder=r"PDVEXPRESSO\Arquivos\Log", mirror=True),
        ]

        self.cfg = Config()
        self.cfg.company_name = "Comércio Aurora Ltda"
        self.cfg.sets.append(bset)
        self.cfg_path = self.path("backup_maximus.ini")

    def _run(self):
        return engine.run_backups(self.cfg, self.cfg_path, self.scratch)

    def test_quatro_origens_viram_um_zip(self):
        result = self._run()
        self.assertTrue(result.all_ok, result.sets[0].message if result.sets else "")
        self.assertEqual(result.total_sets, 1)
        self.assertEqual(len(result.sets[0].items), 4)
        self.assertTrue(all(i.ok for i in result.sets[0].items))

        zips = [n for n in os.listdir(self.destino) if n.endswith(".zip")]
        self.assertEqual(len(zips), 1)
        self.assertTrue(zips[0].startswith("BKP_MAXIMUS"))
        # BKP_MAXIMUS + DDMMYYYYHHMMSS + .zip
        self.assertEqual(len(zips[0]), len("BKP_MAXIMUS") + 14 + 4)

    def test_estrutura_de_pastas_dentro_do_zip(self):
        result = self._run()
        with zipfile.ZipFile(result.sets[0].zip_path) as zf:
            names = [n.replace("/", "\\") for n in zf.namelist()]
        self.assertIn(r"BACKUP\PDVEXPRESSO\PDVEXPRESSO.FDB", names)
        self.assertIn(r"BACKUP\PDVEXPRESSO\nfceConfig.ini", names)
        self.assertIn(r"BACKUP\PDVEXPRESSO\Arquivos\XmlDestinatario\nota1.xml", names)
        self.assertIn(r"BACKUP\PDVEXPRESSO\Arquivos\Log\envio.log", names)
        # Persistência: config e relatório viajam dentro do backup
        self.assertIn("backup_maximus.ini", names)
        self.assertTrue(any(n.startswith("relatorio_backup_") for n in names))

    def test_segunda_execucao_e_incremental(self):
        self._run()
        segunda = self._run()
        detalhes = {i.name: i.detail for i in segunda.sets[0].items}
        self.assertEqual(detalhes["PDV Expresso (banco)"], "ja atualizado")
        self.assertIn("0 copiados", detalhes["XMLs destinatário"])
        self.assertIn("3 iguais", detalhes["XMLs destinatário"])

    def test_modo_completo_gera_um_zip_por_execucao(self):
        self._run()
        time.sleep(1.1)  # o carimbo tem resolução de 1 s
        self._run()
        zips = [n for n in os.listdir(self.destino) if n.endswith(".zip")]
        self.assertEqual(len(zips), 2)

    def test_modo_incremental_mantem_um_zip_so(self):
        self.cfg.sets[0].mode = SetMode.INCREMENTAL
        self._run()
        time.sleep(1.1)
        self._run()
        zips = [n for n in os.listdir(self.destino) if n.endswith(".zip")]
        self.assertEqual(zips, ["BKP_MAXIMUS.zip"])

    def test_espelhamento_propaga_para_o_zip(self):
        self._run()
        os.unlink(self.path("origem/XmlDestinatario/nota2.xml"))
        result = self._run()
        with zipfile.ZipFile(result.sets[0].zip_path) as zf:
            names = zf.namelist()
        self.assertFalse(any("nota2.xml" in n for n in names))
        self.assertTrue(any("nota1.xml" in n for n in names))

    def test_item_com_falha_nao_derruba_o_zip(self):
        self.cfg.sets[0].items.append(BackupItem(
            name="origem inexistente", type=ItemType.FILES,
            source=self.path("NAO_EXISTE"), subfolder="X",
        ))
        result = self._run()
        self.assertFalse(result.all_ok)
        self.assertTrue(os.path.isfile(result.sets[0].zip_path))
        self.assertIn("1 de 5 itens falharam", result.sets[0].message)
        # os 4 bons continuam dentro do arquivo
        with zipfile.ZipFile(result.sets[0].zip_path) as zf:
            self.assertTrue(any("nfceConfig.ini" in n for n in zf.namelist()))

    def test_item_desabilitado_e_ignorado(self):
        self.cfg.sets[0].items[0].enabled = False
        result = self._run()
        self.assertEqual(len(result.sets[0].items), 3)
        with zipfile.ZipFile(result.sets[0].zip_path) as zf:
            self.assertFalse(any("PDVEXPRESSO.FDB" in n for n in zf.namelist()))

    def test_estado_e_gravado_apos_a_execucao(self):
        self._run()
        salva = Config.load(self.cfg_path)
        self.assertEqual(salva.last_run_status, "ok")
        self.assertGreater(salva.last_run_unix, 0)

    def test_relatorio_tem_dados_do_dispositivo_e_da_empresa(self):
        result = self._run()
        with open(result.report_path, encoding="utf-8-sig") as fh:
            texto = fh.read()
        self.assertIn("Comércio Aurora Ltda", texto)
        self.assertIn("CPU:", texto)
        self.assertIn("Memoria:", texto)
        self.assertIn("Armazenamento:", texto)
        self.assertIn("PDV Expresso (banco)", texto)

    def test_progresso_chega_a_cem(self):
        vistos: list[int] = []
        engine.run_backups(self.cfg, self.cfg_path, self.scratch,
                           lambda _f, pct, _m: vistos.append(pct) or True)
        self.assertTrue(vistos)
        self.assertEqual(max(vistos), 100)

    def test_espera_por_unidade_ausente_falha(self):
        self.cfg.sets[0].wait_for_path = self.path("pendrive_ausente")
        self.cfg.sets[0].wait_timeout_sec = 2
        result = self._run()
        self.assertFalse(result.all_ok)
        self.assertIn("nao ficou disponivel", result.sets[0].message)

    def test_conjunto_sem_itens_habilitados(self):
        for item in self.cfg.sets[0].items:
            item.enabled = False
        result = self._run()
        self.assertFalse(result.all_ok)
        self.assertIn("sem itens habilitados", result.sets[0].message)

    def test_sem_conjuntos(self):
        self.cfg.sets.clear()
        result = self._run()
        self.assertEqual(result.total_sets, 0)
        self.assertIn("Nenhum conjunto", result.summary)

    def test_recuperar_config_de_dentro_do_zip(self):
        self.cfg.company_name = "Empresa Recuperada"
        self._run()
        # Simula máquina nova: só o zip, sem INI
        os.unlink(self.cfg_path)
        nova = self.path("maquina_nova")
        os.makedirs(nova, exist_ok=True)
        zip_name = [n for n in os.listdir(self.destino) if n.endswith(".zip")][0]
        import shutil
        shutil.copy2(os.path.join(self.destino, zip_name), nova)

        alvo_ini = os.path.join(nova, "backup_maximus.ini")
        self.assertTrue(engine.recover_config_from_zip(nova, alvo_ini))
        recuperada = Config.load(alvo_ini)
        self.assertEqual(recuperada.company_name, "Empresa Recuperada")
        self.assertEqual(len(recuperada.sets[0].items), 4)


# --------------------------------------------------- retenção e destino
class TestRetention(ScratchCase):
    def setUp(self) -> None:
        super().setUp()
        logger.init(self.scratch)
        self.dest = self.path("U_drive")
        os.makedirs(self.dest, exist_ok=True)
        self.bset = BackupSet(name="BKP_MAXIMUS", destination=self.dest,
                              mode=SetMode.FULL, keep_last=3)

    def _make(self, name: str, age_seconds: float, size: int = 100) -> str:
        full = os.path.join(self.dest, name)
        with open(full, "wb") as fh:
            fh.write(b"x" * size)
        stamp = time.time() - age_seconds
        os.utime(full, (stamp, stamp))
        return full

    def _make_series(self, count: int) -> None:
        for i in range(count):
            self._make(f"BKP_MAXIMUS2608202618{i:04d}.zip", age_seconds=i * 3600)

    def test_lista_do_mais_novo_ao_mais_antigo(self):
        self._make_series(4)
        found = retention.list_backups(self.bset)
        self.assertEqual(len(found), 4)
        self.assertGreater(found[0].mtime, found[-1].mtime)

    def test_ignora_arquivos_de_outro_conjunto(self):
        self._make_series(2)
        self._make("OUTRO_CONJUNTO26082026180000.zip", 10)
        self._make("anotacoes.txt", 10)
        nomes = [b.name for b in retention.list_backups(self.bset)]
        self.assertEqual(len(nomes), 2)
        self.assertTrue(all(n.startswith("BKP_MAXIMUS") for n in nomes))

    def test_expurgo_preserva_os_n_mais_recentes(self):
        self._make_series(6)
        removed, freed, errors = retention.prune(self.bset)
        self.assertEqual(removed, 3)
        self.assertEqual(freed, 300)
        self.assertEqual(errors, [])
        restantes = retention.list_backups(self.bset)
        self.assertEqual(len(restantes), 3)

    def test_expurgo_remove_justamente_os_mais_antigos(self):
        self._make_series(5)
        antes = retention.list_backups(self.bset)
        mantidos_esperados = {b.name for b in antes[:3]}
        retention.prune(self.bset)
        self.assertEqual({b.name for b in retention.list_backups(self.bset)},
                         mantidos_esperados)

    def test_dry_run_nao_apaga(self):
        self._make_series(6)
        count, freed, _ = retention.prune(self.bset, dry_run=True)
        self.assertEqual(count, 3)
        self.assertEqual(freed, 300)
        self.assertEqual(len(retention.list_backups(self.bset)), 6)

    def test_retencao_desligada_nao_remove_nada(self):
        self.bset.keep_last = 0
        self._make_series(6)
        removed, _freed, _errors = retention.prune(self.bset)
        self.assertEqual(removed, 0)
        self.assertEqual(len(retention.list_backups(self.bset)), 6)

    def test_modo_incremental_nunca_expurga(self):
        self.bset.mode = SetMode.INCREMENTAL
        self._make_series(6)
        removed, _freed, _errors = retention.prune(self.bset)
        self.assertEqual(removed, 0)

    def test_menos_arquivos_que_a_retencao(self):
        self._make_series(2)
        removed, _freed, _errors = retention.prune(self.bset)
        self.assertEqual(removed, 0)

    def test_inspecao_do_destino(self):
        self._make_series(5)
        report = retention.inspect(self.bset)
        self.assertTrue(report.reachable)
        self.assertGreater(report.free_bytes, 0)
        self.assertEqual(len(report.backups), 5)
        self.assertEqual(len(report.prunable), 2)
        self.assertEqual(report.used_bytes, 500)
        self.assertIn("livres", retention.describe(report))

    def test_inspecao_de_destino_inexistente(self):
        self.bset.destination = self.path("ainda_nao_existe")
        report = retention.inspect(self.bset)
        self.assertFalse(report.reachable)
        self.assertIn("não existe", report.message)

    def test_expurgo_roda_apos_backup_completo(self):
        """A limpeza acontece depois do zip novo, nunca antes."""
        origem = self.path("origem")
        self.write("origem/dado.txt", "conteudo")
        bset = BackupSet(name="SERIE", staging=self.path("stage"),
                         destination=self.dest, mode=SetMode.FULL, keep_last=2)
        bset.items = [BackupItem(name="dados", type=ItemType.FILES, source=origem)]
        cfg = Config()
        cfg.sets.append(bset)

        for _ in range(3):
            engine.run_backups(cfg, self.path("cfg.ini"), self.scratch)
            time.sleep(1.05)  # o carimbo tem resolução de 1 s

        restantes = retention.list_backups(bset)
        self.assertEqual(len(restantes), 2)


# ------------------------------------------------- validação de caminhos
class TestPathValidation(ScratchCase):
    """Regras do campo de caminho, sem instanciar a interface."""

    def setUp(self) -> None:
        super().setUp()
        from backup_maximus.ui.pathedit import PathKind, PathState, validate
        self.validate = validate
        self.Kind = PathKind
        self.State = PathState
        self.arquivo = self.write("um.txt", "conteudo")
        self.pasta = self.path("uma_pasta")
        os.makedirs(self.pasta, exist_ok=True)

    def test_vazio_e_neutro(self):
        state, msg = self.validate("", self.Kind.DIR)
        self.assertIs(state, self.State.NEUTRAL)
        self.assertEqual(msg, "")

    def test_tipo_none_nunca_reclama(self):
        state, _ = self.validate("qualquer coisa aqui", self.Kind.NONE)
        self.assertIs(state, self.State.NEUTRAL)

    def test_arquivo_existente(self):
        state, msg = self.validate(self.arquivo, self.Kind.FILE)
        self.assertIs(state, self.State.OK)
        self.assertIn("encontrado", msg)

    def test_pasta_onde_se_espera_arquivo(self):
        state, msg = self.validate(self.pasta, self.Kind.FILE)
        self.assertIs(state, self.State.BAD)
        self.assertIn("pasta", msg)

    def test_arquivo_onde_se_espera_pasta(self):
        state, msg = self.validate(self.arquivo, self.Kind.DIR)
        self.assertIs(state, self.State.BAD)
        self.assertIn("arquivo", msg)

    def test_inexistente(self):
        state, msg = self.validate(self.path("nada"), self.Kind.ANY)
        self.assertIs(state, self.State.BAD)
        self.assertIn("não encontrado", msg)

    def test_destino_existente_informa_espaco(self):
        state, msg = self.validate(self.pasta, self.Kind.DESTINATION)
        self.assertIs(state, self.State.OK)
        self.assertIn("livres", msg)

    def test_destino_inexistente_apenas_avisa(self):
        """Destino que ainda não existe é legítimo: o backup cria a pasta."""
        state, msg = self.validate(self.path("uma_pasta/nova"), self.Kind.DESTINATION)
        self.assertIs(state, self.State.WARN)
        self.assertIn("será criada", msg)

    def test_destino_com_pai_inacessivel(self):
        state, _ = self.validate(r"Z:\nao\existe\mesmo", self.Kind.DESTINATION)
        self.assertIs(state, self.State.BAD)

    def test_unc_indisponivel_e_aviso_nao_erro(self):
        """Compartilhamento fora do ar agora pode estar no ar no backup."""
        state, msg = self.validate(r"\\servidor-inexistente\share", self.Kind.DESTINATION)
        self.assertIs(state, self.State.WARN)
        self.assertIn("Rede", msg)

    def test_alias_firebird_nao_e_tratado_como_caminho(self):
        """PDVEXPRESSO é um alias válido; cobrar caminho seria falso positivo."""
        state, msg = self.validate("PDVEXPRESSO", self.Kind.PATH_OR_NAME)
        self.assertIs(state, self.State.NEUTRAL)
        self.assertIn("alias", msg)

    def test_caminho_de_fdb_e_validado_como_caminho(self):
        state, _ = self.validate(self.path("nao_existe.fdb"), self.Kind.PATH_OR_NAME)
        self.assertIs(state, self.State.BAD)

    def test_deteccao_de_caminho_versus_nome(self):
        from backup_maximus.ui.pathedit import looks_like_path
        self.assertFalse(looks_like_path("PDVEXPRESSO"))
        self.assertFalse(looks_like_path("meu_banco"))
        self.assertTrue(looks_like_path(r"C:\dados\ERP.FDB"))
        self.assertTrue(looks_like_path("dados/erp.fdb"))
        self.assertTrue(looks_like_path("ERP.FDB"))
        self.assertTrue(looks_like_path(r"\\srv\share"))


class TestFirebirdAliases(ScratchCase):
    """Leitura do aliases.conf (2.5) e do databases.conf (3+)."""

    def setUp(self) -> None:
        super().setUp()
        from backup_maximus import firebird_aliases
        self.fb = firebird_aliases

    def test_formato_do_firebird_2_5(self):
        texto = (
            "# List of known database aliases\n"
            "#   dummy = c:\\data\\dummy.fdb\n"
            "\n"
            "2025.002 = C:\\Program Files (x86)\\Eagle\\Data\\2025.002.FDB\n"
            "\n"
            "# MIGRACAO\n"
            "MIGRACAO_INICIAL = C:\\Users\\User\\MIGRACAO.FDB\n"
        )
        found = self.fb.parse_alias_file(texto)
        self.assertEqual(len(found), 2)
        self.assertEqual(found[0][0], "2025.002")
        self.assertTrue(found[0][1].endswith("2025.002.FDB"))
        self.assertEqual(found[1][0], "MIGRACAO_INICIAL")

    def test_bloco_de_parametros_do_firebird_3_mais(self):
        texto = (
            "DADOS = C:\\UpSystem\\Dados\\DADOS.FDB\n"
            "{\n"
            "  DefaultDBCachePages = 312144\n"
            "  LockMemSize = 30M\n"
            "}\n"
            "OUTRO = D:\\bases\\OUTRO.FDB\n"
        )
        found = self.fb.parse_alias_file(texto)
        self.assertEqual([n for n, _p in found], ["DADOS", "OUTRO"])

    def test_chave_na_mesma_linha_do_caminho(self):
        found = self.fb.parse_alias_file("X = C:\\x.fdb {\nCache = 10\n}\nY = C:\\y.fdb\n")
        self.assertEqual([n for n, _p in found], ["X", "Y"])
        self.assertTrue(found[0][1].endswith("x.fdb"))

    def test_ignora_base_de_seguranca_e_macros(self):
        texto = (
            "security.db = $(dir_secDb)/security5.fdb\n"
            "{\n RemoteAccess = false\n}\n"
            "REAL = C:\\bases\\REAL.FDB\n"
        )
        found = self.fb.parse_alias_file(texto)
        self.assertEqual([n for n, _p in found], ["REAL"])

    def test_comentarios_e_linhas_vazias(self):
        self.assertEqual(self.fb.parse_alias_file("# nada\n\n   \n"), [])

    def test_nome_de_alias_com_ponto_vira_pasta_valida(self):
        from backup_maximus.ui.alias_dialog import _safe_folder
        self.assertEqual(_safe_folder("2025.002"), "2025.002")
        self.assertEqual(_safe_folder("a/b:c"), "a_b_c")
        self.assertEqual(_safe_folder("   "), "banco")

    def test_le_arquivo_real_gerado_aqui(self):
        caminho = self.write("aliases.conf", "TESTE = C:\\bases\\TESTE.FDB\n")
        inst = self.fb.FirebirdInstance(
            root=self.scratch, version="2.5", config_file=caminho)
        aliases = self.fb.read_aliases(inst)
        self.assertEqual(len(aliases), 1)
        self.assertEqual(aliases[0].name, "TESTE")
        self.assertFalse(aliases[0].exists)   # o .fdb não existe de verdade
        self.assertIn("não encontrado", aliases[0].status)

    def test_deteccao_na_maquina_nao_explode(self):
        """Roda o caminho real; a máquina pode ou não ter Firebird."""
        for inst in self.fb.find_instances():
            self.assertTrue(os.path.isfile(inst.config_file))
            self.assertIsInstance(self.fb.read_aliases(inst), list)


class TestReminder(unittest.TestCase):
    def setUp(self) -> None:
        from backup_maximus import reminder
        self.reminder = reminder

    def test_horario_valido(self):
        self.assertTrue(self.reminder.valid_time("22:00"))
        self.assertTrue(self.reminder.valid_time("07:05"))
        self.assertTrue(self.reminder.valid_time("00:00"))
        self.assertFalse(self.reminder.valid_time("24:00"))
        self.assertFalse(self.reminder.valid_time("7h"))
        self.assertFalse(self.reminder.valid_time(""))

    def test_normalizacao(self):
        self.assertEqual(self.reminder.normalize_time("7:05"), "07:05")
        self.assertEqual(self.reminder.normalize_time(" 22:30 "), "22:30")
        self.assertEqual(self.reminder.normalize_time("xx"), "")

    def _cfg(self, **kwargs):
        cfg = Config()
        cfg.reminder_enabled = kwargs.get("enabled", True)
        cfg.last_run_unix = kwargs.get("last_run", 0)
        cfg.last_run_status = kwargs.get("status", "ok")
        if kwargs.get("with_set", True):
            cfg.sets.append(BackupSet(name="X", destination="C:\\tmp"))
        return cfg

    def test_desligado_nao_notifica(self):
        state = self.reminder.evaluate(self._cfg(enabled=False))
        self.assertFalse(state.should_notify)

    def test_backup_de_hoje_nao_incomoda(self):
        """Avisar sobre algo já feito treina a pessoa a ignorar o aviso."""
        recente = int(time.time() - 3600)
        state = self.reminder.evaluate(self._cfg(last_run=recente, status="ok"))
        self.assertFalse(state.should_notify)

    def test_backup_antigo_notifica(self):
        antigo = int(time.time() - 30 * 3600)
        state = self.reminder.evaluate(self._cfg(last_run=antigo, status="ok"))
        self.assertTrue(state.should_notify)
        self.assertIn("Hora do backup", state.headline)

    def test_ultima_execucao_com_falha_notifica_mesmo_recente(self):
        recente = int(time.time() - 1800)
        state = self.reminder.evaluate(self._cfg(last_run=recente, status="error"))
        self.assertTrue(state.should_notify)
        self.assertIn("falhou", state.headline)

    def test_nunca_rodou_notifica(self):
        state = self.reminder.evaluate(self._cfg(last_run=0))
        self.assertTrue(state.should_notify)

    def test_sem_conjunto_pede_configuracao(self):
        state = self.reminder.evaluate(self._cfg(with_set=False))
        self.assertTrue(state.should_notify)
        self.assertIn("não está configurado", state.headline)


class TestCloud(unittest.TestCase):
    """A camada de nuvem degrada com clareza quando o rclone não existe.

    Os testes de ausência forçam `find_rclone` a devolver vazio em vez de
    dependerem de a máquina ter ou não o rclone: assim valem igual na estação
    do desenvolvedor e no servidor de integração.
    """

    def setUp(self) -> None:
        from backup_maximus import cloud
        self.cloud = cloud
        self._original = cloud.find_rclone

    def tearDown(self) -> None:
        self.cloud.find_rclone = self._original

    def _sem_rclone(self) -> None:
        self.cloud.find_rclone = lambda hint="": ""

    def test_sem_rclone_nao_quebra(self):
        self._sem_rclone()
        self.assertEqual(self.cloud.list_remotes(), [])
        self.assertEqual(self.cloud.list_files("x", "y"), [])
        self.assertEqual(self.cloud.version(), "")
        self.assertFalse(self.cloud.available())

    def test_upload_sem_rclone_explica_o_motivo(self):
        self._sem_rclone()
        result = self.cloud.upload("qualquer.zip", "gdrive", "")
        self.assertFalse(result.ok)
        self.assertIn("rclone", result.message)

    def test_upload_sem_remote_explica_o_motivo(self):
        result = self.cloud.upload("qualquer.zip", "", "")
        self.assertFalse(result.ok)
        esperado = "remote" if self.cloud.available() else "rclone"
        self.assertIn(esperado, result.message.lower())

    def test_assistente_sem_rclone_orienta_a_instalacao(self):
        self._sem_rclone()
        ok, message = self.cloud.open_config_wizard()
        self.assertFalse(ok)
        self.assertIn("rclone", message.lower())

    def test_prune_desligado_nao_faz_nada(self):
        removed, errors = self.cloud.prune("gdrive", "p", "BKP", 0, "inexistente")
        self.assertEqual((removed, errors), (0, []))

    def test_provedores_conhecidos(self):
        self.assertIn("drive", self.cloud.KNOWN_PROVIDERS)
        self.assertIn("onedrive", self.cloud.KNOWN_PROVIDERS)
        self.assertIn("mega", self.cloud.KNOWN_PROVIDERS)


class TestVendorTools(ScratchCase):
    """Busca das ferramentas de terceiros dentro de vendor/.

    Quem baixa o 7-Zip não deveria ter que adivinhar o nome de pasta que o
    programa espera: a busca aceita a pasta arrumada e o pacote oficial
    extraído inteiro, com subpastas por arquitetura.
    """

    def setUp(self) -> None:
        super().setUp()
        from backup_maximus import paths
        self.paths = paths
        self._original = paths.vendor_dir
        vendor = self.path("vendor")
        os.makedirs(vendor, exist_ok=True)
        paths.vendor_dir = lambda: vendor
        self.vendor = vendor

    def tearDown(self) -> None:
        self.paths.vendor_dir = self._original
        super().tearDown()

    def _tool(self, rel: str) -> str:
        # normpath para o separador bater com o que find_vendor_tool devolve
        full = os.path.normpath(os.path.join(self.vendor, *rel.split("/")))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as fh:
            fh.write(b"MZ")   # cabeçalho de executável, só para existir
        return full

    def test_pasta_arrumada(self):
        alvo = self._tool("7zip/7za.exe")
        self.assertEqual(self.paths.find_vendor_tool("7za.exe", "7z.exe"), alvo)

    def test_pacote_oficial_extraido_inteiro(self):
        """vendor/7za/{7za.exe, x64/7za.exe, arm64/7za.exe} — o caso real."""
        self._tool("7za/7za.exe")
        x64 = self._tool("7za/x64/7za.exe")
        self._tool("7za/arm64/7za.exe")
        self._tool("7za/Far/7-ZipFar.dll")
        achado = self.paths.find_vendor_tool("7za.exe", "7z.exe")
        # Numa máquina x64 a preferência é a versão x64.
        if self.paths.arch_order()[0] == "x64":
            self.assertEqual(achado, x64)
        else:
            self.assertTrue(achado.endswith("7za.exe"))

    def test_so_a_versao_de_32_bits(self):
        alvo = self._tool("7za/7za.exe")
        self.assertEqual(self.paths.find_vendor_tool("7za.exe"), alvo)

    def test_pasta_com_nome_qualquer(self):
        alvo = self._tool("ferramentas/compactador/7za.exe")
        self.assertEqual(self.paths.find_vendor_tool("7za.exe"), alvo)

    def test_direto_na_raiz_de_vendor(self):
        alvo = self._tool("rclone.exe")
        self.assertEqual(self.paths.find_vendor_tool("rclone.exe"), alvo)

    def test_ausente_devolve_vazio(self):
        self.assertEqual(self.paths.find_vendor_tool("naoexiste.exe"), "")

    def test_ordem_dos_nomes_e_respeitada(self):
        """7za.exe tem preferência sobre 7z.exe quando os dois existem."""
        za = self._tool("7zip/7za.exe")
        self._tool("7zip/7z.exe")
        self.assertEqual(self.paths.find_vendor_tool("7za.exe", "7z.exe"), za)

    def test_arquitetura_conhecida(self):
        ordem = self.paths.arch_order()
        self.assertEqual(len(ordem), 3)
        self.assertIn("x64", ordem)

    # ------------------------------------------------------ empacotamento
    def test_pacote_leva_binario_e_licenca(self):
        self._tool("7za/x64/7za.exe")
        self._tool("7za/7za.exe")
        with open(os.path.join(self.vendor, "7za", "License.txt"), "w") as fh:
            fh.write("LGPL")
        arquivos = self.paths.bundle_files()
        destinos = {os.path.basename(s) for s, _t in arquivos}
        self.assertIn("7za.exe", destinos)
        self.assertIn("License.txt", destinos)
        # Só uma arquitetura vai para o pacote, não as três.
        self.assertEqual(sum(1 for s, _t in arquivos
                             if os.path.basename(s) == "7za.exe"), 1)

    def test_pacote_nao_inventa_licenca(self):
        self._tool("rclone/rclone.exe")
        arquivos = self.paths.bundle_files()
        nomes = [os.path.basename(s).lower() for s, _t in arquivos]
        self.assertIn("rclone.exe", nomes)
        self.assertFalse(any(n.startswith("license") for n in nomes))

    def test_vendor_vazio(self):
        self.assertEqual(self.paths.bundle_files(), [])


class TestLayoutFits(unittest.TestCase):
    """As telas precisam caber ao abrir, sem cortar campo nem exigir rolagem.

    Corte silencioso é o pior defeito de layout — nada avisa, o campo
    simplesmente não está lá. Este teste falha se um .ui crescer além do que a
    janela reserva.
    """

    def test_nenhum_painel_corta_ou_rola(self):
        try:
            from PySide6.QtWidgets import QApplication  # noqa: F401
        except ImportError:
            self.skipTest("PySide6 nao instalado")
        import os
        if not os.environ.get("DISPLAY") and os.name != "nt":
            self.skipTest("sem servidor grafico")

        from backup_maximus.ui import fitcheck
        self.assertTrue(
            fitcheck.check(verbose=False),
            "Algum painel corta ou precisa rolar. Rode "
            "'python -m backup_maximus.ui.fitcheck' para ver onde."
        )


class TestCloudDetection(unittest.TestCase):
    """Pastas sincronizadas com nuvem recebem tratamento diferente no destino."""

    def test_caminho_comum_nao_e_nuvem(self):
        self.assertEqual(util.cloud_provider(r"C:\Backups"), "")

    def test_vazio(self):
        self.assertEqual(util.cloud_provider(""), "")

    def test_onedrive_quando_presente(self):
        onedrive = os.environ.get("OneDrive", "")
        if not onedrive or not os.path.isdir(onedrive):
            self.skipTest("OneDrive nao configurado nesta maquina")
        self.assertIn("OneDrive", util.cloud_provider(onedrive))
        # subpasta também conta
        self.assertIn("OneDrive",
                      util.cloud_provider(os.path.join(onedrive, "Backups")))

    def test_pasta_de_nome_parecido_nao_conta(self):
        """Prefixo textual não basta: OneDriveOutraCoisa não é o OneDrive."""
        onedrive = os.environ.get("OneDrive", "")
        if not onedrive:
            self.skipTest("OneDrive nao configurado nesta maquina")
        self.assertEqual(util.cloud_provider(onedrive.rstrip("\\") + "XYZ"), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
