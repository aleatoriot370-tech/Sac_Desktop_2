/**
 * SAC - Grupo Lamoia
 * Aplicação SPA (Single Page Application) — frontend completo.
 *
 * Comunica-se com o backend via fetch() nas rotas /api/*.
 * Toda a lógica de negócio permanece no servidor (services.py).
 */

// ============================================================
// Estado global
// ============================================================
const State = {
    usuario: null,
    permissoes: [],
    currentPage: 'home',
};

// ============================================================
// API Helper
// ============================================================
async function api(url, options = {}) {
    const defaults = {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
    };
    if (options.body && !(options.body instanceof FormData)) {
        options.body = JSON.stringify(options.body);
    } else if (options.body instanceof FormData) {
        delete defaults.headers['Content-Type'];
    }
    const resp = await fetch(url, { ...defaults, ...options });
    const data = await resp.json();
    if (!resp.ok) {
        throw new Error(data.erro || `Erro ${resp.status}`);
    }
    return data;
}

// ============================================================
// Toast (notificações)
// ============================================================
function toast(msg, tipo = 'info') {
    let el = document.getElementById('toast');
    if (!el) {
        el = document.createElement('div');
        el.id = 'toast';
        el.className = 'toast';
        document.body.appendChild(el);
    }
    el.textContent = msg;
    el.className = `toast toast-${tipo} show`;
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove('show'), 4000);
}

// ============================================================
// Router (hash-based)
// ============================================================
function navigate(page, params = {}) {
    State.currentPage = page;
    State.pageParams = params;
    render();
}

// ============================================================
// Render principal
// ============================================================
function render() {
    const app = document.getElementById('app');
    if (!State.usuario) {
        app.innerHTML = renderLogin();
        bindLogin();
    } else {
        app.innerHTML = renderShell();
        bindShell();
        renderPage();
    }
}

// ============================================================
// Login
// ============================================================
function renderLogin() {
    return `
    <div class="login-container">
        <div class="login-card">
            <img src="/static/assets/logo.png" alt="Grupo Lamoia" onerror="this.style.display='none'">
            <h2>Acesso ao Sistema</h2>
            <div class="erro" id="login-erro"></div>
            <div class="form-group" style="margin-bottom:12px">
                <input type="text" id="login-user" placeholder="Login" autocomplete="username">
            </div>
            <div class="form-group" style="margin-bottom:16px">
                <input type="password" id="login-pass" placeholder="Senha" autocomplete="current-password">
            </div>
            <button class="btn btn-primary" style="width:100%" id="btn-login">Entrar</button>
        </div>
    </div>`;
}

function bindLogin() {
    const btn = document.getElementById('btn-login');
    const pass = document.getElementById('login-pass');
    const user = document.getElementById('login-user');

    async function doLogin() {
        const loginStr = user.value.trim();
        const senha = pass.value;
        if (!loginStr || !senha) {
            document.getElementById('login-erro').textContent = 'Informe login e senha.';
            return;
        }
        try {
            const data = await api('/api/login', {
                method: 'POST',
                body: { login: loginStr, senha },
            });
            State.usuario = data.usuario;
            await loadPermissoes();
            render();
        } catch (e) {
            document.getElementById('login-erro').textContent = e.message;
            pass.value = '';
        }
    }

    btn.addEventListener('click', doLogin);
    pass.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
    user.addEventListener('keydown', e => { if (e.key === 'Enter') pass.focus(); });
    user.focus();
}

async function loadPermissoes() {
    try {
        const data = await api('/api/permissoes');
        State.permissoes = data.chaves || [];
    } catch {
        State.permissoes = [];
    }
}

function hasPerm(chave) {
    return State.permissoes.includes(chave);
}

// ============================================================
// Shell (topbar + menubar + conteúdo)
// ============================================================
function renderShell() {
    return `
    <div class="app-container">
        <div class="topbar">
            <div class="brand">SAC - Grupo Lamoia</div>
            <div class="user-info">
                <span class="nome">${esc(State.usuario?.Nome || '')}</span>
                <button id="btn-logout">Sair</button>
            </div>
        </div>
        <nav class="menubar" id="menubar">
            ${renderMenus()}
        </nav>
        <main class="main-content" id="page-content">
            <div class="loading"><div class="spinner"></div> Carregando...</div>
        </main>
    </div>
    <div class="modal-overlay" id="modal-overlay">
        <div class="modal" id="modal-container"></div>
    </div>`;
}

function renderMenus() {
    let html = '';

    // Chamados
    if (hasPerm('chamados.abertura_pf') || hasPerm('chamados.lista_pf') || hasPerm('chamados.lista')) {
        html += `<div class="menu-item" data-menu="chamados">Chamados
            <div class="menu-dropdown">
                ${hasPerm('chamados.abertura_pf') ? '<div class="submenu-trigger">Chamado Pessoa Física<div class="submenu-flyout"><a href="#" data-page="chamado-abertura-pf">Formulário Abertura</a><a href="#" data-page="lista-chamado-pf">Lista Chamado PF</a></div></div>' : ''}
                ${hasPerm('chamados.lista') ? '<a href="#" data-page="lista-chamados">Lista de Chamados</a>' : ''}
            </div>
        </div>`;
    }

    // Aprovações
    if (hasPerm('aprovacoes.qualidade_novos') || hasPerm('aprovacoes.qualidade_investigacao') || hasPerm('aprovacoes.patrimonio_novos') || hasPerm('aprovacoes.comercial_reprovados_qualidade') || hasPerm('aprovacoes.comercial_reprovados_patrimonio')) {
        let sub = '';
        if (hasPerm('aprovacoes.qualidade_novos') || hasPerm('aprovacoes.qualidade_investigacao')) {
            sub += `<div class="submenu-trigger">Qualidade<div class="submenu-flyout">
                ${hasPerm('aprovacoes.qualidade_novos') ? '<a href="#" data-page="novos-qualidade">Novos Qualidade</a>' : ''}
                ${hasPerm('aprovacoes.qualidade_investigacao') ? '<a href="#" data-page="investigacoes-abertas">Investigações Abertas</a>' : ''}
            </div></div>`;
        }
        if (hasPerm('aprovacoes.patrimonio_novos')) {
            sub += `<div class="submenu-trigger">Patrimônio<div class="submenu-flyout">
                <a href="#" data-page="novos-patrimonio">Novos Patrimônio</a>
            </div></div>`;
        }
        if (hasPerm('aprovacoes.comercial_reprovados_qualidade') || hasPerm('aprovacoes.comercial_reprovados_patrimonio')) {
            sub += `<div class="submenu-trigger">Comercial<div class="submenu-flyout">
                ${hasPerm('aprovacoes.comercial_reprovados_qualidade') ? '<a href="#" data-page="reprovados-qualidade">Reprovados Qualidade</a>' : ''}
                ${hasPerm('aprovacoes.comercial_reprovados_patrimonio') ? '<a href="#" data-page="reprovados-patrimonio">Reprovados Patrimônio</a>' : ''}
            </div></div>`;
        }
        html += `<div class="menu-item" data-menu="aprovacoes">Aprovações<div class="menu-dropdown">${sub}</div></div>`;
    }

    // Financeiro
    if (hasPerm('financeiro.importacao_valores') || hasPerm('financeiro.lista_pagamento') || hasPerm('financeiro.pagamentos_registrados')) {
        html += `<div class="menu-item" data-menu="financeiro">Financeiro<div class="menu-dropdown">
            ${hasPerm('financeiro.importacao_valores') ? '<a href="#" data-page="importacao-valores">Importação de Valores</a>' : ''}
            ${hasPerm('financeiro.lista_pagamento') ? '<a href="#" data-page="lista-pagamento">Lista para Pagamento</a>' : ''}
            ${hasPerm('financeiro.pagamentos_registrados') ? '<a href="#" data-page="pagamentos-registrados">Pagamentos Registrados</a>' : ''}
        </div></div>`;
    }

    // Administrativo
    if (hasPerm('administrativo.integracao') || hasPerm('administrativo.usuarios')) {
        html += `<div class="menu-item" data-menu="administrativo">Administrativo<div class="menu-dropdown">
            ${hasPerm('administrativo.integracao') ? '<a href="#" data-page="integracao">Integração Informações</a>' : ''}
            ${hasPerm('administrativo.usuarios') ? '<a href="#" data-page="gestao-usuarios">Gestão de Usuários</a>' : ''}
        </div></div>`;
    }

    return html;
}

function bindShell() {
    document.getElementById('btn-logout').addEventListener('click', async () => {
        await api('/api/logout', { method: 'POST' });
        State.usuario = null;
        State.permissoes = [];
        render();
    });

    // Menu links
    document.querySelectorAll('[data-page]').forEach(el => {
        el.addEventListener('click', e => {
            e.preventDefault();
            navigate(el.dataset.page);
        });
    });
}

// ============================================================
// Renderização de páginas
// ============================================================
async function renderPage() {
    const content = document.getElementById('page-content');
    const page = State.currentPage;

    try {
        switch (page) {
            case 'home':
                await renderHome(content);
                break;
            case 'chamado-abertura-pf':
                await renderChamadoAberturaPF(content);
                break;
            case 'lista-chamado-pf':
                await renderListaChamadoPF(content);
                break;
            case 'lista-chamados':
                await renderListaChamados(content);
                break;
            case 'novos-qualidade':
                await renderNovosQualidade(content);
                break;
            case 'investigacoes-abertas':
                await renderInvestigacoesAbertas(content);
                break;
            case 'novos-patrimonio':
                await renderNovosPatrimonio(content);
                break;
            case 'reprovados-qualidade':
                await renderReprovadosQualidade(content);
                break;
            case 'reprovados-patrimonio':
                await renderReprovadosPatrimonio(content);
                break;
            case 'importacao-valores':
                await renderImportacaoValores(content);
                break;
            case 'lista-pagamento':
                await renderListaPagamento(content);
                break;
            case 'pagamentos-registrados':
                await renderPagamentosRegistrados(content);
                break;
            case 'integracao':
                renderIntegracao(content);
                break;
            case 'gestao-usuarios':
                await renderGestaoUsuarios(content);
                break;
            default:
                content.innerHTML = '<p>Página não encontrada.</p>';
        }
    } catch (e) {
        content.innerHTML = `<div class="panel"><p style="color:var(--perigo)">Erro: ${esc(e.message)}</p></div>`;
    }
}

