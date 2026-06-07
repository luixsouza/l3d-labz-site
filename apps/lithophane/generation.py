"""Motor de geração de lithophane — isolado e swappável.

Segue o padrão de `apps/orders/payments.py`: um boundary sem dependência de
Django/ORM/HTTP. Recebe uma `PIL.Image` (já ajustada pelo editor) + as especs e
devolve `(glb_bytes, stl_bytes)`:

- **GLB** para o `<model-viewer>` — malha com relevo + a foto embutida como
  `emissiveTexture` (é o que o toggle "com luz" liga no navegador).
- **STL** imprimível — a mesma malha watertight, sem material.

Relevo invertido (padrão lithophane): pixel claro = fino (passa muita luz),
pixel escuro = grosso (bloqueia a luz).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals

FormatoLitho = Literal["placa", "luminaria"]

# Maior lado da textura emissiva embutida no GLB (controla o tamanho do arquivo).
_TEX_MAX_PX = 512


@dataclass
class EspecsLitho:
    largura_mm: float        # ex: 100.0  (maior lado físico da peça)
    espessura_min_mm: float  # ex: 0.8    (partes claras / finas)
    espessura_max_mm: float  # ex: 3.0    (partes escuras / grossas)
    resolucao_px: int        # ex: 300    (maior lado do heightmap)
    formato: FormatoLitho


class LithophaneGenerator:
    """Converte uma foto numa peça 3D de lithophane. Sem ORM, sem HTTP."""

    @staticmethod
    def gerar(imagem_pil: Image.Image, specs: EspecsLitho) -> tuple[bytes, bytes]:
        """Devolve (glb_bytes, stl_bytes). NÃO toca em ORM/HTTP/FileField."""
        heightmap = _imagem_para_heightmap(imagem_pil, specs)
        malha, uv = _heightmap_para_mesh(heightmap, specs)
        glb = _exportar_glb(malha, uv, imagem_pil)
        stl = malha.export(file_type="stl")
        return glb, stl


# --------------------------------------------------------------------------- #
# Etapas
# --------------------------------------------------------------------------- #
def _imagem_para_heightmap(img: Image.Image, specs: EspecsLitho) -> np.ndarray:
    """Foto -> grade (H,W) float32 de espessuras em mm, com relevo invertido."""
    cinza = img.convert("L")

    # redimensiona mantendo a proporção, maior lado = resolucao_px
    w, h = cinza.size
    escala = specs.resolucao_px / float(max(w, h))
    novo = (max(2, round(w * escala)), max(2, round(h * escala)))
    cinza = cinza.resize(novo, Image.LANCZOS)

    arr = np.asarray(cinza, dtype=np.float32) / 255.0  # 0..1 (claro=1)
    arr = 1.0 - arr                                     # INVERTE: escuro=1 (grosso)
    alturas = arr * (specs.espessura_max_mm - specs.espessura_min_mm) + specs.espessura_min_mm
    return alturas.astype(np.float32)                   # (H, W)


def _heightmap_para_mesh(alturas: np.ndarray, specs: EspecsLitho) -> tuple[trimesh.Trimesh, np.ndarray]:
    """Monta uma malha sólida watertight (topo + base + 4 paredes) a partir do heightmap.

    Vértices do topo e da base são compartilhados pelas paredes (índices reusados),
    o que mantém cada aresta entre exatamente 2 faces -> watertight.
    Retorna (malha, uv) — uv mapeia a foto no topo para a emissiveTexture.
    """
    h, w = alturas.shape
    dx = specs.largura_mm / float(max(w, h) - 1)  # passo físico (mm) por pixel

    ys, xs = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")  # (H,W)
    x = xs * dx
    y = ys * dx

    n = h * w
    top = np.stack([x, y, alturas], axis=-1).reshape(-1, 3)
    bot = np.stack([x, y, np.zeros_like(alturas)], axis=-1).reshape(-1, 3)
    vertices = np.vstack([top, bot]).astype(np.float64)

    def t(i, j):  # índice do vértice do topo
        return i * w + j

    def b(i, j):  # índice do vértice da base
        return n + i * w + j

    faces: list[list[int]] = []

    # --- topo (normal para +Z) e base (normal para -Z, winding invertido) ---
    ii, jj = np.meshgrid(np.arange(h - 1), np.arange(w - 1), indexing="ij")
    v00 = (ii * w + jj).ravel()
    v01 = (ii * w + jj + 1).ravel()
    v10 = ((ii + 1) * w + jj).ravel()
    v11 = ((ii + 1) * w + jj + 1).ravel()
    topo = np.concatenate(
        [np.stack([v00, v01, v11], axis=1), np.stack([v00, v11, v10], axis=1)]
    )
    base = np.concatenate(
        [np.stack([v00 + n, v11 + n, v01 + n], axis=1),
         np.stack([v00 + n, v10 + n, v11 + n], axis=1)]
    )
    faces.extend(topo.tolist())
    faces.extend(base.tolist())

    # --- 4 paredes laterais (reusam vértices de topo/base) ---
    for j in range(w - 1):                       # borda i=0 e i=h-1
        faces.append([t(0, j), b(0, j), b(0, j + 1)])
        faces.append([t(0, j), b(0, j + 1), t(0, j + 1)])
        faces.append([t(h - 1, j), b(h - 1, j + 1), b(h - 1, j)])
        faces.append([t(h - 1, j), t(h - 1, j + 1), b(h - 1, j + 1)])
    for i in range(h - 1):                        # borda j=0 e j=w-1
        faces.append([t(i, 0), b(i + 1, 0), b(i, 0)])
        faces.append([t(i, 0), t(i + 1, 0), b(i + 1, 0)])
        faces.append([t(i, w - 1), b(i, w - 1), b(i + 1, w - 1)])
        faces.append([t(i, w - 1), b(i + 1, w - 1), t(i + 1, w - 1)])

    malha = trimesh.Trimesh(
        vertices=vertices, faces=np.asarray(faces, dtype=np.int64), process=False
    )
    # winding consistente + tampar buracos numéricos, se houver
    trimesh.repair.fix_normals(malha)
    if not malha.is_watertight:
        trimesh.repair.fill_holes(malha)

    # UV: foto mapeada no topo (Y invertido para convenção de imagem); base = (0,0)
    u = (xs / float(w - 1)).reshape(-1)
    v = (1.0 - ys / float(h - 1)).reshape(-1)
    uv_top = np.stack([u, v], axis=1)
    uv = np.vstack([uv_top, np.zeros((n, 2))])
    return malha, uv


def _exportar_glb(malha: trimesh.Trimesh, uv: np.ndarray, imagem_pil: Image.Image) -> bytes:
    """Anexa material PBR branco + emissiveTexture (a foto) e exporta GLB."""
    textura = imagem_pil.convert("RGB")
    if max(textura.size) > _TEX_MAX_PX:
        escala = _TEX_MAX_PX / float(max(textura.size))
        textura = textura.resize(
            (max(1, round(textura.size[0] * escala)), max(1, round(textura.size[1] * escala))),
            Image.LANCZOS,
        )

    material = PBRMaterial(
        name="lithophane",
        baseColorFactor=[255, 255, 255, 255],
        metallicFactor=0.0,
        roughnessFactor=1.0,
        emissiveTexture=textura,
        emissiveFactor=[1.0, 1.0, 1.0],
        doubleSided=False,
    )
    malha.visual = TextureVisuals(uv=uv, material=material)
    cena = trimesh.Scene()
    cena.add_geometry(malha)
    return cena.export(file_type="glb")
