from __future__ import annotations

import datetime as dt
import random
import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox,
    QTextEdit, QPushButton, QMessageBox, QFileDialog, QListWidget, QWidget,
)

from config import Config
from core.database import criar_chamado_pf, salvar_midia
from modules.base_popup_module import BasePopupModule

MARCAS = ["Paletitas", "Luigi", "Natuzon", "Real", "Icream", "Natuca", "Outros"]

PROBLEMAS = [
    "CONE QUEBRADO", "EMBALAGEM DANIFICADA", "EMBALAGEM SUJA",
    "ETIQUETA TROCADA", "FALHA DE IMPRESSÃO", "FALHA DE SELAGEM",
    "OBJETO ESTRANHO", "PALITO QUEBRADO", "PICOLÉ SEM PALITO",
    "PICOLÉ SEM RECHEIO", "PRODUTO ABAIXO DO PESO", "PICOLÉ CORTADO",
    "PRODUTO CRISTALIZADO", "PRODUTO DERRETIDO", "PRODUTO FALTANDO NA CAIXA",
    "PRODUTO REBAIXADO", "PRODUTO SEM RÓTULO", "PRODUTO TROCADO",
    "PRODUTO VAZANDO",
]

EXTENSOES_ACEITAS = {".png", ".jpg", ".jpeg", ".mp4"}


