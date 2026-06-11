"""Importa pastas scrapadas do MakerWorld como produtos com galeria de fotos.

Cada subpasta de --base segue o formato produzido pelo scraper:
    <base>/<slug>/{meta.json, descricao.html, fotos/NN.ext, modelo.3mf?}

O comando cria ou atualiza um Product por pasta (idempotente por slug de diretório).
Foto principal = sorted(fotos/*)[0]; fotos restantes viram galeria (ProductImage).
GIF → converte primeiro frame p/ JPEG quadrado.

Nome do produto: traduzido para pt-br via OpenAI gpt-4o-mini quando OPENAI_API_KEY
estiver disponível; sem a chave, mantém o título em inglês com aviso no stdout.

A UI 3D foi removida. Por padrão o GLB não é gerado; use --com3d para gerar
(apenas se houver modelo.3mf). As dimensões reais (mm→cm) são coletadas do 3mf
independentemente de --com3d.

O STL original NUNCA é publicado.
Pipeline 3D compartilhado via apps.catalog.mesh3d (DRY com importar_copa).

Uso:
    python manage.py importar_makerworld --base /caminho/da/pasta
    python manage.py importar_makerworld --base /caminho --only meu-slug
    python manage.py importar_makerworld --base /caminho --limite 5
    python manage.py importar_makerworld --base /caminho --com3d
    python manage.py importar_makerworld --base /caminho --categoria "Casa & Organização"
"""
from __future__ import annotations

import io
import json
import os
import urllib.request
from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from PIL import Image

from apps.catalog import mesh3d
from apps.catalog.models import Category, Product, ProductImage

# ---------------------------------------------------------------------------
# Mapeamento de keywords → categoria automática
# ---------------------------------------------------------------------------
# As keywords são checadas em (titulo_en + ' ' + ' '.join(tags)).lower()
_KEYWORD_MAP: list[tuple[list[str], str]] = [
    (["airplane", "jet", "plane", "aircraft"], "Aviões"),
    (["star wars", "pokemon", "dragon", "anime", "geek", "marvel", "dc comics"], "Geek"),
    (["valentine", "love", "heart", "gift", "presente"], "Presentes"),
    (["kitchen", "organizer", "desk", "home", "drawer", "storage", "box"], "Casa & Organização"),
    (["toy", "fidget", "kids", "child"], "Brinquedos"),
    (["lamp", "light", "lantern", "candle"], "Decoração"),
]

# Ícone e accent padrão p/ categorias criadas automaticamente
_CAT_DEFAULTS: dict[str, tuple[str, str]] = {
    "Aviões":             ("plane",  "#2BA6E0"),
    "Geek":               ("star",   "#9B59B6"),
    "Presentes":          ("heart",  "#E23B3B"),
    "Casa & Organização": ("box",    "#E0A82B"),
    "Brinquedos":         ("cube",   "#2FA84F"),
    "Decoração":          ("spark",  "#E0552B"),
}


def _detectar_categoria(titulo: str, tags: list[str]) -> str | None:
    """Retorna nome da categoria pela heurística de keywords, ou None se sem match."""
    texto = (titulo + " " + " ".join(tags)).lower()
    for keywords, nome in _KEYWORD_MAP:
        if any(kw in texto for kw in keywords):
            return nome
    return None


def _get_or_create_categoria(nome: str, ordem_hint: int = 100) -> Category:
    """Busca ou cria a categoria pelo nome (get_or_create via slug)."""
    icone, accent = _CAT_DEFAULTS.get(nome, ("cube", "#2FA84F"))
    cat, _ = Category.objects.get_or_create(
        slug=slugify(nome),
        defaults={
            "name": nome,
            "icon": icone,
            "accent": accent,
            "order": ordem_hint,
            "is_highlighted": True,
            "description": f"{nome} impressos em 3D sob demanda pela L3D Labz.",
        },
    )
    return cat


# ---------------------------------------------------------------------------
# Tradução de nome via OpenAI (degradação graciosíssima sem chave)
# ---------------------------------------------------------------------------

