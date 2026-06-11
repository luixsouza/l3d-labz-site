"""Pipeline 3D compartilhado — coletar malhas, construir mesh, exportar GLB.

Extraído do importar_copa para ser reusado por qualquer comando de importação
(importar_copa, importar_makerworld, etc.) sem duplicar código.

Regras fundamentais:
- NUNCA usar force='mesh' em Scene; usar scene.geometry.values() (geometrias únicas)
  com guard MAX_FACES_IN p/ evitar OOM em builds ladrilhados.
- Y-up: GLB/model-viewer assumem Y-up; trimesh é Z-up — a rotação final corrige.
- Decima para TARGET_FACES antes de exportar p/ manter o GLB leve no browser.

Exportações públicas:
    coletar_malhas(pasta, prefs) -> list[Path]
    construir_mesh(malhas, log) -> trimesh.Trimesh
    finalizar_glb(mesh, nome) -> bytes (GLB)
    dimensoes_mm(mesh) -> tuple[float, float, float]  -- bounding box em mm
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Callable

import numpy as np
import trimesh
import trimesh.transformations as tf

from apps.catalog import render3d

# --- constantes ---
# 3MF primeiro: vem MONTADO (transforms do build) — melhor representação do objeto.
# STL costuma ser peças no layout da mesa (espalhadas); para STL multi-peça
# usamos só a peça maior.
MESH_PREF: list[str] = [".3mf", ".stl", ".obj", ".ply"]

# Face-count acima do qual abortamos o dump montado e pegamos a maior geometria única
# (evita OOM em builds ladrilhados com centenas de cópias).
MAX_FACES_IN: int = 6_000_000

# Alvo final de faces no GLB exportado (manter preview leve no browser).
TARGET_FACES: int = 60_000

# Extensões de imagem reconhecidas (para coletar fotos nas pastas).
IMG_EXTS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".webp"})


# ---------------------------------------------------------------------------
# Coletar malhas
# ---------------------------------------------------------------------------

def coletar_malhas(pasta: Path, prefs: list[str] | None = None) -> list[Path]:
    """Varre *pasta* recursivamente e retorna a lista de arquivos 3D preferidos.

    Experimenta cada extensão de *prefs* (padrão: MESH_PREF) em ordem; retorna
    a primeira lista não-vazia.  Nunca mistura extensões (o chamador recebe só
    uma família de arquivos).
    """
    for ext in (prefs or MESH_PREF):
        achados = sorted(p for p in pasta.rglob("*") if p.suffix.lower() == ext)
        if achados:
            return achados
    return []


# ---------------------------------------------------------------------------
# Carregamento interno de .3mf (guard de OOM)
# ---------------------------------------------------------------------------

def _carregar_3mf(path: Path, log: Callable[[str], None] | None = None) -> trimesh.Trimesh | None:
    """Carrega um .3mf MONTADO (aplica os transforms do build).

    Guard de OOM: se as instâncias somarem faces demais (build ladrilhado),
    cai para a maior geometria única (1 cópia) em vez de bakear tudo e
    estourar a RAM.  NUNCA usa force='mesh' num Scene.
    """
    _log = log or (lambda msg: warnings.warn(msg, stacklevel=3))
    loaded = trimesh.load(str(path))
    if isinstance(loaded, trimesh.Trimesh):
        return loaded
    if not isinstance(loaded, trimesh.Scene):
        return None
    # Conta faces de todas as instâncias (considera transforms do build)
    total = 0
    for node in loaded.graph.nodes_geometry:
        g = loaded.geometry.get(loaded.graph[node][1])
        if g is not None and getattr(g, "faces", None) is not None:
            total += len(g.faces)
    if total and total <= MAX_FACES_IN:
        m = loaded.dump(concatenate=True)  # montado com transforms
        return m if isinstance(m, trimesh.Trimesh) and len(m.faces) else None
    # Build ladrilhado: pega só a maior geometria única (evita OOM)
    _log(f"      ! build grande ({total} faces) — usando maior geometria única")
    geoms = [g for g in loaded.geometry.values()
             if isinstance(g, trimesh.Trimesh) and len(g.faces)]
    return max(geoms, key=lambda g: len(g.faces)) if geoms else None


# ---------------------------------------------------------------------------
# Decimar / orientar (helpers internos)
# ---------------------------------------------------------------------------

def _decimar(mesh: trimesh.Trimesh, alvo: int) -> trimesh.Trimesh:
    try:
        return mesh.simplify_quadric_decimation(face_count=alvo)
    except TypeError:
        return mesh.simplify_quadric_decimation(alvo)


def _orientar(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Coloca o objeto "em pé": eixo mais longo na vertical (Z).

    Se for uma placa fina, o eixo FINO vai p/ Z (deita) e o render usa vista
    de cima.  Rotações próprias (sem espelhar — logos não saem invertidos).
    """
    try:
        ext = mesh.extents
        alvo = int(np.argmin(ext)) if ext.min() < 0.30 * ext.max() else int(np.argmax(ext))
        if alvo == 0:
            mesh.apply_transform(tf.rotation_matrix(-np.pi / 2, [0, 1, 0]))
        elif alvo == 1:
            mesh.apply_transform(tf.rotation_matrix(np.pi / 2, [1, 0, 0]))
    except Exception:
        pass
    return mesh


