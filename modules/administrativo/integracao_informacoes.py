from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox,
)

from config import Config
from core.database import get_client
from modules.base_popup_module import BasePopupModule


class IntegracaoInformacoes(BasePopupModule):
    """
    Módulo 1.4.1 - Integração de informações.

    Move/recorta as mídias de Config.MEDIA_STAGING_PATH para
    Config.MEDIA_PATH, renomeando o caminho no banco
    (Sac_fotos_video.localizacao) para o novo destino.
    """

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(usuario_logado, parent)
        self.setWindowTitle("Administrativo - Integração de Informações")
        self.resize(640, 460)
        self._montar_ui()

    def _montar_ui(self):
        layout = self.content_layout()

        titulo = QLabel("Integração de Informações")
        titulo.setObjectName("tituloTela")
        layout.addWidget(titulo)

        descricao = QLabel(
            f"Move os arquivos de mídia de:\n{Config.MEDIA_STAGING_PATH}\n\n"
            f"para:\n{Config.MEDIA_PATH}\n\n"
            "e atualiza o caminho de cada arquivo no banco de dados."
        )
        descricao.setObjectName("subtitulo")
        descricao.setWordWrap(True)
        layout.addWidget(descricao)

        self.btn_integrar = QPushButton("Integrar")
        self.btn_integrar.clicked.connect(self._executar_integracao)
        layout.addWidget(self.btn_integrar)

        layout.addWidget(QLabel("Andamento:"))
        self.painel_log = QTextEdit()
        self.painel_log.setReadOnly(True)
        layout.addWidget(self.painel_log)

    def _log(self, mensagem: str):
        self.painel_log.append(mensagem)
        self.painel_log.repaint()

    def _executar_integracao(self):
        origem = Path(Config.MEDIA_STAGING_PATH)
        destino_dir = Path(Config.MEDIA_PATH)

        if not origem.exists():
            QMessageBox.warning(
                self, "Pasta de origem não encontrada",
                f"A pasta de origem não existe ou não está acessível:\n{origem}",
            )
            return

        destino_dir.mkdir(parents=True, exist_ok=True)
        self.btn_integrar.setEnabled(False)
        self.painel_log.clear()

        arquivos = [p for p in origem.iterdir() if p.is_file()]
        self._log(f"Encontrados {len(arquivos)} arquivo(s) para mover.")

        movidos, falhas = 0, 0
        for arquivo in arquivos:
            destino = destino_dir / arquivo.name
            try:
                shutil.move(str(arquivo), str(destino))
                self._atualizar_localizacao_banco(arquivo.name, str(destino))
                self._log(f"OK: {arquivo.name}")
                movidos += 1
            except Exception as exc:
                self._log(f"ERRO em {arquivo.name}: {exc}")
                falhas += 1

        self._log(f"\nConcluído: {movidos} movido(s), {falhas} falha(s).")
        self.btn_integrar.setEnabled(True)
        QMessageBox.information(
            self, "Integração concluída",
            f"{movidos} arquivo(s) movido(s) com sucesso.\n{falhas} falha(s).",
        )

    @staticmethod
    def _atualizar_localizacao_banco(nome_arquivo: str, novo_caminho: str):
        """Atualiza Sac_fotos_video.localizacao para o novo caminho definitivo."""
        get_client().table("Sac_fotos_video").update(
            {"localizacao": novo_caminho}
        ).eq("nome", nome_arquivo).execute()
