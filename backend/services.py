"""
Lógica de negócio extraída dos módulos PySide6.

Cada função aqui corresponde a uma ação de tela (salvar, aprovar, reprovar,
etc.) e encapsula validação + escrita no banco. As rotas Flask chamam
estas funções e retornam JSON.
"""
from __future__ import annotations

import datetime as dt
import random
import shutil
from pathlib import Path
from typing import Optional

from config import Config
from core import database as db
from core import external_db
from core.auth import autenticar, hash_senha


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------
def login(login_str: str, senha: str) -> tuple[Optional[dict], Optional[str]]:
    """Autentica usuário. Retorna (usuario, None) ou (None, erro)."""
    return autenticar(login_str, senha)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
TODOS_OS_STATUS = [
    "Novo", "Em Investigação", "Aprovado - Qualidade", "Reprovado - Qualidade",
    "Aprovado - Patrimônio", "Reprovado - Patrimônio", "Aprovado - Comercial",
    "Reprovado - Comercial", "Aguardando Financeiro", "Pagamento Programado", "Finalizado",
]


def get_dashboard() -> dict:
    return db.contagem_dashboard()


def get_dashboard_cards(data_inicio: str, data_fim: str) -> list[dict]:
    """
    Contagem de OS por Status_Atual, filtrando pela data em que a OS
    entrou como 'Novo' (criação). Retorna todos os 11 status.
    """
    from core.database import get_client
    # Busca OS que foram criadas no período e conta por Status_Atual
    resp = (
        get_client()
        .table("Status_Sac")
        .select("OS_Id, SAC_OS!inner(Status_Atual)")
        .eq("Status", "Novo")
        .gte("created_at", f"{data_inicio}T00:00:00")
        .lte("created_at", f"{data_fim}T23:59:59")
        .execute()
    )
    contagem = {s: 0 for s in TODOS_OS_STATUS}
    for row in (resp.data or []):
        sac_os = row.get("SAC_OS") or {}
        status = sac_os.get("Status_Atual") or "Novo"
        if status in contagem:
            contagem[status] += 1
    return [{"status": s, "quantidade": contagem[s]} for s in TODOS_OS_STATUS]


def get_dashboard_grafico(data_inicio: str, data_fim: str) -> dict:
    """
    Dados para o gráfico de barras: Abertos vs Finalizados por período.
    Granularidade automática: <=31d=dia, 32-180d=semana, >180d=mês.
    """
    from core.database import get_client
    from datetime import datetime

    d1 = datetime.fromisoformat(data_inicio)
    d2 = datetime.fromisoformat(data_fim)
    delta = (d2 - d1).days

    if delta <= 31:
        gran = "day"
    elif delta <= 180:
        gran = "week"
    else:
        gran = "month"

    # Abertos
    resp_abertos = (
        get_client()
        .table("Status_Sac")
        .select("created_at")
        .eq("Status", "Novo")
        .gte("created_at", f"{data_inicio}T00:00:00")
        .lte("created_at", f"{data_fim}T23:59:59")
        .execute()
    )
    # Finalizados
    resp_finalizados = (
        get_client()
        .table("Status_Sac")
        .select("created_at")
        .eq("Status", "Finalizado")
        .gte("created_at", f"{data_inicio}T00:00:00")
        .lte("created_at", f"{data_fim}T23:59:59")
        .execute()
    )

    def _agrupar(registros, gran):
        buckets = {}
        for r in registros:
            dt_str = r.get("created_at", "")[:19]
            try:
                dt_obj = datetime.fromisoformat(dt_str)
            except Exception:
                continue
            if gran == "day":
                key = dt_obj.strftime("%Y-%m-%d")
            elif gran == "week":
                # Início da semana (segunda)
                seg = dt_obj - __import__("datetime").timedelta(days=dt_obj.weekday())
                key = seg.strftime("%Y-%m-%d")
            else:
                key = dt_obj.strftime("%Y-%m")
            buckets[key] = buckets.get(key, 0) + 1
        return buckets

    abertos = _agrupar(resp_abertos.data or [], gran)
    finalizados = _agrupar(resp_finalizados.data or [], gran)

    # Unifica períodos
    todos_periodos = sorted(set(list(abertos.keys()) + list(finalizados.keys())))

    return {
        "granularidade": gran,
        "periodos": todos_periodos,
        "abertos": [abertos.get(p, 0) for p in todos_periodos],
        "finalizados": [finalizados.get(p, 0) for p in todos_periodos],
    }


