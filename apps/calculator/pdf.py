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

import hashlib
import io
from datetime import date

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ---- paleta L3D Labz (verde Luigi + neutros) ----
_VERDE = colors.HexColor("#2FA84F")
_VERDE_ESC = colors.HexColor("#1E8C3E")
_VERDE_SOFT = colors.HexColor("#EAF7EE")
_INK = colors.HexColor("#111827")
_TEXTO = colors.HexColor("#374151")
_MUTED = colors.HexColor("#6B7280")
_FAINT = colors.HexColor("#9CA3AF")
_HAIR = colors.HexColor("#E5E7EB")
_CARD = colors.HexColor("#F9FAFB")

# ---- marca / contatos (do settings.SITE quando disponível) ----
_SITE = getattr(settings, "SITE", {})
_NAME = _SITE.get("name", "L3D Labz")
_TAG = _SITE.get("tagline", "Impressão 3D sob demanda")
_IG_URL = _SITE.get("instagram", "")
_IG = ("@" + _IG_URL.rstrip("/").split("/")[-1]) if _IG_URL else ""
_URL = "l3dlabz.com.br"
_MAIL = "contato@l3dlabz.com.br"

_PAGE_W, _PAGE_H = A4
_ML = _MR = 2 * cm
_CONTENT_W = _PAGE_W - _ML - _MR


def _format_brl(valor: float) -> str:
    """Formata float como moeda BRL sem depender de locale do SO."""
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


def _ref_orcamento(nome: str, d: date) -> str:
    """Nº de orçamento determinístico a partir do nome do cliente + data."""
    h = int(hashlib.md5((nome or "cliente").encode("utf-8")).hexdigest(), 16) % 10000
    return f"ORC-{d:%Y%m%d}-{h:04d}"


