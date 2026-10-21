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

A release é automática: o workflow `.github/workflows/release.yml` publica
sozinho quando o código chega ao `main` com uma versão que ainda não tem tag.
Não existe passo manual de empacotar nem de anexar arquivo.

1. Mova o que está em **Não lançado** para uma seção nova com a versão e a data.
2. Ajuste `__version__` no `__init__.py`.
3. `python release_info.py --conferir` — acusa versão sem notas, formato
   inválido e conteúdo esquecido em "Não lançado".
4. Commit e push para o `main`.

O workflow então roda os testes e o `fitcheck`, baixa 7-Zip e rclone, gera os
dois formatos, audita o pacote (reprova se a PyQt6 aparecer) e cria a tag com
as notas desta seção. Se algum passo falhar, nada é publicado.

Para republicar sem um commit novo, use *Run workflow* na aba Actions.

A tag leva `v`; o `__version__`, não. É a convenção do Git e a do Python, cada
uma na sua casa.

---

## [Não lançado]

### Corrigido

- **A senha do Firebird passa a ser `masterkey` quando o campo está vazio.**
  SYSDBA/masterkey é o par de fábrica, e exigir que fosse digitado significava
  backup que falha de madrugada por um campo em branco — sendo que o campo em
  branco já era a intenção de "usar o padrão". Vale para o `gbak` e o `gstat`.
- **"Manter últimos" e "Aguardar segundos" pareciam não funcionar.** O
  primeiro fica desligado fora do modo Completo (no Incremental há um zip só,
  sobrescrito), e o segundo não tinha efeito nenhum sem uma unidade escolhida
  — mas ficava editável, convidando a configurar algo que nunca seria lido.
  Agora cada um liga quando produz efeito, e a dica diz o motivo quando não.
- **O campo de horário do lembrete não aceitava digitação.** O `QTimeEdit`
  edita por seção: clicar e digitar não funciona, nem selecionar tudo. Virou
  um campo comum, que aceita `8`, `800`, `8:0` ou `0800`.
- O botão ao lado abre um **mostrador de relógio de verdade**: o primeiro
  clique escolhe a hora e o mostrador passa sozinho para os minutos, o
  segundo fecha. As 24 horas ocupam dois anéis — de fora `00` e `13`–`23`, de
  dentro `12` e `1`–`11` —, então o ponteiro aponta para o mesmo lugar de um
  relógio de parede e a volta da tarde fica por fora.
- O rótulo "Alertar se sem backup há" aparecia cortado. A coluna de rótulos
  das Configurações estava a 1 px do limite no vizinho mais longo; passou a
  ter folga real.

---

## [2.2.1] — 2026-10-21

Correção urgente: a 2.2.0 instalava mas **não abria**.

### Corrigido

- **O programa não iniciava depois de instalado**, falhando ao carregar a
  primeira tela com `No module named 'backup_maximus.ui.generated'`. Os
  formulários da interface são carregados por `importlib` a partir do nome do
  `.ui`, e o PyInstaller não segue import dinâmico: o pacote inteiro ficou de
  fora do executável. O `.spec` passa a declará-los em `hiddenimports`.
- **Os acentos chegavam corrompidos às notas da release.** O passo gravava com
  `python … > NOTAS.md`, e no Windows o stdout redirecionado usa cp1252 — daí
  `versão` virar `vers├úo`. O `release_info.py` ganhou `--saida`, que grava o
  arquivo em UTF-8 sem passar pelo shell.

### Adicionado

- **`vendor/testar_pacote.py`, executado no build e no workflow**: roda o
  executável gerado e verifica que ele abre e carrega os formulários. A
  auditoria existente olha o conteúdo do pacote; esta olha o comportamento, e
  a distinção custou uma release — a 2.2.0 foi empacotada, auditada, assinada
  e instalada sem que nada tentasse executá-la.
- Flag `/autoteste`, que carrega todos os formulários e sai sem abrir janela
  nem tocar na configuração. É o que o teste de fumaça usa.

---

## [2.2.0] — 2026-10-13

Primeira release publicada com artefatos. A 2.1.0 recebeu tag antes de o
workflow de release existir, então não tem instalador nem executável anexados.

### Adicionado

- **Instalador do Windows** (Inno Setup), publicado na release junto com a
  versão portátil. Instala em Program Files, cria os atalhos, registra o
  programa em "Aplicativos instalados" e remove a tarefa do lembrete ao
  desinstalar. O que ele instala é a build **em pasta**: isso cumpre a LGPLv3
  da Qt (DLLs substituíveis) e evita extrair 130 MB a cada execução, num
  programa chamado toda madrugada pelo Agendador de Tarefas.
- **Configuração em `%LOCALAPPDATA%` quando instalado.** A escolha segue o
  DPAPI, que cifra as senhas no escopo do usuário: uma pasta compartilhada
  guardaria segredos que nenhum outro login consegue decifrar. Quem usa a
  versão portátil não muda de comportamento — a cascata de
  `paths.app_data_dir` só desvia quando existe o `instalado.flag` ou quando a
  pasta do programa não aceita gravação.
- **Exportar e importar configurações**, na aba Configurações. Um técnico que
  instala em dez lojas configura uma vez e importa nas outras. O formato é o
  próprio `.ini` do programa: legível, editável, sem um segundo leitor para
  manter em dia.