# ---------------------------------------------------------------------------
# construir_mesh — público
# ---------------------------------------------------------------------------

def construir_mesh(
    malhas: list[Path],
    log: Callable[[str], None] | None = None,
) -> trimesh.Trimesh:
    """Constrói uma Trimesh final a partir de *malhas* (lista de caminhos).

    Para .3mf: carrega montado (com transforms do build); concatena se
    necessário.  Para STL/OBJ/PLY: usa só a maior peça (layout de mesa de
    impressão).  Decima se muito grande, pega o maior componente conectado,
    orienta.

    *log* é chamado com strings de diagnóstico (pt-br).  Se None, usa
    warnings.warn.

    Lança ValueError se não conseguir malha válida.
    """
    _log = log or (lambda msg: warnings.warn(msg, stacklevel=2))

    if malhas[0].suffix.lower() == ".3mf":
        partes: list[trimesh.Trimesh] = []
        for m in malhas:
            try:
                g = _carregar_3mf(m, _log)
                if g is not None and len(g.faces):
                    partes.append(g)
            except Exception as e:
                _log(f"      ! falha lendo {m.name}: {e}")
        if not partes:
            raise ValueError("3mf sem malha válida")
        mesh = trimesh.util.concatenate(partes) if len(partes) > 1 else partes[0]
    else:
        # STL/OBJ multi-peça = layout da mesa de impressão; concatenar
        # espalharia as partes. Usa só a MAIOR peça (corpo principal).
        maior = max(malhas, key=lambda p: p.stat().st_size)
        mesh = trimesh.load(str(maior), force="mesh")
        if not (isinstance(mesh, trimesh.Trimesh) and len(mesh.faces)):
            raise ValueError("sem malha STL válida")

    n0 = len(mesh.faces)
    if n0 > MAX_FACES_IN:
        raise ValueError(f"malha grande demais ({n0} faces) — abortando p/ não estourar RAM")

    # Pré-decima malhas enormes p/ o split (adjacência) caber na RAM
    if n0 > 500_000:
        mesh = _decimar(mesh, 400_000)

    # Maior componente conectado: descarta plates de impressão / peças soltas
    try:
        comps = mesh.split(only_watertight=False)
        if len(comps) > 1:
            mesh = max(comps, key=lambda c: len(c.faces))
            _log(f"      maior de {len(comps)} componentes")
    except Exception:
        pass

    mesh = _orientar(mesh)

    if len(mesh.faces) > TARGET_FACES:
        mesh = _decimar(mesh, TARGET_FACES)
    return mesh


# ---------------------------------------------------------------------------
# finalizar_glb — público
# ---------------------------------------------------------------------------

def finalizar_glb(mesh: trimesh.Trimesh, nome: str = "") -> bytes:
    """Suaviza normais + material PBR colorido e exporta como GLB.

    trimesh trabalha com Z-up; GLB/model-viewer assumem Y-up — sem a rotação
    o modelo aparece deitado no visualizador.  A cor PBR é derivada
    deterministicamente do nome (render3d.cor_rgba_por_nome).
    """
    try:
        mesh.merge_vertices()
        mesh.fix_normals()
    except Exception:
        pass
    # Z-up → Y-up (rotação em torno de X de −90°)
    try:
        mesh.apply_transform(tf.rotation_matrix(-np.pi / 2, [1, 0, 0]))
    except Exception:
        pass
    try:
        mesh.visual = trimesh.visual.TextureVisuals(
            material=trimesh.visual.material.PBRMaterial(
                baseColorFactor=render3d.cor_rgba_por_nome(nome or "produto"),
                metallicFactor=0.0,
                roughnessFactor=0.55,
            )
        )
    except Exception:
        pass
    return mesh.export(file_type="glb")


# ---------------------------------------------------------------------------
# dimensoes_mm — público
# ---------------------------------------------------------------------------

def dimensoes_mm(mesh: trimesh.Trimesh) -> tuple[float, float, float]:
    """Retorna a bounding box do mesh em mm (X, Y, Z) — útil ANTES do finalizar.

    O 3mf traz coordenadas em mm, então mesh.extents já é mm.  Chamar ANTES
    de finalizar_glb pois essa função aplica rotação Z-up→Y-up que troca eixos.
    """
    ext = mesh.extents  # numpy array [dx, dy, dz]
    return float(ext[0]), float(ext[1]), float(ext[2])
