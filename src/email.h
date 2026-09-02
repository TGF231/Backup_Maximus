// Backup Maximus - email.h
// Envio de email de relatorio/alerta via SMTP (System.Net.Mail pelo PowerShell).
// A senha SMTP nunca vai para a linha de comando: e passada por variavel de
// ambiente herdada apenas pelo processo filho.
#pragma once
#include "common.h"
#include "config.h"

namespace bm {

bool SendEmail(const SmtpConfig& smtp, const std::wstring& to,
               const std::wstring& subject, const std::wstring& body,
               const std::wstring& attachmentPath,  // vazio = sem anexo
               std::wstring& errOut);

} // namespace bm
