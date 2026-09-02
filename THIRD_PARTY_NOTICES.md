# Avisos de terceiros

O Backup Maximus distribui e utiliza os componentes abaixo. Cada um mantém a
sua própria licença, que prevalece quanto a ele.

Como conferir o que está de fato empacotado:

```bash
python vendor/conferir.py
```

---

## Vinculado ao programa

### PySide6 / Qt 6 — LGPL v3

A interface gráfica usa PySide6, que vincula as bibliotecas do Qt 6. Ambos são
distribuídos sob a **GNU Lesser General Public License, versão 3**.

Isto impõe obrigações a **qualquer** distribuição do executável, independente da
licença escolhida para o código próprio deste projeto:

1. Declarar que o programa utiliza PySide6/Qt sob LGPLv3 — é o que este arquivo faz.
2. Fornecer o texto da licença junto com o programa.
3. Permitir que o usuário **substitua as bibliotecas Qt** por outra versão
   compatível, e volte a executar o programa.

O item 3 merece atenção: o `build_exe.bat` gera um executável único
(`--onefile`), no qual as bibliotecas ficam fundidas e não podem ser
substituídas pelo usuário. Para cumprir a LGPL na distribuição, publique
**também** a build em pasta (`--onedir`), em que os arquivos `.dll` do Qt ficam
separados e substituíveis, e informe onde obtê-la.

- Site: <https://www.qt.io/qt-for-python>
- Licença: <https://www.gnu.org/licenses/lgpl-3.0.html>
- Código-fonte do Qt: <https://download.qt.io/official_releases/qt/>

### Python — PSF License

- Site: <https://www.python.org/>
- Licença: <https://docs.python.org/3/license.html>

---

## Executados como processos separados

Os componentes abaixo são invocados como programas independentes, por linha de
comando. Isso **não cria obra derivada**, então as licenças copyleft deles não
se estendem ao Backup Maximus. A obrigação que resta é distribuir o texto de
licença de cada um, o que é feito em `vendor/<ferramenta>/License.txt`.

### rclone — MIT

Usado para o envio aos serviços de armazenamento em nuvem.

- Copyright © 2012 por Nick Craig-Wood e colaboradores
- Site: <https://rclone.org/>
- Licença: `vendor/rclone/License.txt` — <https://github.com/rclone/rclone/blob/master/COPYING>

A licença MIT exige que o aviso de copyright e o texto da licença acompanhem o
binário. O `build_exe.bat` empacota o `License.txt` junto com o executável.

### 7-Zip (7za.exe) — LGPL v2.1 ou superior

Usado para compactar a árvore de montagem quando disponível. Sem ele, o
programa recorre ao módulo `zipfile` do Python.

- Copyright © 1999-2026 Igor Pavlov
- Site: <https://www.7-zip.org/>
- Licença: `vendor/7zip/License.txt`

### Ferramentas nativas dos bancos de dados

Não são distribuídas com o Backup Maximus: o programa localiza as que já estão
instaladas na máquina, ou usa o caminho informado na configuração do item.

| Ferramenta | Origem | Licença |
|---|---|---|
| `gbak.exe` | Firebird | IPL / IDPL |
| `sqlcmd.exe` | Microsoft SQL Server | Licença Microsoft |
| `mysqldump.exe` | MySQL / MariaDB | GPL v2 / LGPL |

---

## Recursos

O ícone e a identidade visual do Backup Maximus são próprios.

---

## Como atualizar este arquivo

Ao trocar a versão de uma ferramenta em `vendor/`, confira o `License.txt`
correspondente: alguns projetos mudam de licença entre versões. O
`vendor/conferir.py` avisa quando um `License.txt` está faltando, mas não sabe
dizer se o conteúdo dele mudou.
