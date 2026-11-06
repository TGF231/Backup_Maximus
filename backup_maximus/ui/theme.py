"""Folha de estilo (QSS) da interface, montada sobre os tokens do MegUI.

MegUI é a assinatura visual dos aplicativos da família: acento vermelho-escuro
de marca, igual nos dois temas, neutros de viés azulado, raio máximo de 4px,
nenhuma sombra, uma família tipográfica em dois pesos (400/700).

Todo valor vem de `megui_tokens` — cor, tamanho de tipo e medida. Nenhum
literal de cor mora neste arquivo nem no resto da interface: o que pinta em
Python (relógio, pontos das listas, ícones) puxa de `current()`.

Três usos do acento, e a diferença importa:

* `accent` é **fundo**, e só da ação primária — um elemento por tela.
* `accent_linha` é o acento como **linha** (anel de foco, aba ativa, caixa
  marcada). No escuro o acento puro sobre a superfície dá 1,5:1, abaixo dos
  3:1 de indicador não textual; por isso ele sobe para tijolo só ali.
* `accent_soft` é **seleção**: o texto continua por cima, em `ink`.

As cores semânticas (ok/aviso/erro) ficam separadas do acento: "atenção" nunca
se confunde com "isto é clicável". O olho as separa por luminosidade.
"""

from __future__ import annotations

import os

from .megui_tokens import CLARO, ESCALA_TIPO, ESCURO, FONT_MONO, FONT_UI, Paleta

#: Mantido como nome público: o resto da interface anota tipos com ele.
Palette = Paleta

# Largura da coluna de rótulos dos formulários montados em tempo de execução
# (o assistente de nuvem constrói os campos a partir do que o rclone diz sobre
# cada serviço). Os .ui usam a mesma; múltiplo de 4, como toda medida MegUI.
LABEL_WIDTH = 124

#: Fontes embarcadas — OFL, ver fonts/OFL.txt. Ficam junto do código para o
#: PyInstaller levá-las sem lista à parte, e são carregadas antes da primeira
#: folha de estilo: sem elas o Qt cai num substituto mais largo e os campos
#: medidos no Designer cortam.
FONTES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FAMILIA_UI = "Atkinson Hyperlegible Next"
FAMILIA_MONO = "Atkinson Hyperlegible Mono"

_DICA = ESCALA_TIPO["dica"]["pt"]
_CORPO = ESCALA_TIPO["corpo"]["pt"]
_TITULO = ESCALA_TIPO["titulo"]["pt"]
_DESTAQUE = ESCALA_TIPO["destaque"]["pt"]

_active: Paleta = CLARO
_fontes_carregadas = False


def carregar_fontes() -> bool:
    """Registra as fontes do MegUI no Qt. Idempotente; exige QGuiApplication.

    Devolve False se alguma não carregou — a interface continua, na pilha de
    reserva declarada nos tokens.
    """
    global _fontes_carregadas
    if _fontes_carregadas:
        return True
    from PySide6.QtGui import QFontDatabase
    ok = True
    for nome in sorted(os.listdir(FONTES_DIR)):
        if nome.lower().endswith(".ttf"):
            if QFontDatabase.addApplicationFont(os.path.join(FONTES_DIR, nome)) < 0:
                ok = False
    _fontes_carregadas = ok
    return ok


def current() -> Paleta:
    return _active


def set_dark(dark: bool) -> Paleta:
    """Troca a paleta ativa e devolve a nova."""
    global _active
    _active = ESCURO if dark else CLARO
    return _active


def is_dark() -> bool:
    return _active is ESCURO


