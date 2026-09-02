# Política de Privacidade — Backup Maximus

**Última atualização:** 1 de setembro de 2026
**Aplica-se a:** Backup Maximus, aplicativo de backup para Windows.

> **Preencher antes de publicar:** «RAZÃO SOCIAL», «CNPJ», «ENDEREÇO»,
> «E-MAIL DE CONTATO», «SITE». Os trechos entre «» são os únicos que faltam.

O Backup Maximus é desenvolvido e distribuído por «RAZÃO SOCIAL», inscrita no
CNPJ «CNPJ», com sede em «ENDEREÇO» ("nós"). Dúvidas sobre esta política:
**«E-MAIL DE CONTATO»**.

---

## Resumo

O Backup Maximus é um programa que roda **inteiramente no computador do
usuário**. Não operamos servidor, não recebemos dados de uso e não temos acesso
ao conteúdo dos backups.

Quando o usuário escolhe enviar seus backups para um serviço de nuvem, o envio
vai **direto do computador dele para a conta dele** naquele serviço. Nós não
somos intermediários e não guardamos cópia.

---

## 1. Dados que nós coletamos

**Nenhum.**

O aplicativo não possui telemetria, não envia estatísticas de uso, não reporta
erros para nós e não se comunica com nenhum servidor sob nosso controle. As
únicas conexões de rede que ele faz são as que o próprio usuário configura:

- o servidor de e-mail (SMTP) que o usuário informar, para receber os relatórios;
- o serviço de nuvem que o usuário cadastrar, para receber os arquivos de backup;
- os caminhos de rede (UNC) que o usuário indicar como origem ou destino.

Se o usuário não configurar nenhum desses, o programa não acessa a rede.

---

## 2. Dados que o aplicativo trata no computador do usuário

Tudo abaixo fica **no computador do usuário**, sob controle dele:

