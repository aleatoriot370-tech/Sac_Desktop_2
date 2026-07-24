from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView,
)

from core.database import listar_todos_chamados
from modules.base_popup_module import BasePopupModule
from modules.chamados.ficha_pessoa_fisica import FichaPessoaFisica
from modules.chamados.ficha_pj_qualidade import FichaPJQualidade
from modules.chamados.ficha_pj_patrimonio import FichaPJPatrimonio

STATUS_OPCOES = [
    "", "Novo", "Em Investigação", "Aprovado - Qualidade", "Reprovado - Qualidade",
    "Aprovado - Patrimônio", "Reprovado - Patrimônio", "Aprovado - Comercial",
    "Reprovado - Comercial", "Aguardando Financeiro", "Pagamento Programado", "Finalizado",
]
TIPO_OPCOES = ["", "F", "Q", "P"]


class ListaDeChamados(BasePopupModule):
    """Módulo 1.1.2 - Lista de Chamados (todos os tipos), com exportação em lote."""

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(usuario_logado, parent)
        self.setWindowTitle("Chamados - Lista de Chamados")
        self.resize(880, 600)
        self._resultados: list[dict] = []
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        titulo = QLabel("Lista de Chamados")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        filtros = QHBoxLayout()
        self.campo_os_id = QLineEdit()
        self.campo_os_id.setPlaceholderText("Nº da OS")
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(TIPO_OPCOES)
        self.combo_tipo.currentTextChanged.connect(self._atualizar_campo_busca)
        self.campo_busca = QLineEdit()
        self.campo_busca.setPlaceholderText("CPF (se Tipo=F) ou Código (se Tipo=Q/P)")
        self.combo_status = QComboBox()
        self.combo_status.addItems(STATUS_OPCOES)
        btn_pesquisar = QPushButton("Pesquisar")
        btn_pesquisar.clicked.connect(self._pesquisar)

        filtros.addWidget(self.campo_os_id)
        filtros.addWidget(self.combo_tipo)
        filtros.addWidget(self.campo_busca)
        filtros.addWidget(self.combo_status)
        filtros.addWidget(btn_pesquisar)
        layout.addLayout(filtros)

        dica = QLabel(
            "Duplo clique abre a ficha do chamado. Selecione várias linhas "
            "(Ctrl/Shift) e use 'Exportar selecionados' para abrir cada "
            "ficha e gerar seu PDF."
        )
        dica.setObjectName("subtitulo")
        dica.setWordWrap(True)
        layout.addWidget(dica)

        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(["OS", "Código", "Razão", "Status", "Tipo"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tabela.cellDoubleClicked.connect(self._abrir_ficha)
        layout.addWidget(self.tabela)

        btn_exportar_lote = QPushButton("Exportar selecionados (PDF)")
        btn_exportar_lote.setObjectName("secondary")
        btn_exportar_lote.clicked.connect(self._exportar_selecionados)
        layout.addWidget(btn_exportar_lote)

        self._pesquisar()

    def _atualizar_campo_busca(self, tipo: str):
        if tipo == "F":
            self.campo_busca.setPlaceholderText("CPF do cliente")
        elif tipo in ("Q", "P"):
            self.campo_busca.setPlaceholderText("Código do cliente")
        else:
            self.campo_busca.setPlaceholderText("CPF (se Tipo=F) ou Código (se Tipo=Q/P)")

    def _pesquisar(self):
        os_id = self.campo_os_id.text().strip()
        tipo = self.combo_tipo.currentText() or None
        status_filtro = self.combo_status.currentText() or None
        busca = self.campo_busca.text().strip()

        cpf = busca if tipo == "F" and busca else None
        codigo = int(busca) if tipo in ("Q", "P") and busca.isdigit() else None

        try:
            self._resultados = listar_todos_chamados(
                os_id=int(os_id) if os_id else None,
                status_filtro=status_filtro, tipo_filtro=tipo,
                cpf=cpf, codigo=codigo,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao buscar chamados.\n\n{exc}")
            return

        self.tabela.setRowCount(0)
        for row in self._resultados:
            i = self.tabela.rowCount()
            self.tabela.insertRow(i)
            self.tabela.setItem(i, 0, QTableWidgetItem(str(row["os_id"])))
            self.tabela.setItem(i, 1, QTableWidgetItem(str(row.get("codigo") or 0)))
            self.tabela.setItem(i, 2, QTableWidgetItem(row.get("razao") or ""))
            self.tabela.setItem(i, 3, QTableWidgetItem(row.get("status") or ""))
            self.tabela.setItem(i, 4, QTableWidgetItem(row["tipo"]))

    def _abrir_ficha(self, linha: int, _coluna: int):
        registro = self._resultados[linha]
        self._abrir_ficha_para(registro)
        self._pesquisar()

    def _abrir_ficha_para(self, registro: dict):
        os_id, tipo = registro["os_id"], registro["tipo"]
        if tipo == "F":
            dialogo = FichaPessoaFisica(self.usuario_logado, os_id, parent=self)
        elif tipo == "Q":
            dialogo = FichaPJQualidade(self.usuario_logado, os_id, parent=self)
        else:
            dialogo = FichaPJPatrimonio(self.usuario_logado, os_id, parent=self)
        dialogo.exec()

    def _exportar_selecionados(self):
        linhas_selecionadas = sorted({idx.row() for idx in self.tabela.selectedIndexes()})
        if not linhas_selecionadas:
            QMessageBox.information(self, "Nada selecionado", "Selecione ao menos uma linha para exportar.")
            return

        resposta = QMessageBox.question(
            self, "Exportar em lote",
            f"Exportar {len(linhas_selecionadas)} chamado(s) em PDF, um arquivo por chamado?",
        )
        if resposta != QMessageBox.Yes:
            return

        for i in linhas_selecionadas:
            registro = self._resultados[i]
            # Reaproveita a própria ficha (que já sabe montar seus campos e
            # tem o botão "Exportar PDF") para gerar cada arquivo; o usuário
            # confirma o local de salvamento de cada PDF individualmente.
            self._abrir_ficha_para(registro)

    def descarregar_dados(self):
        self._resultados.clear()
