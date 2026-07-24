from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox,
    QDateEdit, QPushButton, QMessageBox,
)
from PySide6.QtCore import QDate

from core.database import (
    buscar_cabecalho_patrimonio, listar_valores_os, salvar_pagamento, registrar_status,
)
from modules.base_popup_module import BasePopupModule
from ui.visualizador_midias import VisualizadorMidias
from ui.pdf_helper import exportar_pdf

SISTEMAS = ["EFICAZ", "SENIOR"]


class PagamentoPJPatrimonio(BasePopupModule):
    """Módulo 1.3.2.1.3 - Formulário de Pagamento PJ Patrimônio."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Pagamento PJ Patrimônio - OS {os_id}")
        self.resize(680, 780)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        cabecalho_dados = buscar_cabecalho_patrimonio(self.os_id)
        valores = listar_valores_os(self.os_id)
        valor_total = sum(v.get("Valor") or 0 for v in valores)

        titulo = QLabel("Formulário de Pagamento - PJ Patrimônio")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        form = QFormLayout()
        campos_pdf = [
            ("Código do Cliente", cabecalho_dados.get("codigo")),
            ("Razão", cabecalho_dados.get("razao")),
            ("Número da OS de Manutenção", cabecalho_dados.get("numero_os_manutencao")),
            ("Motivo", cabecalho_dados.get("motivo")),
            ("Justificativa", cabecalho_dados.get("justificativa")),
            ("Valor a pagar", f"{valor_total:.2f}"),
        ]
        for label, valor in campos_pdf:
            campo = QLineEdit(str(valor or ""))
            campo.setReadOnly(True)
            form.addRow(f"{label}:", campo)
        layout.addLayout(form)
        self._campos_pdf = campos_pdf

        layout.addLayout(VisualizadorMidias(self.os_id))

        layout.addWidget(QLabel("Dados do pagamento:"))
        form2 = QFormLayout()
        self.campo_data_pg = QDateEdit(QDate.currentDate())
        self.campo_data_pg.setCalendarPopup(True)
        self.campo_codigo_sistema = QLineEdit()
        self.combo_sistema = QComboBox()
        self.combo_sistema.addItems(SISTEMAS)
        self.campo_observacao = QLineEdit()
        form2.addRow("Data Pagamento*:", self.campo_data_pg)
        form2.addRow("Código gerado p/ pagamento*:", self.campo_codigo_sistema)
        form2.addRow("Sistema*:", self.combo_sistema)
        form2.addRow("Observação:", self.campo_observacao)
        layout.addLayout(form2)

        botoes = QHBoxLayout()
        btn_pdf = QPushButton("Gerar PDF")
        btn_pdf.setObjectName("secondary")
        btn_pdf.clicked.connect(self._gerar_pdf)
        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self._salvar)
        botoes.addWidget(btn_pdf)
        botoes.addWidget(btn_salvar)
        layout.addLayout(botoes)

    def _gerar_pdf(self):
        exportar_pdf(self, "Formulário de Pagamento - PJ Patrimônio", self.os_id, self._campos_pdf)

    def _validar(self) -> str | None:
        if not self.campo_codigo_sistema.text().strip():
            return "Informe o Código gerado para pagamento."
        return None

    def _salvar(self):
        erro = self._validar()
        if erro:
            QMessageBox.warning(self, "Dados incompletos", erro)
            return
        try:
            salvar_pagamento(self.os_id, {
                "data_pg": self.campo_data_pg.date().toString("yyyy-MM-dd"),
                "codigo_sistema": self.campo_codigo_sistema.text().strip(),
                "sistema": self.combo_sistema.currentText(),
                "Observacao": self.campo_observacao.text().strip(),
            })
            registrar_status(self.os_id, "Pagamento Programado", self.usuario_logado["id_user"])
            registrar_status(self.os_id, "Finalizado", self.usuario_logado["id_user"])
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao salvar", f"Não foi possível salvar o pagamento.\n\n{exc}")
            return
        QMessageBox.information(self, "Pagamento registrado", f"OS {self.os_id} finalizada com sucesso.")
        self.accept()
