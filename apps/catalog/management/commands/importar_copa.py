"""Importa o 'Pack Copa do Mundo 2026' (do SSD) como produtos reais.

Piloto da importação do catálogo real da L3D Labz. Para cada produto:
- escolhe a malha (prefere .3mf montado; senão junta os .stl das partes),
- decima para ~TARGET_FACES e exporta um GLB leve para o visualizador 3D,
- usa a foto real do pack (ou gera um card de branding se não houver),
- cria/atualiza o Product (preço 0 = sob demanda).

O STL original NÃO é publicado (protege o ativo da loja print-on-demand);
o GLB decimado serve só de preview no viewer. Idempotente (chave = slug).

O pipeline 3D (coletar malhas, construir mesh, finalizar GLB) é compartilhado
via apps.catalog.mesh3d — qualquer outro comando de import reutiliza as mesmas
funções sem duplicação.

Uso (dentro do container, com o SSD montado em /import):
    python manage.py importar_copa --base "/import/Pack Copa do Mundo 2026"
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog import mesh3d, render3d
from apps.catalog.branding import gerar_card
from apps.catalog.models import Category, Product

# Aliases locais para facilitar leitura — valores canônicos vivem em mesh3d.
MESH_PREF = mesh3d.MESH_PREF
IMG_EXTS = mesh3d.IMG_EXTS

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
    def _melhor_imagem(self, pasta: Path) -> Path | None:
        imgs = [p for p in pasta.rglob("*") if p.suffix.lower() in IMG_EXTS]
        return max(imgs, key=lambda p: p.stat().st_size) if imgs else None

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
                malhas = mesh3d.coletar_malhas(pasta, prefs)
                if not malhas:
                    self.stderr.write(f"      ! sem malha 3D — pulando {nome}")
                    continue
                try:
                    mesh = mesh3d.construir_mesh(malhas, log=self.stdout.write)
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
                glb = mesh3d.finalizar_glb(mesh, nome)
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
