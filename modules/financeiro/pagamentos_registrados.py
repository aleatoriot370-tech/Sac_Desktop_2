from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit

from core.database import listar_pagamentos_registrados
from modules.base_popup_module import BasePopupModule

TIPOS = ["", "F", "Q", "P"]


class PagamentosRegistrados(BasePopupModule):
    """Módulo 1.3.3 - Pagamentos Registrados (histórico com filtros)."""

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(usuario_logado, parent)
        self.setWindowTitle("Financeiro - Pagamentos Registrados")
        self.resize(800, 560)
        self._resultados: list[dict] = []
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        titulo = QLabel("Pagamentos Registrados")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        filtros = QHBoxLayout()
        self.usar_filtro_data = QComboBox()
        self.usar_filtro_data.addItems(["Sem filtro de data", "Filtrar por data"])
        self.campo_data = QDateEdit(QDate.currentDate())
        self.campo_data.setCalendarPopup(True)
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(TIPOS)
        btn_pesquisar = QPushButton("Pesquisar")
        btn_pesquisar.clicked.connect(self._pesquisar)

        filtros.addWidget(self.usar_filtro_data)
        filtros.addWidget(self.campo_data)
        filtros.addWidget(self.combo_tipo)
        filtros.addWidget(btn_pesquisar)
        layout.addLayout(filtros)

        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(["OS", "Código", "Razão", "Tipo", "Data Pagamento"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        layout.addWidget(self.tabela)

        self._pesquisar()

    def _pesquisar(self):
        data_filtro = (
            self.campo_data.date().toString("yyyy-MM-dd")
            if self.usar_filtro_data.currentIndex() == 1 else None
        )
        tipo_filtro = self.combo_tipo.currentText() or None

        try:
            self._resultados = listar_pagamentos_registrados(
                data_pg=data_filtro, tipo_filtro=tipo_filtro,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao buscar pagamentos.\n\n{exc}")
            return

        self.tabela.setRowCount(0)
        for row in self._resultados:
            i = self.tabela.rowCount()
            self.tabela.insertRow(i)
            self.tabela.setItem(i, 0, QTableWidgetItem(str(row["os_id"])))
            self.tabela.setItem(i, 1, QTableWidgetItem(str(row.get("codigo") or 0)))
            self.tabela.setItem(i, 2, QTableWidgetItem(row.get("razao") or ""))
            self.tabela.setItem(i, 3, QTableWidgetItem(row["tipo"]))
            self.tabela.setItem(i, 4, QTableWidgetItem(str(row.get("data_pg") or "")))

    def descarregar_dados(self):
        self._resultados.clear()
