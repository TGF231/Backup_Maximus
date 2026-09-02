"""Paleta e folha de estilo (QSS) da interface.

Segue o documento de design: neutros cinza-azulados frios (chrome de utilitário
Windows) com um único acento cobre — a cor do LED de atividade de disco. As
cores semânticas (ok/aviso/erro) são separadas do acento de propósito, para que
"atenção" nunca se confunda com "isto é clicável".

O tema escuro não é uma inversão automática: os neutros mantêm o viés azulado,
o acento sobe de saturação para continuar legível sobre fundo escuro, e o texto
dos botões de acento vira escuro, porque branco sobre laranja claro perde
contraste.
"""

from __future__ import annotations

from dataclasses import dataclass

# ------------------------------------------------------------------ fontes
# O design pede Archivo / IBM Plex Sans / IBM Plex Mono; no Windows caímos para
# as equivalentes locais, sempre com uma pilha de reserva declarada.
FONT_UI = '"Segoe UI", "Noto Sans", sans-serif'
FONT_MONO = '"Cascadia Mono", "Consolas", monospace'

# Geometria — larguras de rótulo, alturas de campo e margens — vive nos arquivos
# .ui, não aqui. Esta folha de estilo define apenas cor, borda, fonte e o
# espaçamento interno mínimo para o texto não encostar na borda; tamanho é
# assunto do Qt Designer.
#
# A exceção são formulários montados em tempo de execução, que não têm .ui onde
# morar: o assistente de nuvem constrói os campos a partir do que o rclone diz
# sobre cada serviço. Para eles alinharem com o resto da interface, a largura da
# coluna de rótulos precisa ser a mesma — e é melhor tê-la num lugar só do que
# repetida no código.
LABEL_WIDTH = 124


@dataclass(frozen=True)
class Palette:
    name: str
    bg: str            # fundo da janela
    surface: str       # painéis e campos
    surface_2: str     # faixas e rodapé
    sunken: str        # fundo de listas
    ink: str           # texto principal
    ink_2: str         # texto secundário
    ink_3: str         # dicas e rótulos apagados
    border: str
    border_2: str
    accent: str        # cobre: ações primárias e seleção
    accent_hover: str
    accent_soft: str
    on_accent: str     # texto sobre o acento
    ok: str
    warn: str
    bad: str


LIGHT = Palette(
    name="claro",
    bg="#F4F6F8",
    surface="#FFFFFF",
    surface_2="#E9EDF1",
    sunken="#FBFCFD",
    ink="#16202A",
    ink_2="#4A5A6A",
    ink_3="#74848F",
    border="#D2DAE2",
    border_2="#BAC5D0",
    accent="#C2410C",
    accent_hover="#9A3412",
    accent_soft="#FBEBE2",
    on_accent="#FFFFFF",
    ok="#15803D",
    warn="#A16207",
    bad="#B4232B",
)

DARK = Palette(
    name="escuro",
    bg="#0F1620",
    surface="#18212C",
    surface_2="#212C39",
    sunken="#131C25",
    ink="#E3E9EF",
    ink_2="#94A4B5",
    ink_3="#6E7F91",
    border="#2B3745",
    border_2="#3A4857",
    accent="#F97316",
    accent_hover="#FB923C",
    accent_soft="#2E1B10",
    on_accent="#1A1005",
    ok="#4ADE80",
    warn="#FBBF24",
    bad="#F87171",
)

_active: Palette = LIGHT


def current() -> Palette:
    return _active


def set_dark(dark: bool) -> Palette:
    """Troca a paleta ativa e devolve a nova."""
    global _active
    _active = DARK if dark else LIGHT
    return _active


def is_dark() -> bool:
    return _active is DARK


def stylesheet() -> str:
    """Folha de estilo completa, com os ícones desenhados em runtime."""
    from . import icons
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
    font-size: 9pt;
}}

