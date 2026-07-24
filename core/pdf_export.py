"""
Geração de PDF genérica para fichas e formulários do SAC.

Todas as telas que têm o botão "Gerar PDF" reaproveitam `gerar_pdf_ficha`,
passando só os dados já carregados na tela (nunca fazemos uma nova
consulta ao banco aqui — este módulo só sabe desenhar o PDF).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

AZUL_ESCURO = colors.HexColor("#12299B")
CINZA_BORDA = colors.HexColor("#D9DEEA")


def gerar_pdf_ficha(
    destino: Path,
    titulo: str,
    os_id: int,
    campos: list[tuple[str, str]],
    tabela: Optional[tuple[list[str], list[list[str]]]] = None,
    observacoes: Optional[list[tuple[str, str]]] = None,
) -> Path:
    """
    Gera um PDF simples de uma ficha/formulário.

    campos: lista de (rótulo, valor) mostrados como texto corrido.
    tabela: opcional, (cabecalhos, linhas) para uma tabela de produtos.
    observacoes: opcional, seções extras no fim (ex: Análise, Justificativa,
                 histórico de aprovação) — mesmo formato de `campos`.
    """
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloSac", parent=estilos["Title"], textColor=AZUL_ESCURO, fontSize=16,
    )
    estilo_rotulo = ParagraphStyle(
        "RotuloSac", parent=estilos["Normal"], fontSize=10, textColor=colors.grey,
    )
    estilo_valor = ParagraphStyle(
        "ValorSac", parent=estilos["Normal"], fontSize=11, spaceAfter=8,
    )

    destino.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(destino), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )

    elementos = [
        Paragraph(titulo, estilo_titulo),
        Paragraph(f"OS nº {os_id}", estilos["Heading3"]),
        Spacer(1, 0.4 * cm),
    ]

    for rotulo, valor in campos:
        elementos.append(Paragraph(rotulo, estilo_rotulo))
        elementos.append(Paragraph(_escapar(valor) or "-", estilo_valor))

    if tabela:
        cabecalhos, linhas = tabela
        elementos.append(Spacer(1, 0.3 * cm))
        elementos.append(Paragraph("Produto", estilos["Heading4"]))
        dados_tabela = [cabecalhos] + linhas
        t = Table(dados_tabela, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        elementos.append(t)

    if observacoes:
        elementos.append(Spacer(1, 0.4 * cm))
        for rotulo, valor in observacoes:
            elementos.append(Paragraph(rotulo, estilo_rotulo))
            elementos.append(Paragraph(_escapar(valor) or "-", estilo_valor))

    doc.build(elementos)
    return destino


def _escapar(valor: str) -> str:
    """Escapa caracteres especiais de XML/HTML usados pelo reportlab (Paragraph usa markup)."""
    if valor is None:
        return ""
    return (
        str(valor)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