def get_dashboard_usuarios(data_inicio: str, data_fim: str) -> list[dict]:
    """
    Tabela de usuários: quem abriu chamados no período, quantos abriu
    e quantos já foram finalizados.
    """
    from core.database import get_client

    resp = (
        get_client()
        .table("Status_Sac")
        .select("OS_Id, id_user, SAC_OS!inner(Status_Atual)")
        .eq("Status", "Novo")
        .gte("created_at", f"{data_inicio}T00:00:00")
        .lte("created_at", f"{data_fim}T23:59:59")
        .execute()
    )

    # Agrupa por usuário
    usuarios = {}  # id_user -> {nome, total_abertos, total_finalizados}
    for row in (resp.data or []):
        uid = row.get("id_user")
        if uid not in usuarios:
            usuarios[uid] = {"nome": "", "total_abertos": 0, "total_finalizados": 0, "_os_ids": set()}
        os_id = row.get("OS_Id")
        if os_id not in usuarios[uid]["_os_ids"]:
            usuarios[uid]["_os_ids"].add(os_id)
            usuarios[uid]["total_abertos"] += 1
            sac_os = row.get("SAC_OS") or {}
            if sac_os.get("Status_Atual") == "Finalizado":
                usuarios[uid]["total_finalizados"] += 1

    # Busca nomes dos usuarios
    if usuarios:
        ids = list(usuarios.keys())
        resp_users = get_client().table("Users").select("id_user, Nome").in_("id_user", ids).execute()
        for u in (resp_users.data or []):
            if u["id_user"] in usuarios:
                usuarios[u["id_user"]]["nome"] = u.get("Nome", "")

    resultado = []
    for uid, data in usuarios.items():
        total = data["total_abertos"]
        finalizados = data["total_finalizados"]
        pct = round(finalizados / total * 100, 1) if total > 0 else 0
        resultado.append({
            "nome": data["nome"],
            "total_abertos": total,
            "total_finalizados": finalizados,
            "percentual_finalizado": pct,
        })
    resultado.sort(key=lambda x: x["total_abertos"], reverse=True)
    return resultado


# ---------------------------------------------------------------------------
# Chamado PF — Abertura (1.1.1.1)
# ---------------------------------------------------------------------------
MARCAS = [
    "Paletitas", "Luigi", "Natuzon", "Real", "Icream", "Natuca", "Outros",
]
PROBLEMAS = [
    "CONE QUEBRADO", "EMBALAGEM DANIFICADA", "EMBALAGEM SUJA",
    "ETIQUETA TROCADA", "FALHA DE IMPRESSÃO", "FALHA DE SELAGEM",
    "OBJETO ESTRANHO", "PALITO QUEBRADO", "PICOLÉ SEM PALITO",
    "PICOLÉ SEM RECHEIO", "PRODUTO ABAIXO DO PESO", "PICOLÉ CORTADO",
    "PRODUTO CRISTALIZADO", "PRODUTO DERRETIDO", "PRODUTO FALTANDO NA CAIXA",
    "PRODUTO REBAIXADO", "PRODUTO SEM RÓTULO", "PRODUTO TROCADO",
    "PRODUTO VAZANDO",
]
EXTENSOES_ACEITAS = {".png", ".jpg", ".jpeg", ".mp4"}


def get_formulario_abertura_data() -> dict:
    """Retorna listas de opções para o formulário de abertura PF."""
    return {"marcas": MARCAS, "problemas": PROBLEMAS}