// ============================================================
// HOME (Dashboard)
// ============================================================
async function renderHome(el) {
    // Default: últimos 7 dias
    const hoje = new Date();
    const seteAtras = new Date(hoje);
    seteAtras.setDate(hoje.getDate() - 7);
    const fmtISO = d => d.toISOString().split('T')[0];
    const defaultFim = fmtISO(hoje);
    const defaultInicio = fmtISO(seteAtras);

    el.innerHTML = `
        <h1 class="titulo-tela">Bem-vindo, ${esc(State.usuario?.Nome || '')}</h1>
        <div class="filtros" style="margin-bottom:24px;background:var(--branco);padding:16px 20px;border-radius:12px;border:1px solid var(--cinza-borda);">
            <div class="form-group"><label>Data início</label><input type="date" id="dash-data-inicio" value="${defaultInicio}"></div>
            <div class="form-group"><label>Data fim</label><input type="date" id="dash-data-fim" value="${defaultFim}"></div>
            <button class="btn btn-primary" id="btn-dash-filtrar" style="align-self:flex-end;">Aplicar filtro</button>
        </div>
        <div id="dash-cards" class="dashboard"></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;">
            <div class="panel" style="min-height:320px;">
                <h3 style="margin-bottom:12px;color:var(--azul-escuro);">Abertos vs. Finalizados</h3>
                <canvas id="dash-chart" style="max-height:280px;"></canvas>
            </div>
            <div class="panel">
                <h3 style="margin-bottom:12px;color:var(--azul-escuro);">Desempenho por Usuário</h3>
                <div class="tabela-container"><table><thead><tr>
                    <th>Usuário</th><th>Total Aberto</th><th>Total Finalizado</th><th>% Finalizado</th>
                </tr></thead><tbody id="dash-tbody-usuarios"></tbody></table></div>
            </div>
        </div>
        <div class="logo-footer">
            <img src="/static/assets/logo.png" alt="Grupo Lamoia" onerror="this.style.display='none'">
        </div>`;

    let chartInstance = null;

    async function carregarDashboard() {
        const di = document.getElementById('dash-data-inicio').value;
        const df = document.getElementById('dash-data-fim').value;
        const params = `data_inicio=${di}&data_fim=${df}`;

        // 1. Cards de status
        try {
            const cards = await api(`/api/dashboard/cards?${params}`);
            const cardsEl = document.getElementById('dash-cards');
            const cores = {
                'Novo': '#1246FF', 'Em Investigação': '#C99A1E',
                'Aprovado - Qualidade': '#2FA84F', 'Reprovado - Qualidade': '#D64545',
                'Aprovado - Patrimônio': '#2FA84F', 'Reprovado - Patrimônio': '#D64545',
                'Aprovado - Comercial': '#2FA84F', 'Reprovado - Comercial': '#D64545',
                'Aguardando Financeiro': '#8B5CF6', 'Pagamento Programado': '#0EA5E9',
                'Finalizado': '#6B7280',
            };
            cardsEl.innerHTML = cards.map(c => `
                <div class="card-status">
                    <div class="valor" style="color:${cores[c.status] || '#1E2233'}">${c.quantidade}</div>
                    <div class="label">${esc(c.status)}</div>
                </div>`).join('');
        } catch (e) { console.error('Erro cards:', e); }

        // 2. Gráfico de barras
        try {
            const grafico = await api(`/api/dashboard/grafico?${params}`);
            const ctx = document.getElementById('dash-chart');
            if (chartInstance) chartInstance.destroy();

            // Registra o plugin de datalabels
            if (typeof Chart !== 'undefined' && typeof ChartDataLabels !== 'undefined') {
                Chart.register(ChartDataLabels);
            }

            chartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: grafico.periodos,
                    datasets: [
                        {
                            label: 'Abertos',
                            data: grafico.abertos,
                            backgroundColor: 'rgba(18, 70, 255, 0.7)',
                            borderColor: '#1246FF',
                            borderWidth: 1,
                        },
                        {
                            label: 'Finalizados',
                            data: grafico.finalizados,
                            backgroundColor: 'rgba(47, 168, 79, 0.7)',
                            borderColor: '#2FA84F',
                            borderWidth: 1,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' },
                        datalabels: {
                            anchor: 'end',
                            align: 'top',
                            color: '#1E2233',
                            font: { weight: 'bold', size: 11 },
                            formatter: v => v > 0 ? v : '',
                        },
                    },
                    scales: {
                        y: { beginAtZero: true, ticks: { stepSize: 1 } },
                    },
                },
            });
        } catch (e) { console.error('Erro gráfico:', e); }

        // 3. Tabela de usuários
        try {
            const usuarios = await api(`/api/dashboard/usuarios?${params}`);
            const tbody = document.getElementById('dash-tbody-usuarios');
            tbody.innerHTML = usuarios.map(u => `
                <tr>
                    <td>${esc(u.nome || '-')}</td>
                    <td>${u.total_abertos}</td>
                    <td>${u.total_finalizados}</td>
                    <td>${u.percentual_finalizado}%</td>
                </tr>`).join('') || '<tr><td colspan="4">Nenhum dado no período.</td></tr>';
        } catch (e) { console.error('Erro usuários:', e); }
    }

    document.getElementById('btn-dash-filtrar').addEventListener('click', carregarDashboard);
    carregarDashboard();
}

// ============================================================
// CHAMADO PF — Abertura (1.1.1.1)
// ============================================================
async function renderChamadoAberturaPF(el) {
    const opcoes = await api('/api/formulario-abertura/opcoes');
    el.innerHTML = `
        <h1 class="titulo-tela">Abertura de Chamado - Pessoa Física</h1>
        <div class="panel">
            <form id="form-abertura-pf" enctype="multipart/form-data">
                <div class="form-grid">
                    <div class="form-group"><label>Nome*</label><input name="nome" required></div>
                    <div class="form-group"><label>E-mail*</label><input name="email" type="email" required></div>
                    <div class="form-group"><label>CPF*</label><input name="cpf" placeholder="Somente números" required></div>
                    <div class="form-group"><label>Celular*</label><input name="celular" placeholder="Somente números" required></div>
                    <div class="form-group full"><label>Motivo* (até 300 caracteres)</label><textarea name="motivo" maxlength="300" required></textarea></div>
                    <div class="form-group"><label>Cidade*</label><input name="cidade" required></div>
                    <div class="form-group"><label>Estado*</label><input name="estado" required></div>
                    <div class="form-group"><label>Marca*</label><select name="marca">${opcoes.marcas.map(m => `<option>${m}</option>`).join('')}</select></div>
                    <div class="form-group"><label>Nome do Produto*</label><input name="nome_produto" required></div>
                    <div class="form-group"><label>Quantidade*</label><input name="quantidade" type="number" min="1" required></div>
                    <div class="form-group"><label>Validade*</label><input name="validade" type="date" required></div>
                    <div class="form-group"><label>Lote*</label><input name="lote" required></div>
                    <div class="form-group"><label>Problema apresentado*</label><select name="problema">${opcoes.problemas.map(p => `<option>${p}</option>`).join('')}</select></div>
                    <div class="form-group"><label>Local de compra*</label><input name="local" required></div>
                </div>
                <div class="section-title">Fotos e vídeos</div>
                <div class="file-upload" id="file-upload-area">
                    <input type="file" id="file-input" multiple accept=".png,.jpg,.jpeg,.mp4">
                    Clique ou arraste arquivos aqui (PNG, JPG, MP4)
                </div>
                <div class="file-list" id="file-list"></div>
                <div class="btn-group">
                    <button type="button" class="btn btn-danger" id="btn-cancelar-pf">Cancelar</button>
                    <button type="submit" class="btn btn-primary">Salvar</button>
                </div>
            </form>
        </div>`;

    const fileInput = document.getElementById('file-input');
    const fileArea = document.getElementById('file-upload-area');
    const fileList = document.getElementById('file-list');
    let arquivos = [];

    fileArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
        for (const f of fileInput.files) arquivos.push(f);
        renderFileList();
    });

    function renderFileList() {
        fileList.innerHTML = arquivos.map((f, i) =>
            `<div class="file-item"><span>${esc(f.name)}</span><span class="file-remove" data-idx="${i}">✕</span></div>`
        ).join('');
        fileList.querySelectorAll('.file-remove').forEach(el => {
            el.addEventListener('click', () => {
                arquivos.splice(parseInt(el.dataset.idx), 1);
                renderFileList();
            });
        });
    }

    document.getElementById('form-abertura-pf').addEventListener('submit', async function(e) {
        e.preventDefault();
        const submitBtn = this.querySelector('button[type=submit]');
        disableBtn(submitBtn);
        const fd = new FormData(this);
        for (const f of arquivos) fd.append('midias', f);
        try {
            const resp = await api('/api/chamados/pf', { method: 'POST', body: fd });
            toast(`Chamado registrado! OS: ${resp.os_id}`, 'success');
            navigate('lista-chamado-pf');
        } catch (err) {
            toast(err.message, 'error');
        }
    });

    document.getElementById('btn-cancelar-pf').addEventListener('click', () => navigate('home'));
}

// ============================================================
// LISTA CHAMADO PF (1.1.1.2)
// ============================================================
async function renderListaChamadoPF(el) {
    el.innerHTML = `
        <h1 class="titulo-tela">Lista de Chamados - Pessoa Física</h1>
        <div class="filtros">
            <div class="form-group"><label>Nº OS</label><input id="filtro-os-pf"></div>
            <div class="form-group"><label>CPF</label><input id="filtro-cpf-pf"></div>
            <div class="form-group"><label>Status</label><select id="filtro-status-pf">
                <option value="">Todos</option>
                ${['Novo','Em Investigação','Aprovado - Qualidade','Reprovado - Qualidade','Aguardando Financeiro','Pagamento Programado','Finalizado'].map(s => `<option>${s}</option>`).join('')}
            </select></div>
            <button class="btn btn-primary" id="btn-pesquisar-pf">Pesquisar</button>
        </div>
        <div class="tabela-container"><table><thead><tr>
            <th>OS</th><th>Nome</th><th>CPF</th><th>Status</th>
        </tr></thead><tbody id="tbody-pf"></tbody></table></div>
        <p class="subtitulo">Dê duplo clique em uma linha para abrir a ficha.</p>`;

    async function pesquisar() {
        const osId = document.getElementById('filtro-os-pf').value.trim();
        const cpf = document.getElementById('filtro-cpf-pf').value.trim();
        const status = document.getElementById('filtro-status-pf').value;
        const params = new URLSearchParams();
        if (osId) params.set('os_id', osId);
        if (cpf) params.set('cpf', cpf);
        if (status) params.set('status', status);
        const dados = await api(`/api/chamados/pf/lista?${params}`);
        const tbody = document.getElementById('tbody-pf');
        tbody.innerHTML = dados.map(r => `
            <tr data-os="${r.os_id}" data-status="${esc(r.status || '')}">
                <td>${r.os_id}</td><td>${esc(r.nome || '')}</td><td>${esc(r.cpf || '')}</td>
                <td><span class="badge ${badgeClass(r.status)}">${esc(r.status || '-')}</span></td>
            </tr>`).join('') || '<tr><td colspan="4">Nenhum resultado.</td></tr>';

        tbody.querySelectorAll('tr[data-os]').forEach(tr => {
            tr.addEventListener('dblclick', () => {
                const osId = tr.dataset.os;
                const status = tr.dataset.status;
                if (status === 'Reprovado - Qualidade') {
                    if (confirm(`OS ${osId}: Status Reprovado - Qualidade.\nDeseja finalizar?`)) {
                        api(`/api/chamados/pf/${osId}/finalizar`, { method: 'POST' })
                            .then(() => { toast('OS finalizada.', 'success'); pesquisar(); })
                            .catch(e => toast(e.message, 'error'));
                    }
                } else {
                    openModalFichaPF(osId);
                }
            });
        });
    }

    document.getElementById('btn-pesquisar-pf').addEventListener('click', pesquisar);
    pesquisar();
}

