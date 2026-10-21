"""Campo de horário do lembrete.

O `QTimeEdit` original só aceitava edição por seção: clicar no campo e digitar
não funcionava, nem selecionar tudo. Este campo existe para aceitar o que as
pessoas realmente digitam, e `normalizar` é onde isso é decidido.
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
class NormalizarTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])
        from backup_maximus.ui import horaedit
        cls.h = horaedit

    def test_hora_sozinha_completa_os_minutos(self):
        self.assertEqual(self.h.normalizar("8"), "08:00")
        self.assertEqual(self.h.normalizar("19"), "19:00")

    def test_quatro_digitos_seguidos(self):
        # É o jeito mais rápido de digitar, e o que o campo deve privilegiar.
        self.assertEqual(self.h.normalizar("0800"), "08:00")
        self.assertEqual(self.h.normalizar("1930"), "19:30")

    def test_dois_pontos_define_onde_cada_parte_comeca(self):
        # Sem olhar o separador, "8:0" vira oitenta horas e o campo "corrige"
        # para 23:00 — o usuário veria o horário trocar sozinho.
        self.assertEqual(self.h.normalizar("8:0"), "08:00")
        self.assertEqual(self.h.normalizar("7:5"), "07:05")
        self.assertEqual(self.h.normalizar("0:0"), "00:00")

    def test_valor_ja_formatado_nao_muda(self):
        for hora in ("00:00", "08:00", "13:45", "23:59"):
            self.assertEqual(self.h.normalizar(hora), hora)

    def test_fora_da_faixa_e_limitado_e_nao_recusado(self):
        # Quem digitou 25:70 quis dizer "tarde", não quis um erro.
        self.assertEqual(self.h.normalizar("25:70"), "23:59")

    def test_sem_digitos_devolve_vazio(self):
        for texto in ("", "abc", "  :  ", ":"):
            self.assertEqual(self.h.normalizar(texto), "")


@unittest.skipIf(_sem_qt(), _sem_qt() or "sem Qt")
class HoraEditTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def _campo(self):
        from backup_maximus.ui.horaedit import HoraEdit
        return HoraEdit()

    def test_ida_e_volta(self):
        campo = self._campo()
        campo.setValue("07:30")
        self.assertEqual(campo.value(), "07:30")

    def test_valor_invalido_cai_no_padrao_em_vez_de_quebrar(self):
        from backup_maximus.ui.horaedit import PADRAO
        campo = self._campo()
        campo.setValue("isso nao e hora")
        self.assertEqual(campo.value(), PADRAO)

    def test_digitacao_crua_e_aceita(self):
        # O que o usuário faz: clica, digita 0800, sai do campo.
        campo = self._campo()
        campo.edit.setText("0800")
        campo._arrumar()
        self.assertEqual(campo.value(), "08:00")

    def test_avisa_quando_o_valor_muda(self):
        campo = self._campo()
        campo.setValue("22:00")
        vistos = []
        campo.valueChanged.connect(vistos.append)
        campo.edit.setText("0615")
        campo._arrumar()
        self.assertEqual(vistos, ["06:15"])

    def test_relogio_acompanha_o_que_foi_digitado(self):
        # Abrir o relógio depois de digitar não pode mostrar outro horário.
        campo = self._campo()
        campo.edit.setText("1745")
        campo._arrumar()
        campo._preparar_painel()
        self.assertEqual((campo._painel.relogio.hora,
                          campo._painel.relogio.minuto), (17, 45))

    def test_relogio_devolve_o_horario_escolhido(self):
        campo = self._campo()
        campo.setValue("22:00")
        campo._painel.definir("22:00")
        campo._painel._atualizar(6, 15)
        self.assertEqual(campo.value(), "06:15")

    def test_relogio_abre_sempre_nas_horas(self):
        # Reabrir no modo minuto deixaria o usuário sem como trocar a hora.
        from backup_maximus.ui.relogio import HORA, MINUTO
        campo = self._campo()
        campo._painel.relogio.definir_modo(MINUTO)
        campo._preparar_painel()
        self.assertIs(campo._painel.relogio.modo, HORA)


if __name__ == "__main__":
    unittest.main()