- **Conjuntos modelo** distribuídos com o programa (PDV Expresso, servidor
  Firebird, arquivos e pastas). São perfis comuns, embutidos — mesma leitura,
  mesma importação, nenhum caminho de código separado.
- **Release automática** pelo GitHub Actions: quando o `main` recebe uma versão
  que ainda não tem tag, o workflow testa, empacota nos três formatos, audita o
  pacote e publica. O gatilho é a ausência da tag, não a edição do arquivo —
  assim reexecutar não duplica release e um comentário alterado não dispara
  build.
- `release_info.py`, fonte única da versão e das notas para o workflow, com
  `--conferir` que recusa publicar sem seção no CHANGELOG.
- **Tela Sobre**, com versão, licenças de terceiros e diagnóstico copiável. É o
  aviso visível que a LGPLv3 da Qt exige, e poupa o suporte de pedir dados que
  o cliente digitaria errado.
- `vendor/auditar_pacote.py`, executado no fim do build: reprova o pacote se
  encontrar biblioteca copyleft forte ou se faltar a licença de algum
  componente embutido.
- Textos da LGPLv3 e da GPLv3 em `licenses/`, embutidos na distribuição — o
  wheel da PySide6 não os traz.
- Build em pasta (`--onedir`) além do executável único, para cumprir o direito
  de substituir a biblioteca Qt que a LGPLv3 assegura.
- Teste que exige que todo `designer/*.ui` esteja registrado em `forms.FORMS`.

### Modificado

- **Aguardar unidade virou um seletor fechado**, sem digitação. Lista as
  unidades com rótulo do volume, tipo e espaço livre — a letra sozinha não
  distingue dois pen drives espetados. As unidades são reescaneadas a cada
  abertura da lista.
  - A unidade configurada continua listada mesmo **ausente**, marcada como tal:
    configurar com o pen drive fora é o caso normal, e sem isso abrir a tela
    apagaria a configuração do conjunto em silêncio.
  - Caminhos **UNC entram pela aba Rede** e passam a aparecer na lista. É onde
    a credencial já está cadastrada — esperar por um caminho de rede sem poder
    acessá-lo só produziria falha na hora do backup.
- O botão **Nuvem…** deixou de abrir o cadastro por API e passou a listar as
  pastas sincronizadas da máquina, marcando o envio direto como **EM BREVE**.
  O interruptor é único (`cloud.ENVIO_POR_API`) e o assistente do rclone segue
  testado, dormente, para voltar quando houver domínio verificado.

### Corrigido

- O `build_exe.bat` repetia as opções na linha de comando e ignorava o `.spec`,
  que existia sem efeito nenhum. Agora o `.spec` é a fonte única.
- **PyQt6 (GPLv3) não estava excluída do empacotamento.** Ela costuma estar
  instalada ao lado da PySide6 na máquina de desenvolvimento; se um hook a
  arrastasse para o pacote, o produto distribuído herdaria a GPL.
- A tela "Sobre" não era compilada por falta de registro em `forms.FORMS`, e o
  build informava sucesso — daí o teste novo.
- **O seletor de unidade podia estourar a largura do formulário.** Um
  `QComboBox` se dimensiona pelo item mais largo, e os itens trazem caminho,
  rótulo do volume e espaço livre — um volume de nome comprido empurraria os
  campos para fora da janela. A caixa fechada passa a ter largura fixa e a
  lista aberta continua larga, que é onde se lê o rótulo.
- **A verificação de layout media com a fonte errada em ambiente sem tela.**
  Sem banco de fontes, o Qt substitui a Segoe UI por uma Sans Serif quase o
  dobro da largura, e a medição reprovava um layout correto. Agora o
  `fitcheck` detecta a ausência e recusa medir, em vez de dar um veredito
  sobre uma fonte que o programa nunca usa.
- **A auditoria do pacote nunca verificou as licenças do vendor.** Desde o
  PyInstaller 6, a build em pasta guarda os dados sob `_internal/`, e a
  verificação comparava com `startswith("vendor/…")` — que nunca casava. Um
  pacote sem o aviso MIT do rclone seria aprovado em silêncio.
- **O download do 7-Zip apontava para versões removidas do site oficial.** O
  7-Zip apaga os pacotes antigos ao lançar uma versão nova, então a URL fixa
  envelheceu e o build quebrou sem ninguém ter mexido em nada — foi o que
  derrubou a primeira tentativa desta release. Agora a versão é descoberta na
  página oficial e ordenada da mais nova para a mais velha, com uma lista
  conhecida como plano B.
- O UNC cadastrado na aba Rede só aparecia no seletor depois de fechar e
  reabrir o programa: a lista era copiada uma vez, em vez de lida a cada
  abertura.

### Segurança

- **Nenhum segredo sai num perfil exportado**: senhas de banco, de rede e do
  e-mail são removidas, e a tela lista o que precisará ser redigitado. Não é só
  cautela — elas não decifrariam no destino, e campos preenchidos que não
  funcionam só apareceriam como falha na primeira madrugada.
- O hash da senha da interface também não viaja: importar um perfil não pode
  trocar a senha de quem já usa a máquina.

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
