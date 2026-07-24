from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)

from core.database import listar_aguardando_pagamento
from modules.base_popup_module import BasePopupModule
from modules.financeiro.pagamento_pf import PagamentoPF
from modules.financeiro.pagamento_pj_qualidade import PagamentoPJQualidade
from modules.financeiro.pagamento_pj_patrimonio import PagamentoPJPatrimonio


class ListaPagamento(BasePopupModule):
    """Módulo 1.3.2 - Lista para Pagamento: OS com Status_Atual = 'Aguardando Financeiro'."""

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(usuario_logado, parent)
        self.setWindowTitle("Financeiro - Lista para Pagamento")
        self.resize(760, 520)
        self._resultados: list[dict] = []
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        titulo = QLabel("Lista para Pagamento")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        dica = QLabel("Dê duplo clique em uma linha para abrir o formulário de pagamento.")
        dica.setObjectName("subtitulo")
        layout.addWidget(dica)

        self.tabela = QTableWidget(0, 4)
        self.tabela.setHorizontalHeaderLabels(["OS", "Código", "Razão", "Tipo"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.cellDoubleClicked.connect(self._abrir_pagamento)
        layout.addWidget(self.tabela)

        self._carregar()

    def _carregar(self):
        try:
            self._resultados = listar_aguardando_pagamento()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar lista.\n\n{exc}")
            return

        self.tabela.setRowCount(0)
        for row in self._resultados:
            i = self.tabela.rowCount()
            self.tabela.insertRow(i)
            self.tabela.setItem(i, 0, QTableWidgetItem(str(row["os_id"])))
            self.tabela.setItem(i, 1, QTableWidgetItem(str(row.get("codigo") or "")))
            self.tabela.setItem(i, 2, QTableWidgetItem(row.get("razao") or ""))
            self.tabela.setItem(i, 3, QTableWidgetItem(row["tipo"]))

    def _abrir_pagamento(self, linha: int, _coluna: int):
        registro = self._resultados[linha]
        os_id = registro["os_id"]
        tipo = registro["tipo"]

        if tipo == "F":
            dialogo = PagamentoPF(self.usuario_logado, os_id, parent=self)
        elif tipo == "Q":
            dialogo = PagamentoPJQualidade(self.usuario_logado, os_id, parent=self)
        else:
            dialogo = PagamentoPJPatrimonio(self.usuario_logado, os_id, parent=self)

        dialogo.exec()
        self._carregar()

    def descarregar_dados(self):
        self._resultados.clear()