def traduzir_nome(titulo_en: str) -> str:
    """Traduz o título do produto para pt-br usando OpenAI gpt-4o-mini.

    Sem OPENAI_API_KEY → retorna titulo_en intocado e imprime aviso no stdout.
    Com a chave → POST para a API com timeout 20s; qualquer falha → fallback
    para titulo_en com aviso (chave NUNCA é logada).
    """
    chave = os.environ.get("OPENAI_API_KEY", "").strip()
    if not chave:
        print(f"OPENAI_API_KEY ausente — mantendo nome em inglês: {titulo_en}")
        return titulo_en

    payload = json.dumps({
        "model": "gpt-4o-mini",
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um tradutor especializado em nomes de produtos de impressão 3D "
                    "para português brasileiro de e-commerce. Traduza o nome de forma curta e "
                    "natural. Mantenha marcas e nomes próprios (Star Wars, Pokémon, etc.). "
                    "Responda SOMENTE o nome traduzido, sem aspas, sem explicações."
                ),
            },
            {"role": "user", "content": titulo_en},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {chave}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip().strip('"')
    except Exception as exc:
        print(f"Falha na tradução de '{titulo_en}': {exc} — mantendo nome em inglês")
        return titulo_en


# ---------------------------------------------------------------------------
# Processamento de foto (normaliza p/ JPEG quadrado)
# ---------------------------------------------------------------------------

