// Backup Maximus - network.h
// Conexao autenticada a compartilhamentos de rede (UNC) via WNetAddConnection2.
#pragma once
#include "common.h"
#include "config.h"

namespace bm {

// Garante acesso ao caminho UNC dado. Se houver credencial configurada cujo
// uncRoot seja prefixo do caminho, conecta com ela. Retorna true se o caminho
// ficou acessivel (ou nao e UNC). errOut recebe descricao em caso de falha.
bool EnsureNetworkAccess(const std::wstring& path,
                         const std::vector<NetCredential>& creds,
                         std::wstring& errOut);

// Desconecta as conexoes abertas por EnsureNetworkAccess nesta execucao.
void DisconnectNetworkShares();

} // namespace bm
