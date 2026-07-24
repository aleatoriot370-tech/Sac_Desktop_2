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


class AnaliseComercialPJ(BasePopupModule):
    """Módulo 1.2.3.1.1 - Análise Comercial PJ (decisão final sobre um chamado reprovado na Qualidade)."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Análise Comercial PJ - OS {os_id}")
        self.resize(880, 800)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        chamado = buscar_chamado_qualidade(self.os_id) or {}
        os_row = buscar_os(self.os_id) or {}
        status_novo = ultimo_registro_status(self.os_id, "Novo")
        status_reprovado = ultimo_registro_status(self.os_id, "Reprovado - Qualidade")

        cabecalho = QLabel(
            f"OS {self.os_id}  •  aberto por "
            f"{(status_novo or {}).get('nome_usuario') or '-'} em "
            f"{self._formatar_data((status_novo or {}).get('created_at'))}"
        )
        cabecalho.setObjectName("subtitulo")
        layout.addWidget(cabecalho)

        titulo = QLabel("Análise Comercial - Pessoa Jurídica")
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

        for label, valor in [("Problema", chamado.get("Problema"))]:
            campo = QLineEdit(str(valor or ""))
            campo.setReadOnly(True)
            f = QFormLayout()
            f.addRow(f"{label}:", campo)
            layout.addLayout(f)

        campo_analise = QLineEdit(chamado.get("Analise Qualidade") or "")
        campo_analise.setReadOnly(True)
        campo_resolucao = QLineEdit(chamado.get("Resolucao_Resposta") or "")
        campo_resolucao.setReadOnly(True)
        form_qualidade = QFormLayout()
        form_qualidade.addRow("Análise (Qualidade):", campo_analise)
        form_qualidade.addRow("Resolução e Resposta:", campo_resolucao)
        layout.addLayout(form_qualidade)

        rodape_reprovacao = QLabel(
            f"Reprovado - Qualidade por {(status_reprovado or {}).get('nome_usuario') or '-'} em "
            f"{self._formatar_data((status_reprovado or {}).get('created_at'))}"
        )
        rodape_reprovacao.setObjectName("subtitulo")
        layout.addWidget(rodape_reprovacao)

        layout.addLayout(VisualizadorMidias(self.os_id))

        layout.addWidget(QLabel("Justificativa*:"))
        self.campo_justificativa = QTextEdit(chamado.get("Justificativa") or "")
        self.campo_justificativa.setMaximumHeight(70)
        layout.addWidget(self.campo_justificativa)

        self._campos_pdf = campos_pdf + [
            ("Problema", chamado.get("Problema")),
            ("Análise (Qualidade)", chamado.get("Analise Qualidade")),
            ("Resolução e Resposta", chamado.get("Resolucao_Resposta")),
        ]
        self._tabela_pdf = (
            ["Descrição", "Marca", "Quantidade", "Validade", "Lote"],
            [[
                chamado.get("produto_descricao") or "", chamado.get("produto_marca") or "",
                str(chamado.get("Quantidade") or ""), str(chamado.get("Validade") or ""),
                chamado.get("Lote") or "",
            ]],
        )

        botoes = QHBoxLayout()
        btn_pdf = QPushButton("Gerar PDF")
        btn_pdf.setObjectName("secondary")
        btn_pdf.clicked.connect(self._gerar_pdf)
        btn_reprovar = QPushButton("Reprovar (Finalizar)")
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
            self, "Análise Comercial - Pessoa Jurídica", self.os_id, self._campos_pdf,
            tabela=self._tabela_pdf,
            observacoes=[("Justificativa", self.campo_justificativa.toPlainText())],
        )

    def _validar_justificativa(self) -> str | None:
        if not self.campo_justificativa.toPlainText().strip():
            return "O campo 'Justificativa' é obrigatório."
        return None

    def _salvar_justificativa(self):
        atualizar_chamado_qualidade(self.os_id, {
            "Justificativa": self.campo_justificativa.toPlainText().strip(),
        })

    def _reprovar(self):
        erro = self._validar_justificativa()
        if erro:
            QMessageBox.warning(self, "Dados incompletos", erro)
            return
        self._salvar_justificativa()
        # Conforme especificação: Reprovado - Comercial encadeia
        # imediatamente para Finalizado (decisão final, sem mais etapas).
        registrar_status(self.os_id, "Reprovado - Comercial", self.usuario_logado["id_user"])
        registrar_status(self.os_id, "Finalizado", self.usuario_logado["id_user"])
        QMessageBox.information(self, "Chamado finalizado", f"OS {self.os_id} reprovada e finalizada.")
        self.accept()

    def _aprovar(self):
        erro = self._validar_justificativa()
        if erro:
            QMessageBox.warning(self, "Dados incompletos", erro)
            return
        self._salvar_justificativa()
        registrar_status(self.os_id, "Aprovado - Comercial", self.usuario_logado["id_user"])
        QMessageBox.information(self, "Chamado aprovado", f"OS {self.os_id} marcada como Aprovado - Comercial.")
        self.accept()
