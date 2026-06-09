"""Render padronizado do modelo 3D -> foto de produto estilo Nike/Apple.

matplotlib (Agg, headless, SEM OpenGL) sombreia a malha num ângulo/luz fixos; o
modelo é composto sobre um fundo quase-branco com uma sombra de contato suave.
SEM texto na imagem (nome/preço ficam no card) — produto centralizado, muito
respiro, look minimalista e consistente entre todos os itens.
"""
from __future__ import annotations

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
_LUZ = np.array([0.40, 0.55, 0.74])
_LUZ = _LUZ / np.linalg.norm(_LUZ)
_MAT = np.array([0.86, 0.88, 0.91])   # alumínio/resina clara (neutro, elegante)
_AMB = 0.52                            # bem iluminado (clean, não escuro)
_FACES_RENDER = 13000

# fundo Apple-ish (#fbfbfd -> #f2f3f5)
_BG_TOP = np.array([251, 251, 253])
_BG_BOT = np.array([238, 239, 242])


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


def _render_modelo(mesh, px: int) -> Image.Image:
    m = mesh
    if len(m.faces) > _FACES_RENDER:
        try:
            m = m.simplify_quadric_decimation(face_count=_FACES_RENDER)
        except Exception:
            pass

    tris = m.vertices[m.faces]
    s = np.clip(m.face_normals @ _LUZ, 0.0, 1.0)
    s = _AMB + (1.0 - _AMB) * s
    rgb = np.clip(_MAT[None, :] * s[:, None], 0.0, 1.0)
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
    """JPEG (bytes): produto centralizado em fundo clean com sombra de contato."""
    img = _fundo(tamanho)
    img.alpha_composite(_sombra(tamanho))
    modelo = _render_modelo(mesh, int(tamanho * 0.80))
    # leve deslocamento p/ cima: produto "flutua" sobre a sombra
    x = (tamanho - modelo.size[0]) // 2
    y = int(tamanho * 0.09)
    img.alpha_composite(modelo, (x, y))

    out = io.BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=92)
    return out.getvalue()
