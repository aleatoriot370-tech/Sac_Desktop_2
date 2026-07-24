from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QListView,
)

from core.database import listar_midias

EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
TAMANHO_MINIATURA = 96


class VisualizadorMidias(QVBoxLayout):
    """
    Sub-layout reutilizável: mostra miniaturas das fotos (e ícone para
    vídeos) de uma OS. Duplo clique abre o arquivo original no programa
    padrão do sistema operacional. Se o arquivo não existir mais no
    caminho salvo (ex.: pasta de rede não mapeada nesta máquina), mostra
    um aviso claro em vez de simplesmente não fazer nada.
    """

    def __init__(self, os_id: int):
        super().__init__()
        titulo = QLabel("Mídias registradas:")
        self.addWidget(titulo)

        self.lista = QListWidget()
        self.lista.setViewMode(QListView.IconMode)
        self.lista.setIconSize(QSize(TAMANHO_MINIATURA, TAMANHO_MINIATURA))
        self.lista.setResizeMode(QListView.Adjust)
        self.lista.setSpacing(8)
        self.lista.setMinimumHeight(TAMANHO_MINIATURA + 50)
        self.lista.setMaximumHeight(TAMANHO_MINIATURA + 50)
        self.lista.setWordWrap(True)
        self.lista.itemDoubleClicked.connect(self._abrir_midia)
        self.addWidget(self.lista)

        self._carregar(os_id)

    def _carregar(self, os_id: int):
        midias = listar_midias(os_id)
        if not midias:
            item = QListWidgetItem("Nenhuma mídia registrada nesta OS.")
            item.setFlags(Qt.NoItemFlags)
            self.lista.addItem(item)
            return

        for midia in midias:
            nome = midia.get("nome") or ""
            caminho = midia.get("localizacao")
            item = QListWidgetItem(nome)
            item.setData(1000, caminho)

            extensao = os.path.splitext(nome)[1].lower()
            if extensao in EXTENSOES_IMAGEM and caminho and os.path.exists(caminho):
                pixmap = QPixmap(caminho)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        TAMANHO_MINIATURA, TAMANHO_MINIATURA,
                        Qt.KeepAspectRatio, Qt.SmoothTransformation,
                    )
                    item.setIcon(QIcon(pixmap))
            else:
                # Vídeo, ou imagem cujo arquivo não está acessível agora
                # (ex.: pasta de rede não mapeada nesta máquina) — mostra
                # um ícone genérico em vez de deixar em branco.
                item.setIcon(self.lista.style().standardIcon(
                    self.lista.style().StandardPixmap.SP_FileIcon
                ))

            self.lista.addItem(item)

    def _abrir_midia(self, item: QListWidgetItem):
        caminho = item.data(1000)
        if not caminho:
            return

        if not os.path.exists(caminho):
            QMessageBox.warning(
                None, "Arquivo não encontrado",
                f"O arquivo de mídia não foi encontrado no caminho salvo:\n\n{caminho}\n\n"
                "Isso costuma acontecer quando a pasta de rede (ex.: unidade P:) "
                "não está mapeada/acessível nesta máquina. Verifique sua conexão "
                "de rede ou o mapeamento da unidade.",
            )
            return

        try:
            if sys.platform == "win32":
                os.startfile(caminho)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.run(["open", caminho], check=True)
            else:
                subprocess.run(["xdg-open", caminho], check=True)
        except Exception as exc:
            QMessageBox.warning(
                None, "Não foi possível abrir o arquivo",
                f"O arquivo existe, mas não foi possível abri-lo automaticamente.\n\n"
                f"Caminho: {caminho}\n\nDetalhes: {exc}",
            )
