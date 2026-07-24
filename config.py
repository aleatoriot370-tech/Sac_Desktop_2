"""
Configuração central do sistema SAC Grupo Lamoia.

IMPORTANTE (segurança):
- Nunca commitar o arquivo .env real. Use .env.example como modelo.
- O Supabase não tem uma "chave de RLS" separada: existem apenas a chave
  `anon` (respeita as policies de RLS de cada tabela) e a chave
  `service_role` (ignora RLS completamente). Se SUPABASE_SERVICE_KEY for
  informada no .env, o app passa a usá-la em vez da anon key — ou seja,
  todo INSERT/UPDATE/SELECT feito pelo app ignora RLS. Isso resolve na
  hora erros como "new row violates row-level security policy", mas
  significa que a segurança de acesso deixa de existir no nível do banco
  e passa a depender inteiramente da UI (menus por perfil). Para um app
  interno de uso só pela equipe, isso costuma ser uma troca aceitável;
  para maior segurança, prefira configurar policies de RLS liberando
  INSERT/UPDATE/SELECT/DELETE para o role "anon" nas tabelas usadas pelo
  app, e deixar SUPABASE_SERVICE_KEY vazia.
- As credenciais do Postgres externo (importação de valores) também vêm do
  .env, e nunca devem ser hardcoded no código-fonte.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv é opcional; se não estiver instalado, seguimos usando
    # apenas variáveis de ambiente já definidas no sistema.
    pass


def _get(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(
            f"Variável de ambiente obrigatória ausente: {name}. "
            f"Confira seu arquivo .env (veja .env.example)."
        )
    return value


class Config:
    # --- Supabase (banco principal) ---
    SUPABASE_URL = _get("SUPABASE_URL", required=True)
    SUPABASE_ANON_KEY = _get("SUPABASE_ANON_KEY", required=True)
    # Opcional: se preenchida, o app usa esta chave (ignora RLS) em vez da anon key.
    SUPABASE_SERVICE_KEY = _get("SUPABASE_SERVICE_KEY", "")

    # --- Postgres externo (somente leitura, para importação de valores) ---
    EXTERNAL_DB_HOST = _get("EXTERNAL_DB_HOST", "")
    EXTERNAL_DB_PORT = _get("EXTERNAL_DB_PORT", "5432")
    EXTERNAL_DB_NAME = _get("EXTERNAL_DB_NAME", "")
    EXTERNAL_DB_USER = _get("EXTERNAL_DB_USER", "")
    EXTERNAL_DB_PASSWORD = _get("EXTERNAL_DB_PASSWORD", "")
    # sslmode do psycopg2: 'disable', 'prefer' (padrão), 'require', 'verify-ca', 'verify-full'.
    # Muitos provedores de Postgres gerenciado (RDS, Azure, DigitalOcean etc.)
    # exigem 'require'. Se a conexão falhar com erro relacionado a SSL, tente
    # mudar este valor no .env.
    EXTERNAL_DB_SSLMODE = _get("EXTERNAL_DB_SSLMODE", "prefer")

    # --- Armazenamento de mídia ---
    # Pasta definitiva onde as mídias do SAC ficam armazenadas.
    MEDIA_PATH = _get(
        "MEDIA_PATH", r"P:\ANÁLISE DE VENDAS\Jamerson\Mídia Sac"
    )
    # Pasta de origem usada pela rotina de integração (1.4.1) que move
    # arquivos do Google Drive local para a pasta definitiva acima.
    MEDIA_STAGING_PATH = _get(
        "MEDIA_STAGING_PATH", r"G:\Meu Drive\Sistema Sac\Midia"
    )

    APP_NAME = "SAC - Grupo Lamoia"
    ASSETS_DIR = Path(__file__).parent / "assets"
    LOGO_PATH = ASSETS_DIR / "logo.png"
