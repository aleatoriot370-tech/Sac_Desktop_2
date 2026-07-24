from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,
)

from core.database import (
    buscar_chamado_qualidade, buscar_os, ultimo_registro_status,
    salvar_valor_produto, registrar_status,
)
from core.external_db import buscar_valor_unitario
from modules.base_popup_module import BasePopupModule


class ImportacaoValoresQualidade(BasePopupModule):
    """Módulo 1.3.1.1 - Importação de Valores Qualidade."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Importação de Valores - Qualidade - OS {os_id}")
        self.resize(820, 560)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        self.chamado = buscar_chamado_qualidade(self.os_id) or {}
        self.os_row = buscar_os(self.os_id) or {}
        status_novo = ultimo_registro_status(self.os_id, "Novo")

        cabecalho = QLabel(
            f"OS {self.os_id}  •  aberto por "
            f"{(status_novo or {}).get('nome_usuario') or '-'} em "
            f"{self._formatar_data((status_novo or {}).get('created_at'))}"
        )
        cabecalho.setObjectName("subtitulo")
        layout.addWidget(cabecalho)

        titulo = QLabel("Importação de Valores - Qualidade")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        form = QFormLayout()
        for label, valor in [
            ("Nome", self.chamado.get("Nome")),
            ("Código do Cliente", self.os_row.get("Codigo")),
            ("Razão", self.chamado.get("razao")),
        ]:
            campo = QLineEdit(str(valor or ""))
            campo.setReadOnly(True)
            form.addRow(f"{label}:", campo)
        layout.addLayout(form)

        layout.addWidget(QLabel("Produto:"))
        self.tabela = QTableWidget(1, 5)
        self.tabela.setHorizontalHeaderLabels(["Descrição", "Marca", "Quantidade", "Validade", "Lote"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setItem(0, 0, QTableWidgetItem(self.chamado.get("produto_descricao") or ""))
        self.tabela.setItem(0, 1, QTableWidgetItem(self.chamado.get("produto_marca") or ""))
        self.tabela.setItem(0, 2, QTableWidgetItem(str(self.chamado.get("Quantidade") or "")))
        self.tabela.setItem(0, 3, QTableWidgetItem(str(self.chamado.get("Validade") or "")))
        self.tabela.setItem(0, 4, QTableWidgetItem(self.chamado.get("Lote") or ""))
        self.tabela.setMaximumHeight(80)
        layout.addWidget(self.tabela)

        form_valor = QFormLayout()
        self.campo_valor_unit = QLineEdit()
        self.campo_valor_unit.setPlaceholderText("0.00")
        self.campo_valor_unit.textChanged.connect(self._recalcular_total)
        self.campo_valor_total = QLineEdit()
        self.campo_valor_total.setReadOnly(True)
        form_valor.addRow("Valor Unit.:", self.campo_valor_unit)
        form_valor.addRow("Valor Total:", self.campo_valor_total)
        layout.addLayout(form_valor)

        btn_integrar = QPushButton("Buscar valor no sistema externo")
        btn_integrar.setObjectName("secondary")
        btn_integrar.clicked.connect(self._buscar_valor_externo)
        layout.addWidget(btn_integrar)

        layout.addStretch()
        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self._salvar)
        layout.addWidget(btn_salvar)

    @staticmethod
    def _formatar_data(valor):
        return (valor or "-")[:16].replace("T", " ")

    def _quantidade(self) -> float:
        try:
            return float(self.chamado.get("Quantidade") or 0)
        except (TypeError, ValueError):
            return 0

    def _recalcular_total(self):
        try:
            unit = float(self.campo_valor_unit.text().replace(",", "."))
        except ValueError:
            self.campo_valor_total.setText("")
            return
        self.campo_valor_total.setText(f"{unit * self._quantidade():.2f}")

    def _buscar_valor_externo(self):
        codigo_cliente = self.os_row.get("Codigo")
        produto_codigo = self.chamado.get("id_produto")
        try:
            valor = buscar_valor_unitario(codigo_cliente, produto_codigo)
        except Exception as exc:
            QMessageBox.warning(
                self, "Falha na integração",
                f"Não foi possível consultar o banco externo. Você pode digitar "
                f"o valor manualmente.\n\nDetalhes: {exc}",
            )
            return
        if valor is None:
            QMessageBox.information(self, "Não encontrado", "Nenhum valor encontrado para este produto/cliente.")
            return
        self.campo_valor_unit.setText(f"{valor:.2f}")

    def _salvar(self):
        if not self.campo_valor_total.text():
            QMessageBox.warning(self, "Dados incompletos", "Informe o Valor Unitário.")
            return
        try:
            valor_total = float(self.campo_valor_total.text())
            salvar_valor_produto(self.os_id, self.chamado.get("id_produto"), valor_total)
            registrar_status(self.os_id, "Aguardando Financeiro", self.usuario_logado["id_user"])
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao salvar", f"Não foi possível salvar.\n\n{exc}")
            return
        QMessageBox.information(self, "Valor salvo", f"OS {self.os_id} encaminhada para pagamento.")
        self.accept()
