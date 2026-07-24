from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
)

from core.database import (
    buscar_cabecalho_patrimonio, listar_produtos_patrimonio,
    ultimo_registro_status, buscar_pagamentos_completos,
)
from modules.base_popup_module import BasePopupModule
from ui.visualizador_midias import VisualizadorMidias
from ui.pdf_helper import exportar_pdf


class FichaPJPatrimonio(BasePopupModule):
    """Módulo 1.1.2.3 - Ficha PJ Patrimônio (somente leitura, com histórico completo)."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Ficha PJ Patrimônio - OS {os_id}")
        self.resize(900, 700)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()
        cabecalho_dados = buscar_cabecalho_patrimonio(self.os_id)
        produtos = listar_produtos_patrimonio(self.os_id)
        valores = buscar_pagamentos_completos(self.os_id)
        valores_por_produto = {v.get("id_produto"): v.get("valor") for v in valores}

        cabecalho = QLabel(f"OS {self.os_id}  •  aberto por {self._status('Novo')}")
        cabecalho.setObjectName("subtitulo")
        layout.addWidget(cabecalho)

        titulo = QLabel("Ficha - PJ Patrimônio")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        form = QFormLayout()
        campos_pdf = [
            ("Código do Cliente", cabecalho_dados.get("codigo")),
            ("Razão", cabecalho_dados.get("razao")),
            ("Número da OS de Manutenção", cabecalho_dados.get("numero_os_manutencao")),
        ]
        for label, valor in campos_pdf:
            campo = QLineEdit(str(valor or ""))
            campo.setReadOnly(True)
            form.addRow(f"{label}:", campo)
        layout.addLayout(form)

        layout.addWidget(QLabel("Produtos:"))
        tabela_produtos = QTableWidget(len(produtos), 4)
        tabela_produtos.setHorizontalHeaderLabels(["id_Produto", "Descrição", "Quantidade", "Valor"])
        tabela_produtos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tabela_produtos.setEditTriggers(QTableWidget.NoEditTriggers)
        linhas_pdf = []
        for i, produto in enumerate(produtos):
            valor = valores_por_produto.get(produto.get("id_Produto"))
            tabela_produtos.setItem(i, 0, QTableWidgetItem(str(produto.get("id_Produto") or "")))
            tabela_produtos.setItem(i, 1, QTableWidgetItem(produto.get("produto_descricao") or ""))
            tabela_produtos.setItem(i, 2, QTableWidgetItem(str(produto.get("Quantidade") or "")))
            tabela_produtos.setItem(i, 3, QTableWidgetItem(str(valor or "")))
            linhas_pdf.append([
                str(produto.get("id_Produto") or ""), produto.get("produto_descricao") or "",
                str(produto.get("Quantidade") or ""), str(valor or ""),
            ])
        tabela_produtos.setMaximumHeight(120)
        layout.addWidget(tabela_produtos)

        form2 = QFormLayout()
        campo_motivo = QLineEdit(cabecalho_dados.get("motivo") or "")
        campo_motivo.setReadOnly(True)
        form2.addRow("Motivo:", campo_motivo)
        layout.addLayout(form2)

        rodape_patrimonio = QLabel(
            f"Decisão Patrimônio: {self._status('Aprovado - Patrimônio') if self._status('Aprovado - Patrimônio') != '-' else self._status('Reprovado - Patrimônio')}"
        )
        rodape_patrimonio.setObjectName("subtitulo")
        layout.addWidget(rodape_patrimonio)

        form3 = QFormLayout()
        campo_justificativa = QLineEdit(cabecalho_dados.get("justificativa") or "")
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
        for i, p in enumerate(valores):
            tabela_pag.setItem(i, 0, QTableWidgetItem(str(p.get("id_produto") or "")))
            tabela_pag.setItem(i, 1, QTableWidgetItem(str(p.get("valor") or "")))
            tabela_pag.setItem(i, 2, QTableWidgetItem(str(p.get("data_pg") or "")))
            tabela_pag.setItem(i, 3, QTableWidgetItem(p.get("codigo_sistema") or ""))
            tabela_pag.setItem(i, 4, QTableWidgetItem(p.get("sistema") or ""))
            tabela_pag.setItem(i, 5, QTableWidgetItem(p.get("observacao") or ""))
        tabela_pag.setMaximumHeight(100)
        layout.addWidget(tabela_pag)

        rodape_final = QLabel(f"Finalizado por: {self._status('Finalizado')}")
        rodape_final.setObjectName("subtitulo")
        layout.addWidget(rodape_final)

        self._campos_pdf = campos_pdf + [
            ("Motivo", cabecalho_dados.get("motivo")),
            ("Justificativa", cabecalho_dados.get("justificativa")),
        ]
        self._tabela_produto_pdf = (["id_Produto", "Descrição", "Quantidade", "Valor"], linhas_pdf)

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
            self, "Ficha - PJ Patrimônio", self.os_id, self._campos_pdf,
            tabela=self._tabela_produto_pdf,
        )