// ============================================================
// LISTA DE CHAMADOS — todos os tipos (1.1.2)
// ============================================================
async function renderListaChamados(el) {
    el.innerHTML = `
        <h1 class="titulo-tela">Lista de Chamados</h1>
        <div class="filtros">
            <div class="form-group"><label>Nº OS</label><input id="filtro-os-todos"></div>
            <div class="form-group"><label>Tipo</label><select id="filtro-tipo-todos">
                <option value="">Todos</option><option value="F">F</option><option value="Q">Q</option><option value="P">P</option>
            </select></div>
            <div class="form-group"><label>CPF / Código</label><input id="filtro-busca-todos" placeholder="CPF (F) ou Código (Q/P)"></div>
            <div class="form-group"><label>Status</label><select id="filtro-status-todos">
                <option value="">Todos</option>
                ${['Novo','Em Investigação','Aprovado - Qualidade','Reprovado - Qualidade','Aprovado - Patrimônio','Reprovado - Patrimônio','Aprovado - Comercial','Reprovado - Comercial','Aguardando Financeiro','Pagamento Programado','Finalizado'].map(s => `<option>${s}</option>`).join('')}
            </select></div>
            <button class="btn btn-primary" id="btn-pesquisar-todos">Pesquisar</button>
        </div>
        <div class="tabela-container"><table><thead><tr>
            <th>OS</th><th>Código</th><th>Razão</th><th>Status</th><th>Tipo</th>
        </tr></thead><tbody id="tbody-todos"></tbody></table></div>
        <p class="subtitulo">Duplo clique abre a ficha do chamado.</p>`;

    let resultados = [];

    async function pesquisar() {
        const osId = document.getElementById('filtro-os-todos').value.trim();
        const tipo = document.getElementById('filtro-tipo-todos').value;
        const busca = document.getElementById('filtro-busca-todos').value.trim();
        const status = document.getElementById('filtro-status-todos').value;
        const params = new URLSearchParams();
        if (osId) params.set('os_id', osId);
        if (tipo) params.set('tipo', tipo);
        if (status) params.set('status', status);
        if (tipo === 'F' && busca) params.set('cpf', busca);
        if (['Q','P'].includes(tipo) && busca) params.set('codigo', busca);

        resultados = await api(`/api/chamados/todos?${params}`);
        const tbody = document.getElementById('tbody-todos');
        tbody.innerHTML = resultados.map(r => `
            <tr data-idx="${resultados.indexOf(r)}">
                <td>${r.os_id}</td><td>${r.codigo || 0}</td><td>${esc(r.razao || '')}</td>
                <td><span class="badge ${badgeClass(r.status)}">${esc(r.status || '-')}</span></td>
                <td>${r.tipo}</td>
            </tr>`).join('') || '<tr><td colspan="5">Nenhum resultado.</td></tr>';

        tbody.querySelectorAll('tr[data-idx]').forEach(tr => {
            tr.addEventListener('dblclick', () => {
                const r = resultados[parseInt(tr.dataset.idx)];
                openFicha(r.os_id, r.tipo);
            });
        });
    }

    document.getElementById('btn-pesquisar-todos').addEventListener('click', pesquisar);
    pesquisar();
}

// ============================================================
// NOVOS QUALIDADE (1.2.1.1)
// ============================================================
async function renderNovosQualidade(el) {
    el.innerHTML = `
        <h1 class="titulo-tela">Novos Qualidade</h1>
        <p class="subtitulo">Duplo clique para abrir o formulário do chamado.</p>
        <div class="tabela-container"><table><thead><tr>
            <th>OS</th><th>Código</th><th>Razão / Nome</th><th>Tipo</th>
        </tr></thead><tbody id="tbody-novos-q"></tbody></table></div>`;

    const dados = await api('/api/aprovacoes/qualidade/novos');
    const tbody = document.getElementById('tbody-novos-q');
    tbody.innerHTML = dados.map(r => `
        <tr data-os="${r.os_id}" data-tipo="${r.tipo}">
            <td>${r.os_id}</td><td>${r.codigo || 0}</td><td>${esc(r.razao || '')}</td><td>${r.tipo}</td>
        </tr>`).join('') || '<tr><td colspan="4">Nenhum resultado.</td></tr>';

    tbody.querySelectorAll('tr[data-os]').forEach(tr => {
        tr.addEventListener('dblclick', () => {
            openFormularioQualidade(tr.dataset.os, tr.dataset.tipo);
        });
    });
}

// ============================================================
// INVESTIGAÇÕES ABERTAS (1.2.1.2)
// ============================================================
async function renderInvestigacoesAbertas(el) {
    el.innerHTML = `
        <h1 class="titulo-tela">Investigações Abertas</h1>
        <p class="subtitulo">Duplo clique para abrir a investigação.</p>
        <div class="tabela-container"><table><thead><tr>
            <th>OS</th><th>Código</th><th>Razão / Nome</th><th>Tipo</th>
        </tr></thead><tbody id="tbody-inv-abertas"></tbody></table></div>`;

    const dados = await api('/api/aprovacoes/qualidade/investigacoes');
    const tbody = document.getElementById('tbody-inv-abertas');
    tbody.innerHTML = dados.map(r => `
        <tr data-os="${r.os_id}" data-tipo="${r.tipo}">
            <td>${r.os_id}</td><td>${r.codigo || 0}</td><td>${esc(r.razao || '')}</td><td>${r.tipo}</td>
        </tr>`).join('') || '<tr><td colspan="4">Nenhum resultado.</td></tr>';

    tbody.querySelectorAll('tr[data-os]').forEach(tr => {
        tr.addEventListener('dblclick', () => {
            openInvestigacao(tr.dataset.os, tr.dataset.tipo);
        });
    });
}

// ============================================================
// NOVOS PATRIMÔNIO (1.2.2.1)
// ============================================================
async function renderNovosPatrimonio(el) {
    el.innerHTML = `
        <h1 class="titulo-tela">Novos Patrimônio</h1>
        <p class="subtitulo">Duplo clique para abrir o formulário.</p>
        <div class="tabela-container"><table><thead><tr>
            <th>OS</th><th>Código</th><th>Razão</th><th>OS Manutenção</th>
        </tr></thead><tbody id="tbody-novos-p"></tbody></table></div>`;

    const dados = await api('/api/aprovacoes/patrimonio/novos');
    const tbody = document.getElementById('tbody-novos-p');
    tbody.innerHTML = dados.map(r => `
        <tr data-os="${r.os_id}">
            <td>${r.os_id}</td><td>${r.codigo || ''}</td><td>${esc(r.razao || '')}</td><td>${esc(r.numero_os_manutencao || '')}</td>
        </tr>`).join('') || '<tr><td colspan="4">Nenhum resultado.</td></tr>';

    tbody.querySelectorAll('tr[data-os]').forEach(tr => {
        tr.addEventListener('dblclick', () => openFormularioPatrimonio(tr.dataset.os));
    });
}

// ============================================================
// REPROVADOS QUALIDADE (1.2.3.1)
// ============================================================
async function renderReprovadosQualidade(el) {
    el.innerHTML = `
        <h1 class="titulo-tela">Reprovados Qualidade</h1>
        <p class="subtitulo">Duplo clique para abrir a análise comercial.</p>
        <div class="tabela-container"><table><thead><tr>
            <th>OS</th><th>Código</th><th>Razão</th>
        </tr></thead><tbody id="tbody-reprov-q"></tbody></table></div>`;

    const dados = await api('/api/aprovacoes/comercial/reprovados-qualidade');
    const tbody = document.getElementById('tbody-reprov-q');
    tbody.innerHTML = dados.map(r => `
        <tr data-os="${r.os_id}">
            <td>${r.os_id}</td><td>${r.codigo || ''}</td><td>${esc(r.razao || '')}</td>
        </tr>`).join('') || '<tr><td colspan="3">Nenhum resultado.</td></tr>';

    tbody.querySelectorAll('tr[data-os]').forEach(tr => {
        tr.addEventListener('dblclick', () => openAnaliseComercialPJ(tr.dataset.os));
    });
}

// ============================================================
// REPROVADOS PATRIMÔNIO (1.2.3.2)
// ============================================================
async function renderReprovadosPatrimonio(el) {
    el.innerHTML = `
        <h1 class="titulo-tela">Reprovados Patrimônio</h1>
        <p class="subtitulo">Duplo clique para abrir a análise comercial.</p>
        <div class="tabela-container"><table><thead><tr>
            <th>OS</th><th>Código</th><th>Razão</th><th>OS Manutenção</th>
        </tr></thead><tbody id="tbody-reprov-p"></tbody></table></div>`;

    const dados = await api('/api/aprovacoes/comercial/reprovados-patrimonio');
    const tbody = document.getElementById('tbody-reprov-p');
    tbody.innerHTML = dados.map(r => `
        <tr data-os="${r.os_id}">
            <td>${r.os_id}</td><td>${r.codigo || ''}</td><td>${esc(r.razao || '')}</td><td>${esc(r.numero_os_manutencao || '')}</td>
        </tr>`).join('') || '<tr><td colspan="4">Nenhum resultado.</td></tr>';

    tbody.querySelectorAll('tr[data-os]').forEach(tr => {
        tr.addEventListener('dblclick', () => openAnaliseComercialPatrimonio(tr.dataset.os));
    });
}

// ============================================================
// IMPORTAÇÃO DE VALORES (1.3.1)
// ============================================================
async function renderImportacaoValores(el) {
    el.innerHTML = `
        <h1 class="titulo-tela">Importação de Valores</h1>
        <p class="subtitulo">Duplo clique para importar os valores do chamado.</p>
        <div class="tabela-container"><table><thead><tr>
            <th>OS</th><th>Código</th><th>Razão</th><th>Status</th><th>Tipo</th>
        </tr></thead><tbody id="tbody-imp"></tbody></table></div>`;

    const dados = await api('/api/financeiro/importacao');
    const tbody = document.getElementById('tbody-imp');
    tbody.innerHTML = dados.map(r => `
        <tr data-os="${r.os_id}" data-tipo="${r.tipo}">
            <td>${r.os_id}</td><td>${r.codigo || ''}</td><td>${esc(r.razao || '')}</td>
            <td><span class="badge ${badgeClass(r.status)}">${esc(r.status || '')}</span></td>
            <td>${r.tipo}</td>
        </tr>`).join('') || '<tr><td colspan="5">Nenhum resultado.</td></tr>';

    tbody.querySelectorAll('tr[data-os]').forEach(tr => {
        tr.addEventListener('dblclick', () => {
            if (tr.dataset.tipo === 'Q') openImportacaoQualidade(tr.dataset.os);
            else openImportacaoPatrimonio(tr.dataset.os);
        });
    });
}

// ============================================================
// LISTA PARA PAGAMENTO (1.3.2)
// ============================================================
async function renderListaPagamento(el) {
    el.innerHTML = `
        <h1 class="titulo-tela">Lista para Pagamento</h1>
        <p class="subtitulo">Duplo clique para abrir o formulário de pagamento.</p>
        <div class="tabela-container"><table><thead><tr>
            <th>OS</th><th>Código</th><th>Razão</th><th>Tipo</th>
        </tr></thead><tbody id="tbody-pag"></tbody></table></div>`;

    const dados = await api('/api/financeiro/pagamento/lista');
    const tbody = document.getElementById('tbody-pag');
    tbody.innerHTML = dados.map(r => `
        <tr data-os="${r.os_id}" data-tipo="${r.tipo}">
            <td>${r.os_id}</td><td>${r.codigo || ''}</td><td>${esc(r.razao || '')}</td><td>${r.tipo}</td>
        </tr>`).join('') || '<tr><td colspan="4">Nenhum resultado.</td></tr>';

    tbody.querySelectorAll('tr[data-os]').forEach(tr => {
        tr.addEventListener('dblclick', () => openPagamento(tr.dataset.os, tr.dataset.tipo));
    });
}