def salvar_chamado_pf(dados: dict, arquivos: list, id_user: int) -> dict:
    """
    Salva um chamado PF completo.
    dados: dict com os campos do formulário.
    arquivos: lista de FileStorage (upload do formulário HTML).
    """
    # Validação
    obrigatorios = [
        "nome", "email", "cpf", "celular", "motivo", "cidade", "estado",
        "marca", "nome_produto", "quantidade", "validade", "lote", "problema", "local",
    ]
    for campo in obrigatorios:
        valor = dados.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            return {"erro": f"O campo '{campo}' é obrigatório."}

    if not dados["cpf"].strip().isdigit():
        return {"erro": "CPF deve conter apenas números."}
    if not dados["celular"].strip().isdigit():
        return {"erro": "Celular deve conter apenas números."}
    if len(dados["motivo"]) > 300:
        return {"erro": "Motivo deve ter no máximo 300 caracteres."}

    # Converte quantidade para inteiro
    try:
        dados["quantidade"] = int(dados["quantidade"])
    except (TypeError, ValueError):
        return {"erro": "Quantidade deve ser um número inteiro."}

    # Cria OS + Sac_PF + Status
    resultado = db.criar_chamado_pf(dados, id_user)
    os_id = resultado["os_id"]

    # Salva mídias
    _salvar_midias(arquivos, os_id)

    return {"os_id": os_id, "mensagem": "Chamado registrado com sucesso!"}


def _salvar_midias(arquivos: list, os_id: int):
    """Renomeia e copia cada mídia para a pasta definitiva."""
    if not arquivos:
        return

    destino_dir = Path(Config.MEDIA_PATH)
    destino_dir.mkdir(parents=True, exist_ok=True)

    for arquivo in arquivos:
        if not arquivo.filename:
            continue
        extensao = Path(arquivo.filename).suffix.lower()
        if extensao not in EXTENSOES_ACEITAS:
            continue

        agora = dt.datetime.now().strftime("%Y%m%d%H%M")
        aleatorio = random.randint(1000, 9999)
        novo_nome = f"Sacpf_{agora}_{aleatorio}{extensao}"
        destino = destino_dir / novo_nome
        arquivo.save(str(destino))
        db.salvar_midia(nome_arquivo=novo_nome, localizacao=str(destino), os_id=os_id)


# ---------------------------------------------------------------------------
# Chamados — Listas
# ---------------------------------------------------------------------------
def listar_chamados_pf(os_id=None, cpf=None, status=None) -> list[dict]:
    return db.listar_chamados_pf(os_id=os_id, cpf=cpf, status_filtro=status)


def listar_todos_chamados(os_id=None, status=None, tipo=None, cpf=None, codigo=None) -> list[dict]:
    return db.listar_todos_chamados(
        os_id=os_id, status_filtro=status, tipo_filtro=tipo,
        cpf=cpf, codigo=codigo,
    )


# ---------------------------------------------------------------------------
# Chamados — Fichas (detalhes somente leitura)
# ---------------------------------------------------------------------------
def get_ficha_pf(os_id: int) -> dict:
    chamado = db.buscar_chamado_pf(os_id) or {}
    status_novo = _fmt_status(os_id, "Novo")
    status_aprovado_q = _fmt_status(os_id, "Aprovado - Qualidade")
    status_reprovado_q = _fmt_status(os_id, "Reprovado - Qualidade")
    status_finalizado = _fmt_status(os_id, "Finalizado")
    pagamentos = db.buscar_pagamentos_completos(os_id)
    midias = db.listar_midias(os_id)

    return {
        "os_id": os_id,
        "chamado": chamado,
        "status_novo": status_novo,
        "decisao_qualidade": status_aprovado_q if status_aprovado_q != "-" else status_reprovado_q,
        "status_finalizado": status_finalizado,
        "pagamentos": pagamentos,
        "midias": midias,
    }


