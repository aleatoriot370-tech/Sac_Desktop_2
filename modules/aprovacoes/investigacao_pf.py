from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QMessageBox,
)

from core.database import (
    buscar_chamado_pf, atualizar_chamado_pf, ultimo_registro_status, registrar_status,
)
from modules.base_popup_module import BasePopupModule
from ui.visualizador_midias import VisualizadorMidias
from ui.pdf_helper import exportar_pdf


class InvestigacaoPF(BasePopupModule):
    """Módulo 1.2.1.2.1 - Investigação Pessoa Física."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Investigação PF - OS {os_id}")
        self.resize(640, 760)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        chamado = buscar_chamado_pf(self.os_id) or {}
        status_novo = ultimo_registro_status(self.os_id, "Novo")

        cabecalho = QLabel(
            f"OS {self.os_id}  •  aberto por "
            f"{(status_novo or {}).get('nome_usuario') or '-'} em "
            f"{self._formatar_data((status_novo or {}).get('created_at'))}"
        )
        cabecalho.setObjectName("subtitulo")
        layout.addWidget(cabecalho)

        titulo = QLabel("Investigação - Pessoa Física")
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
        ]
        for label, valor in campos_pdf:
            campo = QLineEdit(str(valor or ""))
            campo.setReadOnly(True)
            form.addRow(f"{label}:", campo)
        layout.addLayout(form)
        self._campos_pdf = campos_pdf

        layout.addLayout(VisualizadorMidias(self.os_id))

        layout.addWidget(QLabel("Análise* (até 300 caracteres):"))
        self.campo_analise = QTextEdit(chamado.get("Analise") or "")
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
            self, "Investigação - Pessoa Física", self.os_id, self._campos_pdf,
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
        atualizar_chamado_pf(self.os_id, {
            "Analise": self.campo_analise.toPlainText().strip(),
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
        # Conforme especificação (1.2.1.2.1): aprovar já encaminha para
        # "Aguardando Financeiro" automaticamente (só para o fluxo PF).
        registrar_status(self.os_id, "Aprovado - Qualidade", self.usuario_logado["id_user"])
        registrar_status(self.os_id, "Aguardando Financeiro", self.usuario_logado["id_user"])
        QMessageBox.information(
            self, "Chamado aprovado",
            f"OS {self.os_id} aprovada e encaminhada para o Financeiro.",
        )
        self.accept()
