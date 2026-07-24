"""
Matriz de permissões por perfil (Users.Tipo), centralizada em um único
lugar. Cada tela/módulo do sistema tem uma "chave" única (MODULE_KEYS) e
cada perfil tem a lista de chaves que pode acessar.

MELHORIA em relação ao desenho original: em vez de checar o perfil
"na unha" em cada tela (o que tende a divergir com o tempo), o menu
principal (ui/main_window.py) é montado dinamicamente a partir desta
matriz, e cada módulo verifica seu próprio acesso com `pode_acessar`.
Adicionar uma tela nova = adicionar uma linha aqui.
"""
from __future__ import annotations

# Chaves de módulo (usadas também para montar o menu dinamicamente)
M_CHAMADO_ABERTURA_PF = "chamados.abertura_pf"
M_CHAMADO_LISTA_PF = "chamados.lista_pf"
M_CHAMADO_LISTA = "chamados.lista"
M_CHAMADO_FICHA_PF = "chamados.ficha_pf"
M_CHAMADO_FICHA_PJ_Q = "chamados.ficha_pj_qualidade"
M_CHAMADO_FICHA_PJ_P = "chamados.ficha_pj_patrimonio"
M_CHAMADO_FICHA_GERAR = "chamados.ficha_gerar_pdf"

M_APROV_QUALIDADE_NOVOS = "aprovacoes.qualidade_novos"
M_APROV_QUALIDADE_INVESTIGACAO = "aprovacoes.qualidade_investigacao"
M_APROV_PATRIMONIO_NOVOS = "aprovacoes.patrimonio_novos"
M_APROV_COMERCIAL_REPROVADOS_Q = "aprovacoes.comercial_reprovados_qualidade"
M_APROV_COMERCIAL_REPROVADOS_P = "aprovacoes.comercial_reprovados_patrimonio"

M_FIN_IMPORTACAO = "financeiro.importacao_valores"
M_FIN_LISTA_PAGAMENTO = "financeiro.lista_pagamento"
M_FIN_PAGOS = "financeiro.pagamentos_registrados"

M_ADM_INTEGRACAO = "administrativo.integracao"
M_ADM_USUARIOS = "administrativo.usuarios"

TODAS_AS_CHAVES = {
    M_CHAMADO_ABERTURA_PF, M_CHAMADO_LISTA_PF, M_CHAMADO_LISTA,
    M_CHAMADO_FICHA_PF, M_CHAMADO_FICHA_PJ_Q, M_CHAMADO_FICHA_PJ_P,
    M_CHAMADO_FICHA_GERAR,
    M_APROV_QUALIDADE_NOVOS, M_APROV_QUALIDADE_INVESTIGACAO,
    M_APROV_PATRIMONIO_NOVOS,
    M_APROV_COMERCIAL_REPROVADOS_Q, M_APROV_COMERCIAL_REPROVADOS_P,
    M_FIN_IMPORTACAO, M_FIN_LISTA_PAGAMENTO, M_FIN_PAGOS,
    M_ADM_INTEGRACAO, M_ADM_USUARIOS,
}

PERMISSOES: dict[str, set[str]] = {
    "Admin Senior": set(TODAS_AS_CHAVES),
    "Admin Junior": TODAS_AS_CHAVES - {M_ADM_USUARIOS},
    "Comercial": {
        M_CHAMADO_LISTA, M_CHAMADO_FICHA_PF, M_CHAMADO_FICHA_PJ_Q,
        M_CHAMADO_FICHA_PJ_P, M_CHAMADO_FICHA_GERAR,
        M_APROV_COMERCIAL_REPROVADOS_Q, M_APROV_COMERCIAL_REPROVADOS_P,
        M_FIN_LISTA_PAGAMENTO, M_FIN_PAGOS,
    },
    "Financeiro": {
        M_CHAMADO_LISTA, M_CHAMADO_FICHA_PF, M_CHAMADO_FICHA_PJ_Q,
        M_CHAMADO_FICHA_PJ_P, M_CHAMADO_FICHA_GERAR,
        M_FIN_IMPORTACAO, M_FIN_LISTA_PAGAMENTO, M_FIN_PAGOS,
    },
    "Qualidade": {
        M_CHAMADO_ABERTURA_PF, M_CHAMADO_LISTA_PF, M_CHAMADO_LISTA,
        M_CHAMADO_FICHA_PF, M_CHAMADO_FICHA_PJ_Q, M_CHAMADO_FICHA_GERAR,
        M_APROV_QUALIDADE_NOVOS, M_APROV_QUALIDADE_INVESTIGACAO,
    },
    "Patrimônio": {
        M_CHAMADO_LISTA, M_CHAMADO_FICHA_PJ_P,
        M_APROV_PATRIMONIO_NOVOS,
    },
    "User": set(),  # sem acesso a nada, nem consegue logar (ver core/auth.py)
}


def pode_acessar(tipo_usuario: str, chave_modulo: str) -> bool:
    return chave_modulo in PERMISSOES.get(tipo_usuario, set())
