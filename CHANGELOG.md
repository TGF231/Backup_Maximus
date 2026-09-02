# Histórico de mudanças

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Versionamento [semântico](https://semver.org/lang/pt-BR/), com o significado
que faz sentido para um agente de backup instalado em máquina de cliente:

| Parte | Quando muda | O que o cliente sente |
|---|---|---|
| **MAIOR** | O `.ini` muda de um jeito que a versão anterior não lê | Não dá para voltar atrás sem reconfigurar |
| **MENOR** | Recurso novo; a configuração antiga continua valendo | Atualiza e segue |
| **CORREÇÃO** | Só conserto, sem recurso novo | Atualiza sem pensar |

A fonte única da versão é `__version__` em
[`backup_maximus/__init__.py`](backup_maximus/__init__.py). O `.spec`, o
relatório, o log e a barra de título leem de lá.

## Procedimento de lançamento

1. Mova o que está em **Não lançado** para uma seção nova com a versão e a data.
2. Ajuste `__version__` no `__init__.py`.
3. `python -m unittest discover -s tests -p "test_*.py"` e
   `python -m backup_maximus.ui.fitcheck` — os dois têm de passar.
4. `build_exe.bat`, e confira a versão em *Propriedades* do `.exe`.
5. Commit `versão 2.1.0`, tag `v2.1.0`, e anexe o `.exe` à release do GitHub.

A tag leva `v`; o `__version__`, não. É a convenção do Git e a do Python, cada
uma na sua casa.

---

## [Não lançado]

Nada ainda.

---

## [2.1.0] — 2026-09-01

Primeira versão publicada. As anteriores circularam só internamente.

### Adicionado

- **Envio à nuvem** pela API do serviço, via rclone: Google Drive, OneDrive,
  Dropbox, MEGA, S3, B2, SFTP, FTP e WebDAV. O envio é a última etapa do
  conjunto e é confirmado — o backup só conclui depois que o arquivo chega.
- **Cadastro de nuvem dentro do programa**, sem janela de console. Os campos
  de cada serviço vêm do próprio rclone, então acompanham a versão dele.
  Serviços com login no navegador abrem o consentimento no site do provedor.
- **Chave de API própria do aplicativo** para o Google Drive, com escopo
  `drive.file`. A chave compartilhada do rclone está sendo desativada pelo
  Google durante 2026; sem uma chave própria o cadastro do Drive tem prazo.
  Veja [`oauth_app.py`](backup_maximus/oauth_app.py).
- **Detector de aliases do Firebird**, lendo `aliases.conf` (2.5) e
  `databases.conf` (3+), com descoberta das instâncias pelo registro.
- **Lembrete de backup** em horário definido na interface, pelo Agendador de
  Tarefas do Windows — sem processo residente consumindo memória o dia todo.
- **7-Zip e rclone embutidos** no executável, com as licenças de cada um.
  `python vendor/conferir.py` confere o que será empacotado.
- Tema escuro, guardado na configuração.
- Atalhos de teclado, prévia da árvore em modo texto, verificação de espaço
  livre no destino com limpeza de backups antigos, e arrastar-e-soltar nos
  campos de caminho.
- Validação de caminho ao digitar, disparada 2 segundos depois da última tecla.
- `/version` na linha de comando, e a versão nas Propriedades do `.exe`.

### Modificado

- Interface reescrita em **PySide6 (Qt 6)**, com as telas em arquivos `.ui`
  editáveis no Qt Designer — a geometria saiu do código Python.
- Ao escolher o tipo de banco, servidor e porta são preenchidos com o padrão
  **sem** inativar os campos.

### Segurança

- Senhas cifradas com **DPAPI**, válidas só na máquina que as gravou.
- Senha da interface guardada como SHA-256 com salt aleatório, comparada com
  `secrets.compare_digest`.
- As senhas dos serviços de nuvem são cifradas pelo rclone (`--obscure`).

---

## [2.0.0] — interno

Reescrita completa em Python/PySide6 da versão original em C++, preservada em
[`src/`](src/). Mesmo modelo Conjunto → Itens e mesmo formato de `.ini`.

## [1.x] — interno

Versão em C++ que substituiu o `BKP.bat`.
