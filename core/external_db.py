"""
Conexão com o segundo banco de dados (Postgres externo), usado apenas para
importar o último valor de compra de um produto para um cliente
(módulos 1.3.1.1 e 1.3.1.2).

Este banco é tratado como SOMENTE LEITURA a partir desta aplicação: nunca
fazemos INSERT/UPDATE/DELETE nele, apenas SELECT.
"""
from __future__ import annotations

from typing import Optional

import psycopg2
import psycopg2.extras

from config import Config


def _connect():
    if not all([Config.EXTERNAL_DB_HOST, Config.EXTERNAL_DB_NAME, Config.EXTERNAL_DB_USER]):
        raise ConnectionError(
            "As credenciais do banco externo não estão preenchidas no .env "
            "(EXTERNAL_DB_HOST, EXTERNAL_DB_NAME, EXTERNAL_DB_USER, "
            "EXTERNAL_DB_PASSWORD)."
        )
    try:
        return psycopg2.connect(
            host=Config.EXTERNAL_DB_HOST,
            port=Config.EXTERNAL_DB_PORT,
            dbname=Config.EXTERNAL_DB_NAME,
            user=Config.EXTERNAL_DB_USER,
            password=Config.EXTERNAL_DB_PASSWORD,
            sslmode=Config.EXTERNAL_DB_SSLMODE or "prefer",
            connect_timeout=8,
        )
    except Exception as exc:
        # Captura qualquer falha de conexão (timeout de rede, DNS, porta
        # fechada, credenciais erradas, SSL, etc.) e transforma numa
        # mensagem única e específica, para o usuário conseguir diagnosticar
        # sem precisar ler traceback.
        raise ConnectionError(
            f"Não foi possível conectar em {Config.EXTERNAL_DB_HOST}:"
            f"{Config.EXTERNAL_DB_PORT}/{Config.EXTERNAL_DB_NAME} "
            f"como '{Config.EXTERNAL_DB_USER}'.\n\n"
            f"Causas comuns: host/porta incorretos, firewall ou VPN "
            f"bloqueando o acesso, usuário/senha errados, ou o banco não "
            f"aceitar conexões externas (pg_hba.conf).\n\n"
            f"Erro original: {exc}"
        ) from exc


def buscar_valor_unitario(codigo_cliente: int, produto_codigo: int) -> Optional[float]:
    """
    Executa:
        SELECT punit FROM valor_ult_compra
        WHERE codigo_cliente = %s AND produto_codigo = %s

    Retorna None se não encontrar (a tela deve então permitir digitação
    manual do valor, nunca travar o fluxo do usuário).

    Levanta ConnectionError com mensagem detalhada em caso de falha de
    conexão ou consulta, para a tela poder mostrar o motivo real ao usuário.
    """
    query = """
        SELECT punit
        FROM valor_ult_compra
        WHERE codigo_cliente = %s AND produto_codigo = %s
        ORDER BY 1 DESC
        LIMIT 1
    """
    conn = _connect()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(query, (codigo_cliente, produto_codigo))
                row = cur.fetchone()
                return float(row["punit"]) if row else None
    except psycopg2.Error as exc:
        raise ConnectionError(
            f"Falha ao consultar o banco externo (tabela valor_ult_compra): {exc}"
        ) from exc
    finally:
        conn.close()


def testar_conexao() -> tuple[bool, str]:
    """Usado para diagnóstico manual: retorna (sucesso, mensagem)."""
    try:
        conn = _connect()
        conn.close()
        return True, "Conexão bem-sucedida."
    except ConnectionError as exc:
        return False, str(exc)
