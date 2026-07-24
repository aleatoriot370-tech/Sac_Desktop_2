from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)

from core.auth import hash_senha
from core.database import listar_usuarios, criar_ou_atualizar_usuario
from modules.base_popup_module import BasePopupModule

TIPOS_USUARIO = [
    "Admin Senior", "Admin Junior", "Comercial", "Financeiro",
    "Qualidade", "Patrimônio", "User",
]
STATUS_LABELS = {"a": "Ativo", "i": "Inativo"}
STATUS_VALORES = {v: k for k, v in STATUS_LABELS.items()}


class GestaoUsuarios(BasePopupModule):
    """Módulo 1.4.2 - Gestão de Usuários."""

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(usuario_logado, parent)
        self.setWindowTitle("Administrativo - Gestão de Usuários")
        self.resize(760, 640)
        self._id_em_edicao: int | None = None
        self._usuarios: list[dict] = []
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        titulo = QLabel("Gestão de Usuários")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        form = QFormLayout()
        self.campo_login = QLineEdit()
        self.campo_senha = QLineEdit()
        self.campo_senha.setEchoMode(QLineEdit.Password)
        self.campo_senha.setPlaceholderText("Deixe em branco para manter a senha atual (ao editar)")
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(TIPOS_USUARIO)
        self.campo_nome = QLineEdit()
        self.combo_status = QComboBox()
        self.combo_status.addItems(list(STATUS_LABELS.values()))

        form.addRow("Login*:", self.campo_login)
        form.addRow("Senha*:", self.campo_senha)
        form.addRow("Tipo*:", self.combo_tipo)
        form.addRow("Nome*:", self.campo_nome)
        form.addRow("Status*:", self.combo_status)
        layout.addLayout(form)

        botoes_form = QHBoxLayout()
        btn_novo = QPushButton("Novo")
        btn_novo.setObjectName("secondary")
        btn_novo.clicked.connect(self._novo)
        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self._salvar)
        botoes_form.addWidget(btn_novo)
        botoes_form.addWidget(btn_salvar)
        layout.addLayout(botoes_form)

        layout.addWidget(QLabel("Usuários cadastrados:"))
        filtro = QHBoxLayout()
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(["Todos", "Ativo", "Inativo"])
        self.combo_filtro.currentIndexChanged.connect(self._carregar)
        filtro.addWidget(self.combo_filtro)
        layout.addLayout(filtro)

        self.tabela = QTableWidget(0, 4)
        self.tabela.setHorizontalHeaderLabels(["Login", "Nome", "Tipo", "Status"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.cellDoubleClicked.connect(self._carregar_para_edicao)
        layout.addWidget(self.tabela)

        self._carregar()

    def _carregar(self):
        filtro_texto = self.combo_filtro.currentText()
        status_filtro = STATUS_VALORES.get(filtro_texto)
        try:
            self._usuarios = listar_usuarios(status_filtro=status_filtro)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar usuários.\n\n{exc}")
            return

        self.tabela.setRowCount(0)
        for u in self._usuarios:
            i = self.tabela.rowCount()
            self.tabela.insertRow(i)
            self.tabela.setItem(i, 0, QTableWidgetItem(u.get("Login") or ""))
            self.tabela.setItem(i, 1, QTableWidgetItem(u.get("Nome") or ""))
            self.tabela.setItem(i, 2, QTableWidgetItem(u.get("Tipo") or ""))
            self.tabela.setItem(i, 3, QTableWidgetItem(STATUS_LABELS.get(u.get("Status"), u.get("Status") or "")))

    def _carregar_para_edicao(self, linha: int, _coluna: int):
        u = self._usuarios[linha]
        self._id_em_edicao = u["id_user"]
        self.campo_login.setText(u.get("Login") or "")
        self.campo_senha.clear()
        self.combo_tipo.setCurrentText(u.get("Tipo") or TIPOS_USUARIO[0])
        self.campo_nome.setText(u.get("Nome") or "")
        self.combo_status.setCurrentText(STATUS_LABELS.get(u.get("Status"), "Ativo"))

    def _novo(self):
        self._id_em_edicao = None
        self.campo_login.clear()
        self.campo_senha.clear()
        self.combo_tipo.setCurrentIndex(0)
        self.campo_nome.clear()
        self.combo_status.setCurrentIndex(0)

    def _validar(self) -> str | None:
        if not self.campo_login.text().strip():
            return "O campo 'Login' é obrigatório."
        if not self._id_em_edicao and not self.campo_senha.text():
            return "O campo 'Senha' é obrigatório para novos usuários."
        if not self.campo_nome.text().strip():
            return "O campo 'Nome' é obrigatório."
        return None

    def _salvar(self):
        erro = self._validar()
        if erro:
            QMessageBox.warning(self, "Dados incompletos", erro)
            return

        dados = {
            "Login": self.campo_login.text().strip(),
            "Tipo": self.combo_tipo.currentText(),
            "Nome": self.campo_nome.text().strip(),
            "Status": STATUS_VALORES[self.combo_status.currentText()],
        }
        # Senha só é regravada se o usuário digitou algo (evita apagar a
        # senha existente ao só editar nome/tipo/status).
        if self.campo_senha.text():
            dados["Senha"] = hash_senha(self.campo_senha.text())

        try:
            criar_ou_atualizar_usuario(dados, id_user=self._id_em_edicao)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao salvar", f"Não foi possível salvar o usuário.\n\n{exc}")
            return

        QMessageBox.information(self, "Usuário salvo", "Dados salvos com sucesso.")
        self._novo()
        self._carregar()

    def descarregar_dados(self):
        self._usuarios.clear()