// ============================================================
// PAGAMENTOS REGISTRADOS (1.3.3)
// ============================================================
async function renderPagamentosRegistrados(el) {
    el.innerHTML = `
        <h1 class="titulo-tela">Pagamentos Registrados</h1>
        <div class="filtros">
            <div class="form-group"><label>Filtro</label><select id="filtro-data-tipo">
                <option value="0">Sem filtro de data</option>
                <option value="1">Filtrar por data</option>
            </select></div>
            <div class="form-group"><label>Data</label><input type="date" id="filtro-data-pg"></div>
            <div class="form-group"><label>Tipo</label><select id="filtro-tipo-pg">
                <option value="">Todos</option><option value="F">F</option><option value="Q">Q</option><option value="P">P</option>
            </select></div>
            <button class="btn btn-primary" id="btn-pesquisar-pagos">Pesquisar</button>
        </div>
        <div class="tabela-container"><table><thead><tr>
            <th>OS</th><th>Código</th><th>Razão</th><th>Tipo</th><th>Data Pagamento</th>
        </tr></thead><tbody id="tbody-pagos"></tbody></table></div>`;

    async function pesquisar() {
        const usarData = document.getElementById('filtro-data-tipo').value === '1';
        const data = document.getElementById('filtro-data-pg').value;
        const tipo = document.getElementById('filtro-tipo-pg').value;
        const params = new URLSearchParams();
        if (usarData && data) params.set('data_pg', data);
        if (tipo) params.set('tipo', tipo);

        const dados = await api(`/api/financeiro/pagamentos-registrados?${params}`);
        document.getElementById('tbody-pagos').innerHTML = dados.map(r => `
            <tr>
                <td>${r.os_id}</td><td>${r.codigo || 0}</td><td>${esc(r.razao || '')}</td>
                <td>${r.tipo}</td><td>${r.data_pg || ''}</td>
            </tr>`).join('') || '<tr><td colspan="5">Nenhum resultado.</td></tr>';
    }

    document.getElementById('btn-pesquisar-pagos').addEventListener('click', pesquisar);
    pesquisar();
}

// ============================================================
// INTEGRAÇÃO DE INFORMAÇÕES (1.4.1)
// ============================================================
function renderIntegracao(el) {
    el.innerHTML = `
        <h1 class="titulo-tela">Integração de Informações</h1>
        <div class="panel">
            <p class="subtitulo">Move os arquivos de mídia da pasta de staging para a pasta definitiva e atualiza o banco de dados.</p>
            <button class="btn btn-primary" id="btn-integrar">Integrar</button>
            <div class="section-title">Andamento</div>
            <div id="log-integracao" style="background:var(--cinza-fundo);padding:12px;border-radius:8px;max-height:300px;overflow-y:auto;font-family:monospace;font-size:12px;white-space:pre-wrap;"></div>
        </div>`;

    document.getElementById('btn-integrar').addEventListener('click', async () => {
        const btn = document.getElementById('btn-integrar');
        const log = document.getElementById('log-integracao');
        btn.disabled = true;
        log.textContent = 'Executando...\n';
        try {
            const resp = await api('/api/admin/integracao', { method: 'POST' });
            log.textContent = resp.log.join('\n') + `\n\nConcluído: ${resp.movidos} movido(s), ${resp.falhas} falha(s).`;
            toast(`Integração concluída: ${resp.movidos} arquivo(s).`, 'success');
        } catch (e) {
            log.textContent = `Erro: ${e.message}`;
            toast(e.message, 'error');
        }
        btn.disabled = false;
    });
}

// ============================================================
// GESTÃO DE USUÁRIOS (1.4.2)
// ============================================================
async function renderGestaoUsuarios(el) {
    const tiposResp = await api('/api/admin/usuarios/tipos');
    const tipos = tiposResp.tipos;

    el.innerHTML = `
        <h1 class="titulo-tela">Gestão de Usuários</h1>
        <div class="panel">
            <div class="form-grid">
                <div class="form-group"><label>Login*</label><input id="usr-login"></div>
                <div class="form-group"><label>Senha* <small>(branco = manter atual)</small></label><input type="password" id="usr-senha" placeholder="Deixe em branco para manter"></div>
                <div class="form-group"><label>Tipo*</label><select id="usr-tipo">${tipos.map(t => `<option>${t}</option>`).join('')}</select></div>
                <div class="form-group"><label>Nome*</label><input id="usr-nome"></div>
                <div class="form-group"><label>Status*</label><select id="usr-status"><option value="a">Ativo</option><option value="i">Inativo</option></select></div>
            </div>
            <div class="btn-group">
                <button class="btn btn-secondary" id="btn-usr-novo">Novo</button>
                <button class="btn btn-primary" id="btn-usr-salvar">Salvar</button>
            </div>
        </div>
        <div class="section-title">Usuários cadastrados</div>
        <div class="filtros">
            <div class="form-group"><label>Filtro</label><select id="filtro-usr-status">
                <option value="">Todos</option><option value="a">Ativo</option><option value="i">Inativo</option>
            </select></div>
        </div>
        <div class="tabela-container"><table><thead><tr>
            <th>Login</th><th>Nome</th><th>Tipo</th><th>Status</th>
        </tr></thead><tbody id="tbody-usuarios"></tbody></table></div>`;

    let idEdicao = null;

    async function carregar() {
        const status = document.getElementById('filtro-usr-status').value || undefined;
        const dados = await api(`/api/admin/usuarios${status ? `?status=${status}` : ''}`);
        const tbody = document.getElementById('tbody-usuarios');
        tbody.innerHTML = dados.map(u => `
            <tr data-id="${u.id_user}" data-login="${esc(u.Login || '')}" data-nome="${esc(u.Nome || '')}" data-tipo="${esc(u.Tipo || '')}" data-status="${u.Status || ''}">
                <td>${esc(u.Login || '')}</td><td>${esc(u.Nome || '')}</td><td>${esc(u.Tipo || '')}</td>
                <td>${u.Status === 'a' ? 'Ativo' : 'Inativo'}</td>
            </tr>`).join('') || '<tr><td colspan="4">Nenhum usuário.</td></tr>';

        tbody.querySelectorAll('tr[data-id]').forEach(tr => {
            tr.addEventListener('dblclick', () => {
                idEdicao = parseInt(tr.dataset.id);
                document.getElementById('usr-login').value = tr.dataset.login;
                document.getElementById('usr-senha').value = '';
                document.getElementById('usr-tipo').value = tr.dataset.tipo;
                document.getElementById('usr-nome').value = tr.dataset.nome;
                document.getElementById('usr-status').value = tr.dataset.status;
            });
        });
    }

    document.getElementById('btn-usr-novo').addEventListener('click', () => {
        idEdicao = null;
        document.getElementById('usr-login').value = '';
        document.getElementById('usr-senha').value = '';
        document.getElementById('usr-tipo').selectedIndex = 0;
        document.getElementById('usr-nome').value = '';
        document.getElementById('usr-status').value = 'a';
    });

    document.getElementById('btn-usr-salvar').addEventListener('click', async function() {
        disableBtn(this);
        const dados = {
            Login: document.getElementById('usr-login').value.trim(),
            Senha: document.getElementById('usr-senha').value,
            Tipo: document.getElementById('usr-tipo').value,
            Nome: document.getElementById('usr-nome').value.trim(),
            Status: document.getElementById('usr-status').value,
        };
        if (idEdicao) dados.id_user = idEdicao;

        try {
            await api('/api/admin/usuarios', { method: 'POST', body: dados });
            toast('Usuário salvo com sucesso!', 'success');
            idEdicao = null;
            document.getElementById('usr-login').value = '';
            document.getElementById('usr-senha').value = '';
            document.getElementById('usr-nome').value = '';
            carregar();
        } catch (e) {
            toast(e.message, 'error');
        }
    });

    document.getElementById('filtro-usr-status').addEventListener('change', carregar);
    carregar();
}


// ============================================================
// MODAIS — Fichas e Formulários
// ============================================================

function openModal(html) {
    const overlay = document.getElementById('modal-overlay');
    const container = document.getElementById('modal-container');
    container.innerHTML = html;
    overlay.classList.add('active');
    overlay.onclick = e => { if (e.target === overlay) closeModal(); };
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
}

// ---------- Ficha PF ----------
async function openModalFichaPF(osId) {
    const d = await api(`/api/fichas/pf/${osId}`);
    const ch = d.chamado || {};
    openModal(`
        <div class="modal-header"><h2>Ficha Pessoa Física - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
        <div class="modal-body">
            <p class="subtitulo">OS ${d.os_id} • aberto por ${esc(d.status_novo)}</p>
            <table class="info-table">
                ${[['Nome',ch.nome],['E-mail',ch.email],['CPF',ch.cpf],['Celular',ch.celular],['Motivo',ch.motivo],['Cidade',ch.cidade],['Estado',ch.estado],['Marca',ch.marca],['Nome do Produto',ch.nome_produto],['Quantidade',ch.quantidade],['Validade',ch.validade],['Lote',ch.lote],['Problema',ch.problema],['Local de compra',ch.local],['Análise',ch.Analise],['Resolução e Resposta',ch.Resolucao_Resposta]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
            </table>
            <p class="subtitulo">Decisão Qualidade: ${esc(d.decisao_qualidade)}</p>
            ${renderMidiasHTML(d.midias)}
            <div class="section-title">Pagamento</div>
            ${renderPagamentosHTML(d.pagamentos)}
            <p class="subtitulo">Finalizado por: ${esc(d.status_finalizado)}</p>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="gerarPDFFFichaPF(${d.os_id})">Exportar PDF</button>
            <button class="btn btn-primary" onclick="closeModal()">Fechar</button>
        </div>`);
}

// ---------- Ficha PJ Qualidade ----------
async function openFichaPJQualidade(osId) {
    const d = await api(`/api/fichas/pj-qualidade/${osId}`);
    const ch = d.chamado || {};
    const osRow = d.os_row || {};
    const val0 = d.pagamentos?.[0] || {};
    openModal(`
        <div class="modal-header"><h2>Ficha PJ Qualidade - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
        <div class="modal-body">
            <p class="subtitulo">OS ${d.os_id} • aberto por ${esc(d.status_novo)}</p>
            <table class="info-table">
                ${[['Nome',ch.Nome],['Celular',ch.Celular],['Código do Cliente',osRow.Codigo],['Razão',ch.razao],['CPF/CNPJ',ch.cnpj_cpf],['Motivo',ch.Motivo]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
            </table>
            <div class="section-title">Produto</div>
            <div class="tabela-container"><table><thead><tr><th>Descrição</th><th>Marca</th><th>Qtd</th><th>Validade</th><th>Lote</th><th>Valor</th></tr></thead><tbody>
                <tr><td>${esc(ch.produto_descricao||'')}</td><td>${esc(ch.produto_marca||'')}</td><td>${ch.Quantidade||''}</td><td>${ch.Validade||''}</td><td>${esc(ch.Lote||'')}</td><td>${val0.valor||''}</td></tr>
            </tbody></table></div>
            <table class="info-table">
                ${[['Problema',ch.Problema],['Análise',ch['Analise Qualidade']],['Resolução e Resposta',ch.Resolucao_Resposta],['Justificativa',ch.Justificativa]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
            </table>
            <p class="subtitulo">Decisão Qualidade: ${esc(d.decisao_qualidade)}</p>
            <p class="subtitulo">Decisão Comercial: ${esc(d.decisao_comercial)}</p>
            ${renderMidiasHTML(d.midias)}
            <div class="section-title">Pagamento</div>
            ${renderPagamentosHTML(d.pagamentos)}
            <p class="subtitulo">Finalizado por: ${esc(d.status_finalizado)}</p>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="gerarPDFFFichaPJQ(${d.os_id})">Exportar PDF</button>
            <button class="btn btn-primary" onclick="closeModal()">Fechar</button>
        </div>`);
}

