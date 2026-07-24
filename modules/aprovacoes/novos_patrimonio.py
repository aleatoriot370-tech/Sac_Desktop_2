from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)

from core.database import listar_novos_patrimonio
from modules.base_popup_module import BasePopupModule
from modules.aprovacoes.formulario_patrimonio import FormularioPatrimonio


class NovosPatrimonio(BasePopupModule):
    """Módulo 1.2.2.1 - Novos Patrimônio: OS com Tipo P e Status 'Novo'."""

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(usuario_logado, parent)
        self.setWindowTitle("Aprovações - Novos Patrimônio")
        self.resize(760, 520)
        self._resultados: list[dict] = []
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        titulo = QLabel("Novos Patrimônio")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        dica = QLabel("Dê duplo clique em uma linha para abrir o formulário do chamado.")
        dica.setObjectName("subtitulo")
        layout.addWidget(dica)

        self.tabela = QTableWidget(0, 4)
        self.tabela.setHorizontalHeaderLabels(["OS", "Código", "Razão", "OS Manutenção"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.cellDoubleClicked.connect(self._abrir_formulario)
        layout.addWidget(self.tabela)

        self._carregar()

    def _carregar(self):
        try:
            self._resultados = listar_novos_patrimonio()
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
            self.tabela.setItem(i, 3, QTableWidgetItem(row.get("numero_os_manutencao") or ""))

    def _abrir_formulario(self, linha: int, _coluna: int):
        os_id = self._resultados[linha]["os_id"]
        dialogo = FormularioPatrimonio(self.usuario_logado, os_id, parent=self)
        dialogo.exec()
        self._carregar()

    def descarregar_dados(self):
        self._resultados.clear()
