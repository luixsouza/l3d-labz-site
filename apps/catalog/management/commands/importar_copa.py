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

import trimesh
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.branding import gerar_card
from apps.catalog.models import Category, Product

# STL primeiro: geometria crua e previsível. O .3mf pode conter centenas de
# instâncias (build "ladrilhado") que explodem a RAM ao achatar — só usamos
# .3mf quando não há STL.
MESH_PREF = [".stl", ".3mf", ".obj", ".ply"]
MAX_FACES_IN = 6_000_000  # acima disso, aborta o produto (evita OOM do box)
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

    # ---- helpers ----
    def _coletar_malhas(self, pasta: Path) -> list[Path]:
        for ext in MESH_PREF:
            achados = sorted(p for p in pasta.rglob("*") if p.suffix.lower() == ext)
            if achados:
                return achados
        return []

    def _melhor_imagem(self, pasta: Path) -> Path | None:
        imgs = [p for p in pasta.rglob("*") if p.suffix.lower() in IMG_EXTS]
        return max(imgs, key=lambda p: p.stat().st_size) if imgs else None

    def _gerar_glb(self, malhas: list[Path]) -> bytes:
        partes = []
        for m in malhas:
            try:
                # NÃO usar force='mesh': em .3mf isso "assa" todas as instâncias
                # (build ladrilhado) e estoura a RAM. Carrega como cena e pega só
                # as geometrias ÚNICAS (1 cópia do modelo, sem replicar instâncias).
                loaded = trimesh.load(str(m))
                if isinstance(loaded, trimesh.Scene):
                    geoms = [g for g in loaded.geometry.values()
                             if isinstance(g, trimesh.Trimesh) and len(g.faces)]
                    if not geoms:
                        continue
                    geo = trimesh.util.concatenate(geoms) if len(geoms) > 1 else geoms[0]
                elif isinstance(loaded, trimesh.Trimesh) and len(loaded.faces):
                    geo = loaded
                else:
                    continue
                partes.append(geo)
            except Exception as e:
                self.stderr.write(f"      ! falha lendo {m.name}: {e}")
        if not partes:
            raise ValueError("nenhuma malha válida")
        mesh = trimesh.util.concatenate(partes) if len(partes) > 1 else partes[0]
        n = len(mesh.faces)
        if n > MAX_FACES_IN:
            raise ValueError(f"malha grande demais ({n} faces) — abortando p/ não estourar RAM")
        if n > TARGET_FACES:
            try:
                mesh = mesh.simplify_quadric_decimation(face_count=TARGET_FACES)
            except TypeError:
                mesh = mesh.simplify_quadric_decimation(TARGET_FACES)
            self.stdout.write(f"      decimado {n} -> {len(mesh.faces)} faces")
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

            # 3D (pulável via --sem3d para malhas que estouram a RAM)
            glb = None
            if not options["sem3d"]:
                malhas = self._coletar_malhas(pasta)
                if not malhas:
                    self.stderr.write(f"      ! sem malha 3D — pulando {nome}")
                    continue
                try:
                    glb = self._gerar_glb(malhas)
                except Exception as e:
                    self.stderr.write(f"      ! falha no GLB: {e} — pulando")
                    continue

            # imagem
            img_path = self._melhor_imagem(pasta)
            if img_path:
                img_bytes = img_path.read_bytes()
                img_ext = img_path.suffix.lower().lstrip(".").replace("jpeg", "jpg")
            else:
                img_bytes = gerar_card(nome, accent)
                img_ext = "png"

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
