"""Estilo visual centralizado (paleta baseada nas cores da logo do Grupo Lamoia)."""

AZUL_ESCURO = "#12299B"
AZUL_VIVO = "#1246FF"
VERDE_LIMAO = "#B6E23A"
CINZA_FUNDO = "#F4F6FB"
CINZA_BORDA = "#D9DEEA"
BRANCO = "#FFFFFF"
TEXTO = "#1E2233"

QSS = f"""
* {{
    font-family: 'Segoe UI', 'Inter', sans-serif;
    color: {TEXTO};
}}
QMainWindow, QDialog, QWidget#root {{
    background-color: {CINZA_FUNDO};
}}
QScrollArea {{
    background-color: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background-color: {CINZA_FUNDO};
}}
QMenuBar {{
    background-color: {AZUL_ESCURO};
    color: {BRANCO};
    padding: 6px;
    font-size: 13px;
}}
QMenuBar::item {{
    background: transparent;
    padding: 8px 14px;
    border-radius: 6px;
}}
QMenuBar::item:selected {{
    background-color: {AZUL_VIVO};
}}
QMenu {{
    background-color: {BRANCO};
    border: 1px solid {CINZA_BORDA};
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {VERDE_LIMAO};
    color: {AZUL_ESCURO};
}}
QPushButton {{
    background-color: {AZUL_VIVO};
    color: {BRANCO};
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {AZUL_ESCURO};
}}
QPushButton:disabled {{
    background-color: #A9B3C9;
}}
QPushButton#secondary {{
    background-color: {BRANCO};
    color: {AZUL_ESCURO};
    border: 1px solid {AZUL_VIVO};
}}
QPushButton#secondary:hover {{
    background-color: {CINZA_FUNDO};
}}
QPushButton#danger {{
    background-color: #D64545;
}}
QPushButton#danger:hover {{
    background-color: #B23434;
}}
QLineEdit, QComboBox, QDateEdit, QTextEdit {{
    background-color: {BRANCO};
    color: {TEXTO};
    border: 1px solid {CINZA_BORDA};
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{
    border: 1px solid {AZUL_VIVO};
}}
QLineEdit:read-only, QTextEdit:read-only {{
    background-color: {CINZA_FUNDO};
    color: {TEXTO};
}}
QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled {{
    background-color: {CINZA_FUNDO};
    color: #6B7280;
}}
QLabel {{
    background-color: transparent;
}}
QLabel#tituloTela {{
    font-size: 18px;
    font-weight: 700;
    color: {AZUL_ESCURO};
}}
QLabel#subtitulo {{
    font-size: 12px;
    color: #6B7280;
}}
QTableWidget {{
    background-color: {BRANCO};
    color: {TEXTO};
    border: 1px solid {CINZA_BORDA};
    gridline-color: {CINZA_BORDA};
    alternate-background-color: {CINZA_FUNDO};
}}
QTableWidget::item {{
    padding: 4px;
}}
QTableWidget::item:selected, QTableWidget::item:selected:active {{
    background-color: {AZUL_VIVO};
    color: {BRANCO};
}}
QHeaderView::section {{
    background-color: {AZUL_ESCURO};
    color: {BRANCO};
    padding: 8px;
    border: none;
    font-weight: 600;
}}
QListWidget {{
    background-color: {BRANCO};
    color: {TEXTO};
    border: 1px solid {CINZA_BORDA};
    border-radius: 6px;
    padding: 4px;
}}
QListWidget::item {{
    padding: 6px;
    border-radius: 4px;
}}
QListWidget::item:hover {{
    background-color: {CINZA_FUNDO};
}}
QListWidget::item:selected, QListWidget::item:selected:active {{
    background-color: {AZUL_VIVO};
    color: {BRANCO};
}}
QFrame#cardDashboard {{
    background-color: {BRANCO};
    border-radius: 12px;
    border: 1px solid {CINZA_BORDA};
}}
QScrollBar:vertical {{
    background: {CINZA_FUNDO};
    width: 12px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {CINZA_BORDA};
    border-radius: 6px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #A9B3C9;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""
