from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox,
    QDateEdit, QPushButton, QMessageBox,
)
from PySide6.QtCore import QDate

from core.database import (
    buscar_chamado_qualidade, buscar_os, listar_valores_os, salvar_pagamento, registrar_status,
)
from modules.base_popup_module import BasePopupModule
from ui.visualizador_midias import VisualizadorMidias
from ui.pdf_helper import exportar_pdf

SISTEMAS = ["EFICAZ", "SENIOR"]


class PagamentoPJQualidade(BasePopupModule):
    """Módulo 1.3.2.1.2 - Formulário de Pagamento PJ Qualidade."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Pagamento PJ Qualidade - OS {os_id}")
        self.resize(680, 780)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        chamado = buscar_chamado_qualidade(self.os_id) or {}
        os_row = buscar_os(self.os_id) or {}
        valores = listar_valores_os(self.os_id)
        valor_total = sum(v.get("Valor") or 0 for v in valores)

        titulo = QLabel("Formulário de Pagamento - PJ Qualidade")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        form = QFormLayout()
        campos_pdf = [
            ("Nome", chamado.get("Nome")), ("Código do Cliente", os_row.get("Codigo")),
            ("Razão", chamado.get("razao")), ("Motivo", chamado.get("Motivo")),
            ("Problema", chamado.get("Problema")), ("Análise", chamado.get("Analise Qualidade")),
            ("Resolução e Resposta", chamado.get("Resolucao_Resposta")),
            ("Justificativa", chamado.get("Justificativa")),
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
        exportar_pdf(self, "Formulário de Pagamento - PJ Qualidade", self.os_id, self._campos_pdf)

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
