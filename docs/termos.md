# Termos de Serviço — Backup Maximus

**Última atualização:** 2 de setembro de 2026

Estes Termos regem o uso do **Backup Maximus**, aplicativo de backup para
Windows desenvolvido e distribuído por **WALYTECH SOLUÇÕES TECNOLÓGICAS LTDA**,
CNPJ 50.449.577/0001-53, com sede na R. Governador Valadares, 350, Andar 1,
Sala 3, Cidade Nova, Capelinha/MG, CEP 39.680-000 ("nós", "a desenvolvedora").

Ao instalar ou usar o aplicativo, o usuário ("você") concorda com estes Termos.
Se não concordar, não instale nem utilize o programa.

---

## 1. O que o aplicativo faz

O Backup Maximus copia bancos de dados e arquivos indicados por você para uma
estrutura de pastas, compacta essa estrutura em um arquivo `.zip` e o grava no
destino que você definir. Opcionalmente, envia esse arquivo para um serviço de
armazenamento em nuvem da sua escolha, emite relatórios por e-mail e avisa
quando um backup não é executado no prazo configurado.

O programa é executado **no seu computador**, sob seu controle e com as
permissões da sua conta do Windows.

---

## 2. Licença de uso

Sujeito a estes Termos, concedemos a você uma licença **não exclusiva,
intransferível e revogável** para instalar e usar o Backup Maximus nos
computadores da sua organização, conforme o que tiver sido contratado.

Você não pode: (a) remover ou alterar avisos de autoria, marca ou licença;
(b) sublicenciar, alugar ou revender o aplicativo sem autorização escrita;
(c) usá-lo para fins ilícitos ou para copiar dados sobre os quais não tenha
direito de acesso.

Os componentes de terceiros distribuídos junto com o aplicativo têm licenças
próprias, que prevalecem sobre esta seção quanto a eles. Veja
[Avisos de terceiros](../THIRD_PARTY_NOTICES.md).

---

## 3. Suas responsabilidades

O backup é uma medida de proteção, e sua eficácia depende de providências que
só você pode tomar:

- **Testar a restauração periodicamente.** Um arquivo de backup que nunca foi
  restaurado é uma suposição, não uma garantia. Esta é a obrigação mais
  importante desta lista.
- **Conferir os relatórios e os alertas** de backup atrasado, em vez de supor
  que o silêncio significa sucesso.
- **Manter espaço livre suficiente** no destino e na conta de nuvem.
- **Guardar as senhas e credenciais.** A senha da tela de configuração é
  armazenada apenas como hash: **não temos como recuperá-la**.
- **Manter cópias em mais de um lugar.** Um único destino — um pen drive, uma
  pasta de rede, uma conta de nuvem — é um único ponto de falha.
- **Cumprir a legislação aplicável** aos dados que você copia, incluindo a LGPD
  quando os backups contiverem dados pessoais de terceiros.
- **Manter o computador seguro**: atualizações, antivírus e controle de acesso.

---

## 4. Serviços de terceiros

O envio à nuvem depende de serviços operados por terceiros — Google Drive,
Microsoft OneDrive, Dropbox, MEGA, Amazon S3, Backblaze B2, entre outros. O uso
desses serviços é regido pelos termos e pelas políticas de cada um, com quem
você mantém relação direta.

Não temos controle sobre disponibilidade, desempenho, cotas, preços ou mudanças
de política desses serviços, e não respondemos por interrupções, alterações ou
encerramento deles.

O aplicativo utiliza o **rclone** para se comunicar com esses serviços, e
ferramentas nativas de cada banco de dados (`gbak`, `sqlcmd`, `mysqldump`) para
gerar as cópias. Essas ferramentas são de terceiros e possuem licenças próprias.

---

## 5. Privacidade

O tratamento de dados está descrito na [Política de
Privacidade](privacidade.md), que integra estes Termos. Em resumo: o aplicativo
funciona no seu computador, não possui telemetria e não nos envia dados.

---

## 6. Ausência de garantias

O aplicativo é fornecido **"no estado em que se encontra"**, sem garantias de
qualquer natureza, expressas ou implícitas, incluindo — mas não se limitando a —
garantias de comercialização, adequação a uma finalidade específica, precisão ou
funcionamento ininterrupto.

Não garantimos que o aplicativo funcionará sem erros, que estará sempre
disponível, que será compatível com toda configuração de hardware, software,
rede ou banco de dados, ou que os arquivos gerados estarão livres de defeito.

Backups podem falhar por causas alheias ao programa: falha de disco, corrupção
do banco de origem, interrupção de energia, queda de rede, indisponibilidade do
serviço de nuvem, antivírus bloqueando o acesso, ou alteração de permissões.
**Verificar periodicamente a integridade e a restaurabilidade dos backups é
responsabilidade sua.**

---

## 7. Limitação de responsabilidade

Na máxima extensão permitida pela lei aplicável, não responderemos por danos
indiretos, incidentais, especiais, punitivos ou consequenciais, incluindo perda
de dados, perda de lucros, interrupção de negócios ou perda de oportunidade,
decorrentes do uso ou da impossibilidade de uso do aplicativo.

Nossa responsabilidade total, por qualquer causa, fica limitada ao valor
efetivamente pago por você pelo aplicativo nos 12 meses anteriores ao evento.

Nada nestes Termos exclui responsabilidades que não possam ser afastadas pela
legislação aplicável, incluindo o Código de Defesa do Consumidor quando
aplicável à relação.

---

## 8. Atualizações e versões

O aplicativo é versionado de forma semântica (MAIOR.MENOR.CORREÇÃO). A versão
instalada aparece na barra de título e na tela **Sobre**, e o histórico de
mudanças acompanha cada versão distribuída.

Podemos publicar atualizações a nosso critério. Não somos obrigados a manter
compatibilidade indefinida com versões antigas do Windows, de bancos de dados ou
de serviços de nuvem que venham a ser descontinuados por seus fornecedores.

---

## 9. Vigência e encerramento

Estes Termos vigoram enquanto você usar o aplicativo. A licença termina
automaticamente em caso de descumprimento. Encerrada a licença, você deve parar
de usar e desinstalar o programa — os arquivos de backup já gerados continuam
seus.

---

## 10. Alterações destes Termos

Podemos alterar estes Termos, publicando a versão atualizada nesta página com
nova data. Mudanças relevantes serão comunicadas pelos canais de contato
disponíveis. O uso continuado após a publicação significa concordância.

---

## 11. Lei aplicável e foro

Estes Termos são regidos pelas leis da República Federativa do Brasil. Fica
eleito o foro da comarca de **Capelinha, Estado de Minas Gerais**, sede da
desenvolvedora, para dirimir controvérsias, com renúncia a qualquer outro,
ressalvadas as hipóteses de competência legal diversa.

---

## 12. Contato

**WALYTECH SOLUÇÕES TECNOLÓGICAS LTDA**

CNPJ 50.449.577/0001-53

R. Governador Valadares, 350 — Andar 1, Sala 3

Cidade Nova — Capelinha/MG — CEP 39.680-000

**tgf231.dev@gmail.com**