def _foto_para_jpeg_quadrado(caminho: Path) -> bytes:
    """Abre a foto (qualquer formato, incluindo GIF), converte para JPEG quadrado.

    GIF → primeiro frame (seek(0)).
    RGBA → compõe sobre fundo branco antes de salvar JPEG.
    Crop central + pad branco para garantir 1:1.
    """
    img = Image.open(str(caminho))
    # GIF: usa só o primeiro frame
    if getattr(img, "is_animated", False) or img.format == "GIF":
        img.seek(0)
    img = img.convert("RGBA")

    # Crop quadrado central
    w, h = img.size
    lado = min(w, h)
    esq = (w - lado) // 2
    topo = (h - lado) // 2
    img = img.crop((esq, topo, esq + lado, topo + lado))

    # Compõe sobre fundo branco (elimina transparência)
    fundo = Image.new("RGB", (lado, lado), (255, 255, 255))
    fundo.paste(img, mask=img.split()[3])  # canal alpha como máscara

    buf = io.BytesIO()
    fundo.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Comando principal
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = (
        "Importa pastas scrapadas do MakerWorld como produtos com galeria completa. "
        "Nome traduzido p/ pt-br via OpenAI (OPENAI_API_KEY); sem a chave, mantém inglês. "
        "UI 3D removida — GLB não é gerado por padrão (use --com3d se necessário)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--base", required=True,
            help="Diretório raiz com as pastas scrapadas (ex.: /import/makerworld).",
        )
        parser.add_argument(
            "--only", default="",
            help="Processa só a pasta com este slug (ex.: aurashell-lamp).",
        )
        parser.add_argument(
            "--limite", type=int, default=0,
            help="Processa no máximo N pastas (0 = sem limite).",
        )
        parser.add_argument(
            "--com3d", action="store_true",
            help="Gera GLB do modelo.3mf (UI 3D foi removida; padrão é não gerar).",
        )
        parser.add_argument(
            "--categoria", default="",
            help='Categoria padrão quando a detecção automática não encontrar match (ex.: "Geek").',
        )

    def handle(self, *args, **options):
        base = Path(options["base"])
        if not base.is_dir():
            self.stderr.write(self.style.ERROR(f"pasta não encontrada: {base}"))
            return

        only = options["only"].strip()
        limite = options["limite"]
        com3d = options["com3d"]
        cat_padrao = options["categoria"].strip()

        # Coleta subpastas ordenadas
        subpastas = sorted(p for p in base.iterdir() if p.is_dir())
        if only:
            subpastas = [p for p in subpastas if p.name == only]

        importados = 0
        atualizados = 0
        foto_only = 0

        for pasta in subpastas:
            if limite and (importados + atualizados) >= limite:
                break

            slug = slugify(pasta.name)

            # --- meta.json ---
            meta_path = pasta / "meta.json"
            if not meta_path.exists():
                self.stderr.write(f"  ! sem meta.json em {pasta.name} — pulando")
                continue
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception as e:
                self.stderr.write(f"  ! erro ao ler meta.json de {pasta.name}: {e} — pulando")
                continue

            titulo_en = (meta.get("titulo_en") or "").strip()
            titulo_pt = (meta.get("titulo") or "").strip()
            tags = meta.get("tags") or []

            # --- nome do produto (tradução + cache anti-retradução) ---
            existente = Product.objects.filter(slug=slug).first()
            titulo_base = titulo_en or titulo_pt or pasta.name
            # Se o produto já existe e o nome atual difere do titulo original
            # (já foi traduzido/editado manualmente), reutiliza sem chamar a API.
            if existente and existente.name != titulo_base:
                nome_produto = existente.name
            else:
                # traduz SEMPRE: titulo_en vazio significa que o original JÁ é
                # inglês (MakerWorld só preenche titleTranslated p/ não-inglês)
                nome_produto = traduzir_nome(titulo_base)

            # --- categoria automática ---
            nome_cat = _detectar_categoria(nome_produto, tags)
            if not nome_cat:
                # tenta com o título em inglês para keywords em EN
                nome_cat = _detectar_categoria(titulo_base, tags)
            if not nome_cat:
                if cat_padrao:
                    nome_cat = cat_padrao
                else:
                    self.stderr.write(
                        f"  ! sem categoria p/ '{nome_produto}' e --categoria não definido — pulando"
                    )
                    continue
            cat = _get_or_create_categoria(nome_cat)

            self.stdout.write(f"  · {nome_produto} [{nome_cat}]")

            # --- fotos ---
            fotos_dir = pasta / "fotos"
            fotos = sorted(fotos_dir.iterdir()) if fotos_dir.is_dir() else []
            if not fotos:
                self.stderr.write(f"      ! sem fotos em {pasta.name} — pulando")
                continue

            # Foto principal (primeira em ordem alfabética)
            foto_path = fotos[0]
            try:
                jpg_bytes = _foto_para_jpeg_quadrado(foto_path)
            except Exception as e:
                self.stderr.write(f"      ! falha ao processar foto {foto_path.name}: {e} — pulando")
                continue

            # --- pipeline 3D (dimensões sempre; GLB só com --com3d) ---
            glb: bytes | None = None
            dimensions: str = ""

            tmf_path = pasta / "modelo.3mf"
            if tmf_path.exists():
                try:
                    malhas = mesh3d.coletar_malhas(pasta, prefs=[".3mf"])
                    if not malhas:
                        raise FileNotFoundError("modelo.3mf não encontrado pela busca recursiva")
                    mesh = mesh3d.construir_mesh(malhas, log=self.stdout.write)
                    dx, dy, dz = mesh3d.dimensoes_mm(mesh)
                    dimensions = f"{dx/10:.1f}×{dy/10:.1f}×{dz/10:.1f} cm"
                    if com3d:
                        glb = mesh3d.finalizar_glb(mesh, nome_produto)
                        self.stdout.write(f"      GLB gerado — dimensões: {dimensions}")
                    else:
                        self.stdout.write(f"      dimensões: {dimensions} (sem GLB — use --com3d p/ gerar)")
                except Exception as e:
                    self.stderr.write(f"      ! falha no pipeline 3D: {e} — criando foto-only")
                    dimensions = ""
            else:
                self.stdout.write(f"      (foto-only — sem modelo.3mf)")
                foto_only += 1

            # --- descrição pt-br padronizada (não copiar descricao.html) ---
            desc_parts = [
                f"{nome_produto} ({nome_cat}) impresso sob demanda em PLA pela L3D Labz.",
                "Orçamento e prazo pelo WhatsApp.",
            ]
            if dimensions:
                desc_parts.append(f"Dimensões: {dimensions}.")
            description = " ".join(desc_parts)

            # --- salvar produto (idempotente por slug) ---
            eh_novo = existente is None
            p = existente or Product(slug=slug)
            p.category = cat
            p.name = nome_produto
            p.description = description
            p.price = Decimal("0")
            p.compare_at_price = None
            p.stock = 10
            p.material = "PLA+"
            p.is_featured = False
            p.is_active = True
            p.dimensions = dimensions
            p.save()

            p.image.save(f"{slug}.jpg", ContentFile(jpg_bytes), save=False)
            campos = ["image", "dimensions"]
            if glb is not None:
                p.model_3d.save(f"{slug}.glb", ContentFile(glb), save=False)
                campos.append("model_3d")
            p.save(update_fields=campos)

            # --- galeria (fotos[1:] em ordem, idempotente) ---
            p.gallery.all().delete()
            for idx, foto_extra in enumerate(fotos[1:], start=1):
                try:
                    extra_bytes = _foto_para_jpeg_quadrado(foto_extra)
                    gi = ProductImage(product=p, order=idx)
                    gi.image.save(f"{slug}-{idx}.jpg", ContentFile(extra_bytes), save=True)
                except Exception as e:
                    self.stderr.write(f"      ! falha na foto extra {foto_extra.name}: {e} — pulando")

            if eh_novo:
                importados += 1
            else:
                atualizados += 1

        total = importados + atualizados
        self.stdout.write(self.style.SUCCESS(
            f"MakerWorld: {importados} importados, {atualizados} atualizados"
            f" ({foto_only} foto-only) — total processado: {total}"
        ))