/* ---------------------------------------------------------------- abas */
QTabWidget::pane {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: 4px;
    top: -1px;
}}
QTabBar::tab {{
    background: {p.sunken};
    color: {p.ink_3};
    border: 1px solid {p.border};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 7px 20px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {p.surface};
    color: {p.ink};
    font-weight: 600;
    border-top: 2px solid {p.accent};
    padding-top: 6px;
}}
QTabBar::tab:hover:!selected {{ color: {p.ink_2}; }}

/* ------------------------------------------------------------ rótulos
   Os papéis visuais vêm de uma propriedade dinâmica `role`, não do
   objectName: no Qt Designer o objectName precisa ser único por widget, e
   dezenas de rótulos compartilham o mesmo estilo. */
QLabel {{ background: transparent; color: {p.ink}; }}
QLabel[role="section"] {{
    color: {p.ink};
    font-weight: 700;
    font-size: 8pt;
    letter-spacing: 1px;
}}
QLabel[role="field"] {{ color: {p.ink_2}; }}
QLabel[role="hint"] {{ color: {p.ink_3}; font-size: 8pt; }}
QLabel[role="hintWarn"] {{ color: {p.warn}; font-family: {FONT_MONO}; font-size: 8pt; }}
QLabel[role="hintOk"] {{ color: {p.ok}; font-size: 8pt; }}
QLabel[role="hintBad"] {{ color: {p.bad}; font-size: 8pt; }}
QLabel[role="footer"] {{ color: {p.ink_3}; font-family: {FONT_MONO}; font-size: 8pt; }}
QLabel[role="bigStatus"] {{ font-size: 11pt; }}
QLabel[role="mono"] {{ font-family: {FONT_MONO}; color: {p.ink_3}; font-size: 8pt; }}

/* ------------------------------------------------------------- botões */
QPushButton {{
    background: {p.surface};
    color: {p.ink_2};
    border: 1px solid {p.border_2};
    border-radius: 4px;
    padding: 6px 14px;
    min-height: 16px;
}}
QPushButton:hover {{ background: {p.surface_2}; color: {p.ink}; }}
QPushButton:pressed {{ background: {p.border}; }}
QPushButton:disabled {{ background: {p.bg}; color: {p.ink_3}; border-color: {p.border}; }}

QPushButton[role="accent"] {{
    background: {p.accent};
    color: {p.on_accent};
    border: 1px solid {p.accent};
    font-weight: 600;
    padding: 8px 16px;
}}
QPushButton[role="accent"]:hover {{
    background: {p.accent_hover}; border-color: {p.accent_hover};
}}
QPushButton[role="accent"]:pressed {{ background: {p.accent_hover}; }}
QPushButton[role="accent"]:disabled {{
    background: {p.border_2}; border-color: {p.border_2}; color: {p.bg};
}}

QPushButton[role="tiny"] {{ padding: 5px 8px; }}

/* ------------------------------------------------------------- campos */
QLineEdit, QSpinBox {{
    background: {p.sunken};
    color: {p.ink};
    border: 1px solid {p.border_2};
    border-radius: 4px;
    padding: 4px 7px;
    selection-background-color: {p.accent_soft};
    selection-color: {p.ink};
}}
QLineEdit:focus, QSpinBox:focus {{ border-color: {p.accent}; }}
QLineEdit:disabled, QSpinBox:disabled {{
    background: {p.bg}; color: {p.ink_3}; border-color: {p.border};
}}
QLineEdit[mono="true"] {{ font-family: {FONT_MONO}; }}

/* Resultado da validação de caminho, avaliada após a digitação parar. */
QLineEdit[state="ok"] {{ border-color: {p.ok}; }}
QLineEdit[state="warn"] {{ border-color: {p.warn}; }}
QLineEdit[state="bad"] {{ border-color: {p.bad}; }}
/* Alvo de arrastar-e-soltar sob o cursor. */
QLineEdit[dragover="true"] {{
    border: 2px dashed {p.accent};
    background: {p.accent_soft};
}}