def stylesheet() -> str:
    """Folha de estilo completa, com os ícones desenhados em runtime."""
    from . import icons
    carregar_fontes()
    p = _active
    art = icons.paths(p)
    check = art["check"]
    chevron = art["chevron"]
    chevron_off = art["chevron_off"]

    return f"""
QWidget {{
    background: {p.bg};
    color: {p.ink};
    font-family: {FONT_UI};
    font-size: {_CORPO};
}}
QDialog, QMessageBox {{ background: {p.bg}; }}
QMessageBox QLabel {{ color: {p.ink}; }}

/* ---------------------------------------------------------------- abas
   Aba ativa: marca de 2px no topo em accent_linha e peso forte. */
QTabWidget::pane {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: 4px;
    top: -1px;
}}
QTabBar::tab {{
    background: {p.surface2};
    color: {p.ink2};
    border: 1px solid {p.border};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 20px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {p.surface};
    color: {p.ink};
    font-weight: 700;
    border-top: 2px solid {p.accent_linha};
    padding-top: 7px;
}}
QTabBar::tab:hover:!selected {{ color: {p.ink}; background: {p.border}; }}

/* ------------------------------------------------------------ rótulos
   Papel visual é a propriedade dinâmica `role`, não o objectName: no Qt
   Designer o objectName é único por widget, e dezenas de rótulos dividem o
   mesmo estilo. Hierarquia por peso e cor antes de tamanho. */
QLabel {{ background: transparent; color: {p.ink}; }}
QLabel[role="section"] {{
    color: {p.ink};
    font-weight: 700;
    font-size: {_DICA};
    letter-spacing: 1px;
}}
QLabel[role="field"] {{ color: {p.ink2}; }}
QLabel[role="hint"] {{ color: {p.ink3}; font-size: {_DICA}; }}
QLabel[role="hintWarn"] {{ color: {p.warn}; font-family: {FONT_MONO}; font-size: {_DICA}; }}
QLabel[role="hintOk"] {{ color: {p.ok}; font-size: {_DICA}; }}
QLabel[role="hintBad"] {{ color: {p.bad}; font-size: {_DICA}; font-weight: 700; }}
QLabel[role="footer"] {{ color: {p.ink2}; font-family: {FONT_MONO}; font-size: {_DICA}; }}
QLabel[role="mono"] {{ font-family: {FONT_MONO}; color: {p.ink2}; font-size: {_DICA}; }}
QLabel[role="bigStatus"] {{ color: {p.ink}; font-size: {_TITULO}; font-weight: 700; }}
/* Resultado de uma operação: cor, peso e o próprio texto — cor nunca sozinha. */
QLabel[role="statusOk"] {{ color: {p.ok}; font-weight: 700; }}
QLabel[role="statusWarn"] {{ color: {p.warn}; font-weight: 700; }}
QLabel[role="statusBad"] {{ color: {p.bad}; font-weight: 700; }}
/* Cabeçalho do seletor de horário: a parte ativa é a selecionada (estado
   "selecionado" do MegUI), não um segundo botão de acento. */
QLabel[role="clockOn"] {{
    color: {p.ink}; background: {p.accent_soft};
    border: 1px solid {p.accent_linha}; border-radius: 4px;
    font-family: {FONT_MONO}; font-size: {_DESTAQUE}; font-weight: 700;
    padding: 2px 0;
}}
QLabel[role="clockOff"] {{
    color: {p.ink2}; background: {p.surface2};
    border: 1px solid {p.border2}; border-radius: 4px;
    font-family: {FONT_MONO}; font-size: {_DESTAQUE};
    padding: 2px 0;
}}

/* ------------------------------------------------------------- botões
   Seis estados do MegUI: repouso, hover, pressionado, foco, desabilitado,
   selecionado. Desabilitado perde fundo e tinta, mas continua visível. */
QPushButton, QToolButton {{
    background: {p.surface};
    color: {p.ink2};
    border: 1px solid {p.border2};
    border-radius: 4px;
    padding: 4px 12px;
    min-height: 18px;
}}
QPushButton:hover, QToolButton:hover {{ background: {p.surface2}; color: {p.ink}; }}
QPushButton:pressed, QToolButton:pressed {{ background: {p.border}; color: {p.ink}; }}
QPushButton:focus, QToolButton:focus {{ border-color: {p.accent_linha}; }}
QPushButton:disabled, QToolButton:disabled {{
    background: {p.bg}; color: {p.ink3}; border-color: {p.border};
}}
QPushButton:checked, QToolButton:checked {{
    background: {p.accent_soft}; color: {p.ink}; border-color: {p.accent_linha};
}}

/* A ação primária: o único elemento com acento na tela. */
QPushButton[role="accent"] {{
    background: {p.accent};
    color: {p.on_accent};
    border: 1px solid {p.accent_hover};
    font-weight: 700;
    padding: 8px 16px;
}}
QPushButton[role="accent"]:hover, QPushButton[role="accent"]:pressed {{
    background: {p.accent_hover}; border-color: {p.accent_hover};
}}
QPushButton[role="accent"]:focus {{ border-color: {p.accent_linha}; }}
QPushButton[role="accent"]:disabled {{
    background: {p.bg}; color: {p.ink3}; border-color: {p.border};
}}

QPushButton[role="tiny"] {{ padding: 4px 8px; }}

/* Botão de ícone embutido em campo (relógio do horário): sem moldura em
   repouso, um passo de superfície no hover. O menu que ele abre já se
   anuncia pelo próprio ícone — a seta extra do Qt só aperta o botão. */
QToolButton[autoRaise="true"] {{
    background: transparent; border: 1px solid transparent; padding: 4px;
}}
QToolButton[autoRaise="true"]:hover {{ background: {p.surface2}; border-color: {p.border2}; }}
QToolButton[autoRaise="true"]:focus {{ border-color: {p.accent_linha}; }}
QToolButton::menu-indicator {{ image: none; width: 0; }}

/* ------------------------------------------------------------- campos */
QLineEdit, QSpinBox, QPlainTextEdit, QTextEdit {{
    background: {p.sunken};
    color: {p.ink};
    border: 1px solid {p.border2};
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: {p.accent_soft};
    selection-color: {p.ink};
}}
QLineEdit:focus, QSpinBox:focus, QPlainTextEdit:focus, QTextEdit:focus {{
    border-color: {p.accent_linha};
}}
QLineEdit:disabled, QSpinBox:disabled {{
    background: {p.bg}; color: {p.ink3}; border-color: {p.border};
}}
QLineEdit:read-only {{ background: {p.somente_leitura}; }}
QLineEdit[mono="true"] {{ font-family: {FONT_MONO}; }}

/* Resultado da validação de caminho, avaliada após a digitação parar. */
QLineEdit[state="ok"] {{ border-color: {p.ok}; }}
QLineEdit[state="warn"] {{ border-color: {p.warn}; }}
QLineEdit[state="bad"] {{ border-color: {p.bad}; }}
/* Alvo de arrastar-e-soltar sob o cursor: estado "selecionado". */
QLineEdit[dragover="true"] {{
    border: 1px solid {p.accent_linha};
    background: {p.accent_soft};
}}

QComboBox {{
    background: {p.surface};
    color: {p.ink};
    border: 1px solid {p.border2};
    border-radius: 4px;
    padding: 4px 8px;
}}
QComboBox:hover {{ background: {p.surface2}; }}
QComboBox:focus {{ border-color: {p.accent_linha}; }}
QComboBox:disabled {{ background: {p.bg}; color: {p.ink3}; border-color: {p.border}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{ image: url("{chevron}"); width: 12px; height: 12px; }}
QComboBox::down-arrow:disabled {{ image: url("{chevron_off}"); }}
QComboBox QAbstractItemView {{
    background: {p.surface};
    color: {p.ink};
    border: 1px solid {p.border2};
    selection-background-color: {p.accent_soft};
    selection-color: {p.ink};
    outline: none;
    padding: 2px;
}}

QCheckBox {{ background: transparent; color: {p.ink2}; spacing: 8px; }}
QCheckBox:hover {{ color: {p.ink}; }}
QCheckBox:disabled {{ color: {p.ink3}; }}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border: 1px solid {p.border2};
    border-radius: 2px;
    background: {p.surface};
}}
QCheckBox::indicator:hover, QCheckBox::indicator:focus {{ border-color: {p.accent_linha}; }}
QCheckBox::indicator:checked {{
    background: {p.accent_linha};
    border-color: {p.accent_linha};
    image: url("{check}");
}}
QCheckBox::indicator:disabled {{ background: {p.bg}; border-color: {p.border}; }}
QCheckBox::indicator:checked:disabled {{
    background: {p.border2}; border-color: {p.border2};
}}

/* -------------------------------------------------------------- listas */
QTreeWidget, QListWidget {{
    background: {p.surface};
    alternate-background-color: {p.linha_alt};
    color: {p.ink};
    border: 1px solid {p.border2};
    border-radius: 4px;
    outline: none;
}}
QTreeWidget:focus, QListWidget:focus {{ border-color: {p.accent_linha}; }}
QTreeWidget::item, QListWidget::item {{
    padding: 4px 4px;
    border-bottom: 1px solid {p.border};
}}
QTreeWidget::item:selected, QListWidget::item:selected {{
    background: {p.accent_soft};
    color: {p.ink};
    border-left: 2px solid {p.accent_linha};
}}
QTreeWidget::item:hover:!selected, QListWidget::item:hover:!selected {{
    background: {p.surface2};
}}
QHeaderView::section {{
    background: {p.surface2};
    color: {p.ink2};
    border: none;
    border-right: 1px solid {p.border};
    border-bottom: 1px solid {p.border2};
    padding: 4px 8px;
    font-weight: 700;
    font-size: {_DICA};
}}

/* -------------------------------------------------------------- barras */
QProgressBar {{
    background: {p.surface2};
    border: 1px solid {p.border2};
    border-radius: 4px;
    height: 16px;
    text-align: center;
    color: {p.ink};
    font-family: {FONT_MONO};
    font-size: {_DICA};
}}
QProgressBar::chunk {{ background: {p.accent_linha}; border-radius: 3px; }}
QProgressBar[state="ok"]::chunk {{ background: {p.ok}; }}
QProgressBar[state="bad"]::chunk {{ background: {p.bad}; }}

QScrollBar:vertical {{ background: {p.bg}; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {p.border2}; border-radius: 4px; min-height: 24px; margin: 2px;
}}
QScrollBar::handle:vertical:hover {{ background: {p.ink3}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar:horizontal {{ background: {p.bg}; height: 12px; margin: 0; }}
QScrollBar::handle:horizontal {{
    background: {p.border2}; border-radius: 4px; min-width: 24px; margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{ background: {p.ink3}; }}

/* ------------------------------------------------------------ diversos */
QFrame[role="divider"] {{ background: {p.border}; max-height: 1px; border: none; }}
/* Rodapé: só informação — estado, contagem, versão. */
QFrame[role="footerBar"] {{
    background: {p.surface2}; border: none; border-top: 1px solid {p.border};
}}
/* Faixa de regra: agrupamento em surface2 com marca de 2px, sem card. */
QFrame[role="rule"] {{
    background: {p.surface2};
    border: none;
    border-left: 2px solid {p.accent_linha};
    border-radius: 0;
}}
QFrame[role="rule"] QLabel {{ background: transparent; color: {p.ink}; }}

QMenu {{
    background: {p.surface};
    color: {p.ink};
    border: 1px solid {p.border2};
    padding: 4px;
}}
QMenu::item {{ padding: 4px 24px 4px 12px; border-radius: 2px; }}
QMenu::item:selected {{ background: {p.accent_soft}; color: {p.ink}; }}
QMenu::item:disabled {{ color: {p.ink3}; }}
QMenu::separator {{ height: 1px; background: {p.border}; margin: 4px 8px; }}

QToolTip {{
    background: {p.ink};
    color: {p.surface};
    border: none;
    padding: 4px 8px;
}}
"""
