"""
Camada de acesso ao Supabase (banco principal).

Centraliza aqui TODA a lógica de leitura/escrita, para que as telas (ui/ e
modules/) nunca montem queries diretamente.

ATUALIZAÇÃO (schema v2):
  - SAC_OS agora tem a coluna "Status_Atual" (cache do último status),
    conforme sugerido no README. Toda chamada a `registrar_status()` grava
    o histórico em Status_Sac E atualiza esse cache em SAC_OS na mesma
    operação, então o restante do sistema deve preferir ler
    SAC_OS.Status_Atual em vez de recalcular via MAX(created_at).
    Status_Sac continua existindo e é a fonte de verdade para auditoria
    (quem fez o quê e quando).
  - Sac_PF.cpf e Sac_PF.celular agora são "text" (não bigint), então não
    fazemos mais int() nesses campos.
"""
from __future__ import annotations

import datetime as dt
from functools import lru_cache
from typing import Optional

from supabase import create_client, Client

from config import Config


@lru_cache(maxsize=1)
def get_client() -> Client:
    """
    Client Supabase único (singleton) para toda a aplicação.
    Usa SUPABASE_SERVICE_KEY (ignora RLS) se estiver preenchida no .env;
    caso contrário, usa a SUPABASE_ANON_KEY normal (respeita RLS).
    """
    chave = Config.SUPABASE_SERVICE_KEY or Config.SUPABASE_ANON_KEY
    return create_client(Config.SUPABASE_URL, chave)


# ---------------------------------------------------------------------------
# STATUS
# ---------------------------------------------------------------------------
def registrar_status(os_id: int, status: str, id_user: int) -> dict:
    """
    Insere um novo registro de status (histórico/auditoria, nunca UPDATE)
    em Status_Sac E atualiza o cache SAC_OS.Status_Atual na mesma chamada.
    """
    agora = dt.datetime.now(dt.timezone.utc).isoformat()
    payload = {"OS_Id": os_id, "Status": status, "id_user": id_user, "created_at": agora}
    resp = get_client().table("Status_Sac").insert(payload).execute()

    get_client().table("SAC_OS").update({"Status_Atual": status}).eq("OS_id", os_id).execute()

    return resp.data[0] if resp.data else {}


def historico_status(os_id: int) -> list[dict]:
    """Histórico completo de status de uma OS, do mais antigo ao mais novo, com nome do usuário."""
    resp = (
        get_client()
        .table("Status_Sac")
        .select("*, Users(Nome)")
        .eq("OS_Id", os_id)
        .order("created_at", desc=False)
        .execute()
    )
    linhas = resp.data or []
    for linha in linhas:
        linha["nome_usuario"] = (linha.get("Users") or {}).get("Nome")
    return linhas


