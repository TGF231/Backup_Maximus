#include "email.h"
#include "logger.h"
#include <fstream>

namespace bm {

static std::wstring PsQuote(const std::wstring& s) {
    return L"'" + ReplaceAll(s, L"'", L"''") + L"'";
}

bool SendEmail(const SmtpConfig& smtp, const std::wstring& to,
               const std::wstring& subject, const std::wstring& body,
               const std::wstring& attachmentPath, std::wstring& errOut) {
    errOut.clear();
    if (smtp.host.empty()) { errOut = L"SMTP nao configurado."; return false; }
    if (to.empty())        { errOut = L"Email de destino nao configurado."; return false; }

    std::wstring from = smtp.from.empty() ? smtp.user : smtp.from;

    // Corpo vai num arquivo temporario (evita problemas de escaping/limite de linha).
    std::wstring bodyFile = TempFilePath(L"bm_mail", L".txt");
    {
        std::string utf8 = "\xEF\xBB\xBF" + WideToUtf8(body);
        std::ofstream f(bodyFile.c_str(), std::ios::binary);
        f.write(utf8.data(), utf8.size());
    }

    std::wstring script =
        L"$c = New-Object System.Net.Mail.SmtpClient(" + PsQuote(smtp.host) + L"," + std::to_wstring(smtp.port) + L"); "
        L"$c.EnableSsl = $" + (smtp.useSsl ? L"true" : L"false") + L"; ";
    if (!smtp.user.empty()) {
        script += L"$c.Credentials = New-Object System.Net.NetworkCredential(" + PsQuote(smtp.user) +
                  L", $env:BM_SMTP_PASS); ";
    }
    script +=
        L"$m = New-Object System.Net.Mail.MailMessage; "
        L"$m.From = " + PsQuote(from) + L"; "
        L"$m.To.Add(" + PsQuote(to) + L"); "
        L"$m.Subject = " + PsQuote(subject) + L"; "
        L"$m.Body = [System.IO.File]::ReadAllText(" + PsQuote(bodyFile) + L", [System.Text.Encoding]::UTF8); ";
    if (!attachmentPath.empty() && FileExists(attachmentPath)) {
        script += L"$a = New-Object System.Net.Mail.Attachment(" + PsQuote(attachmentPath) + L"); "
                  L"$m.Attachments.Add($a); ";
    }
    script += L"try { $c.Send($m) } finally { $m.Dispose(); $c.Dispose() }";

    // Senha via variavel de ambiente (herdada pelo filho), removida em seguida.
    std::wstring pass = UnprotectSecret(smtp.passEnc);
    if (!smtp.user.empty())
        SetEnvironmentVariableW(L"BM_SMTP_PASS", pass.c_str());

    std::wstring out;
    std::wstring cmd = L"powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command " +
                       QuoteArg(L"$ErrorActionPreference='Stop'; " + script);
    int rc = RunProcessCapture(cmd, out, 120000);

    SetEnvironmentVariableW(L"BM_SMTP_PASS", nullptr);
    if (!pass.empty()) SecureZeroMemory(&pass[0], pass.size() * sizeof(wchar_t));
    DeleteFileW(bodyFile.c_str());

    if (rc != 0) {
        errOut = L"Falha no envio SMTP (rc=" + std::to_wstring(rc) + L"): " + Trim(out).substr(0, 600);
        return false;
    }
    return true;
}

} // namespace bm
