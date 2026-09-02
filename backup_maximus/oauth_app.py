"""A identidade do Backup Maximus perante os serviços de nuvem.

É aqui, e só aqui, que se cola a chave de API criada uma única vez pelo
fornecedor. A loja não cria chave nenhuma: faz o login na conta dela e pronto.

**Por que isto existe.** O rclone traz uma chave compartilhada por todos os
usuários dele no mundo, e a ajuda da versão 1.75 avisa em letras claras:

    The shared client_id is being retired and will stop working during 2026,
    so creating your own is now strongly recommended.

Ou seja, no Google Drive não há a opção de não decidir — ou existe uma chave
nossa, ou o cadastro para de funcionar. Nos demais serviços (OneDrive, Dropbox,
pCloud) a chave compartilhada segue válida e a ajuda deles diz "deixe em branco
normalmente"; por isso só o Drive precisa de chave própria hoje.

**O client_secret não é segredo.** Ele viaja dentro do programa e qualquer um
pode extraí-lo do executável — o Google sabe disso e não trata o secret de
aplicativo instalado como confidencial. O que o par identifica é o aplicativo,
nunca a conta: quem entra é a loja, no navegador, e o arquivo vai para o Drive
dela, consumindo a cota dela.

Como preencher (uma vez, no seu Google Cloud):

1. Entre em console.cloud.google.com com a conta da **empresa**: o nome do app
   e o e-mail de suporte aparecem na tela que o cliente vê ao autorizar.
2. Crie um projeto e, em *APIs e serviços → Biblioteca*, ative a **Google
   Drive API**. Sem isso o login funciona e só o envio falha.
3. Tela de consentimento (*Google Auth Platform*, antes *Tela de permissão
   OAuth*): tipo **Externo**, nome e e-mails de contato.
4. Em *Acesso a dados*, declare **apenas** este escopo:

       https://www.googleapis.com/auth/drive.file

   O console deve classificá-lo como **não sensível**. Se ele aparecer em
   "sensíveis" ou "restritos", foi adicionado o escopo errado — o `.../drive`
   completo é restrito e exige uma auditoria de segurança paga.
5. **Publique o app como "Em produção".** Enquanto ele ficar em "Teste", o
   Google expira a credencial de renovação em 7 dias — o envio noturno pararia
   toda semana, que é o modo mais cruel de um backup falhar. Com escopo não
   sensível a publicação é imediata, sem fila de revisão.
6. *Credenciais → ID do cliente OAuth* → tipo **App para computador**. É esse
   tipo que autoriza o redirecionamento para 127.0.0.1, por onde o rclone
   recebe a resposta; "Aplicativo da Web" exigiria porta fixa, e o rclone
   escolhe uma porta livre a cada vez.
7. Cole o par abaixo e teste com uma conta real antes de distribuir.

Se o repositório for público, mantenha este arquivo fora dele e injete a chave
na hora de gerar o executável: o GitHub e o Google varrem segredos expostos e
podem revogar a credencial por conta própria — o que derrubaria o envio de
todos os clientes de uma vez.

Deixar em branco não quebra o programa: ele recai na chave compartilhada do
rclone e avisa na tela que ela tem prazo.
"""

from __future__ import annotations

#: Par criado pelo fornecedor. Vazio = usa a chave compartilhada do rclone.
DRIVE_CLIENT_ID = ""
DRIVE_CLIENT_SECRET = ""

#: Chaves próprias por serviço. Só o Drive precisa; os outros funcionam bem com
#: a chave que o rclone já embute.
APP_KEYS: dict[str, tuple[str, str]] = {
    "drive": (DRIVE_CLIENT_ID, DRIVE_CLIENT_SECRET),
}

#: Ajustes que aplicamos ao criar o remote, além do que o usuário digitou.
#:
#: `drive.file` dá acesso apenas aos arquivos criados pelo próprio programa —
#: é o suficiente para subir o zip, listar os nossos e expurgar os antigos, e
#: é o que dispensa a verificação de segurança que o Google exige do escopo
#: `drive` completo. Em troca, o destino na nuvem passa a ser uma pasta criada
#: por nós: não dá para apontar para uma pasta que já existia no Drive.
DEFAULTS: dict[str, dict[str, str]] = {
    "drive": {"scope": "drive.file"},
}


def credentials(provider: str) -> tuple[str, str]:
    """Chave do aplicativo para o serviço, ou ('', '') se não houver."""
    client_id, client_secret = APP_KEYS.get(provider, ("", ""))
    return client_id.strip(), client_secret.strip()


def has_key(provider: str) -> bool:
    return bool(credentials(provider)[0])


def defaults(provider: str) -> dict[str, str]:
    return dict(DEFAULTS.get(provider, {}))


def needs_own_key(provider: str) -> bool:
    """Serviços em que a chave compartilhada do rclone não é confiável.

    Hoje só o Drive, por decisão do próprio rclone de aposentar a dele.
    """
    return provider == "drive"
