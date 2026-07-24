from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,
)

from core.database import (
    buscar_chamado_qualidade, buscar_os, ultimo_registro_status, registrar_status,
)
from modules.base_popup_module import BasePopupModule
from ui.visualizador_midias import VisualizadorMidias
from ui.pdf_helper import exportar_pdf


class FormularioQualidadePJ(BasePopupModule):
    """Módulo 1.2.1.1.2 - Formulário Qualidade Pessoa Jurídica."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Formulário Qualidade PJ - OS {os_id}")
        self.resize(880, 700)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        chamado = buscar_chamado_qualidade(self.os_id) or {}
        os_row = buscar_os(self.os_id) or {}
        status_novo = ultimo_registro_status(self.os_id, "Novo")

        cabecalho = QLabel(
            f"OS {self.os_id}  •  aberto por "
            f"{(status_novo or {}).get('nome_usuario') or '-'} em "
            f"{self._formatar_data((status_novo or {}).get('created_at'))}"
        )
        cabecalho.setObjectName("subtitulo")
        layout.addWidget(cabecalho)

        titulo = QLabel("Formulário Qualidade - Pessoa Jurídica")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        form = QFormLayout()
        campos_pdf = [
            ("Nome", chamado.get("Nome")), ("Celular", chamado.get("Celular")),
            ("Código do Cliente", os_row.get("Codigo")), ("Razão", chamado.get("razao")),
            ("CPF/CNPJ", chamado.get("cnpj_cpf")), ("Motivo", chamado.get("Motivo")),
        ]
        for label, valor in campos_pdf:
            campo = QLineEdit(str(valor or ""))
            campo.setReadOnly(True)
            form.addRow(f"{label}:", campo)
        layout.addLayout(form)
        self._campos_pdf = campos_pdf

        layout.addWidget(QLabel("Produto:"))
        tabela = QTableWidget(1, 5)
        tabela.setHorizontalHeaderLabels(
            ["Descrição", "Marca", "Quantidade", "Validade", "Lote"]
        )
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        tabela.setItem(0, 0, QTableWidgetItem(chamado.get("produto_descricao") or ""))
        tabela.setItem(0, 1, QTableWidgetItem(chamado.get("produto_marca") or ""))
        tabela.setItem(0, 2, QTableWidgetItem(str(chamado.get("Quantidade") or "")))
        tabela.setItem(0, 3, QTableWidgetItem(str(chamado.get("Validade") or "")))
        tabela.setItem(0, 4, QTableWidgetItem(chamado.get("Lote") or ""))
        tabela.setMaximumHeight(80)
        layout.addWidget(tabela)

        campo_problema = QLineEdit(chamado.get("Problema") or "")
        campo_problema.setReadOnly(True)
        form_problema = QFormLayout()
        form_problema.addRow("Problema:", campo_problema)
        layout.addLayout(form_problema)
        self._campos_pdf.append(("Problema", chamado.get("Problema")))
        self._tabela_pdf = (
            ["Descrição", "Marca", "Quantidade", "Validade", "Lote"],
            [[
                chamado.get("produto_descricao") or "", chamado.get("produto_marca") or "",
                str(chamado.get("Quantidade") or ""), str(chamado.get("Validade") or ""),
                chamado.get("Lote") or "",
            ]],
        )

        layout.addLayout(VisualizadorMidias(self.os_id))

        botoes = QHBoxLayout()
        btn_pdf = QPushButton("Gerar PDF")
        btn_pdf.setObjectName("secondary")
        btn_pdf.clicked.connect(self._gerar_pdf)
        btn_investigar = QPushButton("Abrir Investigação")
        btn_investigar.clicked.connect(self._abrir_investigacao)
        botoes.addWidget(btn_pdf)
        botoes.addWidget(btn_investigar)
        layout.addLayout(botoes)

    @staticmethod
    def _formatar_data(valor):
        return (valor or "-")[:16].replace("T", " ")

    def _gerar_pdf(self):
        exportar_pdf(
            self, "Formulário Qualidade - Pessoa Jurídica", self.os_id,
            self._campos_pdf, tabela=self._tabela_pdf,
        )

    def _abrir_investigacao(self):
        registrar_status(self.os_id, "Em Investigação", self.usuario_logado["id_user"])
        resposta = QMessageBox.question(
            self, "Investigação aberta",
            f"OS {self.os_id} agora está 'Em Investigação'.\n\n"
            "Deseja abrir a tela de investigação agora?",
        )
        self.accept()
        if resposta == QMessageBox.Yes:
            from modules.aprovacoes.investigacao_pj import InvestigacaoPJ
            dialogo = InvestigacaoPJ(self.usuario_logado, self.os_id, parent=self.parent())
            dialogo.exec()