// ---------- Ficha PJ Patrimônio ----------
async function openFichaPJPatrimonio(osId) {
    const d = await api(`/api/fichas/pj-patrimonio/${osId}`);
    const cab = d.cabecalho || {};
    const valMap = {};
    (d.pagamentos || []).forEach(p => valMap[p.id_produto] = p.valor);

    openModal(`
        <div class="modal-header"><h2>Ficha PJ Patrimônio - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
        <div class="modal-body">
            <p class="subtitulo">OS ${d.os_id} • aberto por ${esc(d.status_novo)}</p>
            <table class="info-table">
                ${[['Código do Cliente',cab.codigo],['Razão',cab.razao],['Nº OS Manutenção',cab.numero_os_manutencao],['Motivo',cab.motivo],['Justificativa',cab.justificativa]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
            </table>
            <div class="section-title">Produtos</div>
            <div class="tabela-container"><table><thead><tr><th>ID</th><th>Descrição</th><th>Qtd</th><th>Valor</th></tr></thead><tbody>
                ${(d.produtos||[]).map(p => `<tr><td>${p.id_Produto||''}</td><td>${esc(p.produto_descricao||'')}</td><td>${p.Quantidade||''}</td><td>${valMap[p.id_Produto]||''}</td></tr>`).join('')}
            </tbody></table></div>
            <table class="info-table">
                ${[['Motivo',cab.motivo],['Justificativa',cab.justificativa]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
            </table>
            <p class="subtitulo">Decisão Patrimônio: ${esc(d.decisao_patrimonio)}</p>
            <p class="subtitulo">Decisão Comercial: ${esc(d.decisao_comercial)}</p>
            ${renderMidiasHTML(d.midias)}
            <div class="section-title">Pagamento</div>
            ${renderPagamentosHTML(d.pagamentos)}
            <p class="subtitulo">Finalizado por: ${esc(d.status_finalizado)}</p>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="gerarPDFFFichaPJP(${d.os_id})">Exportar PDF</button>
            <button class="btn btn-primary" onclick="closeModal()">Fechar</button>
        </div>`);
}

// ---------- Formulário Qualidade PF ----------
async function openFormularioQualidade(osId, tipo) {
    if (tipo === 'F') {
        const d = await api(`/api/aprovacoes/qualidade/formulario-pf/${osId}`);
        const ch = d.chamado || {};
        const sn = d.status_novo || {};
        openModal(`
            <div class="modal-header"><h2>Formulário Qualidade PF - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
            <div class="modal-body">
                <p class="subtitulo">OS ${d.os_id} • aberto por ${esc(sn.nome_usuario||'-')} em ${fmtData(sn.created_at)}</p>
                <table class="info-table">
                    ${[['Nome',ch.nome],['E-mail',ch.email],['CPF',ch.cpf],['Celular',ch.celular],['Motivo',ch.motivo],['Cidade',ch.cidade],['Estado',ch.estado],['Marca',ch.marca],['Nome do Produto',ch.nome_produto],['Lote',ch.lote],['Problema',ch.problema],['Local de compra',ch.local]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
                </table>
                ${renderMidiasHTML(d.midias)}
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="gerarPDFFFichaPF(${d.os_id})">Gerar PDF</button>
                <button class="btn btn-primary" id="btn-abrir-inv-pf">Abrir Investigação</button>
            </div>`);
        document.getElementById('btn-abrir-inv-pf').addEventListener('click', async () => {
            await api('/api/aprovacoes/qualidade/abrir-investigacao', { method: 'POST', body: { os_id: d.os_id, tipo: 'F' } });
            closeModal();
            openInvestigacao(d.os_id, 'F');
        });
    } else {
        const d = await api(`/api/aprovacoes/qualidade/formulario-pj/${osId}`);
        const ch = d.chamado || {};
        const osRow = d.os_row || {};
        const sn = d.status_novo || {};
        openModal(`
            <div class="modal-header"><h2>Formulário Qualidade PJ - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
            <div class="modal-body">
                <p class="subtitulo">OS ${d.os_id} • aberto por ${esc(sn.nome_usuario||'-')} em ${fmtData(sn.created_at)}</p>
                <table class="info-table">
                    ${[['Nome',ch.Nome],['Celular',ch.Celular],['Código do Cliente',osRow.Codigo],['Razão',ch.razao],['CPF/CNPJ',ch.cnpj_cpf],['Motivo',ch.Motivo]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
                </table>
                <div class="section-title">Produto</div>
                <div class="tabela-container"><table><thead><tr><th>Descrição</th><th>Marca</th><th>Qtd</th><th>Validade</th><th>Lote</th></tr></thead><tbody>
                    <tr><td>${esc(ch.produto_descricao||'')}</td><td>${esc(ch.produto_marca||'')}</td><td>${ch.Quantidade||''}</td><td>${ch.Validade||''}</td><td>${esc(ch.Lote||'')}</td></tr>
                </tbody></table></div>
                <table class="info-table"><tr><td>Problema</td><td>${esc(ch.Problema||'-')}</td></tr></table>
                ${renderMidiasHTML(d.midias)}
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="gerarPDFFFichaPJQ(${d.os_id})">Gerar PDF</button>
                <button class="btn btn-primary" id="btn-abrir-inv-pj">Abrir Investigação</button>
            </div>`);
        document.getElementById('btn-abrir-inv-pj').addEventListener('click', async () => {
            await api('/api/aprovacoes/qualidade/abrir-investigacao', { method: 'POST', body: { os_id: d.os_id, tipo: 'Q' } });
            closeModal();
            openInvestigacao(d.os_id, 'Q');
        });
    }
}

// ---------- Investigação PF ----------
async function openInvestigacao(osId, tipo) {
    if (tipo === 'F') {
        const d = await api(`/api/investigacoes/pf/${osId}`);
        const ch = d.chamado || {};
        const sn = d.status_novo || {};
        openModal(`
            <div class="modal-header"><h2>Investigação PF - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
            <div class="modal-body">
                <p class="subtitulo">OS ${d.os_id} • aberto por ${esc(sn.nome_usuario||'-')} em ${fmtData(sn.created_at)}</p>
                <table class="info-table">
                    ${[['Nome',ch.nome],['E-mail',ch.email],['CPF',ch.cpf],['Celular',ch.celular],['Motivo',ch.motivo],['Cidade',ch.cidade],['Estado',ch.estado],['Marca',ch.marca],['Nome do Produto',ch.nome_produto],['Lote',ch.lote],['Problema',ch.problema],['Local de compra',ch.local]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
                </table>
                ${renderMidiasHTML(d.midias)}
                <div class="form-group full"><label>Análise* (até 300 caracteres)</label><textarea id="inv-analise" maxlength="300">${esc(ch.Analise||'')}</textarea></div>
                <div class="form-group full"><label>Resolução e Resposta*</label><textarea id="inv-resolucao">${esc(ch.Resolucao_Resposta||'')}</textarea></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="gerarPDFFFichaPF(${d.os_id})">Gerar PDF</button>
                <button class="btn btn-danger" id="btn-inv-reprovar">Reprovar</button>
                <button class="btn btn-success" id="btn-inv-aprovar">Aprovar</button>
            </div>`);

        async function salvarPF(acao) {
            document.getElementById('btn-inv-reprovar').disabled = true;
            document.getElementById('btn-inv-aprovar').disabled = true;
            const analise = document.getElementById('inv-analise').value;
            const resolucao = document.getElementById('inv-resolucao').value;
            try {
                const resp = await api(`/api/investigacoes/pf/${d.os_id}/salvar`, {
                    method: 'POST',
                    body: { analise, resolucao, acao },
                });
                toast(resp.mensagem, 'success');
                closeModal();
                renderPage();
            } catch (e) { toast(e.message, 'error'); }
        }
        document.getElementById('btn-inv-reprovar').addEventListener('click', () => salvarPF('reprovar'));
        document.getElementById('btn-inv-aprovar').addEventListener('click', () => salvarPF('aprovar'));
    } else {
        const d = await api(`/api/investigacoes/pj/${osId}`);
        const ch = d.chamado || {};
        const osRow = d.os_row || {};
        const sn = d.status_novo || {};
        openModal(`
            <div class="modal-header"><h2>Investigação PJ - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
            <div class="modal-body">
                <p class="subtitulo">OS ${d.os_id} • aberto por ${esc(sn.nome_usuario||'-')} em ${fmtData(sn.created_at)}</p>
                <table class="info-table">
                    ${[['Nome',ch.Nome],['Celular',ch.Celular],['Código do Cliente',osRow.Codigo],['Razão',ch.razao],['CPF/CNPJ',ch.cnpj_cpf],['Motivo',ch.Motivo]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
                </table>
                <div class="section-title">Produto</div>
                <div class="tabela-container"><table><thead><tr><th>Descrição</th><th>Marca</th><th>Qtd</th><th>Validade</th><th>Lote</th></tr></thead><tbody>
                    <tr><td>${esc(ch.produto_descricao||'')}</td><td>${esc(ch.produto_marca||'')}</td><td>${ch.Quantidade||''}</td><td>${ch.Validade||''}</td><td>${esc(ch.Lote||'')}</td></tr>
                </tbody></table></div>
                <table class="info-table"><tr><td>Problema</td><td>${esc(ch.Problema||'-')}</td></tr></table>
                ${renderMidiasHTML(d.midias)}
                <div class="form-group full"><label>Análise* (até 300 caracteres)</label><textarea id="inv-analise-pj" maxlength="300">${esc(ch['Analise Qualidade']||'')}</textarea></div>
                <div class="form-group full"><label>Resolução e Resposta*</label><textarea id="inv-resolucao-pj">${esc(ch.Resolucao_Resposta||'')}</textarea></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="gerarPDFFFichaPJQ(${d.os_id})">Gerar PDF</button>
                <button class="btn btn-danger" id="btn-inv-pj-reprovar">Reprovar</button>
                <button class="btn btn-success" id="btn-inv-pj-aprovar">Aprovar</button>
            </div>`);

        async function salvarPJ(acao) {
            document.getElementById('btn-inv-pj-reprovar').disabled = true;
            document.getElementById('btn-inv-pj-aprovar').disabled = true;
            const analise = document.getElementById('inv-analise-pj').value;
            const resolucao = document.getElementById('inv-resolucao-pj').value;
            try {
                const resp = await api(`/api/investigacoes/pj/${d.os_id}/salvar`, {
                    method: 'POST',
                    body: { analise, resolucao, acao },
                });
                toast(resp.mensagem, 'success');
                closeModal();
                renderPage();
            } catch (e) { toast(e.message, 'error'); }
        }
        document.getElementById('btn-inv-pj-reprovar').addEventListener('click', () => salvarPJ('reprovar'));
        document.getElementById('btn-inv-pj-aprovar').addEventListener('click', () => salvarPJ('aprovar'));
    }
}

