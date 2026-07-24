from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QMessageBox,
)

from core.database import buscar_chamado_pf, ultimo_registro_status, registrar_status
from modules.base_popup_module import BasePopupModule
from ui.visualizador_midias import VisualizadorMidias
from ui.pdf_helper import exportar_pdf


class FormularioQualidadePF(BasePopupModule):
    """
    Módulo 1.2.1.1.1 - Formulário Qualidade Pessoa Física.
    Somente leitura (dados vieram da abertura do chamado). Ação principal:
    abrir investigação, que muda o status e opcionalmente navega para a
    tela de investigação.
    """

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Formulário Qualidade PF - OS {os_id}")
        self.resize(640, 700)
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

        titulo = QLabel("Formulário Qualidade - Pessoa Física")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        form = QFormLayout()
        campos = [
            ("Nome", chamado.get("nome")), ("E-mail", chamado.get("email")),
            ("CPF", chamado.get("cpf")), ("Celular", chamado.get("celular")),
            ("Motivo", chamado.get("motivo")), ("Cidade", chamado.get("cidade")),
            ("Estado", chamado.get("estado")), ("Marca", chamado.get("marca")),
            ("Nome do Produto", chamado.get("nome_produto")),
            ("Lote", chamado.get("lote")), ("Problema", chamado.get("problema")),
            ("Local de compra", chamado.get("local")),
        ]
        for label, valor in campos:
            campo = QLineEdit(str(valor or ""))
            campo.setReadOnly(True)
            form.addRow(f"{label}:", campo)
        layout.addLayout(form)
        self._campos_pdf = campos

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
            self, "Formulário Qualidade - Pessoa Física", self.os_id, self._campos_pdf,
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
            # Import local para evitar import circular entre os dois formulários.
            from modules.aprovacoes.investigacao_pf import InvestigacaoPF
            dialogo = InvestigacaoPF(self.usuario_logado, self.os_id, parent=self.parent())
            dialogo.exec()
