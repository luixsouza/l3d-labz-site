"""Zera o catálogo de produtos com backup JSON reversível.

POR QUE APAGAR Product É SEGURO:
- `OrderItem.product` é FK(SET_NULL, null=True) → deletar Product **não apaga pedidos**;
  o item continua com o snapshot (product_name, unit_price) intacto.
- A galeria (ProductImage) cai por CASCADE — desejado, pois fotos sem produto são lixo.
- Category usa PROTECT em Product.category → **jamais apagamos categorias aqui**.

POR QUE HÁ BACKUP OBRIGATÓRIO:
- A operação é destrutiva e irreversível sem backup.
- O JSON gerado pode ser recarregado com `python manage.py loaddata <arquivo>`.

ARQUIVOS DE MEDIA NÃO SÃO REMOVIDOS:
- Arquivos físicos em media/products/ (imagens, GLB, STL) NÃO são apagados por este
  comando, intencionalmente. O risco de remover arquivos referenciados por outros
  registros (ou simplesmente ainda úteis) é alto. Use `podar_galeria` ou limpeza
  manual do storage para isso.

Uso:
    python manage.py limpar_catalogo               # dry-run (padrão — não apaga nada)
    python manage.py limpar_catalogo --dry-run     # equivalente ao padrão, mais explícito
    python manage.py limpar_catalogo --confirmar   # backup JSON + apaga todos os Product
"""
from __future__ import annotations

import io
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.catalog.models import Category, Product, ProductImage

# ---------------------------------------------------------------------------
# Diretório de backups (criado automaticamente se não existir)
# ---------------------------------------------------------------------------
BACKUP_DIR = Path(settings.BASE_DIR) / "backups"


class Command(BaseCommand):
    help = (
        "Zera o catálogo: faz backup JSON timestamped de todos os Product + ProductImage "
        "e então apaga todos os produtos (categorias ficam intactas). "
        "Sem a flag --confirmar o comando é dry-run por padrão — não apaga nada."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirmar",
            action="store_true",
            help="Executa o backup e o delete. Sem esta flag o comando é dry-run.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry-run explícito (comportamento padrão — não precisa passar).",
        )

    def handle(self, *args, **options):
        confirmar = options["confirmar"]

        # --- contagem inicial ---
        n_produtos = Product.objects.count()
        n_imagens = ProductImage.objects.count()
        n_categorias = Category.objects.count()

        self.stdout.write(
            f"Produtos: {n_produtos} · "
            f"Imagens de galeria: {n_imagens} · "
            f"Categorias: {n_categorias}"
        )

        # --- modo dry-run (default) ---
        if not confirmar:
            self.stdout.write(self.style.WARNING(
                f"[DRY-RUN] Nenhum dado foi apagado. "
                f"Seriam removidos {n_produtos} produto(s) e {n_imagens} imagem(ns) de galeria. "
                f"Rode com --confirmar para executar."
            ))
            return

        # --- confirmar: backup + delete ---

        # 1. garantir diretório de backup
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # 2. nome de arquivo com timestamp UTC para evitar colisão
        timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
        backup_path = BACKUP_DIR / f"catalogo-{timestamp}.json"

        self.stdout.write(f"Gerando backup em: {backup_path}")
        # Captura o output do dumpdata em memória e escreve com UTF-8 explícito.
        # Usar --output do dumpdata no Windows pode gerar arquivos em CP1252 (encoding
        # do sistema), o que impede o loaddata de restaurar corretamente.
        buf = io.StringIO()
        call_command(
            "dumpdata",
            "catalog.Product",
            "catalog.ProductImage",
            indent=2,
            stdout=buf,
        )
        backup_path.write_text(buf.getvalue(), encoding="utf-8")

        tamanho_kb = backup_path.stat().st_size / 1024
        self.stdout.write(
            f"Backup gerado: {backup_path.name} "
            f"({tamanho_kb:.1f} KB, {n_produtos} produto(s), {n_imagens} imagem(ns))"
        )

        # 3. apagar todos os produtos (galeria cai por CASCADE; pedidos ficam intactos via SET_NULL)
        self.stdout.write("Apagando todos os produtos...")
        Product.objects.all().delete()

        # 4. contagem pós-delete
        n_produtos_depois = Product.objects.count()
        n_imagens_depois = ProductImage.objects.count()
        n_categorias_depois = Category.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f"Limpeza concluída. "
            f"Produtos restantes: {n_produtos_depois} · "
            f"Imagens restantes: {n_imagens_depois} · "
            f"Categorias (inalteradas): {n_categorias_depois}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Para restaurar: python manage.py loaddata {backup_path}"
        ))