// ---------- Formulário Patrimônio ----------
async function openFormularioPatrimonio(osId) {
    const d = await api(`/api/aprovacoes/patrimonio/formulario/${osId}`);
    const cab = d.cabecalho || {};
    const sn = d.status_novo || {};
    openModal(`
        <div class="modal-header"><h2>Formulário Patrimônio - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
        <div class="modal-body">
            <p class="subtitulo">OS ${d.os_id} • aberto por ${esc(sn.nome_usuario||'-')} em ${fmtData(sn.created_at)}</p>
            <table class="info-table">
                ${[['Código do Cliente',cab.codigo],['Razão',cab.razao],['Nº OS Manutenção',cab.numero_os_manutencao]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
            </table>
            <div class="section-title">Produtos</div>
            <div class="tabela-container"><table><thead><tr><th>ID</th><th>Descrição</th><th>Qtd</th></tr></thead><tbody>
                ${(d.produtos||[]).map(p => `<tr><td>${p.id_Produto||''}</td><td>${esc(p.produto_descricao||'')}</td><td>${p.Quantidade||''}</td></tr>`).join('')}
            </tbody></table></div>
            ${renderMidiasHTML(d.midias)}
            <div class="form-group full"><label>Motivo* (até 300 caracteres)</label><textarea id="pat-motivo" maxlength="300">${esc(cab.motivo||'')}</textarea></div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="gerarPDFFFichaPJP(${d.os_id})">Gerar PDF</button>
            <button class="btn btn-danger" id="btn-pat-reprovar">Reprovar</button>
            <button class="btn btn-success" id="btn-pat-aprovar">Aprovar</button>
        </div>`);

    async function salvarPat(acao) {
        document.getElementById('btn-pat-reprovar').disabled = true;
        document.getElementById('btn-pat-aprovar').disabled = true;
        const motivo = document.getElementById('pat-motivo').value;
        try {
            const resp = await api(`/api/aprovacoes/patrimonio/${d.os_id}/salvar`, {
                method: 'POST', body: { motivo, acao },
            });
            toast(resp.mensagem, 'success');
            closeModal();
            renderPage();
        } catch (e) { toast(e.message, 'error'); }
    }
    document.getElementById('btn-pat-reprovar').addEventListener('click', () => salvarPat('reprovar'));
    document.getElementById('btn-pat-aprovar').addEventListener('click', () => salvarPat('aprovar'));
}

// ---------- Análise Comercial PJ ----------
async function openAnaliseComercialPJ(osId) {
    const d = await api(`/api/aprovacoes/comercial/pj/${osId}`);
    const ch = d.chamado || {};
    const osRow = d.os_row || {};
    const sn = d.status_novo || {};
    const sr = d.status_reprovado || {};
    openModal(`
        <div class="modal-header"><h2>Análise Comercial PJ - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
        <div class="modal-body">
            <p class="subtitulo">OS ${d.os_id} • aberto por ${esc(sn.nome_usuario||'-')} em ${fmtData(sn.created_at)}</p>
            <table class="info-table">
                ${[['Nome',ch.Nome],['Celular',ch.Celular],['Código do Cliente',osRow.Codigo],['Razão',ch.razao],['CPF/CNPJ',ch.cnpj_cpf],['Motivo',ch.Motivo],['Problema',ch.Problema],['Análise (Qualidade)',ch['Analise Qualidade']],['Resolução e Resposta',ch.Resolucao_Resposta]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
            </table>
            <p class="subtitulo">Reprovado - Qualidade por ${esc(sr.nome_usuario||'-')} em ${fmtData(sr.created_at)}</p>
            ${renderMidiasHTML(d.midias)}
            <div class="form-group full"><label>Justificativa*</label><textarea id="com-just-pj">${esc(ch.Justificativa||'')}</textarea></div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="gerarPDFFFichaPJQ(${d.os_id})">Gerar PDF</button>
            <button class="btn btn-danger" id="btn-com-pj-reprovar">Reprovar (Finalizar)</button>
            <button class="btn btn-success" id="btn-com-pj-aprovar">Aprovar</button>
        </div>`);

    async function salvarComPJ(acao) {
        document.getElementById('btn-com-pj-reprovar').disabled = true;
        document.getElementById('btn-com-pj-aprovar').disabled = true;
        const justificativa = document.getElementById('com-just-pj').value;
        try {
            const resp = await api(`/api/aprovacoes/comercial/pj/${d.os_id}/salvar`, {
                method: 'POST', body: { justificativa, acao },
            });
            toast(resp.mensagem, 'success');
            closeModal();
            renderPage();
        } catch (e) { toast(e.message, 'error'); }
    }
    document.getElementById('btn-com-pj-reprovar').addEventListener('click', () => salvarComPJ('reprovar'));
    document.getElementById('btn-com-pj-aprovar').addEventListener('click', () => salvarComPJ('aprovar'));
}

// ---------- Análise Comercial Patrimônio ----------
async function openAnaliseComercialPatrimonio(osId) {
    const d = await api(`/api/aprovacoes/comercial/patrimonio/${osId}`);
    const cab = d.cabecalho || {};
    const sn = d.status_novo || {};
    const sr = d.status_reprovado || {};
    openModal(`
        <div class="modal-header"><h2>Análise Comercial Patrimônio - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
        <div class="modal-body">
            <p class="subtitulo">OS ${d.os_id} • aberto por ${esc(sn.nome_usuario||'-')} em ${fmtData(sn.created_at)}</p>
            <table class="info-table">
                ${[['Código do Cliente',cab.codigo],['Razão',cab.razao],['Nº OS Manutenção',cab.numero_os_manutencao],['Motivo',cab.motivo]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
            </table>
            <div class="section-title">Produtos</div>
            <div class="tabela-container"><table><thead><tr><th>ID</th><th>Descrição</th><th>Qtd</th></tr></thead><tbody>
                ${(d.produtos||[]).map(p => `<tr><td>${p.id_Produto||''}</td><td>${esc(p.produto_descricao||'')}</td><td>${p.Quantidade||''}</td></tr>`).join('')}
            </tbody></table></div>
            <p class="subtitulo">Reprovado - Patrimônio por ${esc(sr.nome_usuario||'-')} em ${fmtData(sr.created_at)}</p>
            ${renderMidiasHTML(d.midias)}
            <div class="form-group full"><label>Justificativa*</label><textarea id="com-just-pat">${esc(cab.justificativa||'')}</textarea></div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="gerarPDFFFichaPJP(${d.os_id})">Gerar PDF</button>
            <button class="btn btn-danger" id="btn-com-pat-reprovar">Reprovar (Finalizar)</button>
            <button class="btn btn-success" id="btn-com-pat-aprovar">Aprovar</button>
        </div>`);

    async function salvarComPat(acao) {
        document.getElementById('btn-com-pat-reprovar').disabled = true;
        document.getElementById('btn-com-pat-aprovar').disabled = true;
        const justificativa = document.getElementById('com-just-pat').value;
        try {
            const resp = await api(`/api/aprovacoes/comercial/patrimonio/${d.os_id}/salvar`, {
                method: 'POST', body: { justificativa, acao },
            });
            toast(resp.mensagem, 'success');
            closeModal();
            renderPage();
        } catch (e) { toast(e.message, 'error'); }
    }
    document.getElementById('btn-com-pat-reprovar').addEventListener('click', () => salvarComPat('reprovar'));
    document.getElementById('btn-com-pat-aprovar').addEventListener('click', () => salvarComPat('aprovar'));
}

// ---------- Importação de Valores Qualidade ----------
async function openImportacaoQualidade(osId) {
    const d = await api(`/api/financeiro/importacao/qualidade/${osId}`);
    const ch = d.chamado || {};
    const osRow = d.os_row || {};
    const sn = d.status_novo || {};
    const qtd = parseFloat(ch.Quantidade || 0);

    openModal(`
        <div class="modal-header"><h2>Importação Valores - Qualidade - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
        <div class="modal-body">
            <p class="subtitulo">OS ${d.os_id} • aberto por ${esc(sn.nome_usuario||'-')} em ${fmtData(sn.created_at)}</p>
            <table class="info-table">
                ${[['Nome',ch.Nome],['Código do Cliente',osRow.Codigo],['Razão',ch.razao]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
            </table>
            <div class="section-title">Produto</div>
            <div class="tabela-container"><table><thead><tr><th>Descrição</th><th>Marca</th><th>Qtd</th><th>Validade</th><th>Lote</th></tr></thead><tbody>
                <tr><td>${esc(ch.produto_descricao||'')}</td><td>${esc(ch.produto_marca||'')}</td><td>${ch.Quantidade||''}</td><td>${ch.Validade||''}</td><td>${esc(ch.Lote||'')}</td></tr>
            </tbody></table></div>
            <div class="form-grid">
                <div class="form-group"><label>Valor Unit.</label><input id="imp-valor-unit" placeholder="0.00"></div>
                <div class="form-group"><label>Valor Total</label><input id="imp-valor-total" readonly></div>
            </div>
            <div class="btn-group"><button class="btn btn-secondary" id="btn-buscar-externo">Buscar valor no sistema externo</button></div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-primary" id="btn-salvar-imp-q">Salvar</button>
        </div>`);

    document.getElementById('imp-valor-unit').addEventListener('input', () => {
        try {
            const unit = parseFloat(document.getElementById('imp-valor-unit').value.replace(',', '.'));
            document.getElementById('imp-valor-total').value = (unit * qtd).toFixed(2);
        } catch { document.getElementById('imp-valor-total').value = ''; }
    });

    document.getElementById('btn-buscar-externo').addEventListener('click', async () => {
        try {
            const resp = await api('/api/financeiro/importacao/valor-externo', {
                method: 'POST',
                body: { codigo_cliente: osRow.Codigo, produto_codigo: ch.id_produto },
            });
            if (resp.valor !== null && resp.valor !== undefined) {
                document.getElementById('imp-valor-unit').value = resp.valor.toFixed(2);
                document.getElementById('imp-valor-unit').dispatchEvent(new Event('input'));
            } else {
                toast(resp.mensagem || 'Nenhum valor encontrado.', 'info');
            }
        } catch (e) { toast(e.message, 'error'); }
    });

    document.getElementById('btn-salvar-imp-q').addEventListener('click', async function() {
        disableBtn(this);
        const valorUnit = parseFloat(document.getElementById('imp-valor-unit').value.replace(',', '.'));
        if (isNaN(valorUnit)) { toast('Informe o Valor Unitário.', 'error'); return; }
        try {
            const resp = await api(`/api/financeiro/importacao/qualidade/${d.os_id}/salvar`, {
                method: 'POST',
                body: { id_produto: ch.id_produto, valor_unit: valorUnit, quantidade: qtd },
            });
            toast(resp.mensagem, 'success');
            closeModal();
            renderPage();
        } catch (e) { toast(e.message, 'error'); }
    });
}

