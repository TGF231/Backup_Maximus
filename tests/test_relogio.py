"""Mostrador de horário: dois cliques, hora e depois minuto.

As 24 horas ocupam dois anéis concêntricos — de fora `00` e `13`–`23`, de
dentro `12` e `1`–`11`. É a correspondência entre posição no círculo e valor
que faz o ponteiro apontar para o lugar certo, e é a parte fácil de inverter
sem perceber numa refatoração.
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
class MostradorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])
        from backup_maximus.ui import relogio
        cls.m = relogio

    def test_topo_e_meia_noite_por_fora_e_meio_dia_por_dentro(self):
        self.assertEqual(self.m._valor_hora(0, externo=True), 0)
        self.assertEqual(self.m._valor_hora(0, externo=False), 12)

    def test_anel_de_dentro_e_a_manha(self):
        for posicao in range(1, 12):
            self.assertEqual(self.m._valor_hora(posicao, externo=False), posicao)

    def test_anel_de_fora_e_a_tarde(self):
        for posicao in range(1, 12):
            self.assertEqual(self.m._valor_hora(posicao, externo=True),
                             12 + posicao)

    def test_ida_e_volta_de_todas_as_horas(self):
        # Sem isto, inverter os anéis passaria despercebido: a tela continua
        # desenhando, só que apontando para a hora errada.
        for hora in range(24):
            posicao, externo = self.m._posicao_da_hora(hora)
            self.assertEqual(self.m._valor_hora(posicao, externo), hora,
                             f"hora {hora} nao volta")


@unittest.skipIf(_sem_qt(), _sem_qt() or "sem Qt")
class CliquesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def _relogio(self):
        from backup_maximus.ui.relogio import Relogio
        r = Relogio()
        r.resize(210, 210)
        return r

    def _clicar(self, r, ponto):
        from PySide6.QtCore import QEvent, QPointF, Qt
        from PySide6.QtGui import QMouseEvent
        # A sobrecarga com posicao global evita o aviso de depreciacao.
        evento = QMouseEvent(QEvent.MouseButtonRelease, QPointF(*ponto),
                             QPointF(*ponto), Qt.LeftButton, Qt.LeftButton,
                             Qt.NoModifier)
        r.mouseReleaseEvent(evento)

    def test_comeca_nas_horas(self):
        from backup_maximus.ui.relogio import HORA
        self.assertIs(self._relogio().modo, HORA)

    def test_clique_na_hora_passa_para_os_minutos(self):
        # É o que faz o seletor avançar sozinho; sem isso o usuário teria de
        # descobrir onde clicar em seguida.
        from backup_maximus.ui.relogio import MINUTO
        r = self._relogio()
        self._clicar(r, (105, 20))          # topo, anel de fora
        self.assertIs(r.modo, MINUTO)

    def test_topo_do_anel_externo_e_meia_noite(self):
        r = self._relogio()
        self._clicar(r, (105, 20))
        self.assertEqual(r.hora, 0)

    def test_topo_do_anel_interno_e_meio_dia(self):
        r = self._relogio()
        self._clicar(r, (105, 52))          # mais perto do centro
        self.assertEqual(r.hora, 12)

    def test_so_avisa_que_terminou_depois_do_minuto(self):
        from backup_maximus.ui.relogio import MINUTO
        r = self._relogio()
        fim = []
        r.concluido.connect(lambda: fim.append(True))
        self._clicar(r, (105, 20))
        self.assertEqual(fim, [], "fechou antes de escolher o minuto")
        r.definir_modo(MINUTO)
        self._clicar(r, (105, 20))
        self.assertEqual(fim, [True])

    def test_clique_fora_do_mostrador_e_ignorado(self):
        r = self._relogio()
        antes = (r.hora, r.minuto, r.modo)
        self._clicar(r, (4, 4))             # canto, fora do circulo
        self.assertEqual((r.hora, r.minuto, r.modo), antes)

    def test_minuto_do_topo_e_zero(self):
        from backup_maximus.ui.relogio import MINUTO
        r = self._relogio()
        r.definir_modo(MINUTO)
        self._clicar(r, (105, 20))
        self.assertEqual(r.minuto, 0)

    def test_definir_limita_valores_impossiveis(self):
        r = self._relogio()
        r.definir(99, 99)
        self.assertEqual((r.hora, r.minuto), (23, 59))


if __name__ == "__main__":
    unittest.main()
