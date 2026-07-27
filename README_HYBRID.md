# SAC - Grupo Lamoia (Flask + PyWebView)

Aplicação desktop híbrida: **Flask** (backend) + **PyWebView** (janela nativa),
com frontend em HTML/CSS/JS. Aparencia de app desktop nativo, mas com toda a
interface construída em tecnologias web.

## Arquitetura

```
app.py                          → Entry point (Flask + PyWebView)
backend/
    __init__.py
    routes.py                   → Rotas da API REST (/api/*)
    services.py                 → Lógica de negócio (extraída dos módulos PySide6)
frontend/
    templates/
        index.html              → SPA (Single Page Application)
    static/
        css/style.css           → Estilos (paleta Grupo Lamoia)
        js/app.js               → Aplicação JavaScript completa
        assets/                 → Logo e assets estáticos
core/                           → Camada de dados (INALTERADA)
    auth.py                     → Login, hash bcrypt
    database.py                 → Supabase (todas as queries)
    external_db.py              → Postgres externo (importação de valores)
    permissions.py              → Matriz de permissões por perfil
    pdf_export.py               → Geração de PDF (reportlab)
config.py                       → Variáveis de ambiente
assets/                         → Logo original
requirements.txt                → Dependências
sac.spec                        → Spec para PyInstaller
```

## Como rodar

```bash
# 1. Criar venv e instalar dependências
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp .env.example .env           # preencha com suas credenciais

# 3. Executar
python app.py
```

## Mudanças principais em relação ao código original

### O que mudou
- **UI**: PySide6 → HTML/CSS/JS servido pelo Flask
- **Entry point**: `main.py` (PySide6) → `app.py` (Flask + PyWebView)
- **Comunicação**: Sinais Qt → API REST (fetch/JSON)
- **Navegação**: QDialog modais → modais HTML + SPA routing
- **Novos arquivos**: `backend/routes.py`, `backend/services.py`, `frontend/`

### O que NÃO mudou
- **`core/`**: 100% inalterado (database.py, auth.py, permissions.py, external_db.py, pdf_export.py)
- **`config.py`**: 100% inalterado
- **Lógica de negócio**: Extraída dos módulos PySide6 para `backend/services.py`,
  mas as regras são idênticas
- **Banco de dados**: Mesmo Supabase, mesmas tabelas, mesma estrutura
- **Permissões**: Mesma matriz em `core/permissions.py`

### Como funciona a comunicação

```
[Usuário] → [HTML/JS (frontend)] → [fetch /api/*] → [Flask (routes.py)]
    → [services.py] → [core/database.py] → [Supabase]
```

1. O frontend faz chamadas `fetch()` para endpoints Flask em `/api/*`
2. As rotas Flask validam permissões e chamam `services.py`
3. `services.py` contém a lógica de negócio (validação, escrita no banco)
4. `core/database.py` faz o acesso ao Supabase (inalterado)

### Estrutura das rotas API

| Rota | Método | Descrição |
|------|--------|-----------|
| `/api/login` | POST | Autenticação |
| `/api/logout` | POST | Logout |
| `/api/me` | GET | Usuário logado |
| `/api/permissoes` | GET | Permissões do usuário |
| `/api/dashboard` | GET | Contagem por status |
| `/api/chamados/pf` | POST | Criar chamado PF |
| `/api/chamados/pf/lista` | GET | Lista chamados PF |
| `/api/chamados/todos` | GET | Lista todos os chamados |
| `/api/fichas/pf/<os_id>` | GET | Ficha PF |
| `/api/fichas/pj-qualidade/<os_id>` | GET | Ficha PJ Qualidade |
| `/api/fichas/pj-patrimonio/<os_id>` | GET | Ficha PJ Patrimônio |
| `/api/aprovacoes/qualidade/novos` | GET | Novos Qualidade |
| `/api/aprovacoes/qualidade/investigacoes` | GET | Investigações abertas |
| `/api/investigacoes/pf/<os_id>/salvar` | POST | Salvar análise PF |
| `/api/investigacoes/pj/<os_id>/salvar` | POST | Salvar análise PJ |
| `/api/aprovacoes/patrimonio/novos` | GET | Novos Patrimônio |
| `/api/aprovacoes/comercial/reprovados-qualidade` | GET | Reprovados Qualidade |
| `/api/aprovacoes/comercial/reprovados-patrimonio` | GET | Reprovados Patrimônio |
| `/api/financeiro/importacao` | GET | Aguardando importação |
| `/api/financeiro/importacao/valor-externo` | POST | Buscar valor externo |
| `/api/financeiro/pagamento/lista` | GET | Lista para pagamento |
| `/api/financeiro/pagamentos-registrados` | GET | Pagamentos registrados |
| `/api/admin/integracao` | POST | Executar integração |
| `/api/admin/usuarios` | GET/POST | CRUD usuários |
| `/api/pdf/gerar` | POST | Gerar PDF |

## Empacotamento com PyInstaller

```bash
pip install pyinstaller
pyinstaller sac.spec
```

O executável será gerado em `dist/SAC_Grupo_Lamoia/`.

Para resolver paths de assets quando empacotado, use `resource_path()` de `app.py`:

```python
from app import resource_path
logo = resource_path("assets/logo.png")
```

## Compatibilidade

- **Windows**: ✅ (PyWebView usa EdgeChromium/MSHTML)
- **macOS**: ✅ (PyWebView usa WebKit)
- **Linux**: ✅ (PyWebView usa WebKit2Gtk)

## Segurança

- Autenticação via sessão Flask (cookie httponly)
- Cada rota API verifica permissões via `core/permissions.py`
- Senhas armazenadas com hash bcrypt
- Credenciais do banco em variáveis de ambiente (.env)
- PDF gerado no servidor (reportlab)
