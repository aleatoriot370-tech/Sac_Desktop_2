from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame

from core.database import contagem_dashboard


class CardStatus(QFrame):
    def __init__(self, titulo: str, cor: str):
        super().__init__()
        self.setObjectName("cardDashboard")
        self.setMinimumHeight(90)
        layout = QVBoxLayout(self)

        self.label_valor = QLabel("0")
        self.label_valor.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {cor};")
        self.label_valor.setAlignment(Qt.AlignCenter)

        label_titulo = QLabel(titulo)
        label_titulo.setAlignment(Qt.AlignCenter)
        label_titulo.setStyleSheet("font-size: 12px; color: #6B7280;")

        layout.addWidget(self.label_valor)
        layout.addWidget(label_titulo)

    def set_valor(self, valor: int):
        self.label_valor.setText(str(valor))


class DashboardWidget(QWidget):
    """Mini dashboard exibido na Tela Inicial (item 1)."""

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setSpacing(16)

        self.card_novo = CardStatus("Novos", "#1246FF")
        self.card_processo = CardStatus("Em processo", "#C99A1E")
        self.card_finalizado = CardStatus("Finalizados", "#2FA84F")

        layout.addWidget(self.card_novo)
        layout.addWidget(self.card_processo)
        layout.addWidget(self.card_finalizado)

        self.atualizar()

    def atualizar(self):
        try:
            contagem = contagem_dashboard()
        except Exception:
            contagem = {"Novo": 0, "Finalizado": 0, "Em processo": 0}
        self.card_novo.set_valor(contagem.get("Novo", 0))
        self.card_processo.set_valor(contagem.get("Em processo", 0))
        self.card_finalizado.set_valor(contagem.get("Finalizado", 0))
