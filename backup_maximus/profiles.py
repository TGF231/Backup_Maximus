r"""Exportar e importar configurações, e conjuntos modelo.

Para que serve
--------------
Um técnico que instala o Backup Maximus em dez lojas do mesmo cliente configura
os mesmos conjuntos dez vezes. Um perfil exportado reduz isso a importar e
ajustar os caminhos. E quem troca de máquina, ou passa da versão portátil para
a instalada — que guarda os dados em `%LOCALAPPDATA%` —, leva a configuração
junto em vez de refazê-la.

O formato é o próprio `.ini` do programa
----------------------------------------
Não há formato novo: exportar é gravar um `backup_maximus.ini` noutro lugar, e
importar é lê-lo com o mesmo `Config.load`. Um formato próprio significaria um
segundo leitor para manter em dia, e o `.ini` tem a vantagem de ser legível e
editável — o técnico consegue trocar `C:\PDV` por `D:\PDV` no bloco de notas.

Segredos não viajam
-------------------
As senhas são cifradas com DPAPI, que usa a chave do **usuário e da máquina**
que as gravou. Levá-las num perfil não seria só arriscado: seria inútil, porque
não decifram no destino. Pior, os campos chegariam preenchidos e o técnico só
descobriria o problema na primeira madrugada. Então a exportação as remove, e
`campos_pendentes` diz exatamente o que precisa ser digitado de novo.
"""

from __future__ import annotations

import copy
import os
from dataclasses import dataclass, field
from enum import Enum

from . import logger, paths
from .config import BackupSet, Config

#: Extensão sugerida. É um INI de verdade, e ser legível é metade da utilidade.
EXTENSAO = ".ini"

#: Pasta dos modelos que acompanham o programa.
MODELOS = "modelos"


class ImportMode(Enum):
    """O que fazer com os conjuntos que já existem na máquina."""
    SUBSTITUIR = "substituir"     # descarta os atuais e usa só os do perfil
    MESCLAR = "mesclar"           # mesmo nome é atualizado, o resto é somado
    ACRESCENTAR = "acrescentar"   # nada é tocado; colisão de nome ganha sufixo

    @property
    def label(self) -> str:
        return {
            ImportMode.SUBSTITUIR: "Substituir os conjuntos atuais",
            ImportMode.MESCLAR: "Mesclar (atualiza os de mesmo nome)",
            ImportMode.ACRESCENTAR: "Acrescentar como novos",
        }[self]


@dataclass
class ProfileInfo:
    """O que dá para dizer sobre um perfil antes de importá-lo."""
    company: str = ""
    sets: list[str] = field(default_factory=list)
    items: int = 0
    tem_smtp: bool = False
    pendencias: list[str] = field(default_factory=list)

    @property
    def resumo(self) -> str:
        partes = [f"{len(self.sets)} conjunto(s)", f"{self.items} item(ns)"]
        if self.company:
            partes.insert(0, self.company)
        return " · ".join(partes)


# --------------------------------------------------------------- exportação
def sem_segredos(cfg: Config) -> Config:
    """Cópia da configuração sem nada que não sobreviva à troca de máquina.

    Some também o hash da senha da interface: importar um perfil não pode
    trocar a senha de quem já usa o programa nesta máquina.
    """
    limpa = copy.deepcopy(cfg)
    limpa.ui_password_hash = ""
    limpa.ui_password_salt = ""
    limpa.smtp.password_enc = ""
    for credencial in limpa.net_creds:
        credencial.password_enc = ""
    for bset in limpa.sets:
        for item in bset.items:
            item.password_enc = ""
    return limpa


def campos_pendentes(cfg: Config) -> list[str]:
    """O que precisará ser digitado de novo no destino, em português."""
    pendentes: list[str] = []
    if cfg.smtp.host:
        pendentes.append(f"Senha do e-mail ({cfg.smtp.user or cfg.smtp.host})")
    for credencial in cfg.net_creds:
        pendentes.append(f"Senha da rede ({credencial.unc_root})")
    for bset in cfg.sets:
        for item in bset.items:
            if item.type.is_database and item.user:
                pendentes.append(
                    f"Senha do banco ({bset.name} › {item.name})")
    return pendentes


def exportar(cfg: Config, destino: str, apenas_conjuntos: bool = False,
             nomes: list[str] | None = None) -> tuple[bool, str]:
    """Grava um perfil. `nomes` limita quais conjuntos vão junto."""
    perfil = sem_segredos(cfg)

    if nomes is not None:
        escolhidos = [s for s in perfil.sets if s.name in nomes]
        if not escolhidos:
            return False, "Nenhum dos conjuntos escolhidos foi encontrado."
        perfil.sets = escolhidos

    if apenas_conjuntos:
        # Um modelo de conjuntos não carrega empresa, e-mail nem SMTP: esses
        # são da loja, não do modelo.
        vazia = Config()
        vazia.sets = perfil.sets
        perfil = vazia

    try:
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
    except OSError as exc:
        return False, f"Não foi possível criar a pasta: {exc}"

    if not perfil.save(destino):
        return False, "Não foi possível gravar o arquivo."

    logger.info(f"Perfil exportado: {destino} ({len(perfil.sets)} conjunto(s))")
    return True, f"{len(perfil.sets)} conjunto(s) exportado(s) para {destino}"


