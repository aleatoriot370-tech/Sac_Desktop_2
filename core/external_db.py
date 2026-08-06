"""
Conexão com o segundo banco de dados (Postgres externo), usado apenas para
importar o último valor de compra de um produto para um cliente
(módulos 1.3.1.1 e 1.3.1.2).

Este banco é tratado como SOMENTE LEITURA a partir desta aplicação: nunca
fazemos INSERT/UPDATE/DELETE nele, apenas SELECT.
"""
from __future__ import annotations

import logging
from typing import Optional

import psycopg2
import psycopg2.extras

from config import Config

logger = logging.getLogger(__name__)


def _connect():
    # --- Validação das credenciais ---
    faltando = []
    if not Config.EXTERNAL_DB_HOST:
        faltando.append("EXTERNAL_DB_HOST")
    if not Config.EXTERNAL_DB_NAME:
        faltando.append("EXTERNAL_DB_NAME")
    if not Config.EXTERNAL_DB_USER:
        faltando.append("EXTERNAL_DB_USER")
    if faltando:
        raise ConnectionError(
            f"Credenciais do banco externo ausentes no .env: {', '.join(faltando)}. "
            f"Preencha estas variáveis para habilitar a consulta ao sistema externo."
        )

    logger.info(
        "[external_db] Tentando conectar em %s:%s/%s como '%s' (sslmode=%s)",
        Config.EXTERNAL_DB_HOST,
        Config.EXTERNAL_DB_PORT,
        Config.EXTERNAL_DB_NAME,
        Config.EXTERNAL_DB_USER,
        Config.EXTERNAL_DB_SSLMODE or "prefer",
    )
    try:
        conn = psycopg2.connect(
            host=Config.EXTERNAL_DB_HOST,
            port=Config.EXTERNAL_DB_PORT,
            dbname=Config.EXTERNAL_DB_NAME,
            user=Config.EXTERNAL_DB_USER,
            password=Config.EXTERNAL_DB_PASSWORD,
            sslmode=Config.EXTERNAL_DB_SSLMODE or "prefer",
            connect_timeout=8,
        )
        logger.info("[external_db] Conexão estabelecida com sucesso.")
        return conn
    except psycopg2.OperationalError as exc:
        # Erros operacionais: rede, autenticação, SSL, banco não existe
        logger.error("[external_db] OperationalError: %s", exc)
        raise ConnectionError(
            f"Não foi possível conectar ao banco externo.\n\n"
            f"Host: {Config.EXTERNAL_DB_HOST}:{Config.EXTERNAL_DB_PORT}\n"
            f"Banco: {Config.EXTERNAL_DB_NAME}\n"
            f"Usuário: {Config.EXTERNAL_DB_USER}\n"
            f"SSL: {Config.EXTERNAL_DB_SSLMODE or 'prefer'}\n\n"
            f"Causas comuns:\n"
            f"• Host ou porta incorretos\n"
            f"• Firewall / VPN bloqueando o acesso\n"
            f"• Usuário ou senha errados\n"
            f"• Banco não aceita conexões externas (pg_hba.conf)\n"
            f"• SSL incompatível (tente EXTERNAL_DB_SSLMODE=require no .env)\n\n"
            f"Erro original: {exc}"
        ) from exc
    except Exception as exc:
        logger.error("[external_db] Erro inesperado na conexão: %s", exc)
        raise ConnectionError(
            f"Erro inesperado ao conectar ao banco externo: {exc}"
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
    # IMPORTANTE: as colunas codigo_cliente e produto_codigo são VARCHAR no
    # banco externo, por isso comparamos como string (CAST para evitar o erro
    # "operator does not exist: character varying = integer").
    query = """
        SELECT punit
        FROM valor_ult_compra
        WHERE codigo_cliente = %s AND produto_codigo = %s
        ORDER BY 1 DESC
        LIMIT 1
    """

    logger.info(
        "[external_db] buscar_valor_unitario(codigo_cliente=%s, produto_codigo=%s)",
        codigo_cliente, produto_codigo,
    )

    # Validação dos parâmetros
    if codigo_cliente is None or produto_codigo is None:
        raise ConnectionError(
            f"Parâmetros inválidos: codigo_cliente={codigo_cliente}, "
            f"produto_codigo={produto_codigo}. Ambos devem ser números inteiros."
        )

    conn = _connect()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Verifica se a tabela existe
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = 'valor_ult_compra')"
                )
                tabela_existe = cur.fetchone()[0]
                if not tabela_existe:
                    raise ConnectionError(
                        "A tabela 'valor_ult_compra' não existe no banco externo. "
                        "Verifique se o banco e a tabela estão configurados corretamente."
                    )

                # Converte para STRING para casar com as colunas VARCHAR do banco externo
                params = (str(int(codigo_cliente)), str(int(produto_codigo)))
                logger.info("[external_db] Executando query com params: %s", params)
                cur.execute(query, params)
                row = cur.fetchone()
                if row:
                    valor = float(row["punit"])
                    logger.info("[external_db] Valor encontrado: %s", valor)
                    return valor
                logger.info("[external_db] Nenhum valor encontrado para estes parâmetros.")
                return None
    except psycopg2.Error as exc:
        logger.error("[external_db] Erro psycopg2 na consulta: %s", exc)
        raise ConnectionError(
            f"Falha ao consultar o banco externo (tabela valor_ult_compra).\n\n"
            f"Parâmetros: codigo_cliente={codigo_cliente}, produto_codigo={produto_codigo}\n"
            f"Query: SELECT punit FROM valor_ult_compra ...\n\n"
            f"Erro do PostgreSQL: {exc}"
        ) from exc
    finally:
        conn.close()


def testar_conexao() -> tuple[bool, str]:
    """
    Usado para diagnóstico manual: retorna (sucesso, mensagem).
    Além de testar a conexão, verifica se a tabela valor_ult_compra existe.
    """
    try:
        conn = _connect()
        with conn:
            with conn.cursor() as cur:
                # Testa a conexão básica
                cur.execute("SELECT 1")
                logger.info("[external_db] SELECT 1 executado com sucesso.")

                # Verifica se a tabela existe
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = 'valor_ult_compra')"
                )
                tabela_existe = cur.fetchone()[0]
                if tabela_existe:
                    # Conta registros e verifica tipos das colunas
                    cur.execute("SELECT COUNT(*) FROM valor_ult_compra")
                    total = cur.fetchone()[0]
                    # Verifica tipos das colunas para diagnóstico
                    cur.execute(
                        "SELECT column_name, data_type FROM information_schema.columns "
                        "WHERE table_name = 'valor_ult_compra' "
                        "AND column_name IN ('codigo_cliente', 'produto_codigo', 'punit')"
                    )
                    colunas = {r[0]: r[1] for r in cur.fetchall()}
                    msg = (
                        f"Conexão OK. Tabela 'valor_ult_compra' encontrada "
                        f"com {total:,} registro(s).\n"
                        f"Tipos: {colunas}"
                    )
                    logger.info("[external_db] %s", msg)
                    return True, msg
                else:
                    msg = (
                        "Conexão OK, mas a tabela 'valor_ult_compra' NÃO existe "
                        "no banco de dados. Verifique o nome da tabela."
                    )
                    logger.warning("[external_db] %s", msg)
                    return False, msg
    except ConnectionError as exc:
        logger.error("[external_db] Falha no teste de conexão: %s", exc)
        return False, str(exc)
    except Exception as exc:
        logger.error("[external_db] Erro inesperado no teste: %s", exc)
        return False, f"Erro inesperado: {exc}"
