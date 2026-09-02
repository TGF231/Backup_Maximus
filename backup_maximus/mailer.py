"""Envio de relatórios e alertas por SMTP.

A versão C++ precisava chamar o PowerShell para isso; aqui é smtplib, da
biblioteca padrão — sem processo externo e sem a senha passar por linha de
comando ou variável de ambiente.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from .config import SmtpConfig


def send_email(
    smtp: SmtpConfig,
    to_address: str,
    subject: str,
    body: str,
    attachment: str = "",
    timeout: float = 60.0,
) -> tuple[bool, str]:
    if not smtp.host:
        return False, "SMTP nao configurado."
    if not to_address:
        return False, "Email de destino nao configurado."

    sender = smtp.sender or smtp.user
    if not sender:
        return False, "Remetente nao configurado."

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment and os.path.isfile(attachment):
        try:
            with open(attachment, "rb") as fh:
                msg.add_attachment(
                    fh.read(),
                    maintype="text",
                    subtype="plain",
                    filename=os.path.basename(attachment),
                )
        except OSError as exc:
            return False, f"Falha ao ler o anexo: {exc}"

    try:
        # Porta 465 é SSL implícito; as demais usam STARTTLS quando SSL está ligado.
        if smtp.use_ssl and smtp.port == 465:
            server = smtplib.SMTP_SSL(smtp.host, smtp.port, timeout=timeout)
        else:
            server = smtplib.SMTP(smtp.host, smtp.port, timeout=timeout)
        with server:
            server.ehlo()
            if smtp.use_ssl and smtp.port != 465:
                server.starttls()
                server.ehlo()
            if smtp.user:
                server.login(smtp.user, smtp.password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        return False, ("Autenticacao recusada. Em contas Google/Microsoft use "
                       "uma senha de aplicativo, nao a senha da conta.")
    except (smtplib.SMTPException, OSError) as exc:
        return False, f"Falha no envio: {exc}"

    return True, ""