# ---------------------------------------------------------------- leitura
def ler(caminho: str) -> Config | None:
    """Lê um perfil. None se o arquivo não existe ou não é um perfil válido."""
    cfg = Config.load(caminho)
    if cfg is None:
        return None
    # Um INI qualquer carrega sem erro e vem vazio; isso não é um perfil.
    if not cfg.sets and not cfg.company_name and not cfg.smtp.host:
        return None
    return cfg


def descrever(cfg: Config) -> ProfileInfo:
    return ProfileInfo(
        company=cfg.company_name,
        sets=[s.name for s in cfg.sets],
        items=sum(len(s.items) for s in cfg.sets),
        tem_smtp=bool(cfg.smtp.host),
        pendencias=campos_pendentes(cfg),
    )


# --------------------------------------------------------------- importação
def _nome_livre(nome: str, ocupados: set[str]) -> str:
    """`BKP` → `BKP (2)`, preservando o original."""
    if nome not in ocupados:
        return nome
    for n in range(2, 1000):
        candidato = f"{nome} ({n})"
        if candidato not in ocupados:
            return candidato
    return nome


def importar_conjuntos(destino: Config, perfil: Config,
                       modo: ImportMode) -> tuple[int, int]:
    """Traz os conjuntos do perfil. Devolve (acrescentados, atualizados)."""
    vindos = [copy.deepcopy(s) for s in perfil.sets]

    if modo is ImportMode.SUBSTITUIR:
        destino.sets = vindos
        return len(vindos), 0

    if modo is ImportMode.ACRESCENTAR:
        ocupados = {s.name for s in destino.sets}
        for bset in vindos:
            bset.name = _nome_livre(bset.name, ocupados)
            ocupados.add(bset.name)
            destino.sets.append(bset)
        return len(vindos), 0

    # MESCLAR: mesmo nome é substituído no lugar, para a ordem não embaralhar.
    por_nome = {s.name: i for i, s in enumerate(destino.sets)}
    acrescentados = atualizados = 0
    for bset in vindos:
        indice = por_nome.get(bset.name)
        if indice is None:
            destino.sets.append(bset)
            por_nome[bset.name] = len(destino.sets) - 1
            acrescentados += 1
        else:
            destino.sets[indice] = bset
            atualizados += 1
    return acrescentados, atualizados


def importar_gerais(destino: Config, perfil: Config) -> list[str]:
    """Traz as configurações que não são de conjunto. Devolve o que mudou.

    A senha da interface e o agendamento do lembrete ficam de fora de
    propósito: são desta máquina, não do perfil.
    """
    mudou: list[str] = []
    if perfil.company_name:
        destino.company_name = perfil.company_name
        mudou.append("empresa")
    if perfil.notify_email:
        destino.notify_email = perfil.notify_email
        mudou.append("e-mail de aviso")
    if perfil.smtp.host:
        destino.smtp.host = perfil.smtp.host
        destino.smtp.port = perfil.smtp.port
        destino.smtp.use_ssl = perfil.smtp.use_ssl
        destino.smtp.user = perfil.smtp.user
        destino.smtp.sender = perfil.smtp.sender
        mudou.append("servidor de e-mail (sem a senha)")
    if perfil.alert_timeout_hours:
        destino.alert_timeout_hours = perfil.alert_timeout_hours
        mudou.append("prazo do alerta")
    if perfil.net_creds:
        conhecidos = {c.unc_root.lower() for c in destino.net_creds}
        novos = [c for c in perfil.net_creds
                 if c.unc_root.lower() not in conhecidos]
        destino.net_creds.extend(copy.deepcopy(novos))
        if novos:
            mudou.append(f"{len(novos)} caminho(s) de rede (sem as senhas)")
    return mudou


# ------------------------------------------------------------------ modelos
@dataclass
class Modelo:
    nome: str
    caminho: str
    info: ProfileInfo


def pasta_modelos() -> str:
    """Onde ficam os modelos que acompanham o programa."""
    return os.path.join(paths.resource_dir(), MODELOS)


def listar_modelos() -> list[Modelo]:
    """Conjuntos prontos distribuídos com o programa.

    Um modelo é um perfil comum, só que embutido: mesma leitura, mesma
    importação. Assim não há um segundo caminho de código para manter.
    """
    pasta = pasta_modelos()
    if not os.path.isdir(pasta):
        return []

    encontrados: list[Modelo] = []
    for nome_arquivo in sorted(os.listdir(pasta)):
        if not nome_arquivo.lower().endswith(EXTENSAO):
            continue
        caminho = os.path.join(pasta, nome_arquivo)
        cfg = ler(caminho)
        if cfg is None:
            logger.warn(f"Modelo ignorado (nao e um perfil): {nome_arquivo}")
            continue
        rotulo = os.path.splitext(nome_arquivo)[0].replace("_", " ").strip()
        encontrados.append(Modelo(rotulo.capitalize(), caminho, descrever(cfg)))
    return encontrados
