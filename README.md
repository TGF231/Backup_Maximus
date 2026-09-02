# Backup Maximus

Aplicação desktop Windows (Python 3.11+ / PySide6) que substitui o `BKP.bat`: monta a mesma
estrutura de pastas, junta várias origens (bancos, configurações, XMLs, logs) em **um único
arquivo .zip**, espera o pen drive aparecer, e tem tela de configuração protegida por senha
em vez de edição manual de script.

---

## Índice

1. [O modelo: Conjunto → Itens](#o-modelo-conjunto--itens)
2. [Migrando do BKP.bat](#migrando-do-bkpbat)
3. [Requisitos](#requisitos)
4. [Instalação](#instalação)
5. [Primeira execução](#primeira-execução)
6. [Configurando um conjunto](#configurando-um-conjunto)
7. [Modos de execução](#modos-de-execução)
8. [Agendamento e alerta de falha](#agendamento-e-alerta-de-falha)
9. [Onde ficam os arquivos](#onde-ficam-os-arquivos)
10. [Segurança](#segurança)
11. [Armazenamento em nuvem](#armazenamento-em-nuvem)
12. [Ferramentas embutidas no executável](#ferramentas-embutidas-no-executável)
13. [Detectar bancos do Firebird](#detectar-bancos-do-firebird)
14. [Lembrete de backup](#lembrete-de-backup)
15. [Editando as telas no Qt Designer](#editando-as-telas-no-qt-designer)
16. [Testes](#testes)
17. [Solução de problemas](#solução-de-problemas)
18. [Arquitetura do código](#arquitetura-do-código)

---

## O modelo: Conjunto → Itens

A ideia central é a mesma do `.bat`: existe uma **pasta de montagem** (o seu `C:\BACKUP`),
várias origens diferentes despejam conteúdo nela em subpastas organizadas, e no final a
árvore inteira vira **um zip só** no pen drive.

```
CONJUNTO "BKP_MAXIMUS"          →  gera 1 arquivo .zip
├── pasta de montagem: C:\BACKUP
├── destino do zip:    U:\
├── aguardar unidade:  U:\
│
├── ITEM  PDV Expresso (banco)   Firebird PDVEXPRESSO  → PDVEXPRESSO\PDVEXPRESSO.FBK
├── ITEM  Config NFC-e           nfceConfig.ini        → PDVEXPRESSO\
├── ITEM  XMLs destinatário      pasta (espelhada)     → PDVEXPRESSO\Arquivos\XmlDestinatario\
└── ITEM  Logs de transmissão    pasta (espelhada)     → PDVEXPRESSO\Arquivos\Log\

resultado:  U:\BKP_MAXIMUS26082026181429.zip
            └── BACKUP\PDVEXPRESSO\...  (a árvore inteira)
```

Cada item declara **em qual subpasta do zip** ele cai. A pasta de montagem persiste entre
execuções: na segunda vez, só o que mudou é recopiado — é o mesmo ganho do `ROBOCOPY /MIR`,
mas sem depender do robocopy.

### Suporte por tipo de item

| Tipo | Como o conteúdo é obtido |
|---|---|
| Firebird | `gbak -b -g -t` (backup transportável, sem disparar garbage collection) |
| SQL Server | `sqlcmd` executando `BACKUP DATABASE … WITH COPY_ONLY, INIT, CHECKSUM` |
| MySQL / MariaDB | `mysqldump --single-transaction --routines --triggers --events` |
| DBF | cópia dos arquivos `.dbf` |
| Arquivo/Pasta | cópia incremental, com espelhamento opcional (`/MIR`) |

Origem e destino aceitam caminho local, unidade removível ou UNC (`\\servidor\pasta`).

---

## Migrando do BKP.bat

Correspondência direta entre o que o script fazia e onde isso é configurado agora:

| No `BKP.bat` | No Backup Maximus |
|---|---|
| `:VERIFICA_UNIDADE` / `if exist U:\` em laço | Campo **Aguardar unidade** = `U:\` no conjunto |
| `IF NOT EXIST … mkdir` para montar a árvore | Automático: a subpasta de cada item é criada sozinha |
| `GBAK -B -V -user SYSDBA … LOCALHOST:PDVEXPRESSO` | Item tipo **Firebird**, origem `PDVEXPRESSO`, servidor `LOCALHOST` |
| `ROBOCOPY … nfceConfig.ini "C:\Backup\PDVEXPRESSO"` | Item **Arquivo/Pasta**, subpasta `PDVEXPRESSO` |
| `ROBOCOPY … XmlDestinatario … /MIR` | Item **Arquivo/Pasta** com **Espelhar (/MIR)** marcado |
| `WinRAR a -agDDMMYYYYHHMM -afzip U:\BKP_MAXIMUS "C:\BACKUP"` | Conjunto: nome `BKP_MAXIMUS`, destino `U:\`, modo **Completo** |
| Blocos `echo` com barra de progresso ASCII | Janela de progresso nativa, com tempo decorrido |
| Comentar linhas com `REM` para cliente sem PDV | Desmarcar **Item habilitado** |
| Senha `masterkey` em texto plano no script | Senha cifrada com DPAPI no INI |

O nome do zip segue o mesmo padrão do `-ag` do WinRAR: `BKP_MAXIMUS` + `DDMMYYYYHHMMSS`.

**Vantagens práticas sobre o script:**

- Segunda execução é muito mais rápida — o `.FBK` de 60 MB não é recopiado se não mudou
- O relatório diz item por item o que aconteceu (`1 copiados, 2 iguais, 1 removidos`)
- Falha de um item não derruba o backup inteiro: o zip sai com o resto e o erro fica no log
- Alerta por e-mail se o backup não rodar no prazo
- Configuração viaja dentro do próprio zip — reinstalar não perde o que foi configurado

O script mandava toda a saída do `gbak` e do `ROBOCOPY` para `> NUL`, então o desenho ASCII
sempre chegava em *BACKUP REALIZADO COM SUCESSO*, tendo funcionado ou não. Aqui cada item
reporta seu resultado no relatório, no log e na cor da barra de progresso.

---

## Requisitos

**Para executar (a partir do .exe):** nada além do Windows 8.1 ou superior, x64.
O executável gerado pelo `build_exe.bat` já embute o Python e o Qt.

**Para executar a partir do código-fonte:**

- Python 3.11 ou superior
- `pip install PySide6`

**Opcionais, conforme o uso:**

- **7-Zip** — acelera bastante árvores grandes. Sem ele a aplicação usa o compactador
  nativo do Python (`zipfile`), que funciona sozinho, sem depender de nada externo.
- Ferramentas nativas dos bancos que você usar:
  - Firebird → `gbak.exe` (autodetecta `C:\Program Files\Firebird\Firebird_2_5\bin` e similares)
  - SQL Server → `sqlcmd.exe`
  - MySQL/MariaDB → `mysqldump.exe`

  Se estiverem fora do lugar padrão, informe o caminho no campo **Ferramenta** do item.

---

## Instalação

### Opção A — executável único (recomendado para o cliente)

```bash
build_exe.bat
```

Gera `dist\BackupMaximus.exe`. Copie para a pasta definitiva, por exemplo
`C:\BackupMaximus\`. Não exige Python na máquina do cliente.

### Opção B — direto do código-fonte

```bash
pip install PySide6
```

Depois execute `BackupMaximus.pyw` (extensão `.pyw` = sem janela de console).

> Configuração, logs e relatórios ficam **ao lado do executável**. Escolha uma pasta com
> permissão de escrita — evite `C:\Program Files` sem ajustar permissões, ou defina a
> variável de ambiente `BM_HOME` apontando para uma pasta gravável.

---

## Primeira execução

Ao abrir pela primeira vez, a aplicação pede a criação de uma senha (mínimo 4 caracteres,
digitada duas vezes). Essa senha protege a tela de configuração dali em diante.

A senha é guardada apenas como hash SHA-256 com salt aleatório — não há como recuperá-la.
Se for perdida, apague `backup_maximus.ini` e reconfigure (ou recupere de dentro de um zip,
veja [Persistência](#persistência-da-configuração)).

Depois de configurar, vá em **Configurações → Criar atalho na área de trabalho**.

---

## Configurando um conjunto

### Aba Backups

À esquerda, duas listas: **Conjuntos** em cima, **Itens do conjunto** embaixo. Selecionar
um conjunto carrega seus itens; selecionar um item carrega seus campos à direita. Nenhuma
configuração abre uma segunda janela.

Cada linha de item mostra `nome → subpasta`, que é a forma de auditar de relance se a
árvore vai sair como você espera, sem clicar item por item.

**Dados do conjunto:**

| Campo | O que faz |
|---|---|
| **Nome (do zip)** | Prefixo do arquivo gerado. `BKP_MAXIMUS` → `BKP_MAXIMUS26082026181429.zip` |
| **Destino do zip** | Onde o zip é gravado: `U:\`, `E:\backups` ou `\\servidor\backups` |
| **Modo** | **Completo** = zip novo por execução, compressão máxima. **Incremental** = um zip fixo atualizado, compressão rápida |
| **Pasta de montagem** | A árvore intermediária. Vazio = `<pasta do app>\staging\<nome>`. Para reproduzir o `.bat`: `C:\BACKUP` |
| **Manter últimos** | Quantos `.zip` preservar no destino. `0` = todos. Só no modo Completo — no Incremental existe um arquivo só |
| **Aguardar unidade** | Lista as unidades conectadas, com rótulo e espaço livre. Como o pen drive quase nunca está espetado na hora de configurar, o campo também aceita a letra digitada. Vazio = não espera. `0` seg = espera sem limite |
| **Manter a pasta de montagem** | Deixe marcado: é o que torna a segunda execução rápida |

Dois botões de inspeção ficam abaixo de **Executar backup agora**:

- **Prévia da árvore** mostra a estrutura que os itens habilitados vão produzir dentro do
  zip, antes de rodar. É a forma de conferir se as subpastas ficaram como você espera.
- **Espaço e limpeza** mostra o espaço livre no destino, lista os backups daquele conjunto
  com tamanho e data, marca quais a retenção removeria, e permite limpar na hora.

O expurgo automático roda **depois** de o zip novo estar gravado — nunca antes, para não
existir um instante em que a máquina esteja sem backup nenhum.

**Dados do item:**

| Campo | Firebird | SQL Server | MySQL | Arquivo/Pasta |
|---|---|---|---|---|
| **Origem** | alias ou `.fdb` | nome do banco | nome do banco | arquivo ou pasta |
| **Subpasta no zip** | `PDVEXPRESSO` | livre | livre | `PDVEXPRESSO\Arquivos\Log` |
| **Arquivo gerado** | `PDVEXPRESSO.FBK` | `.bak` | `.sql` | — |
| **Servidor / porta** | `LOCALHOST` / `3050` | instância / `1433` | host / `3306` | — |
| **Usuário / senha** | `SYSDBA` | vazio = auth. Windows | usuário | — |
| **Espelhar (/MIR)** | — | — | — | remove do backup o que sumiu da origem |

Deixar **Arquivo gerado** vazio usa `<nome do item>` + extensão padrão do tipo.

Escolher um tipo de banco **preenche servidor, porta e usuário** com os padrões daquele
SGBD (`LOCALHOST:3050` e `SYSDBA` no Firebird, `localhost:1433` no SQL Server,
`localhost:3306` e `root` no MySQL). O preenchimento só ocupa campo vazio: o que você já
digitou nunca é sobrescrito, para trocar o tipo por engano não apagar configuração pronta.
Nenhum campo é bloqueado — instalação fora do padrão continua configurável.

**Testar conexão** valida usuário e senha sem gerar dump. Use antes de confiar no
agendamento: descobrir senha errada agora é melhor do que na primeira madrugada.

**Duplicar** copia o item selecionado — o padrão real de uso é "igual ao anterior, com
outro alias" (o segundo PDV da loja). O mesmo existe para conjuntos.

### Campos de caminho

Os campos que recebem arquivo ou pasta aceitam **arrastar do Explorer**: solte a pasta
sobre o campo e o caminho é preenchido. O campo recusa o que não serve — soltar uma pasta
onde se espera um arquivo não faz nada.

Eles também **se validam sozinhos, dois segundos depois que você para de digitar**. Validar
a cada tecla acusaria erro em todo caminho pela metade; o aviso aparece quando é útil:

| Cor da borda | Significa |
|---|---|
| Verde | Caminho existe e serve |
| Âmbar | Vale a pena olhar, mas não impede: pasta que ainda não existe (será criada), compartilhamento fora do ar agora, ou pasta sincronizada com nuvem |
| Vermelho | Caminho não encontrado, ou é arquivo onde se espera pasta (e vice-versa) |

Um alias Firebird (`PDVEXPRESSO`) não é tratado como caminho — só valores que parecem
caminho (com barra, letra de unidade ou extensão `.fdb`/`.gdb`/`.dbf`) passam pela checagem.

### Atalhos de teclado

Quem configura dez máquinas não larga o teclado. Cada atalho também aparece na dica do
botão correspondente.

| Tecla | Ação | Tecla | Ação |
|---|---|---|---|
| `Ctrl+N` | Novo item | `Ctrl+Shift+N` | Novo conjunto |
| `Ctrl+D` | Duplicar item | `Ctrl+Shift+D` | Duplicar conjunto |
| `Alt+↑` / `Alt+↓` | Mover item | `F2` | Renomear o selecionado |
| `Ctrl+P` | Prévia da árvore | `Ctrl+E` | Espaço e limpeza |
| `Ctrl+S` | Salvar tudo | `F5` | Executar backup agora |
| `Ctrl+T` | Alternar tema | `Ctrl+1/2/3` | Trocar de aba |
| `Esc` | Fechar | | |

### Tema claro e escuro

O botão **Tema escuro / Tema claro** fica no rodapé e a escolha é gravada no
`backup_maximus.ini` (`dark_theme`), valendo para todas as janelas e execuções seguintes,
inclusive a janela de progresso do atalho.

### Aba Configurações

Nome da empresa (aparece no relatório), e-mail de notificação, prazo do alerta de atraso,
SMTP com botão **Testar e-mail**, caminho do 7-Zip, troca da senha e criação do atalho.

### Aba Rede

Uma credencial por compartilhamento (`\\servidor\pasta`, `DOMINIO\usuario`, senha). É
usada automaticamente quando a origem de um item ou o destino de um conjunto estiver
naquele compartilhamento, e desconectada ao final.

---

## Armazenamento em nuvem

Botão **Nuvem…** no conjunto. O zip é enviado **pela API do serviço**, e o backup só é
dado como concluído depois que o arquivo chega — com verificação de integridade
(`--checksum`).

| Serviço | Como |
|---|---|
| Google Drive | API, via rclone |
| OneDrive | API, via rclone |
| MEGA | API, via rclone |
| Dropbox, S3, B2, FTP, SFTP, WebDAV | API, via rclone |
| **Terabox** | **Sem API pública.** Use a pasta do cliente de sincronização como destino |

### Por que rclone e não uma integração por serviço

Google Drive, OneDrive e MEGA têm APIs incompatíveis, cada uma com seu fluxo OAuth, seu
formato de token e sua renovação. Implementar as três significa registrar um aplicativo em
cada provedor, embutir os identificadores no executável e manter três integrações que
quebram em ritmos diferentes.

O rclone já faz exatamente isso, é um executável só, e conversa com a API de verdade de
cada serviço. Encaixa na arquitetura que já existe aqui — a aplicação localiza e chama
ferramentas externas (`7z`, `gbak`, `sqlcmd`, `mysqldump`) e lê o resultado.

### Configurando

1. **Nuvem… → Adicionar…** abre o cadastro **dentro do programa** — sem janela preta.
   Escolha o serviço, confira o nome interno e:
   - **Google Drive, OneDrive, Dropbox e afins**: **Entrar e autorizar no navegador**.
     O navegador padrão abre na página do próprio provedor, você concede o acesso e a
     janela avisa que concluiu. Se o navegador não abrir sozinho, os botões
     **Abrir novamente** e **Copiar link** ficam ali.
   - **MEGA, SFTP, FTP, WebDAV e afins**: um formulário com os campos que o serviço pede.
     Os campos não são uma lista escrita no nosso código: vêm do próprio rclone, então
     acompanham a versão dele.

   Ao **Cadastrar**, o serviço é testado antes de ser dado como pronto — se as credenciais
   não responderem, a janela diz isso na hora, e não na primeira execução noturna.
2. De volta ao diálogo, escolha o **Serviço**, informe a **Pasta na nuvem**
   (ex.: `Backups/Loja1`) e **Testar conexão** — ele lista o que já está lá.
3. **Manter na nuvem** aplica retenção independente da local. A nuvem costuma ter mais
   espaço que o pen drive, e faz sentido guardar mais tempo lá.

### A chave de API do Google Drive

O rclone traz uma chave compartilhada por todos os usuários dele no mundo, e a ajuda da
versão embutida aqui avisa: *"The shared client_id is being retired and will stop working
during 2026."* Nos outros serviços não há esse problema — OneDrive, Dropbox e pCloud
descrevem a chave como *"deixe em branco normalmente"*. **Só o Drive precisa de chave
própria.**

A saída adotada é criar **uma chave só, do fornecedor**, embutida no programa. A loja não
cria chave nenhuma: entra na conta dela no navegador e pronto. Cole o par em
[`backup_maximus/oauth_app.py`](backup_maximus/oauth_app.py) — o passo a passo está no
cabeçalho do arquivo. Dois pontos decidem se funciona:

- **Escopo `drive.file`**, aplicado automaticamente. Dá acesso apenas aos arquivos criados
  pelo próprio programa, que é tudo que um backup precisa, e dispensa a verificação de
  segurança que o Google exige do escopo `drive` completo. Em troca, a pasta de destino
  passa a ser criada por nós — não dá para apontar para uma pasta que já existia no Drive.
- **Publique o app como "Em produção"** no console do Google. Em "Teste", a credencial de
  renovação expira em **7 dias**, e o envio noturno pararia toda semana.

O `client_secret` viaja dentro do executável e pode ser extraído — o Google não trata o
secret de aplicativo instalado como confidencial, justamente por isso. O que o par
identifica é **o aplicativo, nunca a conta**: cada loja faz login na conta dela, o zip vai
para o Drive dela e consome a cota dela. Sua conta não armazena nem paga nada.

Com a chave em branco o programa continua funcionando, recaindo na chave compartilhada do
rclone — mas a tela de cadastro avisa, em âmbar, que ela tem prazo.

Quem preferir que cada cliente use a própria chave marca **"Usar uma chave de API própria
neste computador"** na tela de autorização e informa o par ali. Essa chave vence a
embutida. A chave vale desde o login: trocá-la invalida a autorização já feita, porque o
consentimento pertence ao aplicativo que o pediu.

**Remover…** apaga a credencial guardada pelo rclone. Se outro conjunto usar o mesmo
serviço, a confirmação avisa quais — eles deixariam de enviar. Os arquivos já enviados
permanecem na nuvem.

Nos serviços com login no navegador, a senha do Google ou da Microsoft é digitada **no
site deles**, nunca num campo nosso: o que fica guardado nesta máquina é a credencial
que o serviço devolve, e ela pode ser revogada na conta a qualquer momento. Nos serviços
com usuário e senha, o rclone cifra a senha no arquivo de configuração dele (`--obscure`).

Se o rclone não estiver instalado, o diálogo diz isso em vez de falhar em silêncio.
Instale com `winget install Rclone.Rclone`, ou deixe o `build_exe.bat` embuti-lo.

O envio é a **última** etapa do conjunto, de propósito: se a rede cair, o backup local
continua válido e o relatório diz exatamente o que faltou.

### E a pasta sincronizada?

Continua funcionando: aponte o **Destino do zip** para `C:\Users\<você>\OneDrive\Backups`
e o cliente de sincronização envia. A aplicação reconhece essas pastas e avisa da
diferença — ali o backup "conclui" ao gravar no disco, e quem envia é o cliente, depois.
Máquina desligada ou cliente pausado significa relatório dizendo sucesso com o arquivo
ainda em casa. É a única saída para o Terabox, e é aceitável desde que você saiba disso.

---

## Ferramentas embutidas no executável

O `build_exe.bat` embute o 7-Zip e o rclone no `.exe`, para a máquina do cliente não
precisar de nenhuma instalação extra. Sem eles o programa funciona igual — só compacta
mais devagar (usa o `zipfile` do Python) e fica sem envio à nuvem.

```bash
python vendor\baixar_ferramentas.py
```

```bash
python vendor\conferir.py
```

**A arrumação da pasta é livre.** Você pode extrair o pacote oficial inteiro em
`vendor\7za\` (com as subpastas `x64\`, `arm64\`, `Far\`) ou deixar só o binário em
`vendor\7zip\` — a busca aceita as duas e escolhe a arquitetura desta máquina. Quem baixa
a ferramenta não deveria ter que adivinhar o nome de pasta que o programa espera.

O `conferir.py` mostra qual arquivo foi escolhido, a versão, e o que vai para dentro
do `.exe`:

```
7-Zip    ENCONTRADO  (vendor/, 1,3 MB)
         ...\vendor\7za\x64\7za.exe
         7-Zip (a) 26.02 (x64)
rclone   ENCONTRADO  (vendor/, 81,2 MB)
         rclone v1.75.0
```

O empacotamento leva **só o binário da arquitetura certa**, não a pasta inteira: o pacote
do 7-Zip traz três arquiteturas mais um plugin do Far Manager, e cada MB a mais é MB no
executável que alguém vai copiar por rede.

### Tamanho do executável

O rclone sozinho passa de **80 MB**, o que leva o `.exe` final para perto de 130 MB. Se
isso for demais para distribuir, a alternativa é deixar a pasta `vendor\` **ao lado do
executável** em vez de dentro dele: a aplicação procura ali primeiro, então
`BackupMaximus.exe` + `vendor\rclone\rclone.exe` funciona igual, com o `.exe` pequeno.

### Licenças

O `conferir.py` **avisa quando um binário vai sem o texto da licença**, porque distribuir
sem ele é problema de quem distribui e passa despercebido com facilidade.

| Ferramenta | Licença | Obrigação |
|---|---|---|
| 7-Zip (`7za.exe`) | LGPL 2.1+ | O texto da licença deve acompanhar o binário |
| rclone | MIT | O aviso de copyright deve acompanhar o binário |

Coloque o arquivo de licença junto do executável em `vendor\` e ele entra no pacote.

---

## Detectar bancos do Firebird

Botão **Detectar bancos do Firebird** no conjunto. Digitar o caminho de um `.fdb` à mão é
a parte mais chata e mais sujeita a erro de configurar um backup — e o servidor já sabe
onde os bancos estão.

A aplicação lê a lista direto dele:

| Versão | Arquivo | Como é encontrado |
|---|---|---|
| Firebird 2.5 | `aliases.conf` | Registro do Windows (`Firebird Server\Instances`) e pastas padrão |
| Firebird 3+ | `databases.conf` | Idem |

Cada banco marcado vira um item do tipo Firebird, com **o alias como origem** — não o
caminho. É assim que o `gbak` resolve pelo servidor, e continua valendo se o banco mudar
de pasta. O `gbak` da instalação correspondente já vem preenchido (2.5 usa `bin\gbak.exe`,
3+ usa a raiz), e a porta e o usuário `SYSDBA` também.

Um alias cujo arquivo não existe nesta máquina aparece na lista, mas desmarcado: pode ser
um banco em outro servidor, e essa decisão é sua. A base de segurança do próprio servidor
e os blocos de parâmetros `{ }` do Firebird 3+ são ignorados.

**Falta preencher a senha do SYSDBA** em cada item criado — use **Testar conexão** para
confirmar antes de confiar no agendamento.

---

## Lembrete de backup

Na aba **Configurações**: marque **Mostrar lembrete diário** e escolha o horário. Ao
salvar, a aplicação registra uma tarefa no Agendador do Windows chamada
*Backup Maximus - Lembrete*.

No horário, aparece uma notificação da bandeja e uma janelinha com **Fazer backup agora**
e **Agora não**. A janela se fecha sozinha em 2 minutos — um lembrete não pode virar um
diálogo travado numa máquina de PDV sem ninguém por perto.

**O lembrete é silencioso quando o backup do dia já rodou.** Avisar sobre algo que já foi
feito treina a pessoa a fechar o aviso sem ler. Ele aparece quando:

| Situação | Aparece? |
|---|---|
| Backup concluído há menos de 12 h | Não |
| Backup há mais de 12 h | Sim |
| Última execução terminou com falha | Sim, mesmo se recente |
| Nunca rodou nesta máquina | Sim |
| Nenhum conjunto configurado | Sim, pedindo configuração |

Por que o Agendador e não um processo na bandeja: o lembrete precisa disparar mesmo se
ninguém abriu o programa, e continuar funcionando depois de reiniciar. Um processo
residente some quando o usuário fecha, não sobrevive ao boot sem mais configuração, e
consome memória 23 horas por dia sem fazer nada.

Desmarcar a opção e salvar remove a tarefa. Se o Windows recusar o registro por permissão,
abra o programa como administrador.

---

## Modos de execução

| Comando | Comportamento |
|---|---|
| `BackupMaximus.exe` | Abre a tela de configuração (pede senha) |
| `BackupMaximus.exe /run` | **Quick Run** — executa mostrando barra de progresso e tempo; não abre configurações |
| `BackupMaximus.exe /silent` | Executa sem interface (Agendador de Tarefas) |
| `BackupMaximus.exe /check` | Verifica atraso e dispara alerta |
| `BackupMaximus.exe /check /quiet` | Idem, sem caixa de mensagem — só log e e-mail |
| `BackupMaximus.exe /remind` | Mostra o lembrete (é o que o Agendador executa) |

As flags também aceitam `-silent` e `--silent`, em qualquer caixa.

**Códigos de saída:** `0` = tudo certo · `1` = houve falha · `2` = alerta disparado.

O atalho da área de trabalho aponta para `/run`. Durante a espera pelo pen drive a barra
fica em modo indeterminado e o botão **Cancelar** aparece; no meio do backup não é possível
abortar, para não deixar um zip pela metade indistinguível de um backup bom.

Rodando do código-fonte, troque `BackupMaximus.exe` por `BackupMaximus.pyw` (ou
`python -m backup_maximus`).

---

## Agendamento e alerta de falha

Em PowerShell **como administrador**:

```powershell
$exe = 'C:\BackupMaximus\BackupMaximus.exe'
schtasks /Create /TN "Backup Maximus - Diario" /TR "`"$exe`" /silent" /SC DAILY /ST 22:00 /RL HIGHEST /F
schtasks /Create /TN "Backup Maximus - Watchdog" /TR "`"$exe`" /check /quiet" /SC HOURLY /F
```

O watchdog dispara alerta quando: estourou o prazo configurado, nunca houve backup, ou a
última execução terminou com falhas.

---

## Onde ficam os arquivos

```
C:\BackupMaximus\
├── BackupMaximus.exe
├── backup_maximus.ini          configuração (senhas cifradas)
├── logs\backup_2026-08-26.log  um arquivo por dia, UTF-8
├── reports\relatorio_*.txt     relatório de cada execução
└── staging\<conjunto>\         árvore de montagem (se não configurada em outro lugar)
```

Defina `BM_HOME` para colocar esses dados em outro lugar — útil quando o programa mora em
`Program Files` e os dados precisam ficar numa pasta gravável.

### Persistência da configuração

Cada zip gerado recebe uma cópia do `backup_maximus.ini` e do relatório. Se o INI local
for perdido, coloque um zip de backup ao lado do executável e abra a aplicação: ela extrai
a configuração do zip mais recente automaticamente.

---

## Segurança

- **Senha da interface**: SHA-256 com salt de 16 bytes aleatórios, comparada com
  `compare_digest`. Nunca gravada em texto plano.
- **Senhas de banco, SMTP e rede**: cifradas com **DPAPI** (`CryptProtectData`) em Base64.
  Legíveis apenas pela mesma conta na mesma máquina — copiar o INI para outro computador
  não expõe as senhas (mas exige reconfigurá-las lá).
- Senhas gravadas nunca voltam para a tela: o campo aparece vazio com a marca
  `•••••• (gravada)`, e só é reescrito se você digitar algo novo.
- O envio SMTP usa `smtplib` diretamente — a senha não passa por linha de comando nem por
  variável de ambiente.

Compare com o `.bat`, onde `masterkey` ficava em texto plano numa pasta acessível.

O formato do INI é o mesmo da versão C++ em `src/`: os arquivos de configuração são
intercambiáveis entre as duas implementações.

---

## Testes

```bash
run_tests.bat
```

129 testes cobrindo:

- utilitários de formatação, caminhos UNC e normalização de flags de linha de comando
- ciclo cifra/decifra DPAPI e SHA-256 contra vetor conhecido
- hash de senha com salt (mesma senha → hashes diferentes)
- round-trip do INI no modelo Conjunto→Itens, com subpastas aninhadas e acentuação
- INI corrompido e valores inválidos caindo nos padrões sem derrubar a aplicação
- métricas do dispositivo dentro de faixas válidas
- cópia incremental e espelhamento: recopia só o alterado, remove o que sumiu da origem,
  preserva quando o espelhamento está desligado
- espera por unidade: detecta a que aparece durante a espera, expira, e aceita cancelamento
- retenção: preserva os N mais recentes, remove justamente os mais antigos, ignora
  arquivos de outros conjuntos, nunca expurga no modo Incremental, e roda depois do zip novo
- validação de caminho: alias Firebird não vira erro, destino inexistente é aviso e não
  erro, UNC fora do ar é aviso, detecção de pasta de nuvem
- leitura de aliases do Firebird 2.5 e 3+, incluindo blocos `{ }` e entradas internas
- decisão do lembrete: silencioso após backup recente, insistente após falha
- camada de nuvem degradando com clareza quando o rclone não existe
- layout: nenhuma tela corta ou exige rolagem, no tamanho padrão e no mínimo
- busca das ferramentas em vendor/, em qualquer arrumação de pasta e arquitetura
- execução completa: 4 origens → 1 zip com a árvore correta, config e relatório embutidos,
  segunda execução incremental, item com falha não derruba o zip, recuperação de config

Saída esperada: `Ran 129 tests ... OK`.

---

## Solução de problemas

| Sintoma | Causa provável / correção |
|---|---|
| `gbak.exe não encontrado` | Informe o caminho completo no campo **Ferramenta** do item |
| `Unidade U:\ não ficou disponível` | Pen drive não inserido, ou com outra letra. Espete-o e abra a lista de **Aguardar unidade**: ela é relida a cada abertura e mostra o rótulo do volume, que distingue dois pen drives |
| `BACKUP DATABASE falhou` … *Operating system error 5* | A conta de serviço do SQL Server não escreve na pasta de montagem. Para servidor remoto, aponte a montagem para um UNC que essa conta enxergue |
| Backup de rede falha com erro 1326 | Credencial errada na aba **Rede** |
| Erro 1219 (conflito de credencial) | Já existe sessão com o servidor por outro usuário: `net use \\servidor /delete` |
| Compactação lenta em árvores grandes | Instale o 7-Zip e informe o caminho, ou deixe autodetectar |
| Backup demora igual toda vez | **Manter a pasta de montagem** está desmarcado |
| E-mail não chega | Use **Testar e-mail**. Em Google/Microsoft, use senha de aplicativo |
| Aplicação não grava nada | Pasta do executável sem permissão de escrita — defina `BM_HOME` |
| `rclone não encontrado` | `winget install Rclone.Rclone`, ou rode `python vendoraixar_ferramentas.py` e regere o .exe |
| Nenhum alias detectado | O Firebird não está nesta máquina, ou o `aliases.conf` não tem bancos. Informe o caminho do `.fdb` manualmente |
| Lembrete não dispara | Confira a tarefa *Backup Maximus - Lembrete* no Agendador. Se o registro foi recusado, abra o programa como administrador |
| Envio à nuvem falhou mas o zip existe | É o esperado: o local está íntegro. O relatório traz o erro do rclone |
| 7-Zip em vendor/ não é usado | Rode `python vendor\conferir.py` — ele mostra qual arquivo foi escolhido e por quê |

Todos os erros ficam em `logs\backup_AAAA-MM-DD.log` com o texto completo devolvido pela
ferramenta que falhou.

---

## Editando as telas no Qt Designer

Os layouts ficam em `designer/*.ui` — arquivos padrão do Qt 6, editáveis
visualmente. Nenhuma posição, tamanho ou rótulo está preso em código Python.

```bash
abrir_designer.bat
```

Abre todas as telas. Para uma só: `abrir_designer.bat tab_backups`.

| Arquivo | Tela |
|---|---|
| `main_window.ui` | Janela principal: abas e rodapé |
| `tab_backups.ui` | Aba Backups (conjuntos e itens) |
| `tab_settings.ui` | Aba Configurações |
| `tab_network.ui` | Aba Rede |
| `dialog_password.ui` | Trava de senha |
| `dialog_preview_tree.ui` | Prévia da árvore |
| `dialog_destination.ui` | Espaço e limpeza |
| `window_progress.ui` | Janela do Quick Run |
| `dialog_aliases.ui` | Bancos registrados no Firebird |
| `dialog_cloud.ui` | Envio à nuvem |
| `dialog_cloud_setup.ui` | Cadastro de um serviço de nuvem |

**Depois de salvar no Designer, basta rodar a aplicação.** Ela detecta que o
`.ui` ficou mais novo que o `.py` gerado e recompila sozinha — não há passo de
build para esquecer. `build_ui.bat` força a regeração quando você quiser.

Os arquivos gerados ficam em `backup_maximus/ui/generated/` e são versionados,
para a aplicação rodar mesmo onde o `pyside6-uic` não existe.

### O que saber antes de mexer

**Não renomeie objetos.** O código encontra cada widget pelo `objectName`
(`editSetName`, `listItems`, `btnRun`…). Renomear no Designer quebra a ligação.
Mover, redimensionar, trocar texto e reordenar são seguros.

**A grade de 5 colunas é o que mantém o alinhamento.** Nas abas, cada
formulário usa `QGridLayout` com:

| Coluna | Conteúdo | Largura |
|---|---|---|
| 0 | Rótulo | fixa, 124 px |
| 1 | Campo principal | única que estica |
| 2 | Rótulo embutido de um segundo campo | automática |
| 3 | Campo secundário (porta, retenção, segundos) | automática |
| 4 | Botão `…` | 30 px |

A coluna 4 fica vazia nas linhas sem botão. Como a largura de uma coluna da
grade é a do item mais largo, as linhas com e sem botão terminam na mesma
posição sozinhas — é isso que mantém a borda direita reta. Se você acrescentar
uma linha, siga o mesmo padrão.

**Estilo vem da propriedade `role`, não do objectName.** Um rótulo de seção tem
`role = section`; um de campo, `role = field`; dicas usam `hint`, `hintOk`,
`hintWarn`, `hintBad`. Botões primários usam `role = accent`. No Designer isso
aparece em *Propriedades dinâmicas*. As cores de cada papel estão em
`backup_maximus/ui/theme.py`, e valem para os dois temas.

**`PathEdit` é um widget promovido.** Os campos de caminho são `QLineEdit`
promovidos para `PathEdit` (cabeçalho `backup_maximus.ui.pathedit`) — é o que
lhes dá arrastar-soltar e validação. A propriedade dinâmica `pathKind` diz o que
o campo espera: `file`, `dir`, `dest`, `any`, `path_or_name` ou `none`. Para
criar um campo de caminho novo: coloque um `QLineEdit`, promova para `PathEdit`,
e defina `pathKind`.

**Nenhum tamanho vem do Python.** Largura, altura, margem e espaçamento estão
só nos `.ui`. A folha de estilo (`theme.py`) define cor, borda, fonte e o
espaçamento interno para o texto não encostar na borda — nada de `min-height`
ou largura fixa competindo com o que você define no Designer.

### Duas propriedades que sustentam o layout

Se algo começar a ser cortado ou a exigir rolagem, quase sempre é uma destas:

**`horstretch` na `scrollRight`** (aba Backups). Um `QHBoxLayout` reparte a
sobra de espaço **igualmente** entre seus itens, a menos que alguém tenha
prioridade. Sem `horstretch = 1` no painel direito, a coluna da esquerda incha
e a da direita é espremida até cortar os campos. No Designer:
*sizePolicy → Horizontal Stretch*.

**Altura mínima da janela** (`main_window.ui`, `minimumSize`). O painel direito
precisa de cerca de 620 px de altura útil; a janela reserva isso mais a barra de
abas, o rodapé e as margens. Se você acrescentar linhas ao formulário, aumente
o mínimo junto — senão a aba volta a rolar. Para conferir sem abrir a aplicação:

```bash
python -m backup_maximus.ui.fitcheck
```

Ele imprime, para o tamanho padrão e para o mínimo, quanto o painel direito
precisa e quanto tem, e falha se faltar.

---

## Arquitetura do código

```
backup_maximus/
├── winapi.py       ctypes: DPAPI, métricas, unidades, rede (WNet), console
├── util.py         formatação, caminhos, espera por unidade, execução de processos
├── logger.py       log diário em arquivo, thread-safe
├── config.py       modelo Conjunto→Itens, INI, DPAPI, hash de senha
├── network.py      conexão autenticada a UNC
├── sysinfo.py      métricas de CPU/memória/disco
├── paths.py        pasta do app, dados e ferramentas embutidas
├── filecopy.py     cópia incremental e espelhamento (/MIR nativo)
├── archive.py      árvore inteira em um zip: 7-Zip ou zipfile
├── dbdump.py       dumps nativos: gbak / sqlcmd / mysqldump
├── firebird_aliases.py  leitura do aliases.conf / databases.conf
├── retention.py    espaço no destino e expurgo de backups antigos
├── cloud.py        envio pela API do serviço, via rclone
├── cloud_setup.py  cadastro de serviços sem console (OAuth e formulário)
├── oauth_app.py    a chave de API do aplicativo (cole a sua aqui)
├── reminder.py     lembrete diário e tarefa no Agendador
├── mailer.py       envio SMTP
├── engine.py       orquestração: unidade → árvore → itens → zip → relatório → e-mail
├── __main__.py     despacho dos modos de execução
└── ui/
    ├── forms.py        ponte com os .ui: compila o que estiver desatualizado
    ├── theme.py        paletas clara/escura e folha de estilo (QSS)
    ├── icons.py        ícones desenhados em runtime, por paleta
    ├── widgets.py      pontos de status e papéis visuais
    ├── drivecombo.py  seletor de unidade que aceita a que ainda não existe
    ├── pathedit.py     campo de caminho: arrastar-soltar e validação com atraso
    ├── password.py     trava de senha e diálogos
    ├── preview.py      prévia da árvore e painel de espaço/limpeza
    ├── alias_dialog.py escolha dos bancos registrados no Firebird
    ├── cloud_dialog.py configuração do envio à nuvem
    ├── cloud_setup_dialog.py assistente de cadastro do serviço
    ├── reminder_window.py  notificação e janela do lembrete
    ├── fitcheck.py     confere que as telas cabem sem rolar
    ├── progress.py     janela do Quick Run
    ├── tab_backups.py  aba Backups (conjuntos + itens)
    ├── tab_settings.py abas Configurações e Rede
    ├── app.py          janela principal, atalhos e atalho da área de trabalho
    └── generated/      formulários compilados — não editar à mão

designer/               layouts .ui, editáveis no Qt Designer
```

A separação é deliberada: **`designer/` tem aparência, `ui/*.py` tem comportamento.**
Cada classe carrega seu formulário com `forms.load(...)`, dá nomes curtos aos widgets
que usa, e daí em diante cuida só de sinais, validação e sincronia com o modelo.

O backup roda numa thread de trabalho (`QThread`) e o progresso chega à interface por
sinal do Qt, então a janela nunca congela. A coleta de métricas acontece **depois** do
backup, para não competir por CPU e disco durante a cópia.

A pasta `src/` guarda a implementação anterior em C++ (Win32 API), que continua
funcional e lê o mesmo formato de configuração.
