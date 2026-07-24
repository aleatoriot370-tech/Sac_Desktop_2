from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)

from core.database import listar_reprovados_qualidade
from modules.base_popup_module import BasePopupModule
from modules.aprovacoes.analise_comercial_pj import AnaliseComercialPJ


class ReprovadosQualidade(BasePopupModule):
    """Módulo 1.2.3.1 - Reprovados Qualidade: OS Tipo Q, Status 'Reprovado - Qualidade'."""

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(usuario_logado, parent)
        self.setWindowTitle("Comercial - Reprovados Qualidade")
        self.resize(700, 500)
        self._resultados: list[dict] = []
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        titulo = QLabel("Reprovados Qualidade")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        dica = QLabel("Dê duplo clique em uma linha para abrir a análise comercial.")
        dica.setObjectName("subtitulo")
        layout.addWidget(dica)

        self.tabela = QTableWidget(0, 3)
        self.tabela.setHorizontalHeaderLabels(["OS", "Código", "Razão"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.cellDoubleClicked.connect(self._abrir_analise)
        layout.addWidget(self.tabela)

        self._carregar()

    def _carregar(self):
        try:
            self._resultados = listar_reprovados_qualidade()
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

    def _abrir_analise(self, linha: int, _coluna: int):
        os_id = self._resultados[linha]["os_id"]
        dialogo = AnaliseComercialPJ(self.usuario_logado, os_id, parent=self)
        dialogo.exec()
        self._carregar()

    def descarregar_dados(self):
        self._resultados.clear()
