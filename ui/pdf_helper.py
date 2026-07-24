from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QWidget, QFileDialog, QMessageBox

from core.pdf_export import gerar_pdf_ficha


def exportar_pdf(
    parent: QWidget,
    titulo: str,
    os_id: int,
    campos: list[tuple[str, str]],
    tabela: Optional[tuple[list[str], list[list[str]]]] = None,
    observacoes: Optional[list[tuple[str, str]]] = None,
):
    """
    Abre o diálogo "Salvar como", gera o PDF e oferece abri-lo.
    Reaproveitado por todas as telas com botão "Gerar PDF".
    """
    nome_sugerido = f"OS_{os_id}.pdf"
    caminho, _ = QFileDialog.getSaveFileName(
        parent, "Salvar PDF", nome_sugerido, "PDF (*.pdf)"
    )
    if not caminho:
        return

    try:
        destino = gerar_pdf_ficha(
            Path(caminho), titulo, os_id, campos, tabela=tabela, observacoes=observacoes,
        )
    except Exception as exc:
        QMessageBox.critical(parent, "Erro ao gerar PDF", f"Não foi possível gerar o PDF.\n\n{exc}")
        return

    resposta = QMessageBox.question(
        parent, "PDF gerado", f"PDF salvo em:\n{destino}\n\nDeseja abrir agora?",
    )
    if resposta == QMessageBox.Yes:
        _abrir_arquivo(str(destino))


def _abrir_arquivo(caminho: str):
    if not os.path.exists(caminho):
        return
    if sys.platform == "win32":
        os.startfile(caminho)  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.run(["open", caminho])
    else:
        subprocess.run(["xdg-open", caminho])
