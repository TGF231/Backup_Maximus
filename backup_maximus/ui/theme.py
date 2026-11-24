"""Folha de estilo (QSS) da interface, montada sobre os tokens do MegUI 2.0.

MegUI é a assinatura visual dos aplicativos da família. Desde a 2.0, a mesma
linguagem da página megstation.com: acento vermelho-escuro de marca igual nos
dois temas, cinzas neutros, botão e aba em pílula, cartão de 12px, campo de
8px, Inter na interface e JetBrains Mono nos números, três pesos (400/600/700).

Todo valor vem de `megui_tokens` — cor, tamanho de tipo, raio e altura de
controle. Nenhum literal de cor mora neste arquivo nem no resto da interface:
o que pinta em Python (relógio, pontos das listas, ícones) puxa de `current()`.

Três usos do acento, e a diferença importa:

* `accent` é **fundo**, e só da ação primária — um elemento por tela.
* `accent_linha` é o acento como **linha** (anel de foco, caixa marcada,
  seleção). No escuro o acento puro sobre a superfície dá 1,5:1, abaixo dos
  3:1 de indicador não textual; por isso ele sobe para tijolo só ali.
* `accent_soft` é **seleção**: o texto continua por cima, em `ink`.

O que o QSS do Qt não sabe fazer fica de fora, de propósito, em vez de ser
imitado: sombra (`box-shadow` não existe no QSS — a separação fica na linha
`border`), o brilho da ação primária e a subida de 2px no hover.
"""

from __future__ import annotations

import os

from .megui_tokens import (
    CLARO, DENSIDADES, ESCALA_TIPO, ESCURO, FONT_MONO, FONT_UI, RAIOS, Paleta,
)

#: Mantido como nome público: o resto da interface anota tipos com ele.
Palette = Paleta

# Largura da coluna de rótulos dos formulários montados em tempo de execução
# (o assistente de nuvem constrói os campos a partir do que o rclone diz sobre
# cada serviço). Os .ui usam a mesma; múltiplo de 4, como toda medida MegUI.
LABEL_WIDTH = 140

#: Fontes embarcadas — OFL, ver fonts/*-OFL.txt. São instâncias estáticas
#: (400/600/700) das variáveis do MegUI: o Qt não lê woff2, e escolhe o peso
#: com mais segurança em arquivo estático. Carregadas antes da primeira folha
#: de estilo: sem elas o Qt cai num substituto de outra largura e os campos
#: medidos no Designer cortam.
FONTES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FAMILIA_UI = "Inter"
FAMILIA_MONO = "JetBrains Mono"

_DICA = ESCALA_TIPO["dica"]["pt"]
_CORPO = ESCALA_TIPO["corpo"]["pt"]
_TITULO = ESCALA_TIPO["titulo"]["pt"]
_DESTAQUE = ESCALA_TIPO["destaque"]["pt"]

_RAIO = RAIOS["base"]         # caixa de marcar, item de menu
_CAMPO = RAIOS["campo"]       # campo, seleção
_CARTAO = RAIOS["cartao"]     # lista, painel, menu
# Densidade compacta: a aba Backups é um formulário denso de duas colunas, o
# caso que a densidade compacta do MegUI existe para atender. Só a altura
# muda; cor, raio e tipo são os mesmos da normal.
DENSIDADE = "compacta"
_CONTROLE = DENSIDADES[DENSIDADE]["alturaControle"]
# Pílula = metade da altura. O `999px` do CSS não serve aqui: o QSS do Qt não
# limita o raio à metade do retângulo e desenha a borda torta.
_PILULA = _CONTROLE // 2
# Altura do miolo para o controle fechar em `_CONTROLE` com borda de 1px e o
# padding vertical abaixo.
_PAD_V = 4
_MIOLO = _CONTROLE - 2 * _PAD_V - 2

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
    cima, cima_off = art["seta_cima"], art["seta_cima_off"]
    baixo, baixo_off = art["seta_baixo"], art["seta_baixo_off"]

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
   Aba = rótulo solto em ink2; a ativa é uma pílula em surface2 com contorno
   border e peso forte. Sem linha de acento. O conteúdo fica no fundo da
   janela, sem moldura: os painéis sobem dele. */
QTabWidget::pane {{ background: {p.bg}; border: none; top: 0; }}
QTabBar::tab {{
    background: transparent;
    color: {p.ink2};
    border: 1px solid transparent;
    border-radius: {_PILULA}px;
    padding: {_PAD_V}px 20px;
    min-height: {_MIOLO}px;
    margin: 4px 4px 8px 0;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    background: {p.surface2};
    color: {p.ink};
    border-color: {p.border};
    font-weight: 700;
}}
QTabBar::tab:hover:!selected {{ color: {p.ink}; background: {p.surface2}; }}
QTabBar::tab:selected:focus {{ border-color: {p.accent_linha}; }}

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
    border: 1px solid {p.accent_linha}; border-radius: {_CAMPO}px;
    font-family: {FONT_MONO}; font-size: {_DESTAQUE}; font-weight: 700;
    padding: 2px 0;
}}
QLabel[role="clockOff"] {{
    color: {p.ink2}; background: {p.surface2};
    border: 1px solid transparent; border-radius: {_CAMPO}px;
    font-family: {FONT_MONO}; font-size: {_DESTAQUE};
    padding: 2px 0;
}}

