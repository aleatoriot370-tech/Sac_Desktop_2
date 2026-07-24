from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
)

from core.database import (
    buscar_chamado_qualidade, buscar_os, ultimo_registro_status, buscar_pagamentos_completos,
)
from modules.base_popup_module import BasePopupModule
from ui.visualizador_midias import VisualizadorMidias
from ui.pdf_helper import exportar_pdf


class FichaPJQualidade(BasePopupModule):
    """Módulo 1.1.2.2 - Ficha PJ Qualidade (somente leitura, com histórico completo)."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Ficha PJ Qualidade - OS {os_id}")
        self.resize(900, 700)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()
        chamado = buscar_chamado_qualidade(self.os_id) or {}
        os_row = buscar_os(self.os_id) or {}

        cabecalho = QLabel(f"OS {self.os_id}  •  aberto por {self._status('Novo')}")
        cabecalho.setObjectName("subtitulo")
        layout.addWidget(cabecalho)

        titulo = QLabel("Ficha - PJ Qualidade")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        form = QFormLayout()
        campos_pdf = [
            ("Nome", chamado.get("Nome")), ("Código do Cliente", os_row.get("Codigo")),
            ("Razão", chamado.get("razao")), ("Motivo", chamado.get("Motivo")),
        ]
        for label, valor in campos_pdf:
            campo = QLineEdit(str(valor or ""))
            campo.setReadOnly(True)
            form.addRow(f"{label}:", campo)
        layout.addLayout(form)

        layout.addWidget(QLabel("Produto:"))
        tabela = QTableWidget(1, 6)
        tabela.setHorizontalHeaderLabels(
            ["Descrição", "Marca", "Quantidade", "Validade", "Lote", "Valor"]
        )
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        valores = buscar_pagamentos_completos(self.os_id)
        valor_produto = valores[0].get("valor") if valores else None
        tabela.setItem(0, 0, QTableWidgetItem(chamado.get("produto_descricao") or ""))
        tabela.setItem(0, 1, QTableWidgetItem(chamado.get("produto_marca") or ""))
        tabela.setItem(0, 2, QTableWidgetItem(str(chamado.get("Quantidade") or "")))
        tabela.setItem(0, 3, QTableWidgetItem(str(chamado.get("Validade") or "")))
        tabela.setItem(0, 4, QTableWidgetItem(chamado.get("Lote") or ""))
        tabela.setItem(0, 5, QTableWidgetItem(str(valor_produto or "")))
        tabela.setMaximumHeight(80)
        layout.addWidget(tabela)

        form2 = QFormLayout()
        campos_pdf2 = [
            ("Problema", chamado.get("Problema")), ("Análise", chamado.get("Analise Qualidade")),
            ("Resolução e Resposta", chamado.get("Resolucao_Resposta")),
        ]
        for label, valor in campos_pdf2:
            campo = QLineEdit(str(valor or ""))
            campo.setReadOnly(True)
            form2.addRow(f"{label}:", campo)
        layout.addLayout(form2)

        rodape_qualidade = QLabel(
            f"Decisão Qualidade: {self._status('Aprovado - Qualidade') if self._status('Aprovado - Qualidade') != '-' else self._status('Reprovado - Qualidade')}"
        )
        rodape_qualidade.setObjectName("subtitulo")
        layout.addWidget(rodape_qualidade)

        form3 = QFormLayout()
        campo_justificativa = QLineEdit(chamado.get("Justificativa") or "")
        campo_justificativa.setReadOnly(True)
        form3.addRow("Justificativa:", campo_justificativa)
        layout.addLayout(form3)

        rodape_comercial = QLabel(
            f"Decisão Comercial: {self._status('Aprovado - Comercial') if self._status('Aprovado - Comercial') != '-' else self._status('Reprovado - Comercial')}"
        )
        rodape_comercial.setObjectName("subtitulo")
        layout.addWidget(rodape_comercial)

        layout.addLayout(VisualizadorMidias(self.os_id))

        layout.addWidget(QLabel("Pagamento:"))
        tabela_pag = QTableWidget(len(valores) or 1, 6)
        tabela_pag.setHorizontalHeaderLabels(
            ["Código Produto", "Valor", "Data Pagamento", "Código Pagamento", "Sistema", "Observação"]
        )
        tabela_pag.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tabela_pag.setEditTriggers(QTableWidget.NoEditTriggers)
        linhas_pdf_pag = []
        for i, p in enumerate(valores):
            tabela_pag.setItem(i, 0, QTableWidgetItem(str(p.get("id_produto") or "")))
            tabela_pag.setItem(i, 1, QTableWidgetItem(str(p.get("valor") or "")))
            tabela_pag.setItem(i, 2, QTableWidgetItem(str(p.get("data_pg") or "")))
            tabela_pag.setItem(i, 3, QTableWidgetItem(p.get("codigo_sistema") or ""))
            tabela_pag.setItem(i, 4, QTableWidgetItem(p.get("sistema") or ""))
            tabela_pag.setItem(i, 5, QTableWidgetItem(p.get("observacao") or ""))
            linhas_pdf_pag.append([
                str(p.get("id_produto") or ""), str(p.get("valor") or ""), str(p.get("data_pg") or ""),
                p.get("codigo_sistema") or "", p.get("sistema") or "", p.get("observacao") or "",
            ])
        tabela_pag.setMaximumHeight(100)
        layout.addWidget(tabela_pag)

        rodape_final = QLabel(f"Finalizado por: {self._status('Finalizado')}")
        rodape_final.setObjectName("subtitulo")
        layout.addWidget(rodape_final)

        self._campos_pdf = campos_pdf + campos_pdf2 + [("Justificativa", chamado.get("Justificativa"))]
        self._tabela_produto_pdf = (
            ["Descrição", "Marca", "Quantidade", "Validade", "Lote", "Valor"],
            [[
                chamado.get("produto_descricao") or "", chamado.get("produto_marca") or "",
                str(chamado.get("Quantidade") or ""), str(chamado.get("Validade") or ""),
                chamado.get("Lote") or "", str(valor_produto or ""),
            ]],
        )

        btn_pdf = QPushButton("Exportar PDF")
        btn_pdf.clicked.connect(self._gerar_pdf)
        layout.addWidget(btn_pdf)

    def _status(self, nome_status: str) -> str:
        registro = ultimo_registro_status(self.os_id, nome_status)
        if not registro:
            return "-"
        data = (registro.get("created_at") or "-")[:16].replace("T", " ")
        return f"{registro.get('nome_usuario') or '-'} em {data}"

    def _gerar_pdf(self):
        exportar_pdf(
            self, "Ficha - PJ Qualidade", self.os_id, self._campos_pdf,
            tabela=self._tabela_produto_pdf,
        )
