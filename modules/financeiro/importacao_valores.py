from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)

from core.database import listar_aguardando_importacao
from modules.base_popup_module import BasePopupModule
from modules.financeiro.importacao_valores_qualidade import ImportacaoValoresQualidade
from modules.financeiro.importacao_valores_patrimonio import ImportacaoValoresPatrimonio


class ImportacaoValores(BasePopupModule):
    """Módulo 1.3.1 - Importação de Valores."""

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(usuario_logado, parent)
        self.setWindowTitle("Financeiro - Importação de Valores")
        self.resize(760, 520)
        self._resultados: list[dict] = []
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        titulo = QLabel("Importação de Valores")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        dica = QLabel("Dê duplo clique em uma linha para importar os valores do chamado.")
        dica.setObjectName("subtitulo")
        layout.addWidget(dica)

        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(["OS", "Código", "Razão", "Status", "Tipo"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.cellDoubleClicked.connect(self._abrir_importacao)
        layout.addWidget(self.tabela)

        self._carregar()

    def _carregar(self):
        try:
            self._resultados = listar_aguardando_importacao()
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
            self.tabela.setItem(i, 3, QTableWidgetItem(row.get("status") or ""))
            self.tabela.setItem(i, 4, QTableWidgetItem(row["tipo"]))

    def _abrir_importacao(self, linha: int, _coluna: int):
        registro = self._resultados[linha]
        os_id = registro["os_id"]

        if registro["tipo"] == "Q":
            dialogo = ImportacaoValoresQualidade(self.usuario_logado, os_id, parent=self)
        else:
            dialogo = ImportacaoValoresPatrimonio(self.usuario_logado, os_id, parent=self)

        dialogo.exec()
        self._carregar()

    def descarregar_dados(self):
        self._resultados.clear()
