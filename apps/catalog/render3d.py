"""Render padronizado do modelo 3D -> foto de produto estilo Nike/Apple.

matplotlib (Agg, headless, SEM OpenGL) sombreia a malha num ângulo/luz fixos; o
modelo é composto sobre um fundo quase-branco com uma sombra de contato suave.
SEM texto na imagem (nome/preço ficam no card) — produto centralizado, muito
respiro, look minimalista e consistente entre todos os itens.

Cor do material: derivada deterministicamente do slug/categoria (hash estável)
sobre a paleta L3D Labz. Aceita override via parâmetro `accent`. Iluminação
key + fill para dar contraste real e evitar renderes planos/brancos.
"""
from __future__ import annotations

import hashlib
import io

import matplotlib
matplotlib.use("Agg")  # noqa: E402  (headless, antes do pyplot)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

# ângulo padrão (objetos "em pé"); planos usam vista mais de cima (_VIEW_FLAT)
_VIEW = dict(elev=22, azim=-58)
_VIEW_FLAT = dict(elev=58, azim=-40)

# ---- Iluminação key + fill ----
# Key light: diagonal superior frontal (dominante)
_KEY = np.array([0.40, 0.55, 0.74])
_KEY = _KEY / np.linalg.norm(_KEY)
_KEY_INT = 0.78     # intensidade da key

# Fill light: oposta/inferior (suaviza sombras, dá volume)
_FILL = np.array([-0.55, -0.30, 0.40])
_FILL = _FILL / np.linalg.norm(_FILL)
_FILL_INT = 0.28    # intensidade do fill (mais fraca que a key)

_AMB = 0.22         # ambiente base (mais baixo = mais contraste)

_FACES_RENDER = 13000

# ---- Paleta L3D Labz — cores determinísticas por produto ----
# verde Luigi (marca), azul acento, coral vivo, âmbar, lilás, teal, terra
_PALETA = [
    np.array([0.18, 0.66, 0.31]),   # verde L3D
    np.array([0.17, 0.65, 0.88]),   # azul L3D
    np.array([0.91, 0.35, 0.25]),   # coral
    np.array([0.88, 0.72, 0.18]),   # âmbar
    np.array([0.56, 0.40, 0.88]),   # lilás
    np.array([0.15, 0.72, 0.68]),   # teal
    np.array([0.72, 0.44, 0.20]),   # terra cotta
    np.array([0.22, 0.38, 0.82]),   # azul escuro
]

# fundo Apple-ish (#fbfbfd -> #f2f3f5)
_BG_TOP = np.array([251, 251, 253])
_BG_BOT = np.array([238, 239, 242])


def _cor_por_nome(nome: str) -> np.ndarray:
    """Deriva cor determinística do slug/nome via hash SHA-1.

    Mesma entrada sempre retorna o mesmo índice na paleta.
    """
    h = int(hashlib.sha1(nome.encode(), usedforsecurity=False).hexdigest(), 16)
    return _PALETA[h % len(_PALETA)]


def cor_rgba_por_nome(nome: str) -> list[float]:
    """RGBA [0-1] da paleta p/ material PBR do GLB — mesma cor da foto do produto."""
    return [*_cor_por_nome(nome).tolist(), 1.0]


def _fundo(px: int) -> Image.Image:
    t = np.linspace(0.0, 1.0, px)[:, None]
    col = (_BG_TOP[None, :] * (1 - t) + _BG_BOT[None, :] * t).astype("uint8")
    arr = np.repeat(col[:, None, :], px, axis=1)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def _sombra(px: int) -> Image.Image:
    """Sombra de contato suave sob o produto."""
    a = Image.new("L", (px, px), 0)
    d = ImageDraw.Draw(a)
    cx, cy = px // 2, int(px * 0.70)
    ew, eh = int(px * 0.34), int(px * 0.052)
    d.ellipse([cx - ew, cy - eh, cx + ew, cy + eh], fill=70)
    a = a.filter(ImageFilter.GaussianBlur(px * 0.025))
    base = Image.new("RGBA", (px, px), (15, 18, 22, 0))
    base.putalpha(a)
    return base


def _render_modelo(mesh, px: int, mat_rgb: np.ndarray) -> Image.Image:
    m = mesh
    if len(m.faces) > _FACES_RENDER:
        try:
            m = m.simplify_quadric_decimation(face_count=_FACES_RENDER)
        except Exception:
            pass

    tris = m.vertices[m.faces]
    normals = m.face_normals

    # Iluminação key + fill (dois termos difusos)
    s_key  = np.clip(normals @ _KEY,  0.0, 1.0) * _KEY_INT
    s_fill = np.clip(normals @ _FILL, 0.0, 1.0) * _FILL_INT
    s_total = _AMB + s_key + s_fill

    # Aplica cor do material com iluminação
    rgb = np.clip(mat_rgb[None, :] * s_total[:, None], 0.0, 1.0)
    cores = np.concatenate([rgb, np.ones((len(rgb), 1))], axis=1)

    fig = plt.figure(figsize=(px / 100, px / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1], projection="3d")
    ax.set_axis_off()
    ax.set_facecolor((0, 0, 0, 0))
    pc = Poly3DCollection(tris, facecolors=cores, edgecolors="none",
                          antialiased=True, shade=False)
    ax.add_collection3d(pc)

    v = m.vertices
    ext = v.max(0) - v.min(0)
    c = (v.max(0) + v.min(0)) / 2.0
    r = ext.max() / 2.0 * 1.02
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    try:
        ax.set_box_aspect((1, 1, 1))
    except Exception:
        pass
    # objeto chato (placa/chaveiro plano) -> vista de cima; senão 3/4 padrão
    plano = ext.min() < 0.30 * ext.max()
    ax.view_init(**(_VIEW_FLAT if plano else _VIEW))

    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGBA")


def render_thumb(mesh, nome: str = "", accent: str = "", tamanho: int = 1000) -> bytes:
    """JPEG (bytes): produto centralizado em fundo clean com sombra de contato.

    Cor do material: derivada deterministicamente do `nome` (slug/categoria)
    ou do parâmetro `accent` (se preenchido, ex.: '#2FA84F').
    Iluminação key + fill garante variação de pixel (std > limiar).
    """
    # Determina cor do material
    if accent and accent.startswith("#") and len(accent) in (4, 7):
        # parse hex -> RGB [0,1]
        a = accent.lstrip("#")
        if len(a) == 3:
            a = "".join(c * 2 for c in a)
        try:
            mat_rgb = np.array([int(a[i:i+2], 16) / 255.0 for i in (0, 2, 4)])
        except ValueError:
            mat_rgb = _cor_por_nome(nome or "produto")
    else:
        mat_rgb = _cor_por_nome(nome or "produto")

    img = _fundo(tamanho)
    img.alpha_composite(_sombra(tamanho))
    modelo = _render_modelo(mesh, int(tamanho * 0.80), mat_rgb)
    # leve deslocamento p/ cima: produto "flutua" sobre a sombra
    x = (tamanho - modelo.size[0]) // 2
    y = int(tamanho * 0.09)
    img.alpha_composite(modelo, (x, y))

    out = io.BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=92)
    return out.getvalue()