def get_ficha_pj_qualidade(os_id: int) -> dict:
    chamado = db.buscar_chamado_qualidade(os_id) or {}
    os_row = db.buscar_os(os_id) or {}
    status_novo = _fmt_status(os_id, "Novo")
    status_aprovado_q = _fmt_status(os_id, "Aprovado - Qualidade")
    status_reprovado_q = _fmt_status(os_id, "Reprovado - Qualidade")
    status_aprovado_c = _fmt_status(os_id, "Aprovado - Comercial")
    status_reprovado_c = _fmt_status(os_id, "Reprovado - Comercial")
    status_finalizado = _fmt_status(os_id, "Finalizado")
    pagamentos = db.buscar_pagamentos_completos(os_id)
    midias = db.listar_midias(os_id)

    return {
        "os_id": os_id,
        "chamado": chamado,
        "os_row": os_row,
        "status_novo": status_novo,
        "decisao_qualidade": status_aprovado_q if status_aprovado_q != "-" else status_reprovado_q,
        "decisao_comercial": status_aprovado_c if status_aprovado_c != "-" else status_reprovado_c,
        "status_finalizado": status_finalizado,
        "pagamentos": pagamentos,
        "midias": midias,
    }


def get_ficha_pj_patrimonio(os_id: int) -> dict:
    cabecalho = db.buscar_cabecalho_patrimonio(os_id)
    produtos = db.listar_produtos_patrimonio(os_id)
    status_novo = _fmt_status(os_id, "Novo")
    status_aprovado_p = _fmt_status(os_id, "Aprovado - Patrimônio")
    status_reprovado_p = _fmt_status(os_id, "Reprovado - Patrimônio")
    status_aprovado_c = _fmt_status(os_id, "Aprovado - Comercial")
    status_reprovado_c = _fmt_status(os_id, "Reprovado - Comercial")
    status_finalizado = _fmt_status(os_id, "Finalizado")
    pagamentos = db.buscar_pagamentos_completos(os_id)
    midias = db.listar_midias(os_id)

    return {
        "os_id": os_id,
        "cabecalho": cabecalho,
        "produtos": produtos,
        "status_novo": status_novo,
        "decisao_patrimonio": status_aprovado_p if status_aprovado_p != "-" else status_reprovado_p,
        "decisao_comercial": status_aprovado_c if status_aprovado_c != "-" else status_reprovado_c,
        "status_finalizado": status_finalizado,
        "pagamentos": pagamentos,
        "midias": midias,
    }


def _fmt_status(os_id: int, nome_status: str) -> str:
    registro = db.ultimo_registro_status(os_id, nome_status)
    if not registro:
        return "-"
    data = (registro.get("created_at") or "-")[:16].replace("T", " ")
    return f"{registro.get('nome_usuario') or '-'} em {data}"


# ---------------------------------------------------------------------------
# Aprovações — Qualidade (1.2.1)
# ---------------------------------------------------------------------------
def listar_novos_qualidade() -> list[dict]:
    return db.listar_novos_qualidade()


def listar_investigacoes_abertas() -> list[dict]:
    return db.listar_investigacoes_abertas()


def get_formulario_qualidade_pf(os_id: int) -> dict:
    chamado = db.buscar_chamado_pf(os_id) or {}
    status_novo = db.ultimo_registro_status(os_id, "Novo")
    midias = db.listar_midias(os_id)
    return {
        "os_id": os_id,
        "chamado": chamado,
        "status_novo": status_novo,
        "midias": midias,
    }


def get_formulario_qualidade_pj(os_id: int) -> dict:
    chamado = db.buscar_chamado_qualidade(os_id) or {}
    os_row = db.buscar_os(os_id) or {}
    status_novo = db.ultimo_registro_status(os_id, "Novo")
    midias = db.listar_midias(os_id)
    return {
        "os_id": os_id,
        "chamado": chamado,
        "os_row": os_row,
        "status_novo": status_novo,
        "midias": midias,
    }


def abrir_investigacao(os_id: int, id_user: int, tipo: str) -> dict:
    """Muda status para 'Em Investigação'."""
    db.registrar_status(os_id, "Em Investigação", id_user)
    return {"mensagem": f"OS {os_id} agora está 'Em Investigação'.", "tipo": tipo}


# ---------------------------------------------------------------------------
# Investigações (1.2.1.2)
# ---------------------------------------------------------------------------
def get_investigacao_pf(os_id: int) -> dict:
    chamado = db.buscar_chamado_pf(os_id) or {}
    status_novo = db.ultimo_registro_status(os_id, "Novo")
    midias = db.listar_midias(os_id)
    return {"os_id": os_id, "chamado": chamado, "status_novo": status_novo, "midias": midias}


