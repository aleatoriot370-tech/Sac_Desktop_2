from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)

from core.database import listar_chamados_pf, registrar_status
from modules.base_popup_module import BasePopupModule
from modules.chamados.ficha_pessoa_fisica import FichaPessoaFisica

STATUS_OPCOES = ["", "Novo", "Em Investigação", "Aprovado - Qualidade",
                  "Reprovado - Qualidade", "Aguardando Financeiro",
                  "Pagamento Programado", "Finalizado"]


class ListaChamadoPF(BasePopupModule):
    """Módulo 1.1.1.2 - Lista de Chamados PF."""

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(usuario_logado, parent)
        self.setWindowTitle("Lista de Chamados - Pessoa Física")
        self.resize(820, 560)
        self._resultados: list[dict] = []
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        titulo = QLabel("Lista de Chamados - Pessoa Física")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        filtros = QHBoxLayout()
        self.campo_os_id = QLineEdit()
        self.campo_os_id.setPlaceholderText("Nº da OS")
        self.campo_cpf = QLineEdit()
        self.campo_cpf.setPlaceholderText("CPF do cliente")
        self.combo_status = QComboBox()
        self.combo_status.addItems(STATUS_OPCOES)
        btn_pesquisar = QPushButton("Pesquisar")
        btn_pesquisar.clicked.connect(self._pesquisar)

        filtros.addWidget(self.campo_os_id)
        filtros.addWidget(self.campo_cpf)
        filtros.addWidget(self.combo_status)
        filtros.addWidget(btn_pesquisar)
        layout.addLayout(filtros)

        self.tabela = QTableWidget(0, 4)
        self.tabela.setHorizontalHeaderLabels(["OS", "Nome", "CPF", "Status / Data"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.cellDoubleClicked.connect(self._abrir_detalhe)
        layout.addWidget(self.tabela)

        dica = QLabel("Dê duplo clique em uma linha para abrir a ficha do chamado.")
        dica.setObjectName("subtitulo")
        layout.addWidget(dica)

        self._pesquisar()

    def _pesquisar(self):
        os_id = self.campo_os_id.text().strip()
        cpf = self.campo_cpf.text().strip()
        status_filtro = self.combo_status.currentText() or None

        try:
            self._resultados = listar_chamados_pf(
                os_id=int(os_id) if os_id else None,
                cpf=cpf if cpf else None,
                status_filtro=status_filtro,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao buscar chamados.\n\n{exc}")
            return

        self.tabela.setRowCount(0)
        for row in self._resultados:
            i = self.tabela.rowCount()
            self.tabela.insertRow(i)
            self.tabela.setItem(i, 0, QTableWidgetItem(str(row["os_id"])))
            self.tabela.setItem(i, 1, QTableWidgetItem(row.get("nome") or ""))
            self.tabela.setItem(i, 2, QTableWidgetItem(str(row.get("cpf") or "")))
            status_texto = f"{row.get('status') or '-'}"
            self.tabela.setItem(i, 3, QTableWidgetItem(status_texto))

    def _abrir_detalhe(self, linha: int, _coluna: int):
        registro = self._resultados[linha]
        status_atual = registro.get("status")

        # Modelo simplificado do pop-up de detalhe descrito na especificação.
        # Em uma implementação completa, este seria outro QDialog próprio
        # (ficha_chamado_pf_detalhe.py) reaproveitando o mesmo padrão do
        # FormularioAberturaPF, exibindo produtos, análise de qualidade,
        # resolução/resposta e, condicionalmente, os botões:
        #  - "Dados Financeiro" (se status == Aprovado - Qualidade)
        #  - "Finalizar" (se status == Reprovado - Qualidade)
        if status_atual == "Reprovado - Qualidade":
            resposta = QMessageBox.question(
                self, f"OS {registro['os_id']}",
                "Status atual: Reprovado - Qualidade.\nDeseja finalizar este chamado?",
            )
            if resposta == QMessageBox.Yes:
                registrar_status(
                    registro["os_id"], "Finalizado",
                    id_user=self.usuario_logado["id_user"],
                )
                self._pesquisar()
        else:
            dialogo = FichaPessoaFisica(self.usuario_logado, registro["os_id"], parent=self)
            dialogo.exec()

    def descarregar_dados(self):
        self._resultados.clear()
