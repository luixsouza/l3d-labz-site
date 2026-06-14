"""Geração do PDF de orçamento da L3D Labz usando reportlab.

IMPORTANTE — segurança (decisão D-03 / T-calc-02):
O PDF é o documento do CLIENTE e contém SOMENTE informações públicas:
  - Cabeçalho L3D Labz
  - Nome do cliente
  - Descrição da peça
  - Quantidade
  - Prazo de entrega
  - Observações
  - Preço unitário (preco_venda)
  - Total (preco_venda × quantidade)

PROIBIDO incluir: custo_material, custo_energia, custo_depreciacao,
custo_maoobra, subtotal, ajuste_falha, custo_total, taxa_falha ou margem.
Os custos internos jamais entram neste módulo — a view envia só o dict
{cliente_nome, peca_descricao, quantidade, prazo_entrega, observacoes,
 preco_venda, total}.
"""
from __future__ import annotations

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Identidade visual L3D Labz
_VERDE_L3D = colors.HexColor("#2FA84F")
_VERDE_ESCURO = colors.HexColor("#1E8C3E")
_CINZA_TEXTO = colors.HexColor("#374151")
_CINZA_CLARO = colors.HexColor("#F3F4F6")
_BRANCO = colors.white


def _format_brl(valor: float) -> str:
    """Formata float como moeda BRL sem depender de locale do SO."""
    # usa a mesma lógica que apps/core/formatting.py (compatível com ambientes sem locale pt-br)
    try:
        inteiro = int(valor)
        centavos = round((valor - inteiro) * 100)
        partes: list[str] = []
        n = inteiro
        while n >= 1000:
            partes.insert(0, f"{n % 1000:03d}")
            n //= 1000
        partes.insert(0, str(n))
        return f"R$ {'.'.join(partes)},{centavos:02d}"
    except Exception:
        return f"R$ {valor:.2f}"


def gerar_orcamento_pdf(dados: dict) -> bytes:
    """Gera e retorna os bytes do PDF de orçamento da L3D Labz.

    `dados` deve conter APENAS (sem custos internos):
      cliente_nome, peca_descricao, quantidade, prazo_entrega,
      observacoes, preco_venda, total.
    """
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
        title="Orçamento L3D Labz",
        author="L3D Labz",
    )

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(
        "normal_l3d",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=_CINZA_TEXTO,
        leading=14,
    )
    style_titulo = ParagraphStyle(
        "titulo_l3d",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=_VERDE_L3D,
        spaceAfter=4,
    )
    style_subtitulo = ParagraphStyle(
        "subtitulo_l3d",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#6B7280"),
    )
    style_label = ParagraphStyle(
        "label_l3d",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=1,
    )
    style_valor = ParagraphStyle(
        "valor_l3d",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        textColor=_CINZA_TEXTO,
        spaceAfter=8,
    )
    style_obs = ParagraphStyle(
        "obs_l3d",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=_CINZA_TEXTO,
        leading=14,
        spaceAfter=4,
    )

    story = []

    # ---- cabeçalho ----
    story.append(Paragraph("L3D Labz", style_titulo))
    story.append(Paragraph("Impressão 3D sob demanda", style_subtitulo))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=_VERDE_L3D))
    story.append(Spacer(1, 0.4 * cm))

    # ---- número do orçamento e data ----
    hoje = date.today().strftime("%d/%m/%Y")
    story.append(Paragraph(
        f"<b>ORÇAMENTO</b> &nbsp;·&nbsp; Emitido em {hoje}",
        ParagraphStyle(
            "meta_l3d",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#9CA3AF"),
        ),
    ))
    story.append(Spacer(1, 0.7 * cm))

    # ---- dados do cliente ----
    story.append(Paragraph("CLIENTE", style_label))
    story.append(Paragraph(dados.get("cliente_nome", "—"), style_valor))

    story.append(Paragraph("DESCRIÇÃO DA PEÇA", style_label))
    story.append(Paragraph(dados.get("peca_descricao", "—"), style_valor))

    story.append(Paragraph("PRAZO DE ENTREGA", style_label))
    story.append(Paragraph(dados.get("prazo_entrega", "—"), style_valor))

    obs = dados.get("observacoes", "").strip()
    if obs:
        story.append(Paragraph("OBSERVAÇÕES", style_label))
        story.append(Paragraph(obs, style_obs))

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB")))
    story.append(Spacer(1, 0.5 * cm))

    # ---- tabela de precificação (sem custos internos) ----
    quantidade = dados.get("quantidade", 1)
    preco_venda = dados.get("preco_venda", 0.0)
    total = dados.get("total", 0.0)

    tabela_dados = [
        [
            Paragraph("<b>Descrição</b>", style_normal),
            Paragraph("<b>Qtd.</b>", style_normal),
            Paragraph("<b>Preço unitário</b>", style_normal),
            Paragraph("<b>Total</b>", style_normal),
        ],
        [
            Paragraph(dados.get("peca_descricao", "—"), style_normal),
            Paragraph(str(quantidade), style_normal),
            Paragraph(_format_brl(preco_venda), style_normal),
            Paragraph(_format_brl(total), style_normal),
        ],
    ]

    tabela = Table(
        tabela_dados,
        colWidths=[8 * cm, 2 * cm, 4 * cm, 4 * cm],
        style=TableStyle([
            # cabeçalho
            ("BACKGROUND", (0, 0), (-1, 0), _VERDE_L3D),
            ("TEXTCOLOR", (0, 0), (-1, 0), _BRANCO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("LEFTPADDING", (0, 0), (-1, 0), 8),
            ("RIGHTPADDING", (0, 0), (-1, 0), 8),
            # corpo
            ("BACKGROUND", (0, 1), (-1, -1), _CINZA_CLARO),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("TOPPADDING", (0, 1), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
            ("LEFTPADDING", (0, 1), (-1, -1), 8),
            ("RIGHTPADDING", (0, 1), (-1, -1), 8),
            # borda
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("LINEAFTER", (0, 0), (-2, -1), 0.5, colors.HexColor("#D1D5DB")),
        ]),
    )
    story.append(tabela)
    story.append(Spacer(1, 0.5 * cm))

    # ---- total em destaque ----
    total_tabela = Table(
        [[Paragraph("TOTAL", style_label), Paragraph(f"<b>{_format_brl(total)}</b>", ParagraphStyle(
            "total_val",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=_VERDE_ESCURO,
        ))]],
        colWidths=[14 * cm, 4 * cm],
        style=TableStyle([
            ("ALIGN", (0, 0), (0, 0), "RIGHT"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]),
    )
    story.append(total_tabela)

    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB")))
    story.append(Spacer(1, 0.4 * cm))

    # ---- rodapé ----
    story.append(Paragraph(
        "Este orçamento tem validade de 7 dias corridos a partir da data de emissão. "
        "Para dúvidas ou aprovação, entre em contato com a L3D Labz.",
        ParagraphStyle(
            "rodape_l3d",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#9CA3AF"),
        ),
    ))

    doc.build(story)
    return buf.getvalue()
