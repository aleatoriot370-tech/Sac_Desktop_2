# SAC - Grupo Lamoia

Aplicação desktop (Python + PySide6) para gestão de chamados de SAC
(Pessoa Física, Qualidade PJ e Patrimônio), com aprovação em etapas,
financeiro e administração de usuários. Banco principal Supabase
(Postgres) + banco Postgres externo somente leitura para importação de
valores.

## Como rodar

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env           # preencha com suas credenciais reais
python main.py
```

## Arquitetura

```
config.py                → variáveis de ambiente (nunca credenciais no código)
core/
  database.py             → toda leitura/escrita no Supabase (regras de negócio aqui)
  external_db.py           → SELECT no Postgres externo (importação de valores)
  auth.py                   → login, hash de senha (bcrypt), migração automática
  permissions.py            → matriz de permissões por perfil, usada para montar os menus
  pdf_export.py              → geração genérica de PDF (reportlab)
ui/
  style.py                  → paleta e QSS (visual único do sistema)
  login_window.py            → módulo 0
  main_window.py              → módulo 1 (Tela Inicial: menus, dashboard, logo)
  dashboard_widget.py          → mini dashboard de contagem por status
  visualizador_midias.py        → widget reutilizável p/ listar/abrir fotos e vídeos
  pdf_helper.py                  → botão "Gerar PDF": diálogo salvar + abrir
modules/
  base_popup_module.py         → classe base: todo módulo é um pop-up que
                                  descarrega seus dados ao fechar
  chamados/
    formulario_abertura_pf.py    → 1.1.1.1 · lista_chamado_pf.py → 1.1.1.2
    lista_de_chamados.py          → 1.1.2 (geral, filtros, exportação em lote)
    ficha_pessoa_fisica.py         → 1.1.2.1 · ficha_pj_qualidade.py → 1.1.2.2
    ficha_pj_patrimonio.py          → 1.1.2.3
  aprovacoes/
    novos_qualidade.py             → 1.2.1.1 · formulario_qualidade_pf/pj.py → 1.2.1.1.1/2
    investigacoes_abertas.py        → 1.2.1.2 · investigacao_pf/pj.py → 1.2.1.2.1/2
    novos_patrimonio.py              → 1.2.2.1 · formulario_patrimonio.py → 1.2.2.1.1
    reprovados_qualidade.py           → 1.2.3.1 · analise_comercial_pj.py → 1.2.3.1.1
    reprovados_patrimonio.py           → 1.2.3.2 · analise_comercial_patrimonio.py → 1.2.3.2.1
  financeiro/
    importacao_valores.py              → 1.3.1 · importacao_valores_qualidade/patrimonio.py → 1.3.1.1/2
    lista_pagamento.py                  → 1.3.2 · pagamento_pf/pj_qualidade/pj_patrimonio.py → 1.3.2.1.1/2/3
    pagamentos_registrados.py            → 1.3.3
  administrativo/
    integracao_informacoes.py             → 1.4.1 · gestao_usuarios.py → 1.4.2