def _monograma(canvas, x, y_top, size):
    """Marca minimalista: quadrado verde arredondado com 'L3D' branco."""
    canvas.saveState()
    canvas.setFillColor(_VERDE)
    canvas.roundRect(x, y_top - size, size, size, size * 0.22, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", size * 0.34)
    canvas.drawCentredString(x + size / 2, y_top - size / 2 - size * 0.12, "L3D")
    canvas.restoreState()


def _cabecalho_rodape(canvas, doc):
    """Letterhead (logo + marca + nº/data) e rodapé (contatos) em cada página."""
    canvas.saveState()
    # ---------- CABEÇALHO ----------
    top = _PAGE_H - 1.7 * cm
    marca = 1.55 * cm
    _monograma(canvas, _ML, top, marca)
    tx = _ML + marca + 0.45 * cm
    canvas.setFillColor(_INK)
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(tx, top - 0.62 * cm, _NAME)
    canvas.setFillColor(_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(tx, top - 1.12 * cm, _TAG)
    # bloco direito: ORÇAMENTO / nº / data
    rx = _PAGE_W - _MR
    canvas.setFillColor(_VERDE)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawRightString(rx, top - 0.55 * cm, "O R Ç A M E N T O")
    canvas.setFillColor(_MUTED)
    canvas.setFont("Helvetica", 8.5)
    canvas.drawRightString(rx, top - 1.08 * cm, doc._ref)
    canvas.setFillColor(_FAINT)
    canvas.drawRightString(rx, top - 1.48 * cm, f"Emitido em {doc._hoje}")
    # hairline verde
    hy = top - 1.95 * cm
    canvas.setStrokeColor(_VERDE)
    canvas.setLineWidth(1.1)
    canvas.line(_ML, hy, _PAGE_W - _MR, hy)

    # ---------- RODAPÉ ----------
    fy = 1.6 * cm
    canvas.setStrokeColor(_HAIR)
    canvas.setLineWidth(0.8)
    canvas.line(_ML, fy, _PAGE_W - _MR, fy)
    canvas.setFillColor(_FAINT)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(_ML, fy - 0.42 * cm, f"{_NAME} · Impressão 3D sob demanda")
    contatos = "   ·   ".join(p for p in (_URL, _IG, _MAIL) if p)
    canvas.drawRightString(_PAGE_W - _MR, fy - 0.42 * cm, contatos)
    canvas.restoreState()


def gerar_orcamento_pdf(dados: dict) -> bytes:
    """Gera e retorna os bytes do PDF de orçamento da L3D Labz.

    `dados` deve conter APENAS (sem custos internos):
      cliente_nome, peca_descricao, quantidade, prazo_entrega,
      observacoes, preco_venda, total.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=_ML, rightMargin=_MR,
        topMargin=3.1 * cm, bottomMargin=2.2 * cm,
        title="Orçamento L3D Labz", author="L3D Labz",
    )
    doc._hoje = date.today().strftime("%d/%m/%Y")
    doc._ref = _ref_orcamento(dados.get("cliente_nome", ""), date.today())

    lbl = ParagraphStyle("lbl", fontName="Helvetica-Bold", fontSize=9,
                         textColor=_MUTED, leading=12)
    th = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9,
                        textColor=colors.white, leading=12)
    th_r = ParagraphStyle("th_r", parent=th, alignment=TA_RIGHT)
    td = ParagraphStyle("td", fontName="Helvetica", fontSize=10,
                        textColor=_TEXTO, leading=14)
    td_r = ParagraphStyle("td_r", parent=td, alignment=TA_RIGHT)
    obs_s = ParagraphStyle("obs", fontName="Helvetica", fontSize=10,
                           textColor=_TEXTO, leading=15)

    def _cell(label, valor):
        return Paragraph(
            f'<font name="Helvetica-Bold" size="7.5" color="#6B7280">{label}</font><br/>'
            f'<font name="Helvetica" size="11.5" color="#111827">{valor}</font>',
            ParagraphStyle("c", leading=15))

    story = []

    # ---- card de dados (2x2) ----
    card = Table(
        [[_cell("CLIENTE", dados.get("cliente_nome", "—")),
          _cell("PRAZO DE ENTREGA", dados.get("prazo_entrega", "—"))],
         [_cell("DESCRIÇÃO DA PEÇA", dados.get("peca_descricao", "—")),
          _cell("VALIDADE", "7 dias corridos")]],
        colWidths=[_CONTENT_W * 0.62, _CONTENT_W * 0.38],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _CARD),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
    story.append(card)
    story.append(Spacer(1, 0.7 * cm))

    # ---- tabela de itens (sem custos internos) ----
    qtd = dados.get("quantidade", 1)
    pu = dados.get("preco_venda", 0.0)
    total = dados.get("total", 0.0)
    itens = Table(
        [[Paragraph("DESCRIÇÃO", th), Paragraph("QTD", th_r),
          Paragraph("PREÇO UNIT.", th_r), Paragraph("TOTAL", th_r)],
         [Paragraph(dados.get("peca_descricao", "—"), td), Paragraph(str(qtd), td_r),
          Paragraph(_format_brl(pu), td_r), Paragraph(_format_brl(total), td_r)]],
        colWidths=[_CONTENT_W * 0.48, _CONTENT_W * 0.12, _CONTENT_W * 0.20, _CONTENT_W * 0.20],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _VERDE),
            ("TOPPADDING", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 9),
            ("TOPPADDING", (0, 1), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 11),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 1), (-1, -1), 0.6, _HAIR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
    story.append(itens)
    story.append(Spacer(1, 0.5 * cm))

    # ---- total em destaque (à direita) ----
    total_str = _format_brl(total).replace(" ", " ")  # nbsp: nao quebra "R$ valor"
    tot_box = Table(
        [[Paragraph('<font name="Helvetica-Bold" size="9" color="#1E8C3E">TOTAL</font>', lbl),
          Paragraph(f'<font name="Helvetica-Bold" size="15" color="#1E8C3E">{total_str}</font>',
                    ParagraphStyle("tv", alignment=TA_RIGHT, leading=19))]],
        colWidths=[3.0 * cm, 4.8 * cm],
        hAlign="RIGHT",
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _VERDE_SOFT),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
    story.append(tot_box)

    # ---- observações (opcional) ----
    obs = (dados.get("observacoes") or "").strip()
    if obs:
        story.append(Spacer(1, 0.7 * cm))
        story.append(Paragraph(
            '<font name="Helvetica-Bold" size="7.5" color="#6B7280">OBSERVAÇÕES</font>',
            ParagraphStyle("obs_lbl", leading=12, spaceAfter=4)))
        story.append(Paragraph(obs, obs_s))

    doc.build(story, onFirstPage=_cabecalho_rodape, onLaterPages=_cabecalho_rodape)
    return buf.getvalue()
