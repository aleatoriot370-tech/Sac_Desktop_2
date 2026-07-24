from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame,
)

from config import Config
from core.auth import autenticar


class LoginWindow(QDialog):
    """Módulo 0 - Login."""

    def __init__(self):
        super().__init__()
        self.usuario_autenticado: dict | None = None
        self.setWindowTitle(Config.APP_NAME)
        self.setFixedSize(420, 480)
        self._montar_ui()

    def _montar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        if Config.LOGO_PATH.exists():
            logo = QLabel()
            pix = QPixmap(str(Config.LOGO_PATH)).scaledToWidth(
                220, Qt.SmoothTransformation
            )
            logo.setPixmap(pix)
            logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo)

        titulo = QLabel("Acesso ao Sistema")
        titulo.setObjectName("tituloTela")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        self.campo_login = QLineEdit()
        self.campo_login.setPlaceholderText("Login")
        layout.addWidget(self.campo_login)

        self.campo_senha = QLineEdit()
        self.campo_senha.setPlaceholderText("Senha")
        self.campo_senha.setEchoMode(QLineEdit.Password)
        self.campo_senha.returnPressed.connect(self._entrar)
        layout.addWidget(self.campo_senha)

        self.label_erro = QLabel("")
        self.label_erro.setStyleSheet("color: #D64545;")
        self.label_erro.setAlignment(Qt.AlignCenter)
        self.label_erro.setWordWrap(True)
        layout.addWidget(self.label_erro)

        botoes = QHBoxLayout()
        btn_entrar = QPushButton("Entrar")
        btn_entrar.clicked.connect(self._entrar)
        botoes.addWidget(btn_entrar)
        layout.addLayout(botoes)

        layout.addStretch()

    def _entrar(self):
        login = self.campo_login.text().strip()
        senha = self.campo_senha.text()

        if not login or not senha:
            self.label_erro.setText("Informe login e senha.")
            return

        try:
            usuario, erro = autenticar(login, senha)
        except Exception as exc:  # falha de conexão com Supabase, etc.
            QMessageBox.critical(
                self, "Erro de conexão",
                f"Não foi possível conectar ao banco de dados.\n\nDetalhes: {exc}",
            )
            return

        if erro:
            # Mensagem amigável, conforme especificado: nunca revelar se
            # foi o login ou a senha que errou.
            self.label_erro.setText(erro)
            self.campo_senha.clear()
            return

        self.usuario_autenticado = usuario
        self.accept()