// ---------- Importação de Valores Patrimônio ----------
async function openImportacaoPatrimonio(osId) {
    const d = await api(`/api/financeiro/importacao/patrimonio/${osId}`);
    const cab = d.cabecalho || {};

    openModal(`
        <div class="modal-header"><h2>Importação Valores - Patrimônio - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
        <div class="modal-body">
            <table class="info-table">
                ${[['Código do Cliente',cab.codigo],['Razão',cab.razao]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
            </table>
            <div class="section-title">Produtos</div>
            <div class="tabela-container"><table><thead><tr><th>Descrição</th><th>Marca</th><th>Qtd</th><th>Valor Unit.</th><th>Valor Total</th></tr></thead><tbody>
                ${(d.produtos||[]).map((p, i) => `<tr>
                    <td>${esc(p.produto_descricao||'')}</td><td>${esc(p.produto_marca||'')}</td><td>${p.Quantidade||''}</td>
                    <td><input class="imp-pat-unit" data-idx="${i}" data-qtd="${p.Quantidade||0}" placeholder="0.00" style="width:100px;padding:4px;border:1px solid var(--cinza-borda);border-radius:4px;"></td>
                    <td class="imp-pat-total" data-idx="${i}"></td>
                </tr>`).join('')}
            </tbody></table></div>
            <div class="btn-group"><button class="btn btn-secondary" id="btn-buscar-externo-pat">Buscar valores no sistema externo</button></div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-primary" id="btn-salvar-imp-pat">Salvar</button>
        </div>`);

    // Auto-calc total
    document.querySelectorAll('.imp-pat-unit').forEach(inp => {
        inp.addEventListener('input', () => {
            try {
                const unit = parseFloat(inp.value.replace(',', '.'));
                const qtd = parseFloat(inp.dataset.qtd);
                document.querySelector(`.imp-pat-total[data-idx="${inp.dataset.idx}"]`).textContent = (unit * qtd).toFixed(2);
            } catch {}
        });
    });

    document.getElementById('btn-buscar-externo-pat').addEventListener('click', async () => {
        for (let i = 0; i < (d.produtos || []).length; i++) {
            const p = d.produtos[i];
            try {
                const resp = await api('/api/financeiro/importacao/valor-externo', {
                    method: 'POST',
                    body: { codigo_cliente: cab.codigo, produto_codigo: p.id_Produto },
                });
                if (resp.valor !== null) {
                    const inp = document.querySelector(`.imp-pat-unit[data-idx="${i}"]`);
                    inp.value = resp.valor.toFixed(2);
                    inp.dispatchEvent(new Event('input'));
                }
            } catch {}
        }
        toast('Busca concluída.', 'info');
    });

    document.getElementById('btn-salvar-imp-pat').addEventListener('click', async function() {
        disableBtn(this);
        const valores = [];
        for (let i = 0; i < (d.produtos || []).length; i++) {
            const inp = document.querySelector(`.imp-pat-unit[data-idx="${i}"]`);
            const unit = parseFloat(inp.value.replace(',', '.'));
            if (isNaN(unit)) { toast(`Informe o valor do produto '${d.produtos[i].produto_descricao}'.`, 'error'); return; }
            valores.push({ id_produto: d.produtos[i].id_Produto, valor_unit: unit, quantidade: parseFloat(d.produtos[i].Quantidade || 0) });
        }
        try {
            const resp = await api(`/api/financeiro/importacao/patrimonio/${d.os_id}/salvar`, {
                method: 'POST', body: { valores },
            });
            toast(resp.mensagem, 'success');
            closeModal();
            renderPage();
        } catch (e) { toast(e.message, 'error'); }
    });
}

// ---------- Pagamento PF ----------
async function openPagamento(osId, tipo) {
    if (tipo === 'F') {
        const d = await api(`/api/financeiro/pagamento/pf/${osId}`);
        const ch = d.chamado || {};
        openModal(`
            <div class="modal-header"><h2>Pagamento PF - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
            <div class="modal-body">
                <h3 class="titulo-tela">Formulário de Pagamento - Pessoa Física</h3>
                <table class="info-table">
                    ${[['Nome',ch.nome],['Motivo',ch.motivo],['Nome do Produto',ch.nome_produto],['Lote',ch.lote],['Análise',ch.Analise],['Resolução e Resposta',ch.Resolucao_Resposta]].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
                </table>
                ${renderMidiasHTML(d.midias)}
                <div class="section-title">Dados do pagamento</div>
                <div class="form-grid">
                    <div class="form-group"><label>Código do Produto*</label><input id="pg-codigo-produto"></div>
                    <div class="form-group"><label>Valor*</label><input id="pg-valor" placeholder="0.00"></div>
                    <div class="form-group"><label>Data Pagamento*</label><input type="date" id="pg-data"></div>
                    <div class="form-group"><label>Código gerado p/ pagamento*</label><input id="pg-codigo-sistema"></div>
                    <div class="form-group"><label>Sistema*</label><select id="pg-sistema"><option>EFICAZ</option><option>SENIOR</option></select></div>
                    <div class="form-group"><label>Observação</label><input id="pg-obs"></div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" id="btn-salvar-pg-pf">Salvar</button>
            </div>`);

        document.getElementById('btn-salvar-pg-pf').addEventListener('click', async function() {
            disableBtn(this);
            try {
                const resp = await api(`/api/financeiro/pagamento/pf/${d.os_id}/salvar`, {
                    method: 'POST',
                    body: {
                        codigo_produto: document.getElementById('pg-codigo-produto').value,
                        valor: document.getElementById('pg-valor').value,
                        data_pg: document.getElementById('pg-data').value,
                        codigo_sistema: document.getElementById('pg-codigo-sistema').value,
                        sistema: document.getElementById('pg-sistema').value,
                        observacao: document.getElementById('pg-obs').value,
                    },
                });
                toast(resp.mensagem, 'success');
                closeModal();
                renderPage();
            } catch (e) { toast(e.message, 'error'); }
        });
    } else if (tipo === 'Q') {
        const d = await api(`/api/financeiro/pagamento/pj-qualidade/${osId}`);
        const ch = d.chamado || {};
        const osRow = d.os_row || {};
        openModal(`
            <div class="modal-header"><h2>Pagamento PJ Qualidade - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
            <div class="modal-body">
                <h3 class="titulo-tela">Formulário de Pagamento - PJ Qualidade</h3>
                <table class="info-table">
                    ${[['Nome',ch.Nome],['Código do Cliente',osRow.Codigo],['Razão',ch.razao],['Motivo',ch.Motivo],['Problema',ch.Problema],['Análise',ch['Analise Qualidade']],['Resolução e Resposta',ch.Resolucao_Resposta],['Justificativa',ch.Justificativa],['Valor a pagar',d.valor_total?.toFixed(2)||'0.00']].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
                </table>
                ${renderMidiasHTML(d.midias)}
                <div class="section-title">Dados do pagamento</div>
                <div class="form-grid">
                    <div class="form-group"><label>Data Pagamento*</label><input type="date" id="pg-q-data"></div>
                    <div class="form-group"><label>Código gerado p/ pagamento*</label><input id="pg-q-codigo"></div>
                    <div class="form-group"><label>Sistema*</label><select id="pg-q-sistema"><option>EFICAZ</option><option>SENIOR</option></select></div>
                    <div class="form-group"><label>Observação</label><input id="pg-q-obs"></div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" id="btn-salvar-pg-q">Salvar</button>
            </div>`);

        document.getElementById('btn-salvar-pg-q').addEventListener('click', async function() {
            disableBtn(this);
            try {
                const resp = await api(`/api/financeiro/pagamento/pj/${d.os_id}/salvar`, {
                    method: 'POST',
                    body: {
                        data_pg: document.getElementById('pg-q-data').value,
                        codigo_sistema: document.getElementById('pg-q-codigo').value,
                        sistema: document.getElementById('pg-q-sistema').value,
                        observacao: document.getElementById('pg-q-obs').value,
                    },
                });
                toast(resp.mensagem, 'success');
                closeModal();
                renderPage();
            } catch (e) { toast(e.message, 'error'); }
        });
    } else {
        const d = await api(`/api/financeiro/pagamento/pj-patrimonio/${osId}`);
        const cab = d.cabecalho || {};
        openModal(`
            <div class="modal-header"><h2>Pagamento PJ Patrimônio - OS ${d.os_id}</h2><button class="modal-close" onclick="closeModal()">✕</button></div>
            <div class="modal-body">
                <h3 class="titulo-tela">Formulário de Pagamento - PJ Patrimônio</h3>
                <table class="info-table">
                    ${[['Código do Cliente',cab.codigo],['Razão',cab.razao],['Nº OS Manutenção',cab.numero_os_manutencao],['Motivo',cab.motivo],['Justificativa',cab.justificativa],['Valor a pagar',d.valor_total?.toFixed(2)||'0.00']].map(([l,v]) => `<tr><td>${l}</td><td>${esc(v||'-')}</td></tr>`).join('')}
                </table>
                ${renderMidiasHTML(d.midias)}
                <div class="section-title">Dados do pagamento</div>
                <div class="form-grid">
                    <div class="form-group"><label>Data Pagamento*</label><input type="date" id="pg-p-data"></div>
                    <div class="form-group"><label>Código gerado p/ pagamento*</label><input id="pg-p-codigo"></div>
                    <div class="form-group"><label>Sistema*</label><select id="pg-p-sistema"><option>EFICAZ</option><option>SENIOR</option></select></div>
                    <div class="form-group"><label>Observação</label><input id="pg-p-obs"></div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" id="btn-salvar-pg-p">Salvar</button>
            </div>`);

        document.getElementById('btn-salvar-pg-p').addEventListener('click', async function() {
            disableBtn(this);
            try {
                const resp = await api(`/api/financeiro/pagamento/pj/${d.os_id}/salvar`, {
                    method: 'POST',
                    body: {
                        data_pg: document.getElementById('pg-p-data').value,
                        codigo_sistema: document.getElementById('pg-p-codigo').value,
                        sistema: document.getElementById('pg-p-sistema').value,
                        observacao: document.getElementById('pg-p-obs').value,
                    },
                });
                toast(resp.mensagem, 'success');
                closeModal();
                renderPage();
            } catch (e) { toast(e.message, 'error'); }
        });
    }
}

// ---------- Fichas (abrir por tipo) ----------
function openFicha(osId, tipo) {
    if (tipo === 'F') openModalFichaPF(osId);
    else if (tipo === 'Q') openFichaPJQualidade(osId);
    else openFichaPJPatrimonio(osId);
}


// ============================================================
// Helpers de renderização
// ============================================================

// ---- Lightbox de Mídia ----
let lbFotos = [];
let lbIdx = 0;
let lbZoomAtivo = false;
let lbZoomScale = 1;
const LB_ZOOM_MIN = 1, LB_ZOOM_MAX = 5, LB_ZOOM_STEP = 0.4;

function initLightbox() {
    if (document.getElementById('lightbox')) return;
    const lb = document.createElement('div');
    lb.id = 'lightbox';
    lb.className = 'lightbox';
    lb.onclick = (e) => { if (e.target === lb) fecharLb(); };
    lb.innerHTML = `
        <button class="lb-close" onclick="fecharLb()" title="Fechar (Esc)">✕</button>
        <button class="lb-nav lb-prev" onclick="navLb(-1);event.stopPropagation()" title="Anterior (←)">‹</button>
        <div class="lb-img-wrap" id="lb-wrap" onclick="toggleZoomLb(event)">
            <img id="lb-img" src="" alt="">
        </div>
        <div class="lb-caption" id="lb-caption"></div>
        <div class="lb-counter" id="lb-counter"></div>
        <div class="lb-toolbar">
            <button class="lb-btn" onclick="toggleZoomLb(event)" id="btn-zoom" title="Clique na imagem ou scroll para zoom">
                🔍 <span id="zoom-label">Ampliar</span>
            </button>
            <a class="lb-btn" id="btn-nova-aba" href="#" target="blank" onclick="event.stopPropagation()" title="Abrir em nova aba">
                🔗 Nova aba
            </a>
            <span class="lb-zoom-hint">Scroll do mouse também aplica zoom</span>
        </div>
        <button class="lb-nav lb-next" onclick="navLb(1);event.stopPropagation()" title="Próxima (→)">›</button>
    `;
    document.body.appendChild(lb);

    // Scroll zoom
    document.getElementById('lb-wrap').addEventListener('wheel', e => {
        e.preventDefault(); e.stopPropagation();
        lbZoomScale += e.deltaY < 0 ? LB_ZOOM_STEP : -LB_ZOOM_STEP;
        lbZoomScale = Math.min(Math.max(lbZoomScale, LB_ZOOM_MIN), LB_ZOOM_MAX);
        aplicarZoomLb();
    }, { passive: false });

    // Teclado
    document.addEventListener('keydown', e => {
        const lb = document.getElementById('lightbox');
        if (!lb || !lb.classList.contains('open')) return;
        if (e.key === 'Escape') fecharLb();
        if (e.key === 'ArrowLeft') navLb(-1);
        if (e.key === 'ArrowRight') navLb(1);
        if (e.key === '+' || e.key === '=') { lbZoomScale = Math.min(lbZoomScale + LB_ZOOM_STEP, LB_ZOOM_MAX); aplicarZoomLb(); }
        if (e.key === '-') { lbZoomScale = Math.max(lbZoomScale - LB_ZOOM_STEP, LB_ZOOM_MIN); aplicarZoomLb(); }
        if (e.key === '0') resetZoomLb();
    });
}

