"""
SAC - Grupo Lamoia
Ponto de entrada da aplicação desktop.
"""
import sys

from PySide6.QtWidgets import QApplication

from config import Config
from ui.style import QSS
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.setApplicationName(Config.APP_NAME)

    login = LoginWindow()
    if login.exec() != LoginWindow.Accepted:
        sys.exit(0)

    janela = MainWindow(login.usuario_autenticado)
    janela.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
