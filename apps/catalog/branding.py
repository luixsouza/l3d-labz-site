"""Padronização de imagem de produto com a identidade visual L3D Labz.

Como não temos a foto real do produto, geramos um card consistente: gradiente
radial verde-Luigi, um "tile" central arredondado com o monograma do produto na
cor de acento da categoria, o nome embaixo e o wordmark L3D Labz. Todos os
produtos ganham o mesmo enquadramento → identidade única.

Pipeline isolado (só Pillow/numpy) — reutilizável por qualquer comando/serviço.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# tons do verde Luigi (fundo claro e elegante)
_BG_CENTRO = (246, 251, 247)
_BG_BORDA = (210, 232, 216)
_TEXTO = (22, 32, 26)
_MUTED = (92, 107, 96)


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _fonte(tamanho: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidatos = (
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"] if bold
        else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    )
    for caminho in candidatos:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except OSError:
            continue
    return ImageFont.load_default(size=tamanho)  # Pillow >= 10.1: escalável


def _gradiente_radial(size: int) -> Image.Image:
    yy, xx = np.mgrid[0:size, 0:size]
    c = size / 2.0
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (size * 0.72)
    d = np.clip(d, 0.0, 1.0)[..., None]
    centro = np.array(_BG_CENTRO)
    borda = np.array(_BG_BORDA)
    arr = (centro * (1 - d) + borda * d).astype("uint8")
    return Image.fromarray(arr, "RGB")


def _monograma(nome: str) -> str:
    partes = [p for p in nome.split() if p]
    if len(partes) >= 2:
        return (partes[0][:1] + partes[1][:1]).upper()
    return nome[:2].upper()


def _quebrar(draw, texto, fonte, largura_max) -> list[str]:
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if draw.textlength(teste, font=fonte) <= largura_max:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas[:3]


def gerar_card(nome: str, accent: str = "#2FA84F", tamanho: int = 800) -> bytes:
    """Devolve PNG (bytes) com o card padronizado do produto."""
    img = _gradiente_radial(tamanho)
    draw = ImageDraw.Draw(img)
    acc = _rgb(accent)

    # tile central arredondado na cor da categoria
    tile = int(tamanho * 0.42)
    tx = (tamanho - tile) // 2
    ty = int(tamanho * 0.17)
    draw.rounded_rectangle(
        [tx, ty, tx + tile, ty + tile], radius=int(tile * 0.22), fill=acc
    )
    # leve brilho no topo do tile
    draw.rounded_rectangle(
        [tx, ty, tx + tile, ty + int(tile * 0.5)], radius=int(tile * 0.22),
        fill=tuple(min(255, int(v * 1.12)) for v in acc),
    )
    draw.rounded_rectangle(
        [tx, ty + int(tile * 0.34), tx + tile, ty + tile], radius=int(tile * 0.22), fill=acc
    )

    # monograma centralizado no tile
    mono = _monograma(nome)
    f_mono = _fonte(int(tile * 0.46), bold=True)
    bbox = draw.textbbox((0, 0), mono, font=f_mono)
    mw, mh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (tamanho / 2 - mw / 2 - bbox[0], ty + tile / 2 - mh / 2 - bbox[1]),
        mono, font=f_mono, fill=(255, 255, 255),
    )

    # nome do produto (centralizado, até 3 linhas)
    f_nome = _fonte(int(tamanho * 0.058), bold=True)
    linhas = _quebrar(draw, nome, f_nome, tamanho * 0.82)
    y = int(tamanho * 0.66)
    for ln in linhas:
        w = draw.textlength(ln, font=f_nome)
        draw.text((tamanho / 2 - w / 2, y), ln, font=f_nome, fill=_TEXTO)
        y += int(tamanho * 0.07)

    # wordmark L3D Labz
    f_mark = _fonte(int(tamanho * 0.038), bold=True)
    marca = "L3D Labz"
    w = draw.textlength(marca, font=f_mark)
    draw.text((tamanho / 2 - w / 2, int(tamanho * 0.9)), marca, font=f_mark, fill=acc)
    # impresso em 3D — subtítulo
    f_sub = _fonte(int(tamanho * 0.026))
    sub = "impresso em 3D sob demanda"
    ws = draw.textlength(sub, font=f_sub)
    draw.text((tamanho / 2 - ws / 2, int(tamanho * 0.945)), sub, font=f_sub, fill=_MUTED)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
