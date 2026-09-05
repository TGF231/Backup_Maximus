"""Onde estão as coisas — pasta do app, dados e ferramentas empacotadas.

Separado do resto porque o PyInstaller muda o chão embaixo dos pés: no .exe
empacotado o código roda de um diretório temporário (`sys._MEIPASS`), enquanto
a configuração e os logs precisam ficar ao lado do executável, onde o técnico
consegue achar.
"""

from __future__ import annotations

import os
import sys


def frozen() -> bool:
    """True quando rodando a partir do .exe do PyInstaller."""
    return getattr(sys, "frozen", False)


def install_dir() -> str:
    """Pasta onde o programa está instalado (onde o .exe mora)."""
    if frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_dir() -> str:
    """Pasta de onde ler recursos empacotados.

    No .exe é a pasta temporária que o PyInstaller extrai; rodando do
    código-fonte é a raiz do projeto.
    """
    bundle = getattr(sys, "_MEIPASS", "")
    return bundle if bundle else install_dir()


def vendor_dir() -> str:
    """Ferramentas de terceiros empacotadas (7-Zip, rclone).

    Procura primeiro ao lado do executável — assim dá para trocar a versão de
    uma ferramenta sem recompilar — e depois dentro do pacote.
    """
    beside = os.path.join(install_dir(), "vendor")
    if os.path.isdir(beside):
        return beside
    return os.path.join(resource_dir(), "vendor")


def arch_order() -> tuple[str, ...]:
    """Subpastas de arquitetura, da preferida para a menos preferida.

    Pacotes como o "7-Zip Extra" trazem a mesma ferramenta em x64, arm64 e
    32 bits. Pegar a errada funciona (o Windows roda 32 bits em 64), mas é mais
    lenta — e em ARM a de x64 roda emulada.
    """
    machine = (os.environ.get("PROCESSOR_ARCHITECTURE", "")
               or os.environ.get("PROCESSOR_ARCHITEW6432", "")).lower()
    if "arm" in machine:
        return ("arm64", "x64", "")
    if "64" in machine or "amd64" in machine:
        return ("x64", "", "arm64")
    return ("", "x64", "arm64")


def find_vendor_tool(*filenames: str) -> str:
    """Procura um executável dentro de vendor/, em qualquer arrumação.

    Aceita tanto a pasta arrumada (`vendor/7zip/7za.exe`) quanto o pacote
    oficial extraído inteiro (`vendor/7za/x64/7za.exe`) — quem baixa a ferramenta
    não deveria ter que adivinhar o nome de pasta que o programa espera.
    """
    root = vendor_dir()
    if not os.path.isdir(root):
        return ""

    try:
        subdirs = [d.path for d in os.scandir(root) if d.is_dir()]
    except OSError:
        return ""

    # Primeiro na raiz de vendor/ e nas subpastas diretas, respeitando a
    # arquitetura; só depois uma varredura completa, como último recurso.
    for arch in arch_order():
        for base in [root] + subdirs:
            directory = os.path.join(base, arch) if arch else base
            for name in filenames:
                candidate = os.path.join(directory, name)
                if os.path.isfile(candidate):
                    return candidate

    for current, _dirs, files in os.walk(root):
        for name in filenames:
            if name in files:
                return os.path.join(current, name)
    return ""


def bundle_files() -> list[tuple[str, str]]:
    """Arquivos de terceiros a embutir no .exe: (origem, subpasta no pacote).

    Leva só o binário da arquitetura certa, e não a pasta inteira: o pacote
    oficial do 7-Zip traz três arquiteturas mais um plugin do Far Manager, e o
    rclone sozinho já pesa 80 MB. Cada MB desnecessário aqui é MB no executável
    que alguém vai copiar por rede para a máquina do cliente.
    """
    files: list[tuple[str, str]] = []

    seven = find_vendor_tool("7za.exe", "7z.exe")
    if seven:
        files.append((seven, "vendor/7zip"))
        # A LGPL do 7-Zip exige distribuir o texto da licença junto.
        license_file = _license_beside(seven, _LICENSE_NAMES)
        if license_file:
            files.append((license_file, "vendor/7zip"))

    rclone = find_vendor_tool("rclone.exe")
    if rclone:
        files.append((rclone, "vendor/rclone"))
        license_file = _license_beside(rclone, _LICENSE_NAMES)
        if license_file:
            files.append((license_file, "vendor/rclone"))

    return files


#: Nomes usados por projetos diferentes para o mesmo arquivo.
_LICENSE_NAMES = ("License.txt", "LICENSE.txt", "LICENSE", "license.txt",
                  "COPYING", "COPYING.txt", "LICENSE.md")


def _license_beside(tool: str, names: tuple[str, ...]) -> str:
    """Procura o arquivo de licença junto do executável ou na pasta acima."""
    directory = os.path.dirname(tool)
    for base in (directory, os.path.dirname(directory)):
        for name in names:
            candidate = os.path.join(base, name)
            if os.path.isfile(candidate):
                return candidate
    return ""


#: Marcador criado pelo instalador ao lado do .exe. Sua presença diz que o
#: programa foi instalado (tipicamente em Program Files, onde não se escreve) e
#: que os dados pertencem ao perfil do usuário.
INSTALLED_MARKER = "instalado.flag"

#: Marcador oposto, para quem quer a versão portátil num pen drive mesmo com o
#: programa numa pasta gravável. Vence o automático.
PORTABLE_MARKER = "portatil.flag"

#: Nome da pasta em %LOCALAPPDATA%.
APPDATA_FOLDER = "Backup Maximus"


def _writable(directory: str) -> bool:
    """Se dá para gravar ali de verdade — testando, não deduzindo.

    `os.access(W_OK)` mente em vários casos no Windows: diz que sim para pastas
    protegidas pelo UAC e para a virtualização de Program Files. Um arquivo
    temporário é a única resposta confiável.
    """
    probe = os.path.join(directory, ".bm_write_test")
    try:
        with open(probe, "w", encoding="ascii") as fh:
            fh.write("x")
        os.unlink(probe)
        return True
    except OSError:
        return False


def local_appdata_dir() -> str:
    r"""%LOCALAPPDATA%\Backup Maximus, criada se preciso."""
    base = (os.environ.get("LOCALAPPDATA", "").strip()
            or os.path.join(os.path.expanduser("~"), "AppData", "Local"))
    path = os.path.join(base, APPDATA_FOLDER)
    os.makedirs(path, exist_ok=True)
    return path


def app_data_dir() -> str:
    r"""Onde ficam configuração, logs e relatórios.

    A ordem existe para não quebrar quem já usa o programa hoje. Um cliente com
    a versão portátil numa pasta gravável continua com tudo ao lado do .exe; só
    quem instalar pelo instalador é levado para o AppData.

    1. `BM_HOME`   — decisão explícita de quem administra a máquina.
    2. `portatil.flag` ao lado do .exe — decisão explícita de quem usa.
    3. `instalado.flag` ao lado do .exe — escrito pelo instalador.
    4. Pasta do programa, se der para gravar nela — o comportamento de sempre.
    5. `%LOCALAPPDATA%\Backup Maximus` — o programa está em lugar protegido.
    """
    override = os.environ.get("BM_HOME", "").strip()
    if override:
        os.makedirs(override, exist_ok=True)
        return os.path.abspath(override)

    home = install_dir()
    if os.path.isfile(os.path.join(home, PORTABLE_MARKER)):
        return home
    if os.path.isfile(os.path.join(home, INSTALLED_MARKER)):
        return local_appdata_dir()
    if _writable(home):
        return home
    return local_appdata_dir()
