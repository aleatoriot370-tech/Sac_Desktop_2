from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
)

from core.database import buscar_chamado_pf, ultimo_registro_status, buscar_pagamentos_completos
from modules.base_popup_module import BasePopupModule
from ui.visualizador_midias import VisualizadorMidias
from ui.pdf_helper import exportar_pdf


class FichaPessoaFisica(BasePopupModule):
    """Módulo 1.1.2.1 - Ficha Pessoa Física (somente leitura, com histórico completo)."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Ficha Pessoa Física - OS {os_id}")
        self.resize(820, 700)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()
        chamado = buscar_chamado_pf(self.os_id) or {}
        status_novo = self._status("Novo")

        cabecalho = QLabel(
            f"OS {self.os_id}  •  aberto por {status_novo}"
        )
        cabecalho.setObjectName("subtitulo")
        layout.addWidget(cabecalho)

        titulo = QLabel("Ficha - Pessoa Física")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        form = QFormLayout()
        campos_pdf = [
            ("Nome", chamado.get("nome")), ("E-mail", chamado.get("email")),
            ("CPF", chamado.get("cpf")), ("Celular", chamado.get("celular")),
            ("Motivo", chamado.get("motivo")), ("Cidade", chamado.get("cidade")),
            ("Estado", chamado.get("estado")), ("Marca", chamado.get("marca")),
            ("Nome do Produto", chamado.get("nome_produto")),
            ("Lote", chamado.get("lote")), ("Problema", chamado.get("problema")),
            ("Local de compra", chamado.get("local")),
            ("Análise", chamado.get("Analise")),
            ("Resolução e Resposta", chamado.get("Resolucao_Resposta")),
        ]
        for label, valor in campos_pdf:
            campo = QLineEdit(str(valor or ""))
            campo.setReadOnly(True)
            form.addRow(f"{label}:", campo)
        layout.addLayout(form)
        self._campos_pdf = campos_pdf

        rodape_qualidade = QLabel(f"Decisão Qualidade: {self._status('Aprovado - Qualidade') or self._status('Reprovado - Qualidade')}")
        rodape_qualidade.setObjectName("subtitulo")
        layout.addWidget(rodape_qualidade)

        layout.addLayout(VisualizadorMidias(self.os_id))

        layout.addWidget(QLabel("Pagamento:"))
        pagamentos = buscar_pagamentos_completos(self.os_id)
        tabela_pag = QTableWidget(len(pagamentos) or 1, 6)
        tabela_pag.setHorizontalHeaderLabels(
            ["Código Produto", "Valor", "Data Pagamento", "Código Pagamento", "Sistema", "Observação"]
        )
        tabela_pag.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tabela_pag.setEditTriggers(QTableWidget.NoEditTriggers)
        linhas_pdf_pag = []
        for i, p in enumerate(pagamentos):
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
        self._tabela_pdf = (
            ["Código Produto", "Valor", "Data Pagamento", "Código Pagamento", "Sistema", "Observação"],
            linhas_pdf_pag,
        )

        rodape_final = QLabel(f"Finalizado por: {self._status('Finalizado')}")
        rodape_final.setObjectName("subtitulo")
        layout.addWidget(rodape_final)

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
            self, "Ficha - Pessoa Física", self.os_id, self._campos_pdf, tabela=self._tabela_pdf,
        )
