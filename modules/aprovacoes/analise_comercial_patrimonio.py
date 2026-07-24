from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,
)

from core.database import (
    buscar_cabecalho_patrimonio, listar_produtos_patrimonio,
    atualizar_justificativa_patrimonio, ultimo_registro_status, registrar_status,
)
from modules.base_popup_module import BasePopupModule
from ui.visualizador_midias import VisualizadorMidias
from ui.pdf_helper import exportar_pdf


class AnaliseComercialPatrimonio(BasePopupModule):
    """Módulo 1.2.3.2.1 - Análise Comercial Patrimônio (decisão final)."""

    def __init__(self, usuario_logado: dict, os_id: int, parent=None):
        super().__init__(usuario_logado, parent)
        self.os_id = os_id
        self.setWindowTitle(f"Análise Comercial Patrimônio - OS {os_id}")
        self.resize(880, 760)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        cabecalho_dados = buscar_cabecalho_patrimonio(self.os_id)
        produtos = listar_produtos_patrimonio(self.os_id)
        status_novo = ultimo_registro_status(self.os_id, "Novo")
        status_reprovado = ultimo_registro_status(self.os_id, "Reprovado - Patrimônio")

        cabecalho = QLabel(
            f"OS {self.os_id}  •  aberto por "
            f"{(status_novo or {}).get('nome_usuario') or '-'} em "
            f"{self._formatar_data((status_novo or {}).get('created_at'))}"
        )
        cabecalho.setObjectName("subtitulo")
        layout.addWidget(cabecalho)

        titulo = QLabel("Análise Comercial - Patrimônio")
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

        campo_motivo = QLineEdit(cabecalho_dados.get("motivo") or "")
        campo_motivo.setReadOnly(True)
        form_motivo = QFormLayout()
        form_motivo.addRow("Motivo:", campo_motivo)
        layout.addLayout(form_motivo)

        rodape_reprovacao = QLabel(
            f"Reprovado - Patrimônio por {(status_reprovado or {}).get('nome_usuario') or '-'} em "
            f"{self._formatar_data((status_reprovado or {}).get('created_at'))}"
        )
        rodape_reprovacao.setObjectName("subtitulo")
        layout.addWidget(rodape_reprovacao)

        layout.addLayout(VisualizadorMidias(self.os_id))

        layout.addWidget(QLabel("Justificativa*:"))
        self.campo_justificativa = QTextEdit(cabecalho_dados.get("justificativa") or "")
        self.campo_justificativa.setMaximumHeight(70)
        layout.addWidget(self.campo_justificativa)

        self._campos_pdf = campos_pdf + [("Motivo", cabecalho_dados.get("motivo"))]
        self._tabela_pdf = (["id_Produto", "Descrição", "Quantidade"], linhas_pdf)

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
            self, "Análise Comercial - Patrimônio", self.os_id, self._campos_pdf,
            tabela=self._tabela_pdf,
            observacoes=[("Justificativa", self.campo_justificativa.toPlainText())],
        )

    def _validar_justificativa(self) -> str | None:
        if not self.campo_justificativa.toPlainText().strip():
            return "O campo 'Justificativa' é obrigatório."
        return None

    def _salvar_justificativa(self):
        atualizar_justificativa_patrimonio(self.os_id, self.campo_justificativa.toPlainText().strip())

    def _reprovar(self):
        erro = self._validar_justificativa()
        if erro:
            QMessageBox.warning(self, "Dados incompletos", erro)
            return
        self._salvar_justificativa()
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