QComboBox {{
    background: {p.surface};
    color: {p.ink};
    border: 1px solid {p.border_2};
    border-radius: 4px;
    padding: 4px 7px;
}}
QComboBox:focus {{ border-color: {p.accent}; }}
QComboBox:disabled {{ background: {p.bg}; color: {p.ink_3}; border-color: {p.border}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ image: url("{chevron}"); width: 12px; height: 12px; }}
QComboBox::down-arrow:disabled {{ image: url("{chevron_off}"); }}
QComboBox QAbstractItemView {{
    background: {p.surface};
    color: {p.ink};
    border: 1px solid {p.border_2};
    selection-background-color: {p.accent_soft};
    selection-color: {p.ink};
    outline: none;
    padding: 2px;
}}

QCheckBox {{ background: transparent; color: {p.ink_2}; spacing: 7px; }}
QCheckBox:disabled {{ color: {p.ink_3}; }}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border: 1px solid {p.border_2};
    border-radius: 3px;
    background: {p.surface};
}}
QCheckBox::indicator:hover {{ border-color: {p.accent}; }}
QCheckBox::indicator:checked {{
    background: {p.accent};
    border-color: {p.accent};
    image: url("{check}");
}}
QCheckBox::indicator:disabled {{ background: {p.bg}; border-color: {p.border}; }}
QCheckBox::indicator:checked:disabled {{
    background: {p.border_2}; border-color: {p.border_2};
}}

/* -------------------------------------------------------------- listas */
QTreeWidget, QListWidget {{
    background: {p.sunken};
    color: {p.ink};
    border: 1px solid {p.border_2};
    border-radius: 4px;
    outline: none;
}}
QTreeWidget::item, QListWidget::item {{
    padding: 5px 3px;
    border-bottom: 1px solid {p.border};
}}
QTreeWidget::item:selected, QListWidget::item:selected {{
    background: {p.accent_soft};
    color: {p.ink};
    border-left: 3px solid {p.accent};
}}
QTreeWidget::item:hover:!selected, QListWidget::item:hover:!selected {{
    background: {p.surface_2};
}}
QHeaderView::section {{
    background: {p.surface_2};
    color: {p.ink_3};
    border: none;
    border-bottom: 1px solid {p.border_2};
    padding: 5px 6px;
    font-size: 8pt;
}}

/* -------------------------------------------------------------- barras */
QProgressBar {{
    background: {p.surface_2};
    border: 1px solid {p.border};
    border-radius: 8px;
    height: 16px;
    text-align: center;
    color: {p.ink_2};
    font-size: 8pt;
}}
QProgressBar::chunk {{ background: {p.accent}; border-radius: 7px; }}
QProgressBar[state="ok"]::chunk {{ background: {p.ok}; }}
QProgressBar[state="bad"]::chunk {{ background: {p.bad}; }}

QScrollBar:vertical {{ background: {p.bg}; width: 11px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {p.border_2}; border-radius: 5px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {p.ink_3}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar:horizontal {{ background: {p.bg}; height: 11px; margin: 0; }}
QScrollBar::handle:horizontal {{
    background: {p.border_2}; border-radius: 5px; min-width: 24px;
}}

/* ------------------------------------------------------------ diversos */
QFrame[role="divider"] {{ background: {p.border}; max-height: 1px; border: none; }}
QFrame[role="footerBar"] {{
    background: {p.surface_2}; border-top: 1px solid {p.border};
}}
QFrame[role="rule"] {{
    background: {p.accent_soft};
    border: none;
    border-left: 3px solid {p.accent};
    border-radius: 0 4px 4px 0;
}}
QFrame[role="rule"] QLabel {{ background: transparent; color: {p.ink}; }}

QToolTip {{
    background: {p.ink};
    color: {p.surface};
    border: none;
    padding: 5px 7px;
}}

QMessageBox {{ background: {p.bg}; }}
QMessageBox QLabel {{ color: {p.ink}; }}
QDialog {{ background: {p.bg}; }}
"""