def get_investigacao_pj(os_id: int) -> dict:
    chamado = db.buscar_chamado_qualidade(os_id) or {}
    os_row = db.buscar_os(os_id) or {}
    status_novo = db.ultimo_registro_status(os_id, "Novo")
    midias = db.listar_midias(os_id)
    return {
        "os_id": os_id, "chamado": chamado, "os_row": os_row,
        "status_novo": status_novo, "midias": midias,
    }


def salvar_analise_pf(os_id: int, analise: str, resolucao: str, id_user: int, acao: str) -> dict:
    """Salva análise PF e aprova/reprova."""
    if not analise.strip():
        return {"erro": "O campo 'Análise' é obrigatório."}
    if len(analise) > 300:
        return {"erro": "Análise deve ter no máximo 300 caracteres."}
    if not resolucao.strip():
        return {"erro": "O campo 'Resolução e Resposta' é obrigatório."}

    db.atualizar_chamado_pf(os_id, {"Analise": analise, "Resolucao_Resposta": resolucao})

    if acao == "reprovar":
        db.registrar_status(os_id, "Reprovado - Qualidade", id_user)
        return {"mensagem": f"OS {os_id} reprovada.", "status": "Reprovado - Qualidade"}
    else:
        db.registrar_status(os_id, "Aprovado - Qualidade", id_user)
        db.registrar_status(os_id, "Aguardando Financeiro", id_user)
        return {"mensagem": f"OS {os_id} aprovada e encaminhada para o Financeiro.", "status": "Aprovado - Qualidade"}


def salvar_analise_pj(os_id: int, analise: str, resolucao: str, id_user: int, acao: str) -> dict:
    """Salva análise PJ e aprova/reprova."""
    if not analise.strip():
        return {"erro": "O campo 'Análise' é obrigatório."}
    if len(analise) > 300:
        return {"erro": "Análise deve ter no máximo 300 caracteres."}
    if not resolucao.strip():
        return {"erro": "O campo 'Resolução e Resposta' é obrigatório."}

    db.atualizar_chamado_qualidade(os_id, {
        "Analise Qualidade": analise, "Resolucao_Resposta": resolucao,
    })

    if acao == "reprovar":
        db.registrar_status(os_id, "Reprovado - Qualidade", id_user)
        return {"mensagem": f"OS {os_id} reprovada.", "status": "Reprovado - Qualidade"}
    else:
        db.registrar_status(os_id, "Aprovado - Qualidade", id_user)
        return {"mensagem": f"OS {os_id} aprovada.", "status": "Aprovado - Qualidade"}


# ---------------------------------------------------------------------------
# Aprovações — Patrimônio (1.2.2)
# ---------------------------------------------------------------------------
def listar_novos_patrimonio() -> list[dict]:
    return db.listar_novos_patrimonio()


def get_formulario_patrimonio(os_id: int) -> dict:
    cabecalho = db.buscar_cabecalho_patrimonio(os_id)
    produtos = db.listar_produtos_patrimonio(os_id)
    status_novo = db.ultimo_registro_status(os_id, "Novo")
    midias = db.listar_midias(os_id)
    return {
        "os_id": os_id, "cabecalho": cabecalho, "produtos": produtos,
        "status_novo": status_novo, "midias": midias,
    }


def salvar_patrimonio(os_id: int, motivo: str, id_user: int, acao: str) -> dict:
    if not motivo.strip():
        return {"erro": "O campo 'Motivo' é obrigatório."}
    if len(motivo) > 300:
        return {"erro": "Motivo deve ter no máximo 300 caracteres."}

    db.atualizar_motivo_patrimonio(os_id, motivo)

    if acao == "reprovar":
        db.registrar_status(os_id, "Reprovado - Patrimônio", id_user)
        return {"mensagem": f"OS {os_id} reprovada.", "status": "Reprovado - Patrimônio"}
    else:
        db.registrar_status(os_id, "Aprovado - Patrimônio", id_user)
        return {"mensagem": f"OS {os_id} aprovada.", "status": "Aprovado - Patrimônio"}


