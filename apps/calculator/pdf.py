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
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing, Rect, String
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


def _qr_drawing(url: str, lado: float) -> Drawing | None:
    """Retorna um Drawing quadrado com QR code apontando para `url`, ou None se url vazio.

    Usa reportlab.graphics.barcode.qr (já incluído no reportlab — zero dep nova).
    Cor padrão preta sobre fundo branco: legível por qualquer leitor de câmera.
    """
    if not url:
        return None
    widget = qr.QrCodeWidget(url)
    b = widget.getBounds()  # (x0, y0, x1, y1) do widget em pontos nativos
    w, h = b[2] - b[0], b[3] - b[1]
    if w == 0 or h == 0:
        return None
    d = Drawing(lado, lado, transform=[lado / w, 0, 0, lado / h, 0, 0])
    d.add(widget)
    return d


def _selo_drawing(lado: float) -> Drawing:
    """Retorna um Drawing quadrado com o monograma 'L3D' em verde para uso em células de tabela.

    Equivalente visual a _monograma mas como Flowable Drawing (compatível com platypus/Table).
    Não depende de nenhum dado externo — é sempre renderizado.
    """
    sq_color = _G        # verde L3D
    txt_color = _WHITE   # texto branco
    radius = lado * 0.24
    d = Drawing(lado, lado)
    rect = Rect(0, 0, lado, lado, rx=radius, ry=radius,
                fillColor=sq_color, strokeColor=None, strokeWidth=0)
    d.add(rect)
    font_size = lado * 0.33
    # String fica no centro; y ajustado para o meio menos meia altura do glifo
    txt = String(lado / 2, lado / 2 - font_size * 0.38,
                 "L3D",
                 fontName="Helvetica-Bold",
                 fontSize=font_size,
                 fillColor=txt_color,
                 textAnchor="middle")
    d.add(txt)
    return d


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

    # Selo gráfico "L3D" antes da descrição (melhoria 4): Drawing como Flowable na célula.
    # Sub-tabela [selo+gap | descrição] para alinhar verticalmente ao centro.
    #
    # ATENÇÃO: a tabela `itens` aplica LEFTPADDING=10 + RIGHTPADDING=10 na coluna DESCRIÇÃO,
    # portanto o espaço interno disponível para a sub-tabela é _DESCR_CW − 20pt.
    # Os colWidths da sub-tabela devem somar ≤ _SUB_CW para evitar overflow silencioso.
    #
    # GAP: o respiro entre o Drawing do selo e o texto é incorporado diretamente no colWidth
    # da coluna do selo (_SELO_LADO + _GAP_BADGE), sem usar RIGHTPADDING, para evitar que
    # o reportlab comprima o Drawing abaixo de seu tamanho declarado.
    _ITENS_PAD = 10        # padding lateral de cada célula na tabela itens (pontos)
    _SELO_LADO = 1.0 * cm
    _DESCR_CW = _CW * 0.50   # largura original da coluna DESCRIÇÃO
    _GAP_BADGE = 8         # pontos de respiro selo → texto (aprovação 260616)
    _SUB_CW = _DESCR_CW - 2 * _ITENS_PAD   # espaço real disponível após paddings externos
    _BADGE_COL = _SELO_LADO + _GAP_BADGE    # coluna do badge inclui o gap como espaço extra
    _TEXTO_CW = _SUB_CW - _BADGE_COL       # coluna texto: espaço restante
    selo = _selo_drawing(_SELO_LADO)
    celula_desc_data = Table(
        [[selo, Paragraph(dados.get("peca_descricao", "—"), s_td)]],
        colWidths=[_BADGE_COL, _TEXTO_CW],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
    itens = Table(
        [[Paragraph("DESCRIÇÃO", s_th), Paragraph("QTD", s_thr),
          Paragraph("PREÇO UNIT.", s_thr), Paragraph("TOTAL", s_thr)],
         [celula_desc_data, Paragraph(str(qtd), s_tdr),
          Paragraph(_format_brl(pu), s_tdr), Paragraph(_format_brl(total), s_tdr)]],
        colWidths=[_DESCR_CW, _CW * 0.12, _CW * 0.19, _CW * 0.19],
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

    # ---- CTA "Para aprovar" + QR Instagram ----
    # Exibido entre o resumo e o bloco de condições.
    # Degrada para só texto quando _IG_URL estiver vazio.
    _QR_LADO = 2.4 * cm
    qr_d = _qr_drawing(_IG_URL, _QR_LADO)
    s_cta_h = ParagraphStyle("ctah", fontName="Helvetica-Bold", fontSize=7.5,
                              textColor=_G_DARK, leading=11, spaceAfter=3)
    s_cta_b = ParagraphStyle("ctab", fontName="Helvetica", fontSize=9.5,
                              textColor=_TEXTO, leading=14)
    if _IG:
        cta_txt = (
            f'Gostou do orçamento? Fale com a gente no Instagram '
            f'<font name="Helvetica-Bold" color="#1B7E37">{_IG}</font> '
            f'ou aponte a câmera no QR ao lado.'
        )
    else:
        cta_txt = "Gostou do orçamento? Entre em contato para aprovar."
    cta_texto_col = [
        Paragraph("PARA APROVAR", s_cta_h),
        Paragraph(cta_txt, s_cta_b),
    ]
    if qr_d is not None:
        # duas colunas: texto | QR
        cta_bloco = Table(
            [[cta_texto_col, qr_d]],
            colWidths=[_CW - _QR_LADO - 0.4 * cm, _QR_LADO],
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
    else:
        # sem QR — coluna única
        cta_bloco = Table(
            [[cta_texto_col]],
            colWidths=[_CW],
            style=TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
    story.append(Spacer(1, 0.55 * cm))
    story.append(cta_bloco)

    # ---- condições & observações ----
    # Ordem: observações do cliente (se houver) → política de pagamento → validade/condições gerais.
    obs = (dados.get("observacoes") or "").strip()
    story.append(Spacer(1, 0.7 * cm))
    _PGTO = (
        '<font name="Helvetica-Bold">Sinal de 50% para iniciar a produção, '
        'saldo na entrega.</font>'
    )
    cond_base = ("Validade de 7 dias corridos a partir da emissão. Valores em reais (BRL). "
                 "Produção iniciada após aprovação do orçamento.")
    # monta o parágrafo de condições com pagamento antes da validade
    if obs:
        cond = obs + "<br/><br/>" + _PGTO + "<br/>" + cond_base
    else:
        cond = _PGTO + "<br/>" + cond_base
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
