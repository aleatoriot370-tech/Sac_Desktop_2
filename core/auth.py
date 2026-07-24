"""
Autenticação de usuários.

MELHORIA DE SEGURANÇA em relação ao desenho original:
A especificação original compara Users.Senha diretamente (texto puro).
Isso é um risco sério: qualquer pessoa com acesso de leitura ao banco (ou
a um backup) veria todas as senhas. Aqui:

  - Senhas novas/atualizadas são sempre gravadas com hash bcrypt.
  - No login, se a senha salva ainda não é um hash bcrypt (ou seja, é uma
    senha "legada" em texto puro vinda da base atual), validamos por
    comparação direta uma única vez e imediatamente re-gravamos o hash
    bcrypt no lugar. Assim a migração acontece sozinha, sem exigir troca
    de senha forçada nem script de migração em lote.
"""
from __future__ import annotations

from typing import Optional

import bcrypt

from core.database import buscar_usuario_por_login, get_client

STATUS_ATIVO = "a"
TIPO_SEM_ACESSO = "User"


def _parece_hash_bcrypt(valor: str) -> bool:
    return isinstance(valor, str) and valor.startswith(("$2a$", "$2b$", "$2y$"))


def hash_senha(senha_texto_puro: str) -> str:
    return bcrypt.hashpw(senha_texto_puro.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _senha_confere(senha_digitada: str, senha_salva: str) -> bool:
    if _parece_hash_bcrypt(senha_salva):
        return bcrypt.checkpw(senha_digitada.encode("utf-8"), senha_salva.encode("utf-8"))
    # Senha legada em texto puro
    return senha_digitada == senha_salva


def autenticar(login: str, senha: str) -> tuple[Optional[dict], Optional[str]]:
    """
    Retorna (usuario, None) em caso de sucesso, ou (None, mensagem_erro).

    Regras (conforme especificação):
      - Users.Status deve ser "a" (ativo)
      - Users.Tipo não pode ser "User" (perfil sem nenhum acesso)
    """
    usuario = buscar_usuario_por_login(login)
    if not usuario:
        return None, "Login e senha inválidos."

    if not _senha_confere(senha, usuario.get("Senha", "")):
        return None, "Login e senha inválidos."

    if usuario.get("Status") != STATUS_ATIVO:
        return None, "Usuário inativo. Contate o administrador."

    if usuario.get("Tipo") == TIPO_SEM_ACESSO:
        return None, "Usuário sem permissão de acesso. Contate o administrador."

    # Migração silenciosa de senha legada em texto puro -> bcrypt
    if not _parece_hash_bcrypt(usuario.get("Senha", "")):
        novo_hash = hash_senha(senha)
        get_client().table("Users").update({"Senha": novo_hash}).eq(
            "id_user", usuario["id_user"]
        ).execute()

    return usuario, None
