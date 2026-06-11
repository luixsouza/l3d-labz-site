"""Importa o 'Pack Copa do Mundo 2026' (do SSD) como produtos reais.

Piloto da importação do catálogo real da L3D Labz. Para cada produto:
- escolhe a malha (prefere .3mf montado; senão junta os .stl das partes),
- decima para ~TARGET_FACES e exporta um GLB leve para o visualizador 3D,
- usa a foto real do pack (ou gera um card de branding se não houver),
- cria/atualiza o Product (preço 0 = sob demanda).

O STL original NÃO é publicado (protege o ativo da loja print-on-demand);
o GLB decimado serve só de preview no viewer. Idempotente (chave = slug).

Uso (dentro do container, com o SSD montado em /import):
    python manage.py importar_copa --base "/import/Pack Copa do Mundo 2026"
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import numpy as np
import trimesh
import trimesh.transformations as tf
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog import render3d
from apps.catalog.branding import gerar_card
from apps.catalog.models import Category, Product

# 3MF primeiro: vem MONTADO (transforms do build) — é a "foto do stl montado".
# STL costuma ser peças no layout da mesa de impressão (espalhadas), por isso
# para STL multi-peça usamos só a peça maior. Guard de OOM no 3mf ladrilhado.
MESH_PREF = [".3mf", ".stl", ".obj", ".ply"]
MAX_FACES_IN = 6_000_000  # acima disso, aborta/cai p/ peça única (evita OOM do box)
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
TARGET_FACES = 60000

# (nome limpo, subpasta no pack, categoria, destaque)
PRODUTOS = [
    ("Chaveiro Brasão do Brasil", "Chaveiro Brasão Brasil", "Chaveiros", False),
    ("Chaveiro Copa do Mundo FIFA 2026", "Chaveiro Copa do mundo Fifa 2026", "Chaveiros", False),
    ("Chaveiro Giratório", "Chaveiros Giratórios", "Chaveiros", False),
    ("Chaveiro Trionda", "chaveiro trionda", "Chaveiros", False),
    ("Chaveiro Troféu FIFA", "Chaveiro troféu fifa", "Chaveiros", True),
    ("Mascote Canarinho — Brasil", "Mascote Brasil - Canarinho", "Mascotes", True),
    ("Mascotes Canadá, EUA e México", "Mascotes Canada, EUA e México", "Mascotes", False),
    ("Porta-Figurinhas Copa 2026", "Pack porta figurinhas", "Organizadores", False),
    ("Porta-Lata FIFA 2026", "Porta Lata Fifa 2026", "Organizadores", False),
    ("Troféu FIFA", "Trofeu fifa", "Troféus", True),
]

# categoria -> (icone do sprite, accent)
CATEGORIAS = {
    "Chaveiros": ("tag", "#2FA84F"),
    "Mascotes": ("star", "#2BA6E0"),
    "Organizadores": ("box", "#E0A82B"),
    "Troféus": ("spark", "#E0552B"),
}


class Command(BaseCommand):
    help = "Importa o Pack Copa do Mundo 2026 (SSD) como produtos sob demanda."

    def add_arguments(self, parser):
        parser.add_argument("--base", required=True,
                            help="Caminho do pack (ex.: /import/Pack Copa do Mundo 2026).")
        parser.add_argument("--forcar", action="store_true",
                            help="Regenera media de quem já existe.")
        parser.add_argument("--only", default="",
                            help="Processa só o produto com este slug (isola OOM).")
        parser.add_argument("--sem3d", action="store_true",
                            help="Cria só com foto (sem gerar GLB) — p/ malhas que estouram a RAM.")
        parser.add_argument("--stl", action="store_true",
                            help="Ignora .3mf e usa só STL (p/ 3mf que estoura a RAM).")

    # ---- helpers ----
    def _coletar_malhas(self, pasta: Path, prefs=None) -> list[Path]:
        for ext in (prefs or MESH_PREF):
            achados = sorted(p for p in pasta.rglob("*") if p.suffix.lower() == ext)
            if achados:
                return achados
        return []

    def _melhor_imagem(self, pasta: Path) -> Path | None:
        imgs = [p for p in pasta.rglob("*") if p.suffix.lower() in IMG_EXTS]
        return max(imgs, key=lambda p: p.stat().st_size) if imgs else None

    def _carregar_3mf(self, path: Path):
        """Carrega .3mf MONTADO (aplica os transforms do build). Guard de OOM: se
        as instâncias somarem faces demais (build ladrilhado), cai p/ a maior
        geometria única (1 cópia) em vez de bakear tudo e estourar a RAM."""
        loaded = trimesh.load(str(path))
        if isinstance(loaded, trimesh.Trimesh):
            return loaded
        if not isinstance(loaded, trimesh.Scene):
            return None
        total = 0
        for node in loaded.graph.nodes_geometry:
            g = loaded.geometry.get(loaded.graph[node][1])
            if g is not None and getattr(g, "faces", None) is not None:
                total += len(g.faces)
        if total and total <= MAX_FACES_IN:
            m = loaded.dump(concatenate=True)  # MONTADO
            return m if isinstance(m, trimesh.Trimesh) and len(m.faces) else None
        geoms = [g for g in loaded.geometry.values()
                 if isinstance(g, trimesh.Trimesh) and len(g.faces)]
        return max(geoms, key=lambda g: len(g.faces)) if geoms else None

    def _construir_mesh(self, malhas: list[Path]):
        if malhas[0].suffix.lower() == ".3mf":
            partes = []
            for m in malhas:
                try:
                    g = self._carregar_3mf(m)
                    if g is not None and len(g.faces):
                        partes.append(g)
                except Exception as e:
                    self.stderr.write(f"      ! falha lendo {m.name}: {e}")
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

        # pré-decima malhas enormes p/ o split (adjacência) caber na RAM
        if n0 > 500_000:
            mesh = self._decimar(mesh, 400_000)

        # maior componente conectado: descarta plates de impressão / peças soltas
        try:
            comps = mesh.split(only_watertight=False)
            if len(comps) > 1:
                mesh = max(comps, key=lambda c: len(c.faces))
                self.stdout.write(f"      maior de {len(comps)} componentes")
        except Exception:
            pass

        mesh = self._orientar(mesh)

        if len(mesh.faces) > TARGET_FACES:
            mesh = self._decimar(mesh, TARGET_FACES)
        return mesh

    @staticmethod
    def _decimar(mesh, alvo: int):
        try:
            return mesh.simplify_quadric_decimation(face_count=alvo)
        except TypeError:
            return mesh.simplify_quadric_decimation(alvo)

    def _orientar(self, mesh):
        """Coloca o objeto "em pé": eixo mais longo na vertical (Z). Se for uma
        placa fina, o eixo FINO vai p/ Z (deita) e o render usa vista de cima.
        Rotações próprias (sem espelhar — logos não saem invertidos)."""
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

    def _finalizar_glb(self, mesh, nome: str = "") -> bytes:
        """Suaviza normais + material PBR colorido (mesma cor da foto) p/ o viewer."""
        try:
            mesh.merge_vertices()
            mesh.fix_normals()
        except Exception:
            pass
        # trimesh trabalha com Z-up; GLB/model-viewer assumem Y-up — sem esta
        # rotação o modelo aparece deitado no visualizador
        try:
            mesh.apply_transform(tf.rotation_matrix(-np.pi / 2, [1, 0, 0]))
        except Exception:
            pass
        try:
            mesh.visual = trimesh.visual.TextureVisuals(
                material=trimesh.visual.material.PBRMaterial(
                    baseColorFactor=render3d.cor_rgba_por_nome(nome or "produto"),
                    metallicFactor=0.0, roughnessFactor=0.55,
                )
            )
        except Exception:
            pass
        return mesh.export(file_type="glb")

    # ---- main ----
    def handle(self, *args, **options):
        base = Path(options["base"])
        forcar = options["forcar"]
        if not base.is_dir():
            self.stderr.write(self.style.ERROR(f"pasta não encontrada: {base}"))
            return

        cats: dict[str, Category] = {}
        for ordem, (nome, (icone, accent)) in enumerate(CATEGORIAS.items()):
            cat, _ = Category.objects.get_or_create(
                slug=slugify(nome),
                defaults={"name": nome, "icon": icone, "accent": accent,
                          "order": 10 + ordem, "is_highlighted": True,
                          "description": f"{nome} impressos em 3D sob demanda pela L3D Labz."},
            )
            cats[nome] = cat

        only = options["only"]
        feitos = 0
        for nome, subpasta, cat_nome, destaque in PRODUTOS:
            if only and slugify(nome) != only:
                continue
            pasta = base / subpasta
            if not pasta.is_dir():
                self.stderr.write(f"  ! sem pasta: {subpasta}")
                continue
            slug = slugify(nome)
            existente = Product.objects.filter(slug=slug).first()
            if existente and existente.model_3d and not forcar:
                self.stdout.write(f"  · (pula) {nome}")
                continue

            self.stdout.write(f"  · {nome}")
            cat = cats[cat_nome]
            accent = cat.accent

            # 3D + foto renderizada do modelo (pulável via --sem3d p/ malhas que estouram a RAM)
            glb = None
            if not options["sem3d"]:
                prefs = [".stl", ".obj", ".ply"] if options["stl"] else None
                malhas = self._coletar_malhas(pasta, prefs)
                if not malhas:
                    self.stderr.write(f"      ! sem malha 3D — pulando {nome}")
                    continue
                try:
                    mesh = self._construir_mesh(malhas)
                except Exception as e:
                    self.stderr.write(f"      ! falha na malha: {e} — pulando")
                    continue
                # foto padronizada (render minimalista do próprio modelo)
                try:
                    # cor vem da paleta L3D (determinística por nome) — accent da
                    # categoria é pálido demais p/ material; fica só p/ cards/molduras
                    img_bytes = render3d.render_thumb(mesh, nome)
                    img_ext = "jpg"
                except Exception as e:
                    self.stderr.write(f"      ! falha no render ({e}) — card de fallback")
                    img_bytes, img_ext = gerar_card(nome, accent), "png"
                glb = self._finalizar_glb(mesh, nome)
            else:
                # sem malha utilizável: card de marca consistente
                img_bytes, img_ext = gerar_card(nome, accent), "png"

            p = existente or Product(slug=slug)
            p.category = cat
            p.name = nome
            p.description = (
                f"{nome} impresso em 3D com acabamento premium pela L3D Labz. "
                f"Produzido sob demanda — orçamento e prazo pelo WhatsApp."
            )
            p.price = Decimal("0")
            p.compare_at_price = None
            p.stock = 10
            p.material = "PLA+"
            p.is_featured = destaque
            p.is_active = True
            p.save()
            p.image.save(f"{slug}.{img_ext}", ContentFile(img_bytes), save=False)
            campos = ["image"]
            if glb is not None:
                p.model_3d.save(f"{slug}.glb", ContentFile(glb), save=False)
                campos.append("model_3d")
            p.save(update_fields=campos)
            feitos += 1

        self.stdout.write(self.style.SUCCESS(f"Produtos Copa importados/atualizados: {feitos}"))