function abrirLightbox(idx) {
    lbIdx = idx;
    resetZoomLb();
    atualizarLb();
    document.getElementById('lightbox').classList.add('open');
    document.body.style.overflow = 'hidden';
}
function fecharLb() {
    document.getElementById('lightbox').classList.remove('open');
    document.body.style.overflow = '';
    resetZoomLb();
}
function navLb(dir) {
    lbIdx = (lbIdx + dir + lbFotos.length) % lbFotos.length;
    resetZoomLb();
    atualizarLb();
}
function atualizarLb() {
    const f = lbFotos[lbIdx];
    const img = document.getElementById('lb-img');
    img.src = f.src;
    document.getElementById('lb-caption').textContent = f.nome;
    document.getElementById('lb-counter').textContent = `${lbIdx + 1} / ${lbFotos.length}`;
    document.getElementById('btn-nova-aba').href = f.src;
}
function aplicarZoomLb() {
    const img = document.getElementById('lb-img');
    const wrap = document.getElementById('lb-wrap');
    img.style.transform = `scale(${lbZoomScale})`;
    lbZoomAtivo = lbZoomScale > 1;
    wrap.classList.toggle('zoomed', lbZoomAtivo);
    document.getElementById('zoom-label').textContent = lbZoomAtivo ? 'Reduzir' : 'Ampliar';
}
function toggleZoomLb(e) {
    e.stopPropagation();
    if (lbZoomAtivo) resetZoomLb();
    else { lbZoomScale = 2.5; aplicarZoomLb(); }
}
function resetZoomLb() { lbZoomScale = 1; aplicarZoomLb(); }

function renderMidiasHTML(midias) {
    if (!midias || midias.length === 0) return '<p class="subtitulo">Nenhuma mídia registrada.</p>';
    const extImg = ['png','jpg','jpeg','bmp','gif','webp'];
    const extVid = ['mp4','avi','mov','mkv','wmv','flv','webm'];
    const fotosParaLightbox = [];
    const items = midias.map((m, i) => {
        const ext = (m.nome || '').split('.').pop().toLowerCase();
        const isImg = extImg.includes(ext);
        const isVid = extVid.includes(ext);
        const url = m.localizacao ? `/api/midia/${encodeURIComponent(m.localizacao)}` : '';
        if (isImg && url) {
            fotosParaLightbox.push({ src: url, nome: m.nome || '' });
            const lbIdx = fotosParaLightbox.length - 1;
            return `<div class="midia-item" title="${esc(m.nome||'')}" onclick="abrirLightbox(${lbIdx})"><img src="${url}" alt="${esc(m.nome||'')}" onerror="this.parentElement.classList.add('unavailable');this.alt='❌'" loading="lazy"><div class="midia-nome">${esc(m.nome||'')}</div></div>`;
        }
        if (isVid && url) {
            return `<div class="midia-item video-item" title="${esc(m.nome||'')}" onclick="window.open('${url}','_blank')"><div class="midia-nome">${esc(m.nome||'')}</div></div>`;
        }
        return `<div class="midia-item unavailable" title="${esc(m.nome||'')} – arquivo não encontrado">📷<div class="midia-nome">${esc(m.nome||'')}</div></div>`;
    }).join('');
    // Inicializa lightbox e atualiza array de fotos
    initLightbox();
    lbFotos = fotosParaLightbox;
    const disponiveis = fotosParaLightbox.length;
    const total = midias.length;
    const badge = disponiveis < total
        ? `<span class="badge" style="background:#e74c3c;margin-left:.5rem">${disponiveis}/${total} disponíveis</span>`
        : `<span class="badge badge-novo" style="margin-left:.5rem">${total} foto(s)</span>`;
    return `<div class="section-title">Mídias registradas ${badge}</div><div class="midia-grid">${items}</div>`;
}

function renderPagamentosHTML(pagamentos) {
    if (!pagamentos || pagamentos.length === 0) return '<p class="subtitulo">Nenhum pagamento registrado.</p>';
    return `<div class="tabela-container"><table><thead><tr>
        <th>Código Produto</th><th>Valor</th><th>Data Pagamento</th><th>Código Pagamento</th><th>Sistema</th><th>Observação</th>
    </tr></thead><tbody>
        ${pagamentos.map(p => `<tr>
            <td>${p.id_produto||''}</td><td>${p.valor||''}</td><td>${p.data_pg||''}</td>
            <td>${esc(p.codigo_sistema||'')}</td><td>${esc(p.sistema||'')}</td><td>${esc(p.observacao||'')}</td>
        </tr>`).join('')}
    </tbody></table></div>`;
}

function badgeClass(status) {
    if (!status) return 'badge-novo';
    if (status === 'Novo') return 'badge-novo';
    if (status === 'Finalizado') return 'badge-finalizado';
    if (status.includes('Aprovado')) return 'badge-aprovado';
    if (status.includes('Reprovado')) return 'badge-reprovado';
    return 'badge-processo';
}

function fmtData(valor) {
    if (!valor) return '-';
    return valor.substring(0, 16).replace('T', ' ');
}

function esc(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

// ============================================================
// Prevenir múltiplos cliques em botões de salvar
// ============================================================
function disableBtn(btn) {
    btn.disabled = true;
    btn.dataset.originalText = btn.textContent;
    btn.textContent = 'Salvando...';
    setTimeout(() => {
        btn.disabled = false;
        btn.textContent = btn.dataset.originalText || 'Salvar';
    }, 3000);
}

// ============================================================
// PDF — gerar e baixar
// ============================================================
async function gerarPDF(titulo, osId, campos, tabela, observacoes) {
    const body = { titulo, os_id: osId, campos };
    if (tabela) body.tabela = tabela;
    if (observacoes) body.observacoes = observacoes;
    try {
        toast('Gerando PDF...', 'info');
        // Tenta download direto primeiro (mais confiável)
        const resp = await fetch('/api/pdf/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(body),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.erro || `Erro ${resp.status}`);
        }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `OS_${osId}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast('PDF gerado com sucesso!', 'success');
    } catch (e) {
        toast('Erro ao gerar PDF: ' + e.message, 'error');
    }
}

async function gerarPDFFFichaPF(osId) {
    const d = await api(`/api/fichas/pf/${osId}`);
    const ch = d.chamado || {};
    const campos = [
        ['Nome', ch.nome], ['E-mail', ch.email], ['CPF', ch.cpf],
        ['Celular', ch.celular], ['Motivo', ch.motivo],
        ['Cidade', ch.cidade], ['Estado', ch.estado],
        ['Marca', ch.marca], ['Nome do Produto', ch.nome_produto],
        ['Quantidade', ch.quantidade], ['Validade', ch.validade],
        ['Lote', ch.lote], ['Problema', ch.problema], ['Local de compra', ch.local],
    ];
    const tabela = null;
    const observacoes = [
        ['Aberto por', d.status_novo],
        ['Análise', ch.Analise],
        ['Resolução e Resposta', ch.Resolucao_Resposta],
        ['Decisão Qualidade', d.decisao_qualidade],
        ['Finalizado por', d.status_finalizado],
    ];
    if (d.pagamentos && d.pagamentos.length) {
        observacoes.push(['Pagamentos', '']);
        d.pagamentos.forEach((p, i) => {
            observacoes.push([`Produto ${p.id_produto || i+1}`, `R$ ${p.valor || '0.00'} • ${p.data_pg || '-'} • ${p.sistema || '-'} • ${p.observacao || '-'}`]);
        });
    }
    await gerarPDF('Ficha - Pessoa Física', osId, campos, tabela, observacoes);
}

async function gerarPDFFFichaPJQ(osId) {
    const d = await api(`/api/fichas/pj-qualidade/${osId}`);
    const ch = d.chamado || {};
    const osRow = d.os_row || {};
    const val0 = d.pagamentos?.[0] || {};
    const campos = [
        ['Nome', ch.Nome], ['Celular', ch.Celular],
        ['Código do Cliente', osRow.Codigo], ['Razão', ch.razao],
        ['CPF/CNPJ', ch.cnpj_cpf], ['Motivo', ch.Motivo],
        ['Problema', ch.Problema],
    ];
    const tabela = {
        cabecalhos: ['Descrição', 'Marca', 'Quantidade', 'Validade', 'Lote', 'Valor'],
        linhas: [[
            ch.produto_descricao || '', ch.produto_marca || '',
            String(ch.Quantidade || ''), String(ch.Validade || ''),
            ch.Lote || '', String(val0.valor || 'R$ 0.00'),
        ]],
    };
    const observacoes = [
        ['Aberto por', d.status_novo],
        ['Análise (Qualidade)', ch['Analise Qualidade']],
        ['Resolução e Resposta', ch.Resolucao_Resposta],
        ['Decisão Qualidade', d.decisao_qualidade],
        ['Justificativa', ch.Justificativa],
        ['Decisão Comercial', d.decisao_comercial],
        ['Finalizado por', d.status_finalizado],
    ];
    await gerarPDF('Ficha - PJ Qualidade', osId, campos, tabela, observacoes);
}

async function gerarPDFFFichaPJP(osId) {
    const d = await api(`/api/fichas/pj-patrimonio/${osId}`);
    const cab = d.cabecalho || {};
    const valMap = {};
    (d.pagamentos || []).forEach(p => valMap[p.id_produto] = p.valor);
    const campos = [
        ['Código do Cliente', cab.codigo], ['Razão', cab.razao],
        ['Nº OS Manutenção', cab.numero_os_manutencao],
        ['Motivo', cab.motivo], ['Justificativa', cab.justificativa],
    ];
    const tabela = {
        cabecalhos: ['ID Produto', 'Descrição', 'Marca', 'Quantidade', 'Valor'],
        linhas: (d.produtos || []).map(p => [
            String(p.id_Produto || ''), p.produto_descricao || '',
            p.produto_marca || '', String(p.Quantidade || ''),
            String(valMap[p.id_Produto] ? `R$ ${valMap[p.id_Produto]}` : '-'),
        ]),
    };
    const observacoes = [
        ['Aberto por', d.status_novo],
        ['Decisão Patrimônio', d.decisao_patrimonio],
        ['Decisão Comercial', d.decisao_comercial],
        ['Finalizado por', d.status_finalizado],
    ];
    await gerarPDF('Ficha - PJ Patrimônio', osId, campos, tabela, observacoes);
}


// ============================================================
// Inicialização
// ============================================================
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const data = await api('/api/me');
        State.usuario = data.usuario;
        await loadPermissoes();
    } catch {
        State.usuario = null;
    }
    render();
});
