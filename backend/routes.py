"""
Rotas da API REST do SAC Grupo Lamoia.

Todas as rotas retornam JSON. O frontend (HTML/JS) consome estas rotas
via fetch().
"""
from __future__ import annotations

import base64
from functools import wraps
from io import BytesIO

from flask import Blueprint, request, jsonify, session, send_file

from backend import services
from core.pdf_export import gerar_pdf_ficha
from core.permissions import pode_acessar, PERMISSOES
from pathlib import Path

bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _json():
    """Retorna o body JSON da requisição ou dict vazio."""
    return request.get_json(silent=True) or {}


def _usuario_logado() -> dict | None:
    """Recupera o usuário da sessão."""
    return session.get("usuario")


def login_required(f):
    """Decorator: exige login na sessão."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not _usuario_logado():
            return jsonify({"erro": "Não autenticado."}), 401
        return f(*args, **kwargs)
    return wrapper


def _check_perm(chave: str):
    """Verifica se o usuário logado tem permissão para o módulo."""
    usuario = _usuario_logado()
    if not usuario:
        return False
    return pode_acessar(usuario.get("Tipo", ""), chave)


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------
@bp.route("/login", methods=["POST"])
def api_login():
    dados = _json()
    login_str = dados.get("login", "").strip()
    senha = dados.get("senha", "")

    if not login_str or not senha:
        return jsonify({"erro": "Informe login e senha."}), 400

    usuario, erro = services.login(login_str, senha)
    if erro:
        return jsonify({"erro": erro}), 401

    # Remove senha antes de armazenar na sessão
    usuario_safe = {k: v for k, v in usuario.items() if k != "Senha"}
    session["usuario"] = usuario_safe
    return jsonify({"usuario": usuario_safe})


@bp.route("/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"mensagem": "Logout realizado."})


@bp.route("/me", methods=["GET"])
@login_required
def api_me():
    return jsonify({"usuario": _usuario_logado()})


@bp.route("/permissoes", methods=["GET"])
@login_required
def api_permissoes():
    """Retorna as chaves de módulo que o usuário logado pode acessar."""
    usuario = _usuario_logado()
    tipo = usuario.get("Tipo", "")
    chaves = PERMISSOES.get(tipo, set())
    return jsonify({"tipo": tipo, "chaves": list(chaves)})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@bp.route("/dashboard", methods=["GET"])
@login_required
def api_dashboard():
    try:
        return jsonify(services.get_dashboard())
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/dashboard/cards", methods=["GET"])
@login_required
def api_dashboard_cards():
    """Contagem por status com filtro de data (últimos 7 dias default)."""
    from datetime import datetime, timedelta
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    if not data_inicio:
        data_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not data_fim:
        data_fim = datetime.now().strftime("%Y-%m-%d")
    try:
        return jsonify(services.get_dashboard_cards(data_inicio, data_fim))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/dashboard/grafico", methods=["GET"])
@login_required
def api_dashboard_grafico():
    """Dados para o gráfico Abertos vs Finalizados."""
    from datetime import datetime, timedelta
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    if not data_inicio:
        data_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not data_fim:
        data_fim = datetime.now().strftime("%Y-%m-%d")
    try:
        return jsonify(services.get_dashboard_grafico(data_inicio, data_fim))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/dashboard/usuarios", methods=["GET"])
@login_required
def api_dashboard_usuarios():
    """Tabela de usuários (abertos x finalizados)."""
    from datetime import datetime, timedelta
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    if not data_inicio:
        data_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not data_fim:
        data_fim = datetime.now().strftime("%Y-%m-%d")
    try:
        return jsonify(services.get_dashboard_usuarios(data_inicio, data_fim))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


# ---------------------------------------------------------------------------
# Formulários — opções
# ---------------------------------------------------------------------------
@bp.route("/formulario-abertura/opcoes", methods=["GET"])
@login_required
def api_formulario_abertura_opcoes():
    return jsonify(services.get_formulario_abertura_data())


# ---------------------------------------------------------------------------
# Chamado PF — Abertura (1.1.1.1)
# ---------------------------------------------------------------------------
@bp.route("/chamados/pf", methods=["POST"])
@login_required
def api_criar_chamado_pf():
    if not _check_perm("chamados.abertura_pf"):
        return jsonify({"erro": "Sem permissão."}), 403

    dados = {
        "nome": request.form.get("nome", ""),
        "email": request.form.get("email", ""),
        "cpf": request.form.get("cpf", ""),
        "celular": request.form.get("celular", ""),
        "motivo": request.form.get("motivo", ""),
        "cidade": request.form.get("cidade", ""),
        "estado": request.form.get("estado", ""),
        "marca": request.form.get("marca", ""),
        "nome_produto": request.form.get("nome_produto", ""),
        "quantidade": request.form.get("quantidade"),
        "validade": request.form.get("validade"),
        "lote": request.form.get("lote", ""),
        "problema": request.form.get("problema", ""),
        "local": request.form.get("local", ""),
    }
    arquivos = request.files.getlist("midias")
    usuario = _usuario_logado()

    resultado = services.salvar_chamado_pf(dados, arquivos, usuario["id_user"])
    if resultado.get("erro"):
        return jsonify(resultado), 400
    return jsonify(resultado)


# ---------------------------------------------------------------------------
# Chamados — Listas
# ---------------------------------------------------------------------------
@bp.route("/chamados/pf/lista", methods=["GET"])
@login_required
def api_lista_chamados_pf():
    if not _check_perm("chamados.lista_pf"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        os_id = request.args.get("os_id", type=int)
        cpf = request.args.get("cpf") or None
        status = request.args.get("status") or None
        return jsonify(services.listar_chamados_pf(os_id=os_id, cpf=cpf, status=status))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/chamados/todos", methods=["GET"])
@login_required
def api_lista_todos_chamados():
    if not _check_perm("chamados.lista"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        os_id = request.args.get("os_id", type=int)
        status = request.args.get("status") or None
        tipo = request.args.get("tipo") or None
        cpf = request.args.get("cpf") or None
        codigo = request.args.get("codigo", type=int)
        return jsonify(services.listar_todos_chamados(
            os_id=os_id, status=status, tipo=tipo, cpf=cpf, codigo=codigo,
        ))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/chamados/pf/<int:os_id>/finalizar", methods=["POST"])
@login_required
def api_finalizar_chamado_pf(os_id):
    usuario = _usuario_logado()
    try:
        return jsonify(services.finalizar_chamado_pf(os_id, usuario["id_user"]))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


# ---------------------------------------------------------------------------
# Chamados — Fichas (detalhes)
# ---------------------------------------------------------------------------
@bp.route("/fichas/pf/<int:os_id>", methods=["GET"])
@login_required
def api_ficha_pf(os_id):
    if not _check_perm("chamados.ficha_pf"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        return jsonify(services.get_ficha_pf(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/fichas/pj-qualidade/<int:os_id>", methods=["GET"])
@login_required
def api_ficha_pj_qualidade(os_id):
    if not _check_perm("chamados.ficha_pj_qualidade"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        return jsonify(services.get_ficha_pj_qualidade(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/fichas/pj-patrimonio/<int:os_id>", methods=["GET"])
@login_required
def api_ficha_pj_patrimonio(os_id):
    if not _check_perm("chamados.ficha_pj_patrimonio"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        return jsonify(services.get_ficha_pj_patrimonio(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


# ---------------------------------------------------------------------------
# Aprovações — Qualidade (1.2.1)
# ---------------------------------------------------------------------------
@bp.route("/aprovacoes/qualidade/novos", methods=["GET"])
@login_required
def api_novos_qualidade():
    if not _check_perm("aprovacoes.qualidade_novos"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        return jsonify(services.listar_novos_qualidade())
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/aprovacoes/qualidade/investigacoes", methods=["GET"])
@login_required
def api_investigacoes_abertas():
    if not _check_perm("aprovacoes.qualidade_investigacao"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        return jsonify(services.listar_investigacoes_abertas())
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/aprovacoes/qualidade/formulario-pf/<int:os_id>", methods=["GET"])
@login_required
def api_formulario_qualidade_pf(os_id):
    try:
        return jsonify(services.get_formulario_qualidade_pf(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/aprovacoes/qualidade/formulario-pj/<int:os_id>", methods=["GET"])
@login_required
def api_formulario_qualidade_pj(os_id):
    try:
        return jsonify(services.get_formulario_qualidade_pj(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/aprovacoes/qualidade/abrir-investigacao", methods=["POST"])
@login_required
def api_abrir_investigacao():
    dados = _json()
    os_id = dados.get("os_id")
    tipo = dados.get("tipo", "F")
    usuario = _usuario_logado()
    try:
        return jsonify(services.abrir_investigacao(os_id, usuario["id_user"], tipo))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


# ---------------------------------------------------------------------------
# Investigações (1.2.1.2)
# ---------------------------------------------------------------------------
@bp.route("/investigacoes/pf/<int:os_id>", methods=["GET"])
@login_required
def api_investigacao_pf(os_id):
    try:
        return jsonify(services.get_investigacao_pf(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/investigacoes/pj/<int:os_id>", methods=["GET"])
@login_required
def api_investigacao_pj(os_id):
    try:
        return jsonify(services.get_investigacao_pj(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/investigacoes/pf/<int:os_id>/salvar", methods=["POST"])
@login_required
def api_salvar_analise_pf(os_id):
    dados = _json()
    usuario = _usuario_logado()
    try:
        return jsonify(services.salvar_analise_pf(
            os_id, dados.get("analise", ""), dados.get("resolucao", ""),
            usuario["id_user"], dados.get("acao", "aprovar"),
        ))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/investigacoes/pj/<int:os_id>/salvar", methods=["POST"])
@login_required
def api_salvar_analise_pj(os_id):
    dados = _json()
    usuario = _usuario_logado()
    try:
        return jsonify(services.salvar_analise_pj(
            os_id, dados.get("analise", ""), dados.get("resolucao", ""),
            usuario["id_user"], dados.get("acao", "aprovar"),
        ))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


# ---------------------------------------------------------------------------
# Aprovações — Patrimônio (1.2.2)
# ---------------------------------------------------------------------------
@bp.route("/aprovacoes/patrimonio/novos", methods=["GET"])
@login_required
def api_novos_patrimonio():
    if not _check_perm("aprovacoes.patrimonio_novos"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        return jsonify(services.listar_novos_patrimonio())
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/aprovacoes/patrimonio/formulario/<int:os_id>", methods=["GET"])
@login_required
def api_formulario_patrimonio(os_id):
    try:
        return jsonify(services.get_formulario_patrimonio(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/aprovacoes/patrimonio/<int:os_id>/salvar", methods=["POST"])
@login_required
def api_salvar_patrimonio(os_id):
    dados = _json()
    usuario = _usuario_logado()
    try:
        return jsonify(services.salvar_patrimonio(
            os_id, dados.get("motivo", ""), usuario["id_user"], dados.get("acao", "aprovar"),
        ))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


# ---------------------------------------------------------------------------
# Comercial — Reprovados (1.2.3)
# ---------------------------------------------------------------------------
@bp.route("/aprovacoes/comercial/reprovados-qualidade", methods=["GET"])
@login_required
def api_reprovados_qualidade():
    if not _check_perm("aprovacoes.comercial_reprovados_qualidade"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        return jsonify(services.listar_reprovados_qualidade())
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/aprovacoes/comercial/reprovados-patrimonio", methods=["GET"])
@login_required
def api_reprovados_patrimonio():
    if not _check_perm("aprovacoes.comercial_reprovados_patrimonio"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        return jsonify(services.listar_reprovados_patrimonio())
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/aprovacoes/comercial/pj/<int:os_id>", methods=["GET"])
@login_required
def api_analise_comercial_pj(os_id):
    try:
        return jsonify(services.get_analise_comercial_pj(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/aprovacoes/comercial/patrimonio/<int:os_id>", methods=["GET"])
@login_required
def api_analise_comercial_patrimonio(os_id):
    try:
        return jsonify(services.get_analise_comercial_patrimonio(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/aprovacoes/comercial/pj/<int:os_id>/salvar", methods=["POST"])
@login_required
def api_salvar_analise_comercial_pj(os_id):
    dados = _json()
    usuario = _usuario_logado()
    try:
        return jsonify(services.salvar_analise_comercial_pj(
            os_id, dados.get("justificativa", ""), usuario["id_user"], dados.get("acao", "aprovar"),
        ))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/aprovacoes/comercial/patrimonio/<int:os_id>/salvar", methods=["POST"])
@login_required
def api_salvar_analise_comercial_patrimonio(os_id):
    dados = _json()
    usuario = _usuario_logado()
    try:
        return jsonify(services.salvar_analise_comercial_patrimonio(
            os_id, dados.get("justificativa", ""), usuario["id_user"], dados.get("acao", "aprovar"),
        ))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


# ---------------------------------------------------------------------------
# Financeiro — Importação de Valores (1.3.1)
# ---------------------------------------------------------------------------
@bp.route("/financeiro/importacao", methods=["GET"])
@login_required
def api_aguardando_importacao():
    if not _check_perm("financeiro.importacao_valores"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        return jsonify(services.listar_aguardando_importacao())
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/financeiro/importacao/qualidade/<int:os_id>", methods=["GET"])
@login_required
def api_importacao_valores_qualidade(os_id):
    try:
        return jsonify(services.get_importacao_valores_qualidade(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/financeiro/importacao/patrimonio/<int:os_id>", methods=["GET"])
@login_required
def api_importacao_valores_patrimonio(os_id):
    try:
        return jsonify(services.get_importacao_valores_patrimonio(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/financeiro/importacao/valor-externo", methods=["POST"])
@login_required
def api_buscar_valor_externo():
    dados = _json()
    try:
        codigo_cliente = dados.get("codigo_cliente")
        produto_codigo = dados.get("produto_codigo")
        # Garante conversão para inteiro
        codigo_cliente = int(codigo_cliente) if codigo_cliente is not None else None
        produto_codigo = int(produto_codigo) if produto_codigo is not None else None
        resultado = services.buscar_valor_externo(codigo_cliente, produto_codigo)
        # Se o service retornou um erro, propaga o status code adequado
        if resultado.get("erro"):
            return jsonify(resultado), 400
        return jsonify(resultado)
    except (TypeError, ValueError) as exc:
        return jsonify({"erro": f"Parâmetros inválidos: {exc}"}), 400
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/financeiro/importacao/qualidade/<int:os_id>/salvar", methods=["POST"])
@login_required
def api_salvar_valores_qualidade(os_id):
    dados = _json()
    usuario = _usuario_logado()
    try:
        return jsonify(services.salvar_valores_qualidade(
            os_id, dados.get("id_produto"), dados.get("valor_unit", 0),
            dados.get("quantidade", 0), usuario["id_user"],
        ))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/financeiro/importacao/patrimonio/<int:os_id>/salvar", methods=["POST"])
@login_required
def api_salvar_valores_patrimonio(os_id):
    dados = _json()
    usuario = _usuario_logado()
    try:
        return jsonify(services.salvar_valores_patrimonio(
            os_id, dados.get("valores", []), usuario["id_user"],
        ))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


# ---------------------------------------------------------------------------
# Financeiro — Pagamento (1.3.2)
# ---------------------------------------------------------------------------
@bp.route("/financeiro/pagamento/lista", methods=["GET"])
@login_required
def api_lista_pagamento():
    if not _check_perm("financeiro.lista_pagamento"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        return jsonify(services.listar_aguardando_pagamento())
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/financeiro/pagamento/pf/<int:os_id>", methods=["GET"])
@login_required
def api_pagamento_pf(os_id):
    try:
        return jsonify(services.get_pagamento_pf(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/financeiro/pagamento/pj-qualidade/<int:os_id>", methods=["GET"])
@login_required
def api_pagamento_pj_qualidade(os_id):
    try:
        return jsonify(services.get_pagamento_pj_qualidade(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/financeiro/pagamento/pj-patrimonio/<int:os_id>", methods=["GET"])
@login_required
def api_pagamento_pj_patrimonio(os_id):
    try:
        return jsonify(services.get_pagamento_pj_patrimonio(os_id))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/financeiro/pagamento/pf/<int:os_id>/salvar", methods=["POST"])
@login_required
def api_salvar_pagamento_pf(os_id):
    dados = _json()
    usuario = _usuario_logado()
    try:
        return jsonify(services.salvar_pagamento_pf(os_id, dados, usuario["id_user"]))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/financeiro/pagamento/pj/<int:os_id>/salvar", methods=["POST"])
@login_required
def api_salvar_pagamento_pj(os_id):
    dados = _json()
    usuario = _usuario_logado()
    try:
        return jsonify(services.salvar_pagamento_pj(os_id, dados, usuario["id_user"]))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


# ---------------------------------------------------------------------------
# Financeiro — Pagamentos Registrados (1.3.3)
# ---------------------------------------------------------------------------
@bp.route("/financeiro/pagamentos-registrados", methods=["GET"])
@login_required
def api_pagamentos_registrados():
    if not _check_perm("financeiro.pagamentos_registrados"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        data_pg = request.args.get("data_pg") or None
        tipo = request.args.get("tipo") or None
        return jsonify(services.listar_pagamentos_registrados(data_pg=data_pg, tipo=tipo))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


# ---------------------------------------------------------------------------
# Administrativo — Integração (1.4.1)
# ---------------------------------------------------------------------------
@bp.route("/admin/integracao", methods=["POST"])
@login_required
def api_integracao():
    if not _check_perm("administrativo.integracao"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        return jsonify(services.executar_integracao())
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


# ---------------------------------------------------------------------------
# Administrativo — Gestão de Usuários (1.4.2)
# ---------------------------------------------------------------------------
@bp.route("/admin/usuarios", methods=["GET"])
@login_required
def api_listar_usuarios():
    if not _check_perm("administrativo.usuarios"):
        return jsonify({"erro": "Sem permissão."}), 403
    try:
        status = request.args.get("status") or None
        return jsonify(services.listar_usuarios(status=status))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/admin/usuarios", methods=["POST"])
@login_required
def api_salvar_usuario():
    if not _check_perm("administrativo.usuarios"):
        return jsonify({"erro": "Sem permissão."}), 403
    dados = _json()
    id_user = dados.pop("id_user", None)
    try:
        return jsonify(services.salvar_usuario(dados, id_user=id_user))
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/admin/usuarios/tipos", methods=["GET"])
@login_required
def api_tipos_usuario():
    return jsonify({"tipos": services.TIPOS_USUARIO})


# ---------------------------------------------------------------------------
# Mídia — servir arquivos locais
# ---------------------------------------------------------------------------
@bp.route("/midia/<path:filepath>", methods=["GET"])
@login_required
def api_servir_midia(filepath):
    """Serve um arquivo de mídia do sistema de arquivos local."""
    import os
    import mimetypes
    from config import Config

    # Tenta o caminho direto primeiro
    if os.path.exists(filepath):
        pass  # Encontrou
    else:
        # Tenta com barras invertidas (caminhos Windows salvos com \\\)
        alt = filepath.replace("/", "\\\\")
        if os.path.exists(alt):
            filepath = alt
        else:
            # Tenta normalizar barras
            alt2 = filepath.replace("\\\\", "/").replace("\\", "/")
            if os.path.exists(alt2):
                filepath = alt2
            else:
                # Tenta procurar no MEDIA_PATH
                nome_arquivo = os.path.basename(filepath)
                if nome_arquivo and Config.MEDIA_PATH:
                    candidato = os.path.join(Config.MEDIA_PATH, nome_arquivo)
                    if os.path.exists(candidato):
                        filepath = candidato
                    else:
                        return jsonify({"erro": f"Arquivo não encontrado: {filepath}"}), 404
                else:
                    return jsonify({"erro": f"Arquivo não encontrado: {filepath}"}), 404

    mime, _ = mimetypes.guess_type(filepath)
    mime = mime or "application/octet-stream"
    return send_file(filepath, mimetype=mime)


# ---------------------------------------------------------------------------
# PDF — geração
# ---------------------------------------------------------------------------
@bp.route("/pdf/gerar", methods=["POST"])
@login_required
def api_gerar_pdf():
    """Gera um PDF e retorna como base64 para download no frontend."""
    import tempfile
    dados = _json()
    titulo = dados.get("titulo", "Relatório")
    os_id = dados.get("os_id", 0)
    campos = dados.get("campos", [])  # [(rotulo, valor), ...]
    tabela = dados.get("tabela")      # {cabecalhos: [...], linhas: [[...], ...]}
    observacoes = dados.get("observacoes")  # [(rotulo, valor), ...]

    tabela_tuple = None
    if tabela and tabela.get("cabecalhos") and tabela.get("linhas"):
        tabela_tuple = (tabela["cabecalhos"], tabela["linhas"])

    obs_tuple = None
    if observacoes:
        obs_tuple = [(o[0], o[1]) for o in observacoes]

    # Usa diretório temporário do sistema (funciona em Windows e Linux)
    tmp_dir = Path(tempfile.gettempdir())
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = tmp_dir / f"sac_pdf_{os_id}.pdf"

    try:
        gerar_pdf_ficha(
            pdf_path, titulo, os_id, campos,
            tabela=tabela_tuple, observacoes=obs_tuple,
        )
        if not pdf_path.exists():
            return jsonify({"erro": "PDF não foi gerado (arquivo não encontrado)."}), 500
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        return jsonify({"pdf_base64": pdf_b64, "filename": f"OS_{os_id}.pdf"})
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500


@bp.route("/pdf/download", methods=["POST"])
@login_required
def api_download_pdf():
    """Gera um PDF e retorna como arquivo para download direto (mais confiável)."""
    import tempfile
    from flask import send_file
    dados = _json()
    titulo = dados.get("titulo", "Relatório")
    os_id = dados.get("os_id", 0)
    campos = dados.get("campos", [])
    tabela = dados.get("tabela")
    observacoes = dados.get("observacoes")

    tabela_tuple = None
    if tabela and tabela.get("cabecalhos") and tabela.get("linhas"):
        tabela_tuple = (tabela["cabecalhos"], tabela["linhas"])

    obs_tuple = None
    if observacoes:
        obs_tuple = [(o[0], o[1]) for o in observacoes]

    tmp_dir = Path(tempfile.gettempdir())
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = tmp_dir / f"sac_pdf_{os_id}.pdf"

    try:
        gerar_pdf_ficha(
            pdf_path, titulo, os_id, campos,
            tabela=tabela_tuple, observacoes=obs_tuple,
        )
        if not pdf_path.exists():
            return jsonify({"erro": "PDF não foi gerado."}), 500
        return send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"OS_{os_id}.pdf",
        )
    except Exception as exc:
        return jsonify({"erro": str(exc)}), 500
