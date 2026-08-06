"""
Geração de PDF profissional para fichas e formulários do SAC.

Layout com cabeçalho institucional, seções bem definidas, tabelas
formatadas e rodapé com data de geração.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)

# Cores institucionais
AZUL_ESCURO = colors.HexColor("#12299B")
AZUL_MEDIO = colors.HexColor("#1d4ed8")
AZUL_CLARO = colors.HexColor("#dbeafe")
CINZA_TEXTO = colors.HexColor("#374151")
CINZA_BORDA = colors.HexColor("#D9DEEA")
CINZA_FUNDO = colors.HexColor("#f3f4f6")
VERDE = colors.HexColor("#059669")
VERMELHO = colors.HexColor("#dc2626")


def _criar_estilos():
    """Cria estilos customizados para o PDF."""
    base = getSampleStyleSheet()

    estilos = {}

    estilos["titulo"] = ParagraphStyle(
        "TituloSAC", parent=base["Title"],
        textColor=AZUL_ESCURO, fontSize=18, leading=22,
        spaceAfter=4 * mm, alignment=TA_CENTER,
    )
    estilos["subtitulo"] = ParagraphStyle(
        "SubtituloSAC", parent=base["Normal"],
        textColor=CINZA_TEXTO, fontSize=10, leading=13,
        spaceAfter=6 * mm, alignment=TA_CENTER,
    )
    estilos["secao"] = ParagraphStyle(
        "SecaoSAC", parent=base["Heading2"],
        textColor=AZUL_ESCURO, fontSize=12, leading=15,
        spaceBefore=6 * mm, spaceAfter=3 * mm,
        borderWidth=0, borderPadding=0,
    )
    estilos["rotulo"] = ParagraphStyle(
        "RotuloSAC", parent=base["Normal"],
        textColor=colors.HexColor("#6b7280"), fontSize=8,
        leading=10, spaceAfter=1 * mm,
    )
    estilos["valor"] = ParagraphStyle(
        "ValorSAC", parent=base["Normal"],
        textColor=CINZA_TEXTO, fontSize=10, leading=13,
        spaceAfter=4 * mm,
    )
    estilos["valor_negrito"] = ParagraphStyle(
        "ValorNegritoSAC", parent=base["Normal"],
        textColor=CINZA_TEXTO, fontSize=10, leading=13,
        spaceAfter=4 * mm, fontName="Helvetica-Bold",
    )
    estilos["rodape"] = ParagraphStyle(
        "RodapeSAC", parent=base["Normal"],
        textColor=colors.HexColor("#9ca3af"), fontSize=7,
        leading=9, alignment=TA_CENTER,
    )
    estilos["status_ok"] = ParagraphStyle(
        "StatusOK", parent=base["Normal"],
        textColor=VERDE, fontSize=10, leading=13,
        fontName="Helvetica-Bold",
    )
    estilos["status_erro"] = ParagraphStyle(
        "StatusErro", parent=base["Normal"],
        textColor=VERMELHO, fontSize=10, leading=13,
        fontName="Helvetica-Bold",
    )

    return estilos


def _cabecalho_institucional(estilos: dict, titulo: str, os_id: int) -> list:
    """Cria o cabeçalho institucional do PDF."""
    elementos = []

    # Linha superior azul
    elementos.append(HRFlowable(
        width="100%", thickness=3, color=AZUL_ESCURO,
        spaceAfter=4 * mm,
    ))

    # Título
    elementos.append(Paragraph(titulo, estilos["titulo"]))

    # Subtítulo com OS
    elementos.append(Paragraph(
        f"OS nº <b>{os_id}</b> • Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        estilos["subtitulo"],
    ))

    # Linha separadora
    elementos.append(HRFlowable(
        width="100%", thickness=0.5, color=CINZA_BORDA,
        spaceAfter=4 * mm,
    ))

    return elementos


def _secao_titulo(estilos: dict, titulo: str) -> Paragraph:
    """Cria um título de seção com ícone."""
    return Paragraph(f"■ {titulo}", estilos["secao"])


def _campo_info(estilos: dict, rotulo: str, valor: str) -> list:
    """Cria um par rótulo/valor."""
    return [
        Paragraph(rotulo, estilos["rotulo"]),
        Paragraph(_escapar(valor) or "—", estilos["valor"]),
    ]


def _tabela_profissional(
    cabecalhos: list[str],
    linhas: list[list[str]],
    larguras: Optional[list[float]] = None,
) -> Table:
    """Cria uma tabela profissional com cabeçalho colorido."""
    dados = [cabecalhos] + linhas
    t = Table(dados, hAlign="LEFT", colWidths=larguras)
    t.setStyle(TableStyle([
        # Cabeçalho
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Corpo
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("TEXTCOLOR", (0, 1), (-1, -1), CINZA_TEXTO),
        # Linhas alternadas
        *[("BACKGROUND", (0, i), (-1, i), CINZA_FUNDO) for i in range(2, len(dados), 2)],
        # Bordas
        ("GRID", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, AZUL_ESCURO),
        # Alinhamento
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _rodape() -> list:
    """Cria o rodapé do PDF."""
    return [
        Spacer(1, 8 * mm),
        HRFlowable(width="100%", thickness=0.5, color=CINZA_BORDA, spaceAfter=2 * mm),
        Paragraph(
            f"Documento gerado automaticamente pelo sistema SAC • {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            ParagraphStyle("Rodape", fontSize=7, textColor=colors.HexColor("#9ca3af"), alignment=TA_CENTER),
        ),
    ]


def gerar_pdf_ficha(
    destino: Path,
    titulo: str,
    os_id: int,
    campos: list[tuple[str, str]],
    tabela: Optional[tuple[list[str], list[list[str]]]] = None,
    observacoes: Optional[list[tuple[str, str]]] = None,
) -> Path:
    """
    Gera um PDF profissional de uma ficha/formulário.

    campos: lista de (rótulo, valor) mostrados como texto corrido.
    tabela: opcional, (cabecalhos, linhas) para uma tabela de produtos.
    observacoes: opcional, seções extras no fim (ex: Análise, Justificativa,
                 histórico de aprovação) — mesmo formato de `campos`.
    """
    estilos = _criar_estilos()

    destino.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(destino), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )

    elementos = []

    # Cabeçalho institucional
    elementos.extend(_cabecalho_institucional(estilos, titulo, os_id))

    # Seção: Dados do Chamado
    elementos.append(_secao_titulo(estilos, "Dados do Chamado"))

    # Organiza campos em grid de 2 colunas para economizar espaço
    pares = []
    for rotulo, valor in campos:
        pares.append([
            Paragraph(f"<font color='#6b7280' size='8'>{rotulo}</font>", estilos["valor"]),
            Paragraph(_escapar(valor) or "—", estilos["valor"]),
        ])

    # Layout em tabela de 2 colunas (campo: valor | campo: valor)
    linhas_grid = []
    for i in range(0, len(pares), 2):
        linha = pares[i]
        if i + 1 < len(pares):
            linha.extend(pares[i + 1])
        else:
            linha.extend([Paragraph("", estilos["valor"]), Paragraph("", estilos["valor"])])
        linhas_grid.append(linha)

    if linhas_grid:
        tabela_grid = Table(linhas_grid, hAlign="LEFT")
        tabela_grid.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, CINZA_BORDA),
        ]))
        elementos.append(tabela_grid)

    # Tabela de produtos (se houver)
    if tabela:
        cabecalhos, linhas = tabela
        elementos.append(Spacer(1, 3 * mm))
        elementos.append(_secao_titulo(estilos, "Produtos"))
        elementos.append(_tabela_profissional(cabecalhos, linhas))

    # Observações / Análise / Justificativa
    if observacoes:
        elementos.append(Spacer(1, 3 * mm))
        elementos.append(_secao_titulo(estilos, "Observações e Decisões"))
        for rotulo, valor in observacoes:
            elementos.extend(_campo_info(estilos, rotulo, valor))

    # Rodapé
    elementos.extend(_rodape())

    doc.build(elementos)
    return destino


def _escapar(valor) -> str:
    """Escapa caracteres especiais de XML/HTML usados pelo reportlab (Paragraph usa markup)."""
    if valor is None:
        return ""
    return (
        str(valor)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
