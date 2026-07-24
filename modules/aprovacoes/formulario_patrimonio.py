from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,
)

from core.database import (
    buscar_cabecalho_patrimonio, listar_produtos_patrimonio,
    atualizar_motivo_patrimonio, ultimo_registro_status, registrar_status,
)
from modules.base_popup_module import BasePopupModule
from ui.visualizador_midias import VisualizadorMidias
from ui.pdf_helper import exportar_pdf


class FormularioPatrimonio(BasePopupModule):
    """Módulo 1.2.2.1.1 - Formulário Patrimônio."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Formulário Patrimônio - OS {os_id}")
        self.resize(880, 700)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        cabecalho_dados = buscar_cabecalho_patrimonio(self.os_id)
        produtos = listar_produtos_patrimonio(self.os_id)
        status_novo = ultimo_registro_status(self.os_id, "Novo")

        cabecalho = QLabel(
            f"OS {self.os_id}  •  aberto por "
            f"{(status_novo or {}).get('nome_usuario') or '-'} em "
            f"{self._formatar_data((status_novo or {}).get('created_at'))}"
        )
        cabecalho.setObjectName("subtitulo")
        layout.addWidget(cabecalho)

        titulo = QLabel("Formulário Patrimônio")
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
        tabela_produtos = QTableWidget(len(produtos), 3)
        tabela_produtos.setHorizontalHeaderLabels(["id_Produto", "Descrição", "Quantidade"])
        tabela_produtos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tabela_produtos.setEditTriggers(QTableWidget.NoEditTriggers)
        linhas_pdf = []
        for i, produto in enumerate(produtos):
            tabela_produtos.setItem(i, 0, QTableWidgetItem(str(produto.get("id_Produto") or "")))
            tabela_produtos.setItem(i, 1, QTableWidgetItem(produto.get("produto_descricao") or ""))
            tabela_produtos.setItem(i, 2, QTableWidgetItem(str(produto.get("Quantidade") or "")))
            linhas_pdf.append([
                str(produto.get("id_Produto") or ""), produto.get("produto_descricao") or "",
                str(produto.get("Quantidade") or ""),
            ])
        tabela_produtos.setMaximumHeight(120)
        layout.addWidget(tabela_produtos)

        layout.addLayout(VisualizadorMidias(self.os_id))

        layout.addWidget(QLabel("Motivo* (até 300 caracteres):"))
        self.campo_motivo = QTextEdit(cabecalho_dados.get("motivo") or "")
        self.campo_motivo.setMaximumHeight(70)
        layout.addWidget(self.campo_motivo)

        self._campos_pdf = campos_pdf
        self._tabela_pdf = (["id_Produto", "Descrição", "Quantidade"], linhas_pdf)

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
            self, "Formulário Patrimônio", self.os_id, self._campos_pdf,
            tabela=self._tabela_pdf,
            observacoes=[("Motivo", self.campo_motivo.toPlainText())],
        )

    def _validar_motivo(self) -> str | None:
        texto = self.campo_motivo.toPlainText().strip()
        if not texto:
            return "O campo 'Motivo' é obrigatório."
        if len(texto) > 300:
            return "Motivo deve ter no máximo 300 caracteres."
        return None

    def _salvar_motivo(self):
        atualizar_motivo_patrimonio(self.os_id, self.campo_motivo.toPlainText().strip())

    def _reprovar(self):
        erro = self._validar_motivo()
        if erro:
            QMessageBox.warning(self, "Dados incompletos", erro)
            return
        self._salvar_motivo()
        registrar_status(self.os_id, "Reprovado - Patrimônio", self.usuario_logado["id_user"])
        QMessageBox.information(self, "Chamado reprovado", f"OS {self.os_id} marcada como Reprovado - Patrimônio.")
        self.accept()

    def _aprovar(self):
        erro = self._validar_motivo()
        if erro:
            QMessageBox.warning(self, "Dados incompletos", erro)
            return
        self._salvar_motivo()
        registrar_status(self.os_id, "Aprovado - Patrimônio", self.usuario_logado["id_user"])
        QMessageBox.information(self, "Chamado aprovado", f"OS {self.os_id} marcada como Aprovado - Patrimônio.")
        self.accept()