| Dado | Onde fica | Para quê |
|---|---|---|
| Nome da empresa, e-mails de aviso, caminhos de origem e destino | `backup_maximus.ini`, ao lado do programa | Configuração dos backups |
| Senhas de banco de dados, de rede e de e-mail | Mesmo arquivo, **cifradas com DPAPI** do Windows | Executar os backups |
| Senha da tela de configuração | Mesmo arquivo, como hash SHA-256 com salt | Proteger as configurações |
| Registros de execução | Pasta `logs\` | Diagnóstico |
| Relatórios de backup | Pasta `reports\` | Conferência do que rodou |
| Conteúdo dos backups | Pasta de montagem e arquivos `.zip` | O backup em si |
| Credencial do serviço de nuvem | Arquivo de configuração do rclone, no perfil do usuário | Enviar os arquivos |

A cifragem por DPAPI vincula os segredos à máquina e à conta do Windows que os
gravou: copiar o arquivo de configuração para outro computador não revela as
senhas.

---

## 3. Informações do dispositivo no relatório

Ao final de cada execução, o aplicativo reúne, para o relatório:

- nome do computador;
- percentual de uso do processador;
- memória total, usada e percentual;
- espaço total, livre e percentual do disco de destino.

Esses dados servem para o responsável perceber que o disco está enchendo ou que
a máquina está sobrecarregada. **Eles não são enviados para nós.** Se o usuário
tiver configurado o envio de relatórios, eles vão por e-mail para o endereço que
ele mesmo informou, usando o servidor SMTP que ele mesmo informou.

---

## 4. Uso de dados do Google (Google Drive)

Quando o usuário opta por enviar backups ao Google Drive, ele autoriza o acesso
no site do próprio Google. **A senha da conta Google nunca é digitada no nosso
aplicativo** e nunca passa por ele.

### Qual acesso é solicitado

Solicitamos exclusivamente o escopo:

```
https://www.googleapis.com/auth/drive.file
```

Esse escopo dá acesso **apenas aos arquivos criados pelo próprio aplicativo**.
O Backup Maximus **não consegue ver, ler, listar ou alterar** nenhum outro
arquivo do Google Drive do usuário — fotos, documentos, planilhas e qualquer
conteúdo anterior permanecem inacessíveis para ele.

### O que é feito com esse acesso

Somente três operações, todas sobre os arquivos que o próprio programa criou:

1. **Enviar** o arquivo `.zip` de backup para a pasta de destino.
2. **Listar** os backups enviados anteriormente, para aplicar a retenção.
3. **Apagar** backups antigos, conforme o número de cópias que o usuário mandou
   manter.

### Onde fica a credencial

A credencial devolvida pelo Google é gravada **no computador do usuário**, pelo
rclone. Ela não é transmitida para nós, não é enviada a terceiros e não sai
daquela máquina.

### Uso Limitado

O uso e a transferência de informações recebidas das APIs do Google pelo Backup
Maximus obedecem à [Política de Dados do Usuário dos Serviços de API do
Google](https://developers.google.com/terms/api-services-user-data-policy),
incluindo os requisitos de **Uso Limitado**. Especificamente, não usamos dados
do Google para publicidade, não os vendemos, não os transferimos a terceiros e
não os utilizamos para treinar modelos de inteligência artificial — o que seria
impossível de qualquer forma, já que esses dados nunca chegam até nós.

### Como revogar

A qualquer momento, em
[myaccount.google.com/permissions](https://myaccount.google.com/permissions),
removendo o acesso do Backup Maximus. O envio à nuvem para de funcionar; os
backups locais continuam normalmente, e os arquivos já enviados permanecem na
conta do usuário.

---

## 5. Outros serviços de nuvem

O mesmo vale para OneDrive, Dropbox, MEGA, Amazon S3, Backblaze B2, SFTP, FTP e
WebDAV: a conexão é direta entre o computador do usuário e a conta dele. Cada
serviço tem sua própria política de privacidade, que rege o que acontece com os
arquivos depois de enviados.

---

## 6. Compartilhamento com terceiros

Não compartilhamos dados de usuários com ninguém, porque não os possuímos.

Não vendemos dados. Não fazemos publicidade. Não usamos dados de usuários para
treinar modelos de inteligência artificial.

---

## 7. Retenção e exclusão

Como os dados ficam no computador do usuário e na conta de nuvem dele, o
controle é inteiramente dele:

- **Configurações e senhas:** apagar `backup_maximus.ini`.
- **Logs e relatórios:** apagar as pastas `logs\` e `reports\`.
- **Credencial de nuvem:** botão **Remover…** na tela de nuvem do aplicativo,
  ou revogação na conta do provedor.
- **Backups enviados:** apagar pela interface do serviço de nuvem.

Não há nada a solicitar a nós, porque não há nada conosco a apagar.

---

## 8. Direitos do titular (LGPD)

A Lei Geral de Proteção de Dados assegura ao titular direitos de acesso,
correção, portabilidade, eliminação e informação sobre compartilhamento.

Como não realizamos tratamento de dados pessoais de usuários do aplicativo,
esses direitos são exercidos diretamente sobre os arquivos no computador do
usuário, conforme a seção anterior. Para dúvidas ou solicitações relacionadas a
esta política, escreva para **«E-MAIL DE CONTATO»**.

**Atenção ao papel de cada um:** se o usuário utiliza o Backup Maximus para
copiar bancos de dados que contêm dados pessoais de terceiros — clientes,
funcionários, fornecedores —, ele é o **controlador** desses dados perante a
LGPD, e as obrigações correspondentes são dele. Nós não temos acesso a esse
conteúdo e não atuamos como operador em relação a ele.

---

## 9. Segurança

- Segredos cifrados com DPAPI, vinculados à máquina e à conta do Windows.
- Senha da interface guardada como hash SHA-256 com salt aleatório, comparada
  em tempo constante.
- Senhas de serviços de nuvem cifradas pelo rclone no arquivo de configuração dele.
- Conexões SMTP com STARTTLS ou SSL, conforme a configuração do usuário.
- Autenticação nos serviços de nuvem por OAuth, sem que a senha da conta passe
  pelo aplicativo.

Nenhuma medida é infalível. A segurança do computador onde o programa roda —
antivírus, atualizações, controle de acesso físico e de conta — é
responsabilidade do usuário.

---

## 10. Crianças

O Backup Maximus é uma ferramenta administrativa destinada a uso profissional.
Não é direcionado a menores de 18 anos e não coleta dados de crianças ou
adolescentes.

---

## 11. Alterações desta política

Alterações relevantes serão publicadas nesta mesma página, com a data de
atualização no topo. Se a mudança afetar o tratamento de dados do Google, ela
será refletida também na configuração do aplicativo no Google Cloud.

---

## 12. Contato

«RAZÃO SOCIAL»
CNPJ «CNPJ»
«ENDEREÇO»
**«E-MAIL DE CONTATO»**
