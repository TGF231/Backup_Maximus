# -*- coding: utf-8 -*-
"""GERADO por gerar/gerar_tema.py — não editar à mão."""
# Copiado sem alteração de MegUI 2.0.0 (gerar/saida/tema_tokens.py), o design
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
    bg="#F8F8F8",
    surface="#FFFFFF",
    surface2="#F0F1F2",
    sunken="#F8F8F8",
    linha_alt="#FAFAFA",
    somente_leitura="#F0F1F2",
    ink="#292A2E",
    ink2="#505258",
    ink3="#6B6E76",
    border="#DDDEE1",
    border2="#B7B9BE",
    accent="#7D0E0E",
    accent_hover="#5C0A0A",
    accent_linha="#7D0E0E",
    accent_soft="#FAF0F0",
    on_accent="#FFFFFF",
    ok="#15803D",
    warn="#A16207",
    bad="#D92D20",
    info="#1565C0",
)

ESCURO = Paleta(
    nome="escuro",
    bg="#1F1F21",
    surface="#242528",
    surface2="#2B2C2F",
    sunken="#18191A",
    linha_alt="#222326",
    somente_leitura="#2B2C2F",
    ink="#CECFD2",
    ink2="#A9ABAF",
    ink3="#96999E",
    border="#37383B",
    border2="#4B4D52",
    accent="#7D0E0E",
    accent_hover="#9B1616",
    accent_linha="#DC4A42",
    accent_soft="#3A1A1A",
    on_accent="#FFFFFF",
    ok="#4ADE80",
    warn="#FBBF24",
    bad="#FF8A8A",
    info="#60A5FA",
)


FONT_UI = '"Inter", sans-serif'
FONT_MONO = '"JetBrains Mono", monospace'
PESOS = [400, 600, 700]

ESCALA_TIPO = {"dica": {"px": 12, "pt": "9pt", "peso": 400, "altura": 1.4}, "corpo": {"px": 14, "pt": "10.5pt", "peso": 400, "altura": 1.5}, "titulo": {"px": 18, "pt": "13.5pt", "peso": 700, "altura": 1.3}, "destaque": {"px": 24, "pt": "18pt", "peso": 700, "altura": 1.2}}
ESPACO = {"meio": 2, "1": 4, "2": 8, "3": 12, "4": 16, "6": 24, "8": 32, "12": 48}
DENSIDADES = {"normal": {"multiplicador": 1.0, "alturaLinha": 32, "alturaControle": 36}, "compacta": {"multiplicador": 0.75, "alturaLinha": 24, "alturaControle": 28}}
RAIO = 6
RAIOS = {"base": 6, "campo": 8, "cartao": 12, "pilula": 999}
ELEVACAO = {"claro": {"elevada": "0 1px 1px #1E1F2140, 0 0 1px #1E1F214F", "janela": "0 8px 12px #1E1F2126, 0 0 1px #1E1F214F"}, "escuro": {"elevada": "0 1px 1px #01040480, 0 0 1px #01040480", "janela": "0 0 0 1px #BDBDBD1F, 0 8px 12px #0104045C, 0 0 1px 1px #01040480"}, "brilho": "rgba(125, 14, 14, 0.55)", "brilhoAcao": "0 14px 34px -10px", "brilhoAcaoHover": "0 18px 40px -10px", "fioDeLuz": "inset 0 1px 0 rgba(255, 255, 255, 0.18)", "subida": 2, "subidaCartao": 3}
LAYOUT = {"barraTitulo": 44, "faixaAbas": 44, "rodape": 28, "painelContexto": {"min": 280, "max": 360}, "aba": {"min": 120, "max": 220, "fechar": 16, "fecharAncora": "direita, sempre"}, "acaoFlutuante": {"tamanho": 48, "margem": 20, "reservaFim": 88, "ancora": "inferior-direita do conteudo", "nota": "A regiao rolavel reserva reservaFim no fim (tamanho + 2x margem do retrato) para a acao nunca cobrir a ultima linha."}, "conteudoMax": 1440, "tabelaHierarquica": {"modulo": "opcional — apenas onde a tabela e o conteudo principal e o dado tem hierarquia declarada", "faixaNivel": 28, "niveisMax": 5, "niveisVisiveis": 3, "abasPlanilha": 26, "marcaAtivo": 2, "marcaCor": "accentLinha", "nota": "Niveis acima da grade (modelo PVA); abas de planilha abaixo da grade (modelo Excel) listando os filhos da linha selecionada. Marca de acento em cima na aba de topo, embaixo na aba de planilha."}, "virada": {"razao": 1.0, "largura": 900, "regra": "o que vier primeiro"}}
MOVIMENTO = {"decorativo": "proibido", "instantaneo": 0, "feedback": 220, "painel": 220, "easing": "cubic-bezier(0.2, 0.7, 0.2, 1)"}
