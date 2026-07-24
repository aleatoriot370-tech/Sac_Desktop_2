from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,
)

from core.database import (
    buscar_chamado_qualidade, buscar_os, atualizar_chamado_qualidade,
    ultimo_registro_status, registrar_status,
)
from modules.base_popup_module import BasePopupModule
from ui.visualizador_midias import VisualizadorMidias
from ui.pdf_helper import exportar_pdf


class InvestigacaoPJ(BasePopupModule):
    """Módulo 1.2.1.2.2 - Investigação Pessoa Jurídica."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Investigação PJ - OS {os_id}")
        self.resize(880, 760)
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

        titulo = QLabel("Investigação - Pessoa Jurídica")
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

        layout.addWidget(QLabel("Produto:"))
        tabela = QTableWidget(1, 5)
        tabela.setHorizontalHeaderLabels(["Descrição", "Marca", "Quantidade", "Validade", "Lote"])
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
        form2 = QFormLayout()
        form2.addRow("Problema:", campo_problema)
        layout.addLayout(form2)

        self._campos_pdf = campos_pdf + [("Problema", chamado.get("Problema"))]
        self._tabela_pdf = (
            ["Descrição", "Marca", "Quantidade", "Validade", "Lote"],
            [[
                chamado.get("produto_descricao") or "", chamado.get("produto_marca") or "",
                str(chamado.get("Quantidade") or ""), str(chamado.get("Validade") or ""),
                chamado.get("Lote") or "",
            ]],
        )

        layout.addLayout(VisualizadorMidias(self.os_id))

        layout.addWidget(QLabel("Análise* (até 300 caracteres):"))
        self.campo_analise = QTextEdit(chamado.get("Analise Qualidade") or "")
        self.campo_analise.setMaximumHeight(70)
        layout.addWidget(self.campo_analise)

        layout.addWidget(QLabel("Resolução e Resposta*:"))
        self.campo_resolucao = QTextEdit(chamado.get("Resolucao_Resposta") or "")
        self.campo_resolucao.setMaximumHeight(70)
        layout.addWidget(self.campo_resolucao)

        botoes = QHBoxLayout()
        btn_pdf = QPushButton("Gerar PDF")
        btn_pdf.setObjectName("secondary")
        btn_pdf.clicked.connect(self._gerar_pdf)
        btn_reprovar = QPushButton("Reprovar")
        btn_reprovar.setObjectName("danger")
        btn_reprovar.clicked.connect(self._reprovar)
        btn_aprovar = QPushButton("Aprovar")
        btn_aprovar.clicked.connect(self._aprovar)
        botoes.addWidget(btn_pdf)
        botoes.addWidget(btn_reprovar)
        botoes.addWidget(btn_aprovar)
        layout.addLayout(botoes)

    @staticmethod
    def _formatar_data(valor):
        return (valor or "-")[:16].replace("T", " ")

    def _gerar_pdf(self):
        exportar_pdf(
            self, "Investigação - Pessoa Jurídica", self.os_id, self._campos_pdf,
            tabela=self._tabela_pdf,
            observacoes=[
                ("Análise", self.campo_analise.toPlainText()),
                ("Resolução e Resposta", self.campo_resolucao.toPlainText()),
            ],
        )

    def _validar_analise(self) -> str | None:
        if not self.campo_analise.toPlainText().strip():
            return "O campo 'Análise' é obrigatório."
        if len(self.campo_analise.toPlainText()) > 300:
            return "Análise deve ter no máximo 300 caracteres."
        if not self.campo_resolucao.toPlainText().strip():
            return "O campo 'Resolução e Resposta' é obrigatório."
        return None

    def _salvar_analise(self):
        atualizar_chamado_qualidade(self.os_id, {
            "Analise Qualidade": self.campo_analise.toPlainText().strip(),
            "Resolucao_Resposta": self.campo_resolucao.toPlainText().strip(),
        })

    def _reprovar(self):
        erro = self._validar_analise()
        if erro:
            QMessageBox.warning(self, "Dados incompletos", erro)
            return
        self._salvar_analise()
        registrar_status(self.os_id, "Reprovado - Qualidade", self.usuario_logado["id_user"])
        QMessageBox.information(self, "Chamado reprovado", f"OS {self.os_id} marcada como Reprovado - Qualidade.")
        self.accept()

    def _aprovar(self):
        erro = self._validar_analise()
        if erro:
            QMessageBox.warning(self, "Dados incompletos", erro)
            return
        self._salvar_analise()
        # Conforme especificação (1.2.1.2.2): PJ aprovado NÃO segue
        # automaticamente para o financeiro — ainda passa por
        # Importação de Valores (módulo 1.3.1) antes.
        registrar_status(self.os_id, "Aprovado - Qualidade", self.usuario_logado["id_user"])
        QMessageBox.information(self, "Chamado aprovado", f"OS {self.os_id} marcada como Aprovado - Qualidade.")
        self.accept()
