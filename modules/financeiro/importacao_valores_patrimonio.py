from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,
)

from core.database import (
    buscar_cabecalho_patrimonio, listar_produtos_patrimonio,
    salvar_valor_produto, registrar_status,
)
from core.external_db import buscar_valor_unitario
from modules.base_popup_module import BasePopupModule

COL_VALOR_UNIT = 3
COL_VALOR_TOTAL = 4


class ImportacaoValoresPatrimonio(BasePopupModule):
    """Módulo 1.3.1.2 - Importação de Valores Patrimônio (um ou mais produtos por OS)."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Importação de Valores - Patrimônio - OS {os_id}")
        self.resize(900, 560)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        self.cabecalho_dados = buscar_cabecalho_patrimonio(self.os_id)
        self.produtos = listar_produtos_patrimonio(self.os_id)

        titulo = QLabel("Importação de Valores - Patrimônio")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        form = QFormLayout()
        for label, valor in [
            ("Código do Cliente", self.cabecalho_dados.get("codigo")),
            ("Razão", self.cabecalho_dados.get("razao")),
        ]:
            campo = QLineEdit(str(valor or ""))
            campo.setReadOnly(True)
            form.addRow(f"{label}:", campo)
        layout.addLayout(form)

        layout.addWidget(QLabel("Produtos:"))
        self.tabela = QTableWidget(len(self.produtos), 5)
        self.tabela.setHorizontalHeaderLabels(
            ["Descrição", "Marca", "Quantidade", "Valor Unit.", "Valor Total"]
        )
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        for i, produto in enumerate(self.produtos):
            self.tabela.setItem(i, 0, QTableWidgetItem(produto.get("produto_descricao") or ""))
            self.tabela.setItem(i, 1, QTableWidgetItem(produto.get("produto_marca") or ""))
            self.tabela.setItem(i, 2, QTableWidgetItem(str(produto.get("Quantidade") or "")))
            self.tabela.setItem(i, COL_VALOR_UNIT, QTableWidgetItem(""))
            self.tabela.setItem(i, COL_VALOR_TOTAL, QTableWidgetItem(""))
        self.tabela.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tabela)

        btn_integrar = QPushButton("Buscar valores no sistema externo")
        btn_integrar.setObjectName("secondary")
        btn_integrar.clicked.connect(self._buscar_valores_externo)
        layout.addWidget(btn_integrar)

        layout.addStretch()
        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self._salvar)
        layout.addWidget(btn_salvar)

    def _on_item_changed(self, item):
        if item.column() != COL_VALOR_UNIT:
            return
        linha = item.row()
        try:
            unit = float(item.text().replace(",", "."))
            qtd = float(self.produtos[linha].get("Quantidade") or 0)
        except ValueError:
            return
        self.tabela.blockSignals(True)
        self.tabela.setItem(linha, COL_VALOR_TOTAL, QTableWidgetItem(f"{unit * qtd:.2f}"))
        self.tabela.blockSignals(False)

    def _buscar_valores_externo(self):
        codigo_cliente = self.cabecalho_dados.get("codigo")
        algum_erro = False
        detalhe_erro = ""
        for i, produto in enumerate(self.produtos):
            try:
                valor = buscar_valor_unitario(codigo_cliente, produto.get("id_Produto"))
            except Exception as exc:
                algum_erro = True
                detalhe_erro = str(exc)
                continue
            if valor is not None:
                self.tabela.setItem(i, COL_VALOR_UNIT, QTableWidgetItem(f"{valor:.2f}"))
        if algum_erro:
            QMessageBox.warning(
                self, "Falha na integração",
                f"Não foi possível consultar o banco externo. Você pode digitar "
                f"os valores manualmente.\n\nDetalhes: {detalhe_erro}",
            )

    def _salvar(self):
        valores_validos = []
        for i, produto in enumerate(self.produtos):
            item_total = self.tabela.item(i, COL_VALOR_TOTAL)
            if not item_total or not item_total.text():
                QMessageBox.warning(
                    self, "Dados incompletos",
                    f"Informe o Valor Unitário do produto '{produto.get('produto_descricao')}'.",
                )
                return
            valores_validos.append((produto.get("id_Produto"), float(item_total.text())))

        try:
            for id_produto, valor_total in valores_validos:
                salvar_valor_produto(self.os_id, id_produto, valor_total)
            registrar_status(self.os_id, "Aguardando Financeiro", self.usuario_logado["id_user"])
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao salvar", f"Não foi possível salvar.\n\n{exc}")
            return

        QMessageBox.information(self, "Valores salvos", f"OS {self.os_id} encaminhada para pagamento.")
        self.accept()