def ultimo_registro_status(os_id: int, nome_status: str) -> Optional[dict]:
    """
    Busca o último registro de um status específico (ex: "Novo",
    "Aprovado - Qualidade") de uma OS — usado nas telas para mostrar
    "Nome do usuário que criou Status X e a data".
    """
    resp = (
        get_client()
        .table("Status_Sac")
        .select("*, Users(Nome)")
        .eq("OS_Id", os_id)
        .eq("Status", nome_status)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not resp.data:
        return None
    linha = resp.data[0]
    linha["nome_usuario"] = (linha.get("Users") or {}).get("Nome")
    return linha


# ---------------------------------------------------------------------------
# SAC_OS
# ---------------------------------------------------------------------------
def criar_os(codigo: int, tipo: str) -> dict:
    """tipo: "F" (Pessoa Física), "Q" (Qualidade PJ) ou "P" (Patrimônio)."""
    payload = {
        "Codigo": codigo,
        "Tipo": tipo,
        "Criação": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    resp = get_client().table("SAC_OS").insert(payload).execute()
    return resp.data[0] if resp.data else {}


def buscar_os(os_id: int) -> Optional[dict]:
    resp = get_client().table("SAC_OS").select("*").eq("OS_id", os_id).limit(1).execute()
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# Chamado Pessoa Física (Sac_PF)
# ---------------------------------------------------------------------------
def criar_chamado_pf(dados: dict, id_user: int) -> dict:
    """
    Fluxo completo de abertura de um chamado PF (módulo 1.1.1.1):
      1. Cria a OS (Codigo=0, Tipo="F")
      2. Cria o registro em Sac_PF vinculado à OS
      3. Registra o Status inicial "Novo"
    """
    os_criada = criar_os(codigo=0, tipo="F")
    os_id = os_criada["OS_id"]

    payload_pf = {
        **dados,
        "OS_id": os_id,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    resp_pf = get_client().table("Sac_PF").insert(payload_pf).execute()
    pf_criado = resp_pf.data[0] if resp_pf.data else {}

    registrar_status(os_id, "Novo", id_user)

    return {"os_id": os_id, "id_pf": pf_criado.get("id_pf")}


def buscar_chamado_pf(os_id: int) -> Optional[dict]:
    resp = get_client().table("Sac_PF").select("*").eq("OS_id", os_id).limit(1).execute()
    return resp.data[0] if resp.data else None


def atualizar_chamado_pf(os_id: int, dados: dict) -> dict:
    resp = get_client().table("Sac_PF").update(dados).eq("OS_id", os_id).execute()
    return resp.data[0] if resp.data else {}


def salvar_midia(nome_arquivo: str, localizacao: str, os_id: int) -> dict:
    payload = {"nome": nome_arquivo, "localizacao": localizacao, "OS_id": os_id}
    resp = get_client().table("Sac_fotos_video").insert(payload).execute()
    return resp.data[0] if resp.data else {}


def listar_midias(os_id: int) -> list[dict]:
    resp = get_client().table("Sac_fotos_video").select("*").eq("OS_id", os_id).execute()
    return resp.data or []


def listar_chamados_pf(
    os_id: Optional[int] = None,
    cpf: Optional[str] = None,
    status_filtro: Optional[str] = None,
) -> list[dict]:
    """Lista de acompanhamento (módulo 1.1.1.2), lendo Status_Atual em cache de SAC_OS."""
    query = get_client().table("Sac_PF").select("*, SAC_OS!inner(Status_Atual, Criação)")
    if os_id:
        query = query.eq("OS_id", os_id)
    if cpf:
        query = query.eq("cpf", cpf)
    if status_filtro:
        query = query.eq("SAC_OS.Status_Atual", status_filtro)
    resp = query.execute()

    resultado = []
    for r in resp.data or []:
        sac_os = r.get("SAC_OS") or {}
        resultado.append(
            {
                "os_id": r["OS_id"],
                "nome": r.get("nome"),
                "cpf": r.get("cpf"),
                "status": sac_os.get("Status_Atual"),
            }
        )
    return resultado


# ---------------------------------------------------------------------------
# Chamado Pessoa Jurídica - Qualidade (Sac_Qualidade)
# ---------------------------------------------------------------------------
def buscar_cliente_por_codigo(codigo: int) -> Optional[dict]:
    resp = get_client().table("Clientes").select("*").eq("Codigo", codigo).limit(1).execute()
    return resp.data[0] if resp.data else None


def buscar_chamado_qualidade(os_id: int) -> Optional[dict]:
    """Retorna o registro de Sac_Qualidade de uma OS, já com a Razão do cliente."""
    resp = (
        get_client()
        .table("Sac_Qualidade")
        .select("*")
        .eq("OS_id", os_id)
        .limit(1)
        .execute()
    )
    if not resp.data:
        return None
    registro = resp.data[0]
    cliente = buscar_cliente_por_codigo(registro.get("id_codigo")) if registro.get("id_codigo") else None
    registro["razao"] = (cliente or {}).get("Razao")
    registro["cnpj_cpf"] = (cliente or {}).get("CNPJ/CPF")

    produto = buscar_produto(registro.get("id_produto")) if registro.get("id_produto") else None
    registro["produto_descricao"] = (produto or {}).get("Descricao")
    registro["produto_marca"] = (produto or {}).get("Marca")
    return registro


def buscar_produto(id_produto: int) -> Optional[dict]:
    resp = get_client().table("Produto").select("*").eq("id_Produto", id_produto).limit(1).execute()
    return resp.data[0] if resp.data else None


def atualizar_chamado_qualidade(os_id: int, dados: dict) -> dict:
    resp = (
        get_client()
        .table("Sac_Qualidade")
        .update(dados)
        .eq("OS_id", os_id)
        .execute()
    )
    return resp.data[0] if resp.data else {}


def listar_novos_qualidade() -> list[dict]:
    """Módulo 1.2.1.1 - OS com Tipo F ou Q e Status_Atual = 'Novo'."""
    return _listar_pf_e_qualidade_por_status("Novo")


def listar_investigacoes_abertas() -> list[dict]:
    """Módulo 1.2.1.2 - OS com Tipo F ou Q e Status_Atual = 'Em Investigação'."""
    return _listar_pf_e_qualidade_por_status("Em Investigação")


def _listar_pf_e_qualidade_por_status(status: str) -> list[dict]:
    resp = (
        get_client()
        .table("SAC_OS")
        .select("*")
        .in_("Tipo", ["F", "Q"])
        .eq("Status_Atual", status)
        .execute()
    )
    linhas = resp.data or []
    resultado = []
    for os_row in linhas:
        os_id = os_row["OS_id"]
        tipo = os_row["Tipo"]
        if tipo == "F":
            chamado = buscar_chamado_pf(os_id) or {}
            resultado.append({
                "os_id": os_id, "tipo": "F", "codigo": 0,
                "razao": chamado.get("nome"),
            })
        else:
            chamado = buscar_chamado_qualidade(os_id) or {}
            resultado.append({
                "os_id": os_id, "tipo": "Q", "codigo": chamado.get("id_codigo"),
                "razao": chamado.get("razao"),
            })
    return resultado


# ---------------------------------------------------------------------------
# Chamado Pessoa Jurídica - Patrimônio (Sac_Patrimonio)
# ---------------------------------------------------------------------------
def listar_produtos_patrimonio(os_id: int) -> list[dict]:
    """
    Uma OS de Patrimônio pode ter várias linhas de produto em
    Sac_Patrimonio (uma por item). Retorna todas, já com a descrição e
    marca do produto.
    """
    resp = get_client().table("Sac_Patrimonio").select("*").eq("OS_id", os_id).execute()
    linhas = resp.data or []
    for linha in linhas:
        produto = buscar_produto(linha.get("id_Produto")) if linha.get("id_Produto") else None
        linha["produto_descricao"] = (produto or {}).get("Descricao")
        linha["produto_marca"] = (produto or {}).get("Marca")
    return linhas


def buscar_cabecalho_patrimonio(os_id: int) -> dict:
    """
    Dados de cabeçalho (código do cliente, razão, nº da OS de manutenção,
    motivo, justificativa) são os mesmos em todas as linhas de produto da
    OS — usamos a primeira linha como referência.
    """
    linhas = listar_produtos_patrimonio(os_id)
    if not linhas:
        return {}
    primeira = linhas[0]
    cliente = buscar_cliente_por_codigo(primeira.get("Codigo")) if primeira.get("Codigo") else None
    return {
        "codigo": primeira.get("Codigo"),
        "razao": (cliente or {}).get("Razao"),
        "numero_os_manutencao": primeira.get("Numero_OS"),
        "motivo": primeira.get("Motivo"),
        "justificativa": primeira.get("Justificativa"),
    }


def atualizar_motivo_patrimonio(os_id: int, motivo: str):
    """Motivo é gravado em todas as linhas de produto da OS (mesmo padrão do schema atual)."""
    get_client().table("Sac_Patrimonio").update({"Motivo": motivo}).eq("OS_id", os_id).execute()


def atualizar_justificativa_patrimonio(os_id: int, justificativa: str):
    get_client().table("Sac_Patrimonio").update({"Justificativa": justificativa}).eq(
        "OS_id", os_id
    ).execute()


def listar_novos_patrimonio() -> list[dict]:
    """Módulo 1.2.2.1 - OS com Tipo P e Status_Atual = 'Novo'."""
    return _listar_patrimonio_por_status("Novo")


def listar_reprovados_patrimonio() -> list[dict]:
    """Módulo 1.2.3.2 - OS com Tipo P e Status_Atual = 'Reprovado - Patrimônio'."""
    return _listar_patrimonio_por_status("Reprovado - Patrimônio")


def _listar_patrimonio_por_status(status: str) -> list[dict]:
    resp = (
        get_client()
        .table("SAC_OS")
        .select("*")
        .eq("Tipo", "P")
        .eq("Status_Atual", status)
        .execute()
    )
    resultado = []
    for os_row in resp.data or []:
        cabecalho = buscar_cabecalho_patrimonio(os_row["OS_id"])
        resultado.append({
            "os_id": os_row["OS_id"],
            "codigo": cabecalho.get("codigo"),
            "razao": cabecalho.get("razao"),
            "numero_os_manutencao": cabecalho.get("numero_os_manutencao"),
        })
    return resultado


# ---------------------------------------------------------------------------
# Comercial - Reprovados Qualidade (reaproveita Sac_Qualidade)
# ---------------------------------------------------------------------------
def listar_reprovados_qualidade() -> list[dict]:
    """Módulo 1.2.3.1 - OS com Tipo Q e Status_Atual = 'Reprovado - Qualidade'."""
    resp = (
        get_client()
        .table("SAC_OS")
        .select("*")
        .eq("Tipo", "Q")
        .eq("Status_Atual", "Reprovado - Qualidade")
        .execute()
    )
    resultado = []
    for os_row in resp.data or []:
        chamado = buscar_chamado_qualidade(os_row["OS_id"]) or {}
        resultado.append({
            "os_id": os_row["OS_id"],
            "codigo": chamado.get("id_codigo"),
            "razao": chamado.get("razao"),
        })
    return resultado


# ---------------------------------------------------------------------------
# Lista de Chamados geral (todos os tipos)
# ---------------------------------------------------------------------------
def listar_todos_chamados(
    os_id: Optional[int] = None,
    status_filtro: Optional[str] = None,
    tipo_filtro: Optional[str] = None,
    cpf: Optional[str] = None,
    codigo: Optional[int] = None,
) -> list[dict]:
    """Módulo 1.1.2 - Lista de Chamados (Tipo F, Q ou P), com filtros combinados."""
    query = get_client().table("SAC_OS").select("*")
    if os_id:
        query = query.eq("OS_id", os_id)
    if status_filtro:
        query = query.eq("Status_Atual", status_filtro)
    if tipo_filtro:
        query = query.eq("Tipo", tipo_filtro)
    resp = query.execute()

    resultado = []
    for os_row in resp.data or []:
        os_id_atual, tipo = os_row["OS_id"], os_row["Tipo"]
        if tipo == "F":
            chamado = buscar_chamado_pf(os_id_atual) or {}
            if cpf and chamado.get("cpf") != cpf:
                continue
            codigo_linha, razao = 0, chamado.get("nome")
        elif tipo == "Q":
            chamado = buscar_chamado_qualidade(os_id_atual) or {}
            if codigo and chamado.get("id_codigo") != codigo:
                continue
            codigo_linha, razao = chamado.get("id_codigo"), chamado.get("razao")
        else:
            cabecalho = buscar_cabecalho_patrimonio(os_id_atual)
            if codigo and cabecalho.get("codigo") != codigo:
                continue
            codigo_linha, razao = cabecalho.get("codigo"), cabecalho.get("razao")

        resultado.append({
            "os_id": os_id_atual, "codigo": codigo_linha, "razao": razao,
            "status": os_row.get("Status_Atual"), "tipo": tipo,
        })
    return resultado


def buscar_pagamentos_completos(os_id: int) -> list[dict]:
    """
    Junta Valor_OS + Sac_pg_financeiro para exibir a tabela "Pagamento"
    nas fichas de detalhe (1.1.2.1 / 1.1.2.2 / 1.1.2.3).
    """
    valores = listar_valores_os(os_id)
    pagamentos = get_client().table("Sac_pg_financeiro").select("*").eq("OS_id", os_id).execute().data or []
    pagamento = pagamentos[0] if pagamentos else {}

    linhas = []
    for v in valores:
        linhas.append({
            "id_produto": v.get("id_Produto"),
            "valor": v.get("Valor"),
            "data_pg": pagamento.get("data_pg"),
            "codigo_sistema": pagamento.get("codigo_sistema"),
            "sistema": pagamento.get("sistema"),
            "observacao": pagamento.get("Observacao"),
        })
    return linhas



def buscar_usuario_por_login(login: str) -> Optional[dict]:
    resp = get_client().table("Users").select("*").eq("Login", login).limit(1).execute()
    return resp.data[0] if resp.data else None


def listar_usuarios(status_filtro: Optional[str] = None) -> list[dict]:
    query = get_client().table("Users").select("*")
    if status_filtro:
        query = query.eq("Status", status_filtro)
    resp = query.execute()
    return resp.data or []


def criar_ou_atualizar_usuario(dados: dict, id_user: Optional[int] = None) -> dict:
    if id_user:
        resp = get_client().table("Users").update(dados).eq("id_user", id_user).execute()
    else:
        resp = get_client().table("Users").insert(dados).execute()
    return resp.data[0] if resp.data else {}


# ---------------------------------------------------------------------------
# Financeiro - Importação de Valores (Valor_OS)
# ---------------------------------------------------------------------------
def listar_aguardando_importacao() -> list[dict]:
    """
    Módulo 1.3.1 - OS com Tipo Q ou P e Status_Atual em
    ('Aprovado - Qualidade', 'Aprovado - Comercial', 'Aprovado - Patrimônio').
    """
    status_aceitos = ["Aprovado - Qualidade", "Aprovado - Comercial", "Aprovado - Patrimônio"]
    resp = (
        get_client()
        .table("SAC_OS")
        .select("*")
        .in_("Tipo", ["Q", "P"])
        .in_("Status_Atual", status_aceitos)
        .execute()
    )
    resultado = []
    for os_row in resp.data or []:
        os_id, tipo = os_row["OS_id"], os_row["Tipo"]
        if tipo == "Q":
            chamado = buscar_chamado_qualidade(os_id) or {}
            codigo, razao = chamado.get("id_codigo"), chamado.get("razao")
        else:
            cabecalho = buscar_cabecalho_patrimonio(os_id)
            codigo, razao = cabecalho.get("codigo"), cabecalho.get("razao")
        resultado.append({
            "os_id": os_id, "tipo": tipo, "codigo": codigo, "razao": razao,
            "status": os_row["Status_Atual"],
        })
    return resultado


def salvar_valor_produto(os_id: int, id_produto: int, valor: float) -> dict:
    payload = {"OS_id": os_id, "id_Produto": id_produto, "Valor": valor}
    resp = get_client().table("Valor_OS").insert(payload).execute()
    return resp.data[0] if resp.data else {}


def listar_valores_os(os_id: int) -> list[dict]:
    resp = get_client().table("Valor_OS").select("*").eq("OS_id", os_id).execute()
    return resp.data or []


# ---------------------------------------------------------------------------
# Financeiro - Pagamento (Sac_pg_financeiro)
# ---------------------------------------------------------------------------
def listar_aguardando_pagamento() -> list[dict]:
    """Módulo 1.3.2 - OS com Tipo F, Q ou P e Status_Atual = 'Aguardando Financeiro'."""
    resp = (
        get_client()
        .table("SAC_OS")
        .select("*")
        .eq("Status_Atual", "Aguardando Financeiro")
        .execute()
    )
    resultado = []
    for os_row in resp.data or []:
        os_id, tipo = os_row["OS_id"], os_row["Tipo"]
        if tipo == "F":
            chamado = buscar_chamado_pf(os_id) or {}
            codigo, razao = 0, chamado.get("nome")
        elif tipo == "Q":
            chamado = buscar_chamado_qualidade(os_id) or {}
            codigo, razao = chamado.get("id_codigo"), chamado.get("razao")
        else:
            cabecalho = buscar_cabecalho_patrimonio(os_id)
            codigo, razao = cabecalho.get("codigo"), cabecalho.get("razao")
        resultado.append({"os_id": os_id, "tipo": tipo, "codigo": codigo, "razao": razao})
    return resultado


def salvar_pagamento(os_id: int, dados_pagamento: dict) -> dict:
    """
    dados_pagamento: {data_pg, codigo_sistema, sistema, Observacao}
    Grava em Sac_pg_financeiro.
    """
    payload = {**dados_pagamento, "OS_id": os_id}
    resp = get_client().table("Sac_pg_financeiro").insert(payload).execute()
    return resp.data[0] if resp.data else {}


def listar_pagamentos_registrados(
    data_pg: Optional[str] = None,
    tipo_filtro: Optional[str] = None,
) -> list[dict]:
    """Módulo 1.3.3 - histórico de pagamentos já feitos."""
    query = get_client().table("Sac_pg_financeiro").select("*, SAC_OS!inner(Tipo, Codigo)")
    if data_pg:
        query = query.eq("data_pg", data_pg)
    resp = query.execute()

    resultado = []
    for r in resp.data or []:
        sac_os = r.get("SAC_OS") or {}
        tipo = sac_os.get("Tipo")
        if tipo_filtro and tipo != tipo_filtro:
            continue
        os_id = r["OS_id"]
        if tipo == "F":
            chamado = buscar_chamado_pf(os_id) or {}
            razao = chamado.get("nome")
        elif tipo == "Q":
            chamado = buscar_chamado_qualidade(os_id) or {}
            razao = chamado.get("razao")
        else:
            cabecalho = buscar_cabecalho_patrimonio(os_id)
            razao = cabecalho.get("razao")
        resultado.append({
            "os_id": os_id, "tipo": tipo, "codigo": sac_os.get("Codigo") or 0,
            "razao": razao, "data_pg": r.get("data_pg"),
        })
    return resultado


# ---------------------------------------------------------------------------
# Dashboard (contagem por status - tela inicial)
# ---------------------------------------------------------------------------
def contagem_dashboard() -> dict[str, int]:
    """Retorna {"Novo": n, "Finalizado": n, "Em processo": n} lendo Status_Atual em cache."""
    resp = get_client().table("SAC_OS").select("Status_Atual").execute()
    contagem = {"Novo": 0, "Finalizado": 0, "Em processo": 0}
    for row in resp.data or []:
        status = row.get("Status_Atual") or "Novo"
        if status == "Novo":
            contagem["Novo"] += 1
        elif status == "Finalizado":
            contagem["Finalizado"] += 1
        else:
            contagem["Em processo"] += 1
    return contagem
