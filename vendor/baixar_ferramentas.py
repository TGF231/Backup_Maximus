"""Baixa 7-Zip e rclone para dentro de vendor/, para irem junto no executável.

Rode uma vez antes de gerar o .exe:

    python vendor\\baixar_ferramentas.py

Por que não já vêm no repositório
---------------------------------
São binários de terceiros com licença própria. Baixá-los na hora, da origem
oficial, deixa claro de onde vieram e mantém o repositório só com código nosso.
O download é verificado: o script mostra o tamanho e o SHA-256 do que baixou,
para você conferir contra o que o site publica antes de distribuir.

Licenças (a obrigação de cumprir é de quem distribui o instalador)
-----------------------------------------------------------------
7-Zip  : LGPL 2.1+ . O 7za.exe do pacote "7-Zip Extra" pode ser redistribuído;
         inclua o texto da licença junto (o script o baixa também).
rclone : MIT.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import urllib.request
import zipfile

VENDOR = os.path.dirname(os.path.abspath(__file__))

#: Origem oficial de cada ferramenta. Atualize a versão quando quiser subir.
SOURCES = {
    "7zip": {
        "url": "https://www.7-zip.org/a/7z2408-extra.7z",
        "alt_url": "https://www.7-zip.org/a/7z2409-extra.7z",
        "note": ("Pacote '7-Zip Extra'. Se o .7z não puder ser aberto sem um "
                 "7-Zip já instalado, baixe manualmente e extraia 7za.exe "
                 "para vendor/7zip/."),
        "wanted": ("7za.exe", "License.txt", "LICENSE.txt", "readme.txt"),
    },
    "rclone": {
        "url": "https://downloads.rclone.org/rclone-current-windows-amd64.zip",
        "note": "Pacote oficial do rclone para Windows 64 bits.",
        "wanted": ("rclone.exe", "LICENSE.txt", "LICENSE", "COPYING"),
    },
}


def _already_present(*names: str) -> bool:
    """A ferramenta já está em vendor/, em qualquer subpasta?"""
    sys.path.insert(0, os.path.dirname(VENDOR))
    from backup_maximus.paths import find_vendor_tool
    return bool(find_vendor_tool(*names))


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, target: str) -> bool:
    print(f"  baixando {url}")
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": "BackupMaximus/vendor-fetch"})
        with urllib.request.urlopen(request, timeout=120) as response, \
                open(target, "wb") as out:
            shutil.copyfileobj(response, out)
    except Exception as exc:  # rede é imprevisível; a mensagem importa mais
        print(f"  FALHOU: {exc}")
        return False
    size = os.path.getsize(target)
    print(f"  ok — {size:,} bytes")
    print(f"  SHA-256: {_sha256(target)}")
    return True


def _extract_zip(archive: str, dest: str, wanted: tuple[str, ...]) -> list[str]:
    extracted: list[str] = []
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        for entry in zf.namelist():
            base = os.path.basename(entry)
            if base in wanted:
                with zf.open(entry) as src, open(os.path.join(dest, base), "wb") as out:
                    shutil.copyfileobj(src, out)
                extracted.append(base)
    return extracted


def fetch_rclone() -> bool:
    spec = SOURCES["rclone"]
    dest = os.path.join(VENDOR, "rclone")
    # A busca aceita qualquer arrumação de pasta, então uma extração manual
    # feita à mão já conta como pronta.
    if _already_present("rclone.exe"):
        print("rclone: já presente em vendor/, pulando.")
        return True

    print("rclone:")
    archive = os.path.join(VENDOR, "_rclone.zip")
    if not _download(spec["url"], archive):
        return False
    got = _extract_zip(archive, dest, spec["wanted"])
    os.unlink(archive)
    if "rclone.exe" not in got:
        print("  FALHOU: rclone.exe não encontrado no pacote.")
        return False
    print(f"  extraído para vendor/rclone/: {', '.join(got)}")
    return True


def fetch_sevenzip() -> bool:
    dest = os.path.join(VENDOR, "7zip")
    if _already_present("7za.exe", "7z.exe"):
        print("7-Zip: já presente em vendor/, pulando.")
        return True

    print("7-Zip:")
    print("  O pacote oficial vem em .7z, que precisa de um 7-Zip para abrir —")
    print("  o problema do ovo e da galinha. Duas saídas:")
    print()
    print("  a) Se você já tem 7-Zip instalado, o script usa ele agora.")
    print("  b) Senão, baixe manualmente https://www.7-zip.org/download.html")
    print("     (linha '7-Zip Extra'), extraia e copie 7za.exe e License.txt")
    print("     para vendor/7zip/.")
    print()

    seven = (shutil.which("7z")
             or next((p for p in (r"C:\Program Files\7-Zip\7z.exe",
                                  r"C:\Program Files (x86)\7-Zip\7z.exe")
                      if os.path.isfile(p)), ""))
    if not seven:
        print("  Nenhum 7-Zip instalado para extrair o pacote. Use a opção (b).")
        return False

    archive = os.path.join(VENDOR, "_7zextra.7z")
    if not (_download(SOURCES["7zip"]["url"], archive)
            or _download(SOURCES["7zip"]["alt_url"], archive)):
        return False

    os.makedirs(dest, exist_ok=True)
    import subprocess
    code = subprocess.run(
        [seven, "e", archive, f"-o{dest}", "-y", "7za.exe", "License.txt"],
        capture_output=True,
    ).returncode
    os.unlink(archive)

    if not os.path.isfile(os.path.join(dest, "7za.exe")):
        print(f"  FALHOU ao extrair (código {code}). Use a opção (b).")
        return False
    print("  extraído para vendor/7zip/: 7za.exe")
    return True


def main() -> int:
    print("=" * 62)
    print(" Backup Maximus — ferramentas de terceiros para vendor/")
    print("=" * 62)
    print()
    results = {"7-Zip": fetch_sevenzip(), "rclone": fetch_rclone()}
    print()
    print("-" * 62)
    for name, ok in results.items():
        print(f"  {name:<8} {'pronto' if ok else 'PENDENTE — veja acima'}")
    print()
    print("Confira o SHA-256 mostrado acima contra o publicado no site oficial")
    print("antes de distribuir o executável.")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