class FormularioAberturaPF(BasePopupModule):
    """
    Módulo 1.1.1.1 - Formulário de Abertura de chamado Pessoa Física.

    Fluxo do botão Salvar (conforme especificação, com melhoria de
    atomicidade): cria SAC_OS -> cria Sac_PF -> registra Status "Novo" ->
    copia e renomeia as mídias -> mostra o número da OS gerado -> limpa
    os campos.
    """

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(usuario_logado, parent)
        self.setWindowTitle("Abertura de Chamado - Pessoa Física")
        self.resize(640, 760)
        self._arquivos_selecionados: list[Path] = []
        self._montar_ui()

    # ------------------------------------------------------------------
    def _montar_ui(self):
        layout_geral = self.content_layout()

        titulo = QLabel("Abertura de Chamado - Pessoa Física")
        titulo.setObjectName("tituloTela")
        layout_geral.addWidget(titulo)

        form = QFormLayout()
        self.campo_nome = QLineEdit()
        self.campo_email = QLineEdit()
        self.campo_cpf = QLineEdit()
        self.campo_cpf.setPlaceholderText("Somente números")
        self.campo_celular = QLineEdit()
        self.campo_celular.setPlaceholderText("Somente números")
        self.campo_motivo = QTextEdit()
        self.campo_motivo.setMaximumHeight(70)
        self.campo_cidade = QLineEdit()
        self.campo_estado = QLineEdit()
        self.combo_marca = QComboBox()
        self.combo_marca.addItems(MARCAS)
        self.campo_produto = QLineEdit()
        self.campo_lote = QLineEdit()
        self.combo_problema = QComboBox()
        self.combo_problema.addItems(PROBLEMAS)
        self.campo_local_compra = QLineEdit()

        form.addRow("Nome*:", self.campo_nome)
        form.addRow("E-mail*:", self.campo_email)
        form.addRow("CPF*:", self.campo_cpf)
        form.addRow("Celular*:", self.campo_celular)
        form.addRow("Motivo* (até 300 caracteres):", self.campo_motivo)
        form.addRow("Cidade*:", self.campo_cidade)
        form.addRow("Estado*:", self.campo_estado)
        form.addRow("Marca*:", self.combo_marca)
        form.addRow("Nome do Produto*:", self.campo_produto)
        form.addRow("Lote*:", self.campo_lote)
        form.addRow("Problema apresentado*:", self.combo_problema)
        form.addRow("Local de compra*:", self.campo_local_compra)
        layout_geral.addLayout(form)

        # Mídias
        label_midia = QLabel("Fotos e vídeos:")
        layout_geral.addWidget(label_midia)
        self.lista_midias = QListWidget()
        self.lista_midias.setMaximumHeight(90)
        layout_geral.addWidget(self.lista_midias)

        btn_midia = QPushButton("Adicionar mídia (foto/vídeo)")
        btn_midia.setObjectName("secondary")
        btn_midia.clicked.connect(self._selecionar_midia)
        layout_geral.addWidget(btn_midia)

        # Botões finais
        botoes = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("danger")
        btn_cancelar.clicked.connect(self._cancelar)
        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self._salvar)
        botoes.addWidget(btn_cancelar)
        botoes.addWidget(btn_salvar)
        layout_geral.addLayout(botoes)

    # ------------------------------------------------------------------
    def _selecionar_midia(self):
        arquivos, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar fotos/vídeos", "",
            "Mídia (*.png *.jpg *.jpeg *.mp4)",
        )
        for caminho in arquivos:
            p = Path(caminho)
            if p.suffix.lower() in EXTENSOES_ACEITAS:
                self._arquivos_selecionados.append(p)
                self.lista_midias.addItem(p.name)

    # ------------------------------------------------------------------
    def _validar(self) -> str | None:
        obrigatorios = {
            "Nome": self.campo_nome.text().strip(),
            "E-mail": self.campo_email.text().strip(),
            "CPF": self.campo_cpf.text().strip(),
            "Celular": self.campo_celular.text().strip(),
            "Motivo": self.campo_motivo.toPlainText().strip(),
            "Cidade": self.campo_cidade.text().strip(),
            "Estado": self.campo_estado.text().strip(),
            "Nome do Produto": self.campo_produto.text().strip(),
            "Lote": self.campo_lote.text().strip(),
            "Local de compra": self.campo_local_compra.text().strip(),
        }
        for campo, valor in obrigatorios.items():
            if not valor:
                return f"O campo '{campo}' é obrigatório."

        if not self.campo_cpf.text().strip().isdigit():
            return "CPF deve conter apenas números."
        if not self.campo_celular.text().strip().isdigit():
            return "Celular deve conter apenas números."
        if len(self.campo_motivo.toPlainText()) > 300:
            return "Motivo deve ter no máximo 300 caracteres."
        return None

    # ------------------------------------------------------------------
    def _cancelar(self):
        resposta = QMessageBox.question(
            self, "Cancelar abertura",
            "Tem certeza que deseja cancelar? Todos os dados digitados serão perdidos.",
        )
        if resposta == QMessageBox.Yes:
            self._limpar_formulario()
            self.reject()

    # ------------------------------------------------------------------
    def _salvar(self):
        erro = self._validar()
        if erro:
            QMessageBox.warning(self, "Dados incompletos", erro)
            return

        dados = {
            "nome": self.campo_nome.text().strip(),
            "email": self.campo_email.text().strip(),
            "cpf": self.campo_cpf.text().strip(),
            "celular": self.campo_celular.text().strip(),
            "motivo": self.campo_motivo.toPlainText().strip(),
            "cidade": self.campo_cidade.text().strip(),
            "estado": self.campo_estado.text().strip(),
            "marca": self.combo_marca.currentText(),
            "nome_produto": self.campo_produto.text().strip(),
            "lote": self.campo_lote.text().strip(),
            "problema": self.combo_problema.currentText(),
            "local": self.campo_local_compra.text().strip(),
        }

        try:
            resultado = criar_chamado_pf(dados, id_user=self.usuario_logado["id_user"])
            os_id = resultado["os_id"]
            self._salvar_midias(os_id)
        except Exception as exc:
            QMessageBox.critical(
                self, "Erro ao salvar",
                f"Não foi possível salvar o chamado.\n\nDetalhes: {exc}",
            )
            return

        QMessageBox.information(
            self, "Chamado registrado",
            f"Chamado registrado com sucesso!\n\nNúmero da OS: {os_id}",
        )
        self._limpar_formulario()
        self.accept()

    # ------------------------------------------------------------------
    def _salvar_midias(self, os_id: int):
        """
        Renomeia e copia cada mídia para a pasta definitiva, no padrão:
        Sacpf_AAAAMMDDHHMM_(numero aleatorio).ext
        """
        destino_dir = Path(Config.MEDIA_PATH)
        destino_dir.mkdir(parents=True, exist_ok=True)

        for arquivo in self._arquivos_selecionados:
            agora = dt.datetime.now().strftime("%Y%m%d%H%M")
            aleatorio = random.randint(1000, 9999)
            novo_nome = f"Sacpf_{agora}_{aleatorio}{arquivo.suffix.lower()}"
            destino = destino_dir / novo_nome
            shutil.copy2(arquivo, destino)
            salvar_midia(
                nome_arquivo=novo_nome,
                localizacao=str(destino),
                os_id=os_id,
            )

    # ------------------------------------------------------------------
    def _limpar_formulario(self):
        self.campo_nome.clear()
        self.campo_email.clear()
        self.campo_cpf.clear()
        self.campo_celular.clear()
        self.campo_motivo.clear()
        self.campo_cidade.clear()
        self.campo_estado.clear()
        self.combo_marca.setCurrentIndex(0)
        self.campo_produto.clear()
        self.campo_lote.clear()
        self.combo_problema.setCurrentIndex(0)
        self.campo_local_compra.clear()
        self.lista_midias.clear()
        self._arquivos_selecionados.clear()

    def descarregar_dados(self):
        self._arquivos_selecionados.clear()
