"""Catálogo MakerWorld: branding de imagem + seed + filtro de material."""
from __future__ import annotations

import io
import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from apps.catalog.branding import gerar_card
from apps.catalog.models import Category, Product
from apps.catalog.queries import ProductQuery

_MEDIA = tempfile.mkdtemp(prefix="mw-test-")


class BrandingTests(TestCase):
    def test_gerar_card_devolve_png_valido(self):
        png = gerar_card("Dragão Flexi", "#2BA6E0")
        im = Image.open(io.BytesIO(png))
        self.assertEqual(im.format, "PNG")
        self.assertEqual(im.size, (800, 800))


@override_settings(MEDIA_ROOT=_MEDIA)
class SeedMakerworldTests(TestCase):
    def test_seed_cria_categorias_produtos_e_fotos(self):
        call_command("seed_makerworld")
        self.assertGreaterEqual(Category.objects.count(), 8)
        self.assertGreaterEqual(Product.objects.count(), 24)
        # toda foto padronizada foi salva
        com_foto = [p for p in Product.objects.all() if p.image]
        self.assertGreaterEqual(len(com_foto), 24)
        self.assertTrue(com_foto[0].image.name.endswith(".png"))

    def test_seed_idempotente(self):
        call_command("seed_makerworld")
        n = Product.objects.count()
        call_command("seed_makerworld")
        self.assertEqual(Product.objects.count(), n)

    def test_filtro_material(self):
        call_command("seed_makerworld")
        resina = ProductQuery.search(material="Resina")
        self.assertGreater(resina.count(), 0)
        self.assertTrue(all(p.material == "Resina" for p in resina))
        self.assertIn("Resina", ProductQuery.materials())