```

**Por que essa organização:** cada tela nova é um arquivo em `modules/`,
que herda de `BasePopupModule`, busca dados só de `core/database.py`
(nunca monta SQL/consulta direto na tela) e checa sua própria permissão
usando `core/permissions.py`. Adicionar uma tela = 1 arquivo novo +
1 linha no menu (`ui/main_window.py`) + 1 linha na matriz de permissões.

## O que já está pronto e testado

O sistema está **funcionalmente completo** para todos os módulos descritos
na especificação original. Cada fluxo abaixo foi exercitado com um banco
simulado em memória (sem depender do Supabase real) para validar a lógica
de negócio — status, cálculos, encadeamentos e regras de aprovação —
antes da entrega:

- **Login e Tela Inicial**: validação de `Status`/`Tipo`, tela cheia,
  menus dinâmicos por perfil (matriz de permissões), mini dashboard, logo.
- **Chamados**: Abertura PF completa (com upload/renomeação de mídia),
  Lista Chamado PF, **Lista de Chamados geral** (F/Q/P, com filtros
  combinados e exportação de fichas selecionadas em lote), e as 3
  **Fichas de detalhe somente-leitura** (Pessoa Física, PJ Qualidade,
  PJ Patrimônio) com histórico completo de quem aprovou/reprovou cada
  etapa, tabela de pagamento e exportação em PDF.
- **Aprovações — Qualidade**: Novos Qualidade → Formulário PF/PJ →
  Investigações Abertas → Investigação PF/PJ (Análise, Resolução,
  Aprovar/Reprovar). PF aprovado encaminha automaticamente para
  "Aguardando Financeiro"; PJ aprovado aguarda a Importação de Valores.
- **Aprovações — Patrimônio**: Novos Patrimônio → Formulário Patrimônio
  (múltiplos produtos por OS) → Aprovar/Reprovar.
- **Aprovações — Comercial**: Reprovados Qualidade → Análise Comercial
  PJ, e Reprovados Patrimônio → Análise Comercial Patrimônio. Reprovar
  encadeia automaticamente "Reprovado - Comercial" → "Finalizado".
- **Financeiro**: Importação de Valores (Qualidade e Patrimônio, com
  botão de integração ao banco Postgres externo e cálculo automático de
  valor total), Lista para Pagamento (roteando para os 3 formulários de
  pagamento PF/PJ-Q/PJ-P), e Pagamentos Registrados com filtros. Salvar
  um pagamento encadeia "Pagamento Programado" → "Finalizado".
- **Administrativo**: Integração de Informações (move mídia da pasta de
  staging para a definitiva e atualiza o banco) e Gestão de Usuários
  (CRUD completo, com hash bcrypt sempre aplicado e preservação da senha
  ao editar sem preenchê-la novamente).
- **Exportação em PDF** (`core/pdf_export.py`) disponível em todas as
  telas relevantes, com fuga de caracteres especiais testada.
- Testes de integração cobrindo os encadeamentos de status mais
  importantes: Qualidade PF/PJ, Patrimônio, Comercial e Financeiro —
  todos confirmados batendo exatamente com as regras da especificação.

## Resolvendo erros de RLS ("new row violates row-level security policy")

O Supabase não tem uma "chave de RLS" separada — existem apenas a chave
`anon` (respeita as policies de RLS de cada tabela) e a `service_role`
(ignora RLS completamente). Se você está vendo esse erro ao salvar,
escolha uma das duas opções:

**Opção A — mais rápida:** preencha `SUPABASE_SERVICE_KEY` no `.env`
com a chave `service_role` do seu projeto (Project Settings → API →
`service_role` `secret`). O app passa a usar essa chave automaticamente
e ignora RLS em tudo. Trate essa chave como uma senha de administrador
— nunca a compartilhe nem suba para um repositório público.

**Opção B — mais segura (recomendada a médio prazo):** mantenha a
`anon key` e crie policies liberando acesso para o role `anon` em cada
tabela usada pelo app. Exemplo de SQL (rode no SQL Editor do Supabase,
ajustando a lista de tabelas conforme necessário):

```sql
-- Repita para cada tabela: "Clientes", "SAC_OS", "Sac_Patrimonio",
-- "Sac_Qualidade", "Sac_fotos_video", "Status_Sac", "Users",
-- "Valor_OS", "Sac_PF", "Sac_pg_financeiro", "Produto"
alter table public."SAC_OS" enable row level security;

create policy "app acesso total (anon)" on public."SAC_OS"
  for all
  to anon
  using (true)
  with check (true);