# ---------------------------------------------------------------------------
# Comercial — Reprovados (1.2.3)
# ---------------------------------------------------------------------------
def listar_reprovados_qualidade() -> list[dict]:
    return db.listar_reprovados_qualidade()


def listar_reprovados_patrimonio() -> list[dict]:
    return db.listar_reprovados_patrimonio()


def get_analise_comercial_pj(os_id: int) -> dict:
    chamado = db.buscar_chamado_qualidade(os_id) or {}
    os_row = db.buscar_os(os_id) or {}
    status_novo = db.ultimo_registro_status(os_id, "Novo")
    status_reprovado = db.ultimo_registro_status(os_id, "Reprovado - Qualidade")
    midias = db.listar_midias(os_id)
    return {
        "os_id": os_id, "chamado": chamado, "os_row": os_row,
        "status_novo": status_novo, "status_reprovado": status_reprovado,
        "midias": midias,
    }


def get_analise_comercial_patrimonio(os_id: int) -> dict:
    cabecalho = db.buscar_cabecalho_patrimonio(os_id)
    produtos = db.listar_produtos_patrimonio(os_id)
    status_novo = db.ultimo_registro_status(os_id, "Novo")
    status_reprovado = db.ultimo_registro_status(os_id, "Reprovado - Patrimônio")
    midias = db.listar_midias(os_id)
    return {
        "os_id": os_id, "cabecalho": cabecalho, "produtos": produtos,
        "status_novo": status_novo, "status_reprovado": status_reprovado,
        "midias": midias,
    }


def salvar_analise_comercial_pj(os_id: int, justificativa: str, id_user: int, acao: str) -> dict:
    if not justificativa.strip():
        return {"erro": "O campo 'Justificativa' é obrigatório."}

    db.atualizar_chamado_qualidade(os_id, {"Justificativa": justificativa})

    if acao == "reprovar":
        db.registrar_status(os_id, "Reprovado - Comercial", id_user)
        db.registrar_status(os_id, "Finalizado", id_user)
        return {"mensagem": f"OS {os_id} reprovada e finalizada.", "status": "Finalizado"}
    else:
        db.registrar_status(os_id, "Aprovado - Comercial", id_user)
        return {"mensagem": f"OS {os_id} aprovada comercialmente.", "status": "Aprovado - Comercial"}


def salvar_analise_comercial_patrimonio(os_id: int, justificativa: str, id_user: int, acao: str) -> dict:
    if not justificativa.strip():
        return {"erro": "O campo 'Justificativa' é obrigatório."}

    db.atualizar_justificativa_patrimonio(os_id, justificativa)

    if acao == "reprovar":
        db.registrar_status(os_id, "Reprovado - Comercial", id_user)
        db.registrar_status(os_id, "Finalizado", id_user)
        return {"mensagem": f"OS {os_id} reprovada e finalizada.", "status": "Finalizado"}
    else:
        db.registrar_status(os_id, "Aprovado - Comercial", id_user)
        return {"mensagem": f"OS {os_id} aprovada comercialmente.", "status": "Aprovado - Comercial"}


# ---------------------------------------------------------------------------
# Financeiro — Importação de Valores (1.3.1)
# ---------------------------------------------------------------------------
def listar_aguardando_importacao() -> list[dict]:
    return db.listar_aguardando_importacao()


def get_importacao_valores_qualidade(os_id: int) -> dict:
    chamado = db.buscar_chamado_qualidade(os_id) or {}
    os_row = db.buscar_os(os_id) or {}
    status_novo = db.ultimo_registro_status(os_id, "Novo")
    return {
        "os_id": os_id, "chamado": chamado, "os_row": os_row,
        "status_novo": status_novo,
    }


def get_importacao_valores_patrimonio(os_id: int) -> dict:
    cabecalho = db.buscar_cabecalho_patrimonio(os_id)
    produtos = db.listar_produtos_patrimonio(os_id)
    return {"os_id": os_id, "cabecalho": cabecalho, "produtos": produtos}