/* ------------------------------------------------------------- botões
   Botão é pílula na superfície, contorno border e peso médio; a cor cheia é
   só da ação primária. Desabilitado perde fundo e tinta, mas continua visível. */
QPushButton {{
    background: {p.surface};
    color: {p.ink};
    border: 1px solid {p.border};
    border-radius: {_PILULA}px;
    padding: {_PAD_V}px 16px;
    min-height: {_MIOLO}px;
    font-weight: 600;
}}
QPushButton:hover {{ border-color: {p.border2}; }}
QPushButton:pressed {{ background: {p.surface2}; border-color: {p.border2}; }}
QPushButton:focus {{ border-color: {p.accent_linha}; }}
QPushButton:disabled {{
    background: transparent; color: {p.ink3}; border-color: {p.border};
}}
QPushButton:checked {{
    background: {p.accent_soft}; color: {p.ink}; border-color: {p.accent_linha};
}}

/* A ação primária: o único elemento com acento na tela. */
QPushButton[role="accent"] {{
    background: {p.accent};
    color: {p.on_accent};
    border: 1px solid {p.accent_hover};
    font-weight: 700;
}}
QPushButton[role="accent"]:hover, QPushButton[role="accent"]:pressed {{
    background: {p.accent_hover}; border-color: {p.accent_hover};
}}
QPushButton[role="accent"]:focus {{ border-color: {p.accent_linha}; }}
QPushButton[role="accent"]:disabled {{
    background: transparent; color: {p.ink3}; border-color: {p.border};
}}

QPushButton[role="tiny"] {{ padding: {_PAD_V}px 8px; }}

/* Botão de ícone embutido em campo (relógio do horário): sem moldura em
   repouso, contorno no hover. O menu que ele abre já se anuncia pelo ícone —
   a seta extra do Qt só aperta o botão. */
QToolButton {{
    background: transparent; color: {p.ink2};
    border: 1px solid transparent; border-radius: {_RAIO}px; padding: 4px;
}}
QToolButton:hover {{ background: {p.surface2}; border-color: {p.border2}; }}
QToolButton:focus {{ border-color: {p.accent_linha}; }}
QToolButton::menu-indicator {{ image: none; width: 0; }}

/* ------------------------------------------------------------- campos
   Campo de uma linha = preenchimento surface2, sem contorno em repouso,
   cantos de 8px. Contorno border2 no hover, anel accent_linha no foco.
   O campo de várias linhas mantém o contorno: sem ele não se vê onde começa. */
QLineEdit, QSpinBox {{
    background: {p.surface2};
    color: {p.ink};
    border: 1px solid transparent;
    border-radius: {_CAMPO}px;
    padding: 2px 8px;
    min-height: {_MIOLO}px;
    selection-background-color: {p.accent_soft};
    selection-color: {p.ink};
}}
QPlainTextEdit, QTextEdit {{
    background: {p.sunken};
    color: {p.ink};
    border: 1px solid {p.border2};
    border-radius: {_CAMPO}px;
    padding: 6px 10px;
    selection-background-color: {p.accent_soft};
    selection-color: {p.ink};
}}
QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{ border-color: {p.border2}; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus,
QPlainTextEdit:focus, QTextEdit:focus {{ border-color: {p.accent_linha}; }}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{
    background: transparent; color: {p.ink3}; border-color: {p.border};
}}
QLineEdit:read-only {{ background: {p.somente_leitura}; }}
QLineEdit[mono="true"], QSpinBox {{ font-family: {FONT_MONO}; }}

/* Setas do campo numérico: dois botões sem moldura à direita, desenhados na
   tinta do tema — o desenho nativo é preto nos dois temas. */
/* O QLineEdit de dentro do campo numérico e da seleção editável herdaria a
   regra de campo acima (fundo, recuo, altura mínima) e esconderia o texto. */
QAbstractSpinBox QLineEdit, QComboBox QLineEdit {{
    background: transparent; border: none; padding: 0; min-height: 0;
}}
/* Todo campo numérico tem setas: com as setas estilizadas, o Qt encolhe a
   área de texto de um QSpinBox sem botões para 1px. */
QSpinBox {{ padding-right: 28px; }}
QSpinBox::up-button {{
    subcontrol-origin: border; subcontrol-position: top right;
    width: 24px; border: none; background: transparent;
    border-top-right-radius: {_CAMPO}px;
}}
QSpinBox::down-button {{
    subcontrol-origin: border; subcontrol-position: bottom right;
    width: 24px; border: none; background: transparent;
    border-bottom-right-radius: {_CAMPO}px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {p.border}; }}
