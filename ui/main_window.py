from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu, QMessageBox,
)

from config import Config
from core.permissions import pode_acessar
from core import permissions as perm
from ui.dashboard_widget import DashboardWidget

from modules.chamados.formulario_abertura_pf import FormularioAberturaPF
from modules.chamados.lista_chamado_pf import ListaChamadoPF
from modules.chamados.lista_de_chamados import ListaDeChamados
from modules.aprovacoes.novos_qualidade import NovosQualidade
from modules.aprovacoes.investigacoes_abertas import InvestigacoesAbertas
from modules.aprovacoes.novos_patrimonio import NovosPatrimonio
from modules.aprovacoes.reprovados_qualidade import ReprovadosQualidade
from modules.aprovacoes.reprovados_patrimonio import ReprovadosPatrimonio
from modules.financeiro.importacao_valores import ImportacaoValores
from modules.financeiro.lista_pagamento import ListaPagamento
from modules.financeiro.pagamentos_registrados import PagamentosRegistrados
from modules.administrativo.integracao_informacoes import IntegracaoInformacoes
from modules.administrativo.gestao_usuarios import GestaoUsuarios


class MainWindow(QMainWindow):
    """
    Módulo 1 - Tela Inicial.

    Abre em tela cheia (showMaximized), monta os menus suspensos
    dinamicamente de acordo com a matriz de permissões do usuário logado,
    mostra o mini dashboard e o logo da empresa no rodapé.

    Cada módulo é aberto como pop-up modal (QDialog) e é destruído ao
    fechar (WA_DeleteOnClose + descarregar_dados), conforme especificado.
    """

    def __init__(self, usuario_logado: dict):
        super().__init__()
        self.usuario_logado = usuario_logado
        self.setWindowTitle(Config.APP_NAME)
        self._montar_ui()
        self.showMaximized()

    # ------------------------------------------------------------------
    def _montar_ui(self):
        raiz = QWidget()
        raiz.setObjectName("root")
        layout = QVBoxLayout(raiz)

        boas_vindas = QLabel(f"Bem-vindo: {self.usuario_logado.get('Nome', '')}")
        boas_vindas.setObjectName("tituloTela")
        layout.addWidget(boas_vindas)

        self.dashboard = DashboardWidget()
        layout.addWidget(self.dashboard)

        layout.addStretch()

        logo_label = QLabel()
        if Config.LOGO_PATH.exists():
            pix = QPixmap(str(Config.LOGO_PATH)).scaledToWidth(180, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        self.setCentralWidget(raiz)
        self._montar_menus()

    # ------------------------------------------------------------------
    def _tipo(self) -> str:
        return self.usuario_logado.get("Tipo", "")

    def _acao(self, menu: QMenu, titulo: str, chave_modulo: str, callback):
        """Adiciona um item de menu somente se o usuário tiver permissão."""
        if not pode_acessar(self._tipo(), chave_modulo):
            return
        acao = QAction(titulo, self)
        acao.triggered.connect(callback)
        menu.addAction(acao)

    def _montar_menus(self):
        barra = self.menuBar()

        # --- Chamados ---
        menu_chamados = QMenu("Chamados", self)
        submenu_pf = QMenu("Chamado Pessoa Física", self)
        self._acao(submenu_pf, "Formulário Abertura", perm.M_CHAMADO_ABERTURA_PF,
                   self._abrir_formulario_abertura_pf)
        self._acao(submenu_pf, "Lista Chamado PF", perm.M_CHAMADO_LISTA_PF,
                   self._abrir_lista_chamado_pf)
        if submenu_pf.actions():
            menu_chamados.addMenu(submenu_pf)

        self._acao(menu_chamados, "Lista de Chamados", perm.M_CHAMADO_LISTA,
                   self._abrir_lista_de_chamados)
        self._acao(menu_chamados, "Ficha Chamado", perm.M_CHAMADO_FICHA_GERAR,
                   self._abrir_lista_de_chamados)
        if menu_chamados.actions():
            barra.addMenu(menu_chamados)

        # --- Aprovações ---
        menu_aprov = QMenu("Aprovações", self)

        sub_qualidade = QMenu("Qualidade", self)
        self._acao(sub_qualidade, "Novos Qualidade", perm.M_APROV_QUALIDADE_NOVOS,
                   self._abrir_novos_qualidade)
        self._acao(sub_qualidade, "Investigações Abertas", perm.M_APROV_QUALIDADE_INVESTIGACAO,
                   self._abrir_investigacoes_abertas)
        if sub_qualidade.actions():
            menu_aprov.addMenu(sub_qualidade)

        sub_patrimonio = QMenu("Patrimônio", self)
        self._acao(sub_patrimonio, "Novos Patrimônio", perm.M_APROV_PATRIMONIO_NOVOS,
                   self._abrir_novos_patrimonio)
        if sub_patrimonio.actions():
            menu_aprov.addMenu(sub_patrimonio)

        sub_comercial = QMenu("Comercial", self)
        self._acao(sub_comercial, "Reprovados Qualidade", perm.M_APROV_COMERCIAL_REPROVADOS_Q,
                   self._abrir_reprovados_qualidade)
        self._acao(sub_comercial, "Reprovados Patrimônio", perm.M_APROV_COMERCIAL_REPROVADOS_P,
                   self._abrir_reprovados_patrimonio)
        if sub_comercial.actions():
            menu_aprov.addMenu(sub_comercial)

        if menu_aprov.actions():
            barra.addMenu(menu_aprov)

        # --- Financeiro ---
        menu_fin = QMenu("Financeiro", self)
        self._acao(menu_fin, "Importação de Valores", perm.M_FIN_IMPORTACAO,
                   self._abrir_importacao_valores)
        self._acao(menu_fin, "Lista para Pagamento", perm.M_FIN_LISTA_PAGAMENTO,
                   self._abrir_lista_pagamento)
        self._acao(menu_fin, "Pagamentos Registrados", perm.M_FIN_PAGOS,
                   self._abrir_pagamentos_registrados)
        if menu_fin.actions():
            barra.addMenu(menu_fin)

        # --- Administrativo ---
        menu_adm = QMenu("Administrativo", self)
        self._acao(menu_adm, "Integração informações", perm.M_ADM_INTEGRACAO,
                   self._abrir_integracao_informacoes)
        self._acao(menu_adm, "Gestão de Usuários", perm.M_ADM_USUARIOS,
                   self._abrir_gestao_usuarios)
        if menu_adm.actions():
            barra.addMenu(menu_adm)

    # ------------------------------------------------------------------
    def _abrir_formulario_abertura_pf(self):
        dialogo = FormularioAberturaPF(self.usuario_logado, parent=self)
        dialogo.exec()
        self.dashboard.atualizar()

    def _abrir_lista_chamado_pf(self):
        dialogo = ListaChamadoPF(self.usuario_logado, parent=self)
        dialogo.exec()
        self.dashboard.atualizar()

    def _abrir_lista_de_chamados(self):
        dialogo = ListaDeChamados(self.usuario_logado, parent=self)
        dialogo.exec()
        self.dashboard.atualizar()

    def _abrir_novos_qualidade(self):
        dialogo = NovosQualidade(self.usuario_logado, parent=self)
        dialogo.exec()
        self.dashboard.atualizar()

    def _abrir_investigacoes_abertas(self):
        dialogo = InvestigacoesAbertas(self.usuario_logado, parent=self)
        dialogo.exec()
        self.dashboard.atualizar()

    def _abrir_novos_patrimonio(self):
        dialogo = NovosPatrimonio(self.usuario_logado, parent=self)
        dialogo.exec()
        self.dashboard.atualizar()

    def _abrir_reprovados_qualidade(self):
        dialogo = ReprovadosQualidade(self.usuario_logado, parent=self)
        dialogo.exec()
        self.dashboard.atualizar()

    def _abrir_reprovados_patrimonio(self):
        dialogo = ReprovadosPatrimonio(self.usuario_logado, parent=self)
        dialogo.exec()
        self.dashboard.atualizar()

    def _abrir_importacao_valores(self):
        dialogo = ImportacaoValores(self.usuario_logado, parent=self)
        dialogo.exec()
        self.dashboard.atualizar()

    def _abrir_lista_pagamento(self):
        dialogo = ListaPagamento(self.usuario_logado, parent=self)
        dialogo.exec()
        self.dashboard.atualizar()

    def _abrir_pagamentos_registrados(self):
        dialogo = PagamentosRegistrados(self.usuario_logado, parent=self)
        dialogo.exec()

    def _abrir_integracao_informacoes(self):
        dialogo = IntegracaoInformacoes(self.usuario_logado, parent=self)
        dialogo.exec()

    def _abrir_gestao_usuarios(self):
        dialogo = GestaoUsuarios(self.usuario_logado, parent=self)
        dialogo.exec()

    def _nao_implementado(self, nome_tela: str):
        def _callback():
            QMessageBox.information(
                self, "Em construção",
                f"A tela '{nome_tela}' segue o mesmo padrão do módulo "
                f"'Formulário Abertura PF' e ainda será implementada.",
            )
        return _callback