def buscar_valor_externo(codigo_cliente: int, produto_codigo: int) -> dict:
    try:
        valor = external_db.buscar_valor_unitario(codigo_cliente, produto_codigo)
        if valor is None:
            return {"valor": None, "mensagem": "Nenhum valor encontrado."}
        return {"valor": valor}
    except Exception as exc:
        return {"erro": str(exc)}


def salvar_valores_qualidade(os_id: int, id_produto: int, valor_unit: float, quantidade: float, id_user: int) -> dict:
    valor_total = valor_unit * quantidade
    db.salvar_valor_produto(os_id, id_produto, valor_total)
    db.registrar_status(os_id, "Aguardando Financeiro", id_user)
    return {"mensagem": f"OS {os_id} encaminhada para pagamento.", "valor_total": valor_total}


def salvar_valores_patrimonio(os_id: int, valores: list[dict], id_user: int) -> dict:
    """valores: [{id_produto, valor_unit, quantidade}, ...]"""
    for v in valores:
        valor_total = v["valor_unit"] * v["quantidade"]
        db.salvar_valor_produto(os_id, v["id_produto"], valor_total)
    db.registrar_status(os_id, "Aguardando Financeiro", id_user)
    return {"mensagem": f"OS {os_id} encaminhada para pagamento."}


# ---------------------------------------------------------------------------
# Financeiro — Pagamento (1.3.2)
# ---------------------------------------------------------------------------
def listar_aguardando_pagamento() -> list[dict]:
    return db.listar_aguardando_pagamento()


def get_pagamento_pf(os_id: int) -> dict:
    chamado = db.buscar_chamado_pf(os_id) or {}
    midias = db.listar_midias(os_id)
    return {"os_id": os_id, "chamado": chamado, "midias": midias}


def get_pagamento_pj_qualidade(os_id: int) -> dict:
    chamado = db.buscar_chamado_qualidade(os_id) or {}
    os_row = db.buscar_os(os_id) or {}
    valores = db.listar_valores_os(os_id)
    valor_total = sum(v.get("Valor") or 0 for v in valores)
    midias = db.listar_midias(os_id)
    return {
        "os_id": os_id, "chamado": chamado, "os_row": os_row,
        "valor_total": valor_total, "midias": midias,
    }


def get_pagamento_pj_patrimonio(os_id: int) -> dict:
    cabecalho = db.buscar_cabecalho_patrimonio(os_id)
    valores = db.listar_valores_os(os_id)
    valor_total = sum(v.get("Valor") or 0 for v in valores)
    midias = db.listar_midias(os_id)
    return {
        "os_id": os_id, "cabecalho": cabecalho,
        "valor_total": valor_total, "midias": midias,
    }


def salvar_pagamento_pf(os_id: int, dados: dict, id_user: int) -> dict:
    erros = _validar_pagamento(dados, pf=True)
    if erros:
        return {"erro": erros}

    db.salvar_valor_produto(os_id, int(dados["codigo_produto"]), float(dados["valor"]))
    db.salvar_pagamento(os_id, {
        "data_pg": dados["data_pg"],
        "codigo_sistema": dados["codigo_sistema"],
        "sistema": dados["sistema"],
        "Observacao": dados.get("observacao", ""),
    })
    db.registrar_status(os_id, "Pagamento Programado", id_user)
    db.registrar_status(os_id, "Finalizado", id_user)
    return {"mensagem": f"OS {os_id} finalizada com sucesso."}


def salvar_pagamento_pj(os_id: int, dados: dict, id_user: int) -> dict:
    erros = _validar_pagamento(dados, pf=False)
    if erros:
        return {"erro": erros}

    db.salvar_pagamento(os_id, {
        "data_pg": dados["data_pg"],
        "codigo_sistema": dados["codigo_sistema"],
        "sistema": dados["sistema"],
        "Observacao": dados.get("observacao", ""),
    })
    db.registrar_status(os_id, "Pagamento Programado", id_user)
    db.registrar_status(os_id, "Finalizado", id_user)
    return {"mensagem": f"OS {os_id} finalizada com sucesso."}