QSpinBox::up-arrow {{ image: url("{cima}"); width: 10px; height: 10px; }}
QSpinBox::down-arrow {{ image: url("{baixo}"); width: 10px; height: 10px; }}
QSpinBox::up-arrow:disabled, QSpinBox::up-arrow:off {{ image: url("{cima_off}"); }}
QSpinBox::down-arrow:disabled, QSpinBox::down-arrow:off {{ image: url("{baixo_off}"); }}

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
    background: {p.surface2};
    color: {p.ink};
    border: 1px solid transparent;
    border-radius: {_CAMPO}px;
    padding: 2px 8px;
    min-height: {_MIOLO}px;
}}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{ image: url("{chevron}"); width: 12px; height: 12px; }}
QComboBox::down-arrow:disabled {{ image: url("{chevron_off}"); }}
QComboBox QAbstractItemView {{
    background: {p.surface};
    color: {p.ink};
    border: 1px solid {p.border};
    border-radius: {_CAMPO}px;
    selection-background-color: {p.accent_soft};
    selection-color: {p.ink};
    outline: none;
    padding: 4px;
}}

QCheckBox {{ background: transparent; color: {p.ink}; spacing: 8px; }}
QCheckBox:disabled {{ color: {p.ink3}; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {p.border2};
    border-radius: 4px;
    background: {p.surface};
}}
QCheckBox::indicator:hover, QCheckBox::indicator:focus {{ border-color: {p.accent_linha}; }}
QCheckBox::indicator:checked {{
    background: {p.accent_linha};
    border-color: {p.accent_linha};
    image: url("{check}");
}}
QCheckBox::indicator:disabled {{ background: transparent; border-color: {p.border}; }}
QCheckBox::indicator:checked:disabled {{
    background: {p.border2}; border-color: {p.border2};
}}

/* -------------------------------------------------------------- listas
   Lista é cartão: sobe do fundo em surface, contorno border, 12px. */
QTreeWidget, QListWidget {{
    background: {p.surface};
    alternate-background-color: {p.linha_alt};
    color: {p.ink};
    border: 1px solid {p.border};
    border-radius: {_CARTAO}px;
    padding: 4px;
    outline: none;
}}
QTreeWidget:focus, QListWidget:focus {{ border-color: {p.accent_linha}; }}
QTreeWidget::item, QListWidget::item {{
    padding: 6px 8px;
    border-radius: {_RAIO}px;
}}
QTreeWidget::item:selected, QListWidget::item:selected {{
    background: {p.accent_soft};
    color: {p.ink};
}}
QTreeWidget::item:hover:!selected, QListWidget::item:hover:!selected {{
    background: {p.surface2};
}}
QHeaderView::section {{
    background: {p.surface};
    color: {p.ink2};
    border: none;
    border-bottom: 1px solid {p.border};
    padding: 6px 8px;
    font-weight: 600;
    font-size: {_DICA};
}}

/* -------------------------------------------------------------- barras
   Trilho em pílula; o preenchimento é linha de progresso, accent_linha. */
QProgressBar {{
    background: {p.surface2};
    border: 1px solid {p.border};
    border-radius: 8px;
    min-height: 14px;
    max-height: 16px;
    text-align: center;
    color: {p.ink};
    font-family: {FONT_MONO};
    font-size: {_DICA};
}}
QProgressBar::chunk {{ background: {p.accent_linha}; border-radius: 7px; }}
QProgressBar[state="ok"]::chunk {{ background: {p.ok}; }}
QProgressBar[state="bad"]::chunk {{ background: {p.bad}; }}

QScrollBar:vertical {{ background: transparent; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {p.border2}; border-radius: 4px; min-height: 24px; margin: 2px;
}}
QScrollBar::handle:vertical:hover {{ background: {p.ink3}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 0; }}
QScrollBar::handle:horizontal {{
    background: {p.border2}; border-radius: 4px; min-width: 24px; margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{ background: {p.ink3}; }}

/* ------------------------------------------------------------ diversos */
QFrame[role="divider"] {{ background: {p.border}; max-height: 1px; border: none; }}
/* Rodapé: só informação — estado, contagem, versão. No fundo da janela. */
QFrame[role="footerBar"] {{
    background: {p.bg}; border: none; border-top: 1px solid {p.border};
}}
/* Faixa de regra: cartão em surface, 12px. */
QFrame[role="rule"] {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {_CARTAO}px;
}}
QFrame[role="rule"] QLabel {{ background: transparent; color: {p.ink}; }}

QMenu {{
    background: {p.surface};
    color: {p.ink};
    border: 1px solid {p.border};
    border-radius: {_CARTAO}px;
    padding: 6px;
}}
QMenu::item {{ padding: 6px 24px 6px 12px; border-radius: {_RAIO}px; }}
QMenu::item:selected {{ background: {p.accent_soft}; color: {p.ink}; }}
QMenu::item:disabled {{ color: {p.ink3}; }}
QMenu::separator {{ height: 1px; background: {p.border}; margin: 4px 8px; }}

QToolTip {{
    background: {p.ink};
    color: {p.surface};
    border: none;
    border-radius: {_RAIO}px;
    padding: 4px 8px;
}}
"""