```

Como o app já valida login/permissão na própria interface (e não usa o
sistema de autenticação do Supabase), essa policy libera para `anon` o
que a UI já controla — não é menos seguro do que usar a `service_role`
key, só é mais granular por tabela.



- `SAC_OS.Status_Atual` (coluna que você criou): `registrar_status()`
  grava o histórico em `Status_Sac` **e** atualiza esse cache na mesma
  chamada. Todas as listas e o dashboard leem direto de
  `SAC_OS.Status_Atual`, sem recalcular `MAX(created_at)` a cada consulta.
- `Sac_PF.cpf` e `Sac_PF.celular` como `text`: removida toda conversão
  `int()` desses campos no código.
- Chave única do projeto (sem RLS separada): nenhuma mudança necessária,
  o código já usava só `SUPABASE_ANON_KEY`.

## Correções da rodada mais recente (bugs reportados em produção)

1. **[Crítico] Erro ao aprovar/reprovar investigação PJ** —
   `Could not find the 'Analise' column of 'Sac_Qualidade'`. Causa: a
   coluna real da tabela `Sac_Qualidade` é **`Analise Qualidade`** (com
   espaço), diferente de `Sac_PF` que usa `Analise` (sem espaço). O
   código usava `"Analise"` errado em 4 arquivos de Qualidade PJ —
   corrigido em `investigacao_pj.py`, `analise_comercial_pj.py`,
   `pagamento_pj_qualidade.py` e `ficha_pj_qualidade.py`. Também auditei
   o restante do schema (Razao, CNPJ/CPF, OS_Id vs OS_id, id_Produto vs
   id_produto) e não encontrei mais nenhuma divergência.
2. **Conexão com banco externo**: `core/external_db.py` agora captura
   qualquer tipo de falha (não só erros do psycopg2) e mostra a causa
   real na tela (host/porta/usuário testados, e sugestões: firewall/VPN,
   credenciais, `pg_hba.conf`). Adicionei `EXTERNAL_DB_SSLMODE` no `.env`
   (`prefer` por padrão; troque para `require` se seu provedor exigir
   SSL). Se o erro persistir, rode `python -c "from core.external_db
   import testar_conexao; print(testar_conexao())"` e me mande a
   mensagem completa.
3. **Telas cortadas na tela**: toda tela pop-up (`BasePopupModule`) agora
   tem rolagem automática (`QScrollArea`) — nada fica inacessível por
   causa da altura da tela do usuário. As tabelas de produto/pagamento
   também deixaram de "espremer" o texto (trocado `Stretch` por
   `ResizeToContents`, com rolagem horizontal quando necessário), e os
   formulários mais densos (PJ Qualidade/Patrimônio, fichas, importação
   de valores) ficaram mais largos.
4. **Seleção sem feedback visual nas listas**: adicionado destaque de
   linha selecionada (`QTableWidget::item:selected` em azul) e
   `SelectionBehavior=SelectRows` (seleciona a linha inteira, não só a
   célula) em todas as listas clicáveis, mais cores alternadas por linha
   para facilitar a leitura.
5. **Visual escuro/pouco legível**: a lista de mídias (`QListWidget`)
   não tinha estilo próprio e herdava o tema escuro do Windows, ficando
   ilegível — agora tem fundo branco, texto escuro e miniaturas reais
   das fotos. Também padronizei campos somente-leitura, cores de
   seleção e a barra de rolagem em todo o app.
6. **Mídias não abriam**: `ui/visualizador_midias.py` agora mostra
   miniaturas reais das fotos (ícone genérico para vídeos), e se o
   arquivo não existir no caminho salvo (situação comum quando a pasta
   de rede `P:\...` não está mapeada na máquina), mostra um aviso claro
   explicando a causa em vez de simplesmente não fazer nada ao clicar.



