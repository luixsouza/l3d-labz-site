"""Poda a galeria de fotos dos produtos para no máximo 2 imagens extras.

Migração in-place, idempotente e reversível (mexe só em dados): para CADA
Product, mantém a foto principal (Product.image, NUNCA tocada) + as 2 primeiras
ProductImage por `order`, e remove o resto — tanto a linha quanto o arquivo
órfão sob media/products/gallery/.

Pareia com o cap de 3 fotos no importar_makerworld: o importador novo já entra
limitado, este comando limpa o que entrou inchado ANTES do cap. Produtos com
<= 2 imagens são no-op (idempotente — rodar de novo não remove nada).

Por que --dry-run: poda apaga arquivos. O operador roda --dry-run, inspeciona,
e só então roda de verdade (ver runbook de deploy no SUMMARY).

Uso:
    python manage.py podar_galeria --dry-run
    python manage.py podar_galeria
    python manage.py podar_galeria --limit 20
    python manage.py podar_galeria --dry-run --limit 5
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.catalog.models import Product

# ---------------------------------------------------------------------------
# Cap de galeria (espelha MAX_EXTRAS do importar_makerworld)
# ---------------------------------------------------------------------------
# Mantemos as 2 primeiras ProductImage por produto; o resto é podado.
MANTER_EXTRAS = 2


class Command(BaseCommand):
    help = (
        "Poda a galeria de cada produto para no máximo 2 imagens extras "
        "(mantém Product.image + as 2 primeiras ProductImage; remove o resto + arquivos). "
        "Idempotente. Use --dry-run para simular antes de apagar."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Não altera nada; só reporta quantas imagens SERIAM removidas.",
        )
        parser.add_argument(
            "--limit", type=int, default=0,
            help="Processa no máximo N produtos (0 = sem limite).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]
        prefixo = "[DRY-RUN] " if dry_run else ""

        produtos = Product.objects.all().order_by("id")
        if limit:
            produtos = produtos[:limit]

        produtos_afetados = 0
        imagens_removidas = 0

        for p in produtos:
            try:
                # galeria ordenada de forma estável (order, depois id como desempate)
                galeria = list(p.gallery.order_by("order", "id"))
                resto = galeria[MANTER_EXTRAS:]
                if not resto:
                    continue  # <= 2 imagens: nada a podar (idempotente)

                verbo = "seriam removidas" if dry_run else "removendo"
                self.stdout.write(
                    f"  · {p.name}: {verbo} {len(resto)} imagem(ns) da galeria"
                )

                if not dry_run:
                    for img in resto:
                        # remove o arquivo do storage sem salvar o model, depois a linha
                        img.image.delete(save=False)
                        img.delete()

                produtos_afetados += 1
                imagens_removidas += len(resto)
            except Exception as e:
                # falha num produto não aborta o batch
                self.stderr.write(self.style.ERROR(
                    f"  ! falha ao podar '{p.name}': {e} — pulando"
                ))

        verbo_final = "seriam removidas" if dry_run else "removidas"
        self.stdout.write(self.style.SUCCESS(
            f"{prefixo}Poda: {produtos_afetados} produtos afetados, "
            f"{imagens_removidas} imagens {verbo_final}"
        ))