def _validar_pagamento(dados: dict, pf: bool) -> Optional[str]:
    if pf:
        if not dados.get("codigo_produto", "").strip().isdigit():
            return "Informe um Código do Produto numérico."
        try:
            float(dados.get("valor", "0").replace(",", "."))
        except ValueError:
            return "Informe um Valor numérico válido."
    if not dados.get("codigo_sistema", "").strip():
        return "Informe o Código gerado para pagamento."
    return None


# ---------------------------------------------------------------------------
# Financeiro — Pagamentos Registrados (1.3.3)
# ---------------------------------------------------------------------------
def listar_pagamentos_registrados(data_pg=None, tipo=None) -> list[dict]:
    return db.listar_pagamentos_registrados(data_pg=data_pg, tipo_filtro=tipo)


# ---------------------------------------------------------------------------
# Administrativo — Integração de Informações (1.4.1)
# ---------------------------------------------------------------------------
def executar_integracao() -> dict:
    """Move mídias de MEDIA_STAGING_PATH para MEDIA_PATH."""
    from core.database import get_client

    origem = Path(Config.MEDIA_STAGING_PATH)
    destino_dir = Path(Config.MEDIA_PATH)

    if not origem.exists():
        return {"erro": f"Pasta de origem não encontrada: {origem}"}

    destino_dir.mkdir(parents=True, exist_ok=True)
    arquivos = [p for p in origem.iterdir() if p.is_file()]

    movidos, falhas = 0, 0
    log = []
    for arquivo in arquivos:
        destino = destino_dir / arquivo.name
        try:
            shutil.move(str(arquivo), str(destino))
            get_client().table("Sac_fotos_video").update(
                {"localizacao": str(destino)}
            ).eq("nome", arquivo.name).execute()
            log.append(f"OK: {arquivo.name}")
            movidos += 1
        except Exception as exc:
            log.append(f"ERRO em {arquivo.name}: {exc}")
            falhas += 1

    return {"movidos": movidos, "falhas": falhas, "log": log}


# ---------------------------------------------------------------------------
# Administrativo — Gestão de Usuários (1.4.2)
# ---------------------------------------------------------------------------
TIPOS_USUARIO = [
    "Admin Senior", "Admin Junior", "Comercial", "Financeiro",
    "Qualidade", "Patrimônio", "User",
]


def listar_usuarios(status=None) -> list[dict]:
    return db.listar_usuarios(status_filtro=status)


def get_usuario(id_user: int) -> Optional[dict]:
    """Busca um usuário específico pelo id."""
    from core.database import get_client
    resp = get_client().table("Users").select("*").eq("id_user", id_user).limit(1).execute()
    return resp.data[0] if resp.data else None


def salvar_usuario(dados: dict, id_user: int = None) -> dict:
    """Cria ou atualiza um usuário."""
    if not dados.get("Login", "").strip():
        return {"erro": "O campo 'Login' é obrigatório."}
    if not id_user and not dados.get("Senha"):
        return {"erro": "O campo 'Senha' é obrigatório para novos usuários."}
    if not dados.get("Nome", "").strip():
        return {"erro": "O campo 'Nome' é obrigatório."}

    # Hash da senha se fornecida
    if dados.get("Senha"):
        dados["Senha"] = hash_senha(dados["Senha"])
    elif id_user:
        dados.pop("Senha", None)  # Não sobrescreve senha existente

    try:
        resultado = db.criar_ou_atualizar_usuario(dados, id_user=id_user)
        return {"mensagem": "Usuário salvo com sucesso.", "usuario": resultado}
    except Exception as exc:
        return {"erro": str(exc)}


# ---------------------------------------------------------------------------
# Chamado PF — Finalizar reprovado (1.1.1.2)
# ---------------------------------------------------------------------------
def finalizar_chamado_pf(os_id: int, id_user: int) -> dict:
    db.registrar_status(os_id, "Finalizado", id_user)
    return {"mensagem": f"OS {os_id} finalizada."}
