"""Geração do PDF de orçamento da L3D Labz usando reportlab (layout premium).

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
from datetime import date, timedelta

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ---- paleta L3D Labz ----
_G_LIGHT = colors.HexColor("#34B85A")
_G = colors.HexColor("#2FA84F")
_G_DARK = colors.HexColor("#1B7E37")
_G_SOFT = colors.HexColor("#EAF7EE")
_INK = colors.HexColor("#0F172A")
_TEXTO = colors.HexColor("#334155")
_MUTED = colors.HexColor("#64748B")
_FAINT = colors.HexColor("#94A3B8")
_HAIR = colors.HexColor("#E2E8F0")
_WMARK = colors.HexColor("#F1F6F2")
_WHITE = colors.white
_WHITE_DIM = colors.HexColor("#D7F0DE")

# ---- marca / contatos (de settings.SITE quando disponível) ----
_SITE = getattr(settings, "SITE", {})
_NAME = _SITE.get("name", "L3D Labz")
_TAG = _SITE.get("tagline", "Impressão 3D sob demanda")
_IG_URL = _SITE.get("instagram", "")
_IG = ("@" + _IG_URL.rstrip("/").split("/")[-1]) if _IG_URL else ""
_URL = "l3dlabz.com.br"
_MAIL = "contato@l3dlabz.com.br"

_PW, _PH = A4
_ML = _MR = 1.8 * cm
_CW = _PW - _ML - _MR
_BAND = 3.5 * cm
_FOOT = 1.45 * cm


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


def _monograma(c, x, ytop, size, sq_color, txt_color):
    c.saveState()
    c.setFillColor(sq_color)
    c.roundRect(x, ytop - size, size, size, size * 0.24, stroke=0, fill=1)
    c.setFillColor(txt_color)
    c.setFont("Helvetica-Bold", size * 0.33)
    c.drawCentredString(x + size / 2, ytop - size / 2 - size * 0.11, "L3D")
    c.restoreState()


def _decor(c, doc):
    """Faixas full-bleed (cabeçalho com gradiente + rodapé escuro) e marca d'água."""
    c.saveState()
    # marca d'água
    c.setFillColor(_WMARK)
    c.setFont("Helvetica-Bold", 170)
    c.drawCentredString(_PW / 2, 7.5 * cm, "L3D")
    # faixa de cabeçalho (gradiente verde)
    c.saveState()
    p = c.beginPath()
    p.rect(0, _PH - _BAND, _PW, _BAND)
    c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(0, _PH, _PW, _PH - _BAND, (_G_LIGHT, _G_DARK), (0, 1), extend=True)
    c.restoreState()
    # monograma branco
    msz = 1.55 * cm
    myt = _PH - (_BAND - msz) / 2
    _monograma(c, _ML, myt, msz, _WHITE, _G_DARK)
    tx = _ML + msz + 0.5 * cm
    c.setFillColor(_WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(tx, _PH - _BAND / 2 + 0.08 * cm, _NAME)
    c.setFillColor(_WHITE_DIM)
    c.setFont("Helvetica", 8.5)
    c.drawString(tx, _PH - _BAND / 2 - 0.42 * cm, _TAG)
    # direita: ORÇAMENTO + pill com nº
    rx = _PW - _MR
    c.setFillColor(_WHITE)
    c.setFont("Helvetica-Bold", 15)
    c.drawRightString(rx, _PH - _BAND / 2 + 0.45 * cm, "O R Ç A M E N T O")
    rtxt = doc._ref
    c.setFont("Helvetica-Bold", 9)
    tw = c.stringWidth(rtxt, "Helvetica-Bold", 9)
    pill_w = tw + 0.7 * cm
    pill_h = 0.52 * cm
    px = rx - pill_w
    py = _PH - _BAND / 2 - 0.28 * cm
    c.setFillColor(_WHITE)
    c.roundRect(px, py, pill_w, pill_h, pill_h / 2, stroke=0, fill=1)
    c.setFillColor(_G_DARK)
    c.drawCentredString(px + pill_w / 2, py + 0.15 * cm, rtxt)
    # faixa de rodapé
    c.setFillColor(_INK)
    c.rect(0, 0, _PW, _FOOT, fill=1, stroke=0)
    c.setStrokeColor(_G)
    c.setLineWidth(2)
    c.line(0, _FOOT, _PW, _FOOT)
    c.setFillColor(_WHITE)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(_ML, _FOOT / 2 - 0.08 * cm, "Obrigado pela preferência.")
    c.setFillColor(_FAINT)
    c.setFont("Helvetica", 8)
    contatos = "   ·   ".join(t for t in (_URL, _IG, _MAIL) if t)
    c.drawRightString(_PW - _MR, _FOOT / 2 - 0.08 * cm, contatos)
    c.restoreState()


def gerar_orcamento_pdf(dados: dict) -> bytes:
    """Gera e retorna os bytes do PDF de orçamento da L3D Labz (layout premium).

    `dados` deve conter APENAS (sem custos internos):
      cliente_nome, peca_descricao, quantidade, prazo_entrega,
      observacoes, preco_venda, total.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=_ML, rightMargin=_MR,
        topMargin=_BAND + 0.8 * cm, bottomMargin=_FOOT + 0.6 * cm,
        title="Orçamento L3D Labz", author="L3D Labz",
    )
    doc._ref = _ref_orcamento(dados.get("cliente_nome", ""), date.today())
    hoje = date.today()
    val = hoje + timedelta(days=7)

    s_lblm = ParagraphStyle("lm", fontName="Helvetica-Bold", fontSize=7.5, textColor=_MUTED, leading=11)
    s_th = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8.5, textColor=_WHITE, leading=11)
    s_thr = ParagraphStyle("thr", parent=s_th, alignment=TA_RIGHT)
    s_td = ParagraphStyle("td", fontName="Helvetica", fontSize=9.5, textColor=_TEXTO, leading=13)
    s_tdr = ParagraphStyle("tdr", parent=s_td, alignment=TA_RIGHT)
    s_obs = ParagraphStyle("o", fontName="Helvetica", fontSize=9.5, textColor=_TEXTO, leading=14)

    story = []

    # ---- Faturar para / Detalhes ----
    detalhes = Table(
        [[Paragraph("EMISSÃO", s_lblm), Paragraph(hoje.strftime("%d/%m/%Y"), s_tdr)],
         [Paragraph("VALIDADE", s_lblm), Paragraph(val.strftime("%d/%m/%Y"), s_tdr)],
         [Paragraph("PRAZO", s_lblm), Paragraph(dados.get("prazo_entrega", "—"), s_tdr)]],
        colWidths=[_CW * 0.20, _CW * 0.20],
        style=TableStyle([
            ("LINEBELOW", (0, 0), (-1, -2), 0.5, _HAIR),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
    topo = Table(
        [[Paragraph('<font name="Helvetica-Bold" size="7.5" color="#1B7E37">FATURAR PARA</font><br/>'
                    f'<font name="Helvetica-Bold" size="14" color="#0F172A">{dados.get("cliente_nome","—")}</font>',
                    ParagraphStyle("fp", leading=18)),
          detalhes]],
        colWidths=[_CW * 0.58, _CW * 0.42],
        style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                          ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(topo)
    story.append(Spacer(1, 0.6 * cm))

    # ---- tabela de itens (sem custos internos) ----
    qtd = dados.get("quantidade", 1)
    pu = dados.get("preco_venda", 0.0)
    total = dados.get("total", 0.0)
    itens = Table(
        [[Paragraph("DESCRIÇÃO", s_th), Paragraph("QTD", s_thr),
          Paragraph("PREÇO UNIT.", s_thr), Paragraph("TOTAL", s_thr)],
         [Paragraph(dados.get("peca_descricao", "—"), s_td), Paragraph(str(qtd), s_tdr),
          Paragraph(_format_brl(pu), s_tdr), Paragraph(_format_brl(total), s_tdr)]],
        colWidths=[_CW * 0.50, _CW * 0.12, _CW * 0.19, _CW * 0.19],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _G), ("ROUNDEDCORNERS", [5, 5, 0, 0]),
            ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 10), ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 1), (-1, -1), 0.6, _HAIR), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
    story.append(itens)
    story.append(Spacer(1, 0.45 * cm))

    # ---- resumo: subtotal + total card (à direita) ----
    sub_row = Table(
        [[Paragraph("Subtotal", ParagraphStyle("sl", fontName="Helvetica", fontSize=9.5,
                                               textColor=_MUTED, alignment=TA_RIGHT)),
          Paragraph(_format_brl(total), ParagraphStyle("sv", fontName="Helvetica", fontSize=9.5,
                                                       textColor=_TEXTO, alignment=TA_RIGHT))]],
        colWidths=[4.1 * cm, 4.1 * cm],
        style=TableStyle([("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                          ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    tot_card = Table(
        [[Paragraph('<font name="Helvetica-Bold" size="9" color="#FFFFFF">TOTAL</font>',
                    ParagraphStyle("tl", leading=12)),
          Paragraph(f'<font name="Helvetica-Bold" size="15" color="#FFFFFF">{_format_brl(total)}</font>',
                    ParagraphStyle("tv", alignment=TA_RIGHT, leading=19))]],
        colWidths=[2.4 * cm, 5.8 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _G_DARK), ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
    resumo = Table([[sub_row], [tot_card]], colWidths=[8.2 * cm], hAlign="RIGHT",
                   style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                     ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, 0), 2)]))
    story.append(resumo)

    # ---- condições & observações ----
    obs = (dados.get("observacoes") or "").strip()
    story.append(Spacer(1, 0.7 * cm))
    cond = ("Validade de 7 dias corridos a partir da emissão. Valores em reais (BRL). "
            "Produção iniciada após aprovação do orçamento.")
    if obs:
        cond = obs + "<br/><br/>" + cond
    bloco = Table(
        [[Paragraph('<font name="Helvetica-Bold" size="7.5" color="#1B7E37">CONDIÇÕES &amp; OBSERVAÇÕES</font>',
                    ParagraphStyle("cl", leading=12, spaceAfter=4))],
         [Paragraph(cond, s_obs)]],
        colWidths=[_CW],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _G_SOFT), ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (0, 0), 12), ("BOTTOMPADDING", (0, 0), (0, 0), 2),
            ("TOPPADDING", (0, 1), (0, 1), 0), ("BOTTOMPADDING", (0, 1), (0, 1), 12),
        ]))
    story.append(bloco)

    doc.build(story, onFirstPage=_decor, onLaterPages=_decor)
    return buf.getvalue()