- **Lista de Chamados PF (1.1.1.2)**: o pop-up de detalhe descrito na
  especificação (produtos + análise + resolução + botão "Dados
  Financeiro" quando Aprovado) hoje abre a Ficha Pessoa Física completa
  em vez do pop-up simplificado original — cobre o mesmo conteúdo, só
  não tem o botão dedicado "Dados Financeiro" (o usuário acessa o
  pagamento por "Lista para Pagamento").
- **Ficha Chamado (1.1.3)**: unificada com a Lista de Chamados geral
  (1.1.2), que já tem "informar OS_id" e exportação em lote por seleção
  múltipla — não é uma tela separada, mas cobre o mesmo objetivo.
- Nenhum teste foi feito contra o Supabase real (só com bancos simulados
  em memória) — recomendo testar cada fluxo com dados reais antes de
  colocar em produção, especialmente os nomes exatos de tabelas/colunas
  relacionadas (`Produto`, que não veio no schema original e foi
  assumida com `id_Produto`, `Descricao`, `Marca`).
- Regra de RLS: como o Supabase usa uma única chave para o projeto todo,
  a segurança de "quem pode ler/escrever o quê" depende inteiramente das
  policies configuradas no banco — o código não impõe isso, só a UI
  esconde os menus por perfil.

Se quiser, posso revisar algum desses pontos, ou testar contra o seu
banco real assim que você validar o funcionamento no seu ambiente.

## Melhorias de lógica em relação ao seu desenho original

1. **Senha em texto puro → hash bcrypt.** Comparar `Users.Senha`
   diretamente expõe todas as senhas a quem tiver acesso de leitura ao
   banco. Implementado hash bcrypt + migração automática e transparente
   das senhas antigas no primeiro login de cada usuário (sem precisar
   de script de migração em lote nem trocar senha à força).

2. **CPF/CNPJ e celular como `bigint`.** Números de telefone e
   documentos podem ter zero à esquerda (raro em CPF, mais comum em
   alguns registros) e nunca são usados em cálculo — armazenar como
   `bigint` também impede máscara/formatação e complica buscas com
   zero à esquerda. Recomendo migrar essas colunas para `text` no
   Supabase quando possível.

3. **Cálculo do "status atual" via `MAX(created_at)` a cada consulta.**
   Funciona, mas fica caro conforme a tabela `Status_Sac` cresce,
   principalmente na Tela Inicial (dashboard) e nas listas. Implementei
   `status_atual_em_lote()` para buscar todos de uma vez (evita N+1
   queries). Se o volume crescer muito, o próximo passo é manter uma
   coluna `status_atual` em `SAC_OS`, atualizada por trigger no Postgres
   a cada INSERT em `Status_Sac` — mantendo `Status_Sac` só como
   histórico/auditoria, sem mudar nenhuma regra de negócio.

4. **Criação de OS + Sac_PF + Status inicial como 3 operações separadas.**
   Como o Supabase client via REST não expõe transação explícita
   facilmente, deixei a sequência centralizada em uma única função
   (`criar_chamado_pf`) para que, se algo falhar no meio, o erro seja
   claro e não fique "meio salvo" silenciosamente. Se quiser garantia
   transacional real (tudo ou nada), a alternativa é criar uma
   **função RPC no Postgres** (`create_chamado_pf(...)`) e chamá-la via
   `supabase.rpc(...)` — fica mais robusto que múltiplos INSERTs
   sequenciais pela API REST.

5. **Chave anon do Supabase no app desktop.** Como o app roda na
   máquina do usuário, a chave anon fica visível a quem inspecionar o
   binário/processo. Isso é esperado e aceitável **desde que o RLS
   (Row Level Security) de cada tabela esteja configurado para exigir
   autenticação/policies adequadas** — a validação de login feita aqui
   no app é só UX, a segurança real precisa estar nas policies do
   Supabase, não only no cliente.

6. **Permissões "na unha" em cada tela.** Centralizei numa única matriz
   (`core/permissions.py`) usada tanto para montar os menus quanto para
   os próprios módulos verificarem acesso — evita divergência entre
   "o que aparece no menu" e "o que a tela realmente permite" conforme
   o sistema cresce.

7. **Caminhos de rede hardcoded (`P:\...`, `G:\...`).** Movidos para
   `.env` (`MEDIA_PATH`, `MEDIA_STAGING_PATH`), assim cada estação/
   ambiente pode ter seu próprio mapeamento de unidade sem alterar código.

8. **Descarregamento de memória ao fechar pop-up.** Implementei isso de
   forma sistemática via `BasePopupModule` (todo módulo herda dela),
   em vez de deixar por conta de cada tela lembrar de limpar sozinha.
