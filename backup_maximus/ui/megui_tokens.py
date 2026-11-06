# -*- coding: utf-8 -*-
"""GERADO por gerar/gerar_tema.py — não editar à mão."""
# Copiado sem alteração de MegUI 1.0.0 (gerar/saida/tema_tokens.py), o design
# system dos aplicativos da família. Valor novo entra em megui.tokens.json do
# MegUI e este arquivo é regerado — nunca editado aqui.

from dataclasses import dataclass


@dataclass(frozen=True)
class Paleta:
    nome: str
    bg: str
    surface: str
    surface2: str
    sunken: str
    linha_alt: str
    somente_leitura: str
    ink: str
    ink2: str
    ink3: str
    border: str
    border2: str
    accent: str
    accent_hover: str
    accent_linha: str
    accent_soft: str
    on_accent: str
    ok: str
    warn: str
    bad: str
    info: str


CLARO = Paleta(
    nome="claro",
    bg="#F4F6F8",
    surface="#FFFFFF",
    surface2="#E9EDF1",
    sunken="#FBFCFD",
    linha_alt="#F7F9FB",
    somente_leitura="#EFF2F5",
    ink="#16202A",
    ink2="#4A5A6A",
    ink3="#5B6974",
    border="#D2DAE2",
    border2="#BAC5D0",
    accent="#7D0E0E",
    accent_hover="#5C0A0A",
    accent_linha="#7D0E0E",
    accent_soft="#F3E8E3",
    on_accent="#FFFFFF",
    ok="#15803D",
    warn="#A16207",
    bad="#D92D20",
    info="#1565C0",
)

ESCURO = Paleta(
    nome="escuro",
    bg="#0F1620",
    surface="#18212C",
    surface2="#212C39",
    sunken="#131C25",
    linha_alt="#1C2632",
    somente_leitura="#222C38",
    ink="#E3E9EF",
    ink2="#94A4B5",
    ink3="#8796A9",
    border="#2B3745",
    border2="#3A4857",
    accent="#7D0E0E",
    accent_hover="#9B1616",
    accent_linha="#DC4A42",
    accent_soft="#2E1A16",
    on_accent="#FFFFFF",
    ok="#4ADE80",
    warn="#FBBF24",
    bad="#FF8A8A",
    info="#60A5FA",
)


FONT_UI = '"Atkinson Hyperlegible Next", sans-serif'
FONT_MONO = '"Atkinson Hyperlegible Mono", monospace'
PESOS = [400, 700]

ESCALA_TIPO = {"dica": {"px": 11, "pt": "8pt", "peso": 400, "altura": 1.35}, "corpo": {"px": 13, "pt": "9pt", "peso": 400, "altura": 1.45}, "titulo": {"px": 17, "pt": "12pt", "peso": 700, "altura": 1.25}, "destaque": {"px": 22, "pt": "16pt", "peso": 700, "altura": 1.2}}
ESPACO = {"meio": 2, "1": 4, "2": 8, "3": 12, "4": 16, "6": 24, "8": 32, "12": 48}
DENSIDADES = {"normal": {"multiplicador": 1.0, "alturaLinha": 24, "alturaControle": 28}, "compacta": {"multiplicador": 0.75, "alturaLinha": 20, "alturaControle": 24}}
RAIO = 4
LAYOUT = {"barraTitulo": 32, "faixaAbas": 32, "rodape": 24, "painelContexto": {"min": 280, "max": 360}, "aba": {"min": 120, "max": 220, "fechar": 16, "fecharAncora": "direita, sempre"}, "acaoFlutuante": {"tamanho": 40, "margem": 16, "reservaFim": 64, "ancora": "inferior-direita do conteudo", "nota": "A regiao rolavel reserva reservaFim no fim (tamanho + 2x margem do retrato) para a acao nunca cobrir a ultima linha."}, "conteudoMax": 1440, "tabelaHierarquica": {"modulo": "opcional — apenas onde a tabela e o conteudo principal e o dado tem hierarquia declarada", "faixaNivel": 28, "niveisMax": 5, "niveisVisiveis": 3, "abasPlanilha": 26, "marcaAtivo": 2, "marcaCor": "accentLinha", "nota": "Niveis acima da grade (modelo PVA); abas de planilha abaixo da grade (modelo Excel) listando os filhos da linha selecionada. Marca de acento em cima na aba de topo, embaixo na aba de planilha."}, "virada": {"razao": 1.0, "largura": 900, "regra": "o que vier primeiro"}}
MOVIMENTO = {"decorativo": "proibido", "instantaneo": 0, "feedback": 120, "painel": 180, "easing": "cubic-bezier(0.2, 0, 0, 1)"}
