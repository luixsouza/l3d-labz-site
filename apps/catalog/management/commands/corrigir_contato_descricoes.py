"""Reescreve Product.description: substitui menções de WhatsApp por Instagram @l3d_labz.

O comando localiza produtos cujas descrições ainda citam "WhatsApp" (legado dos
importadores antigos) e substitui as frases de contato conhecidas pela frase canônica
de Instagram. É idempotente: rodar duas vezes não altera nada na segunda passagem.

Frases substituídas (case-insensitive, regex):
  - "Orçamento e prazo pelo WhatsApp."
  - "orçamento e prazo pelo WhatsApp."        (variante minúscula inicial)
  - "preço e prazo combinados no WhatsApp."   (seed_makerworld)
  - Fallback: qualquer palavra "WhatsApp" isolada -> "Instagram @l3d_labz"

Frase canônica de destino: "Orçamento e prazo pelo Instagram @l3d_labz."

Uso:
    python manage.py corrigir_contato_descricoes --dry-run
    python manage.py corrigir_contato_descricoes --dry-run --limite 5
    python manage.py corrigir_contato_descricoes
    python manage.py corrigir_contato_descricoes --limite 100
"""
from __future__ import annotations

import re

from django.core.management.base import BaseCommand

from apps.catalog.models import Product

# ---------------------------------------------------------------------------
# Constante canônica
# ---------------------------------------------------------------------------

FRASE_INSTAGRAM = "Orçamento e prazo pelo Instagram @l3d_labz."

# Padrões de substituição, aplicados em ordem (mais específico primeiro).
# Regex case-insensitive; cada tupla é (padrão, substituição).
_SUBSTITUICOES: list[tuple[str, str]] = [
    # Variante 1: importar_makerworld / importar_copa — frase completa
    (
        r"[Oo]rçamento e prazo pelo WhatsApp\.",
        FRASE_INSTAGRAM,
    ),
    # Variante 2: seed_makerworld — frase ligeiramente diferente
    (
        r"[Pp]reço e prazo combinados no WhatsApp\.",
        FRASE_INSTAGRAM,
    ),
    # Fallback genérico: palavra "WhatsApp" avulsa que não foi capturada acima
    (
        r"\bWhatsApp\b",
        "Instagram @l3d_labz",
    ),
]

_COMPILED: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pat, re.IGNORECASE), repl)
    for pat, repl in _SUBSTITUICOES
]


def _corrigir(texto: str) -> str:
    """Aplica todas as substituições em sequência e devolve o texto corrigido."""
    for pattern, repl in _COMPILED:
        texto = pattern.sub(repl, texto)
    return texto


class Command(BaseCommand):
    help = (
        "Reescreve Product.description trocando menções de WhatsApp por Instagram @l3d_labz. "
        "Idempotente — produtos sem 'WhatsApp' na descrição são pulados."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Mostra as alterações propostas sem gravar no banco.",
        )
        parser.add_argument(
            "--limite",
            type=int,
            default=0,
            metavar="N",
            help="Processa no máximo N produtos (0 = sem limite).",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        limite: int = options["limite"]

        if dry_run:
            self.stdout.write(self.style.WARNING("modo dry-run — nada será salvo"))

        # Filtra só produtos com "whatsapp" na descrição (case-insensitive).
        qs = Product.objects.filter(description__icontains="whatsapp").order_by("pk")
        if limite > 0:
            qs = qs[:limite]

        total = 0
        alterados = 0
        ja_ok = 0

        for p in qs:
            total += 1
            desc = p.description or ""

            # Segurança extra: pula se description é vazia ou None
            if not desc.strip():
                ja_ok += 1
                continue

            nova_desc = _corrigir(desc)

            if nova_desc == desc:
                # Nenhuma troca necessária (não deve acontecer dado o filtro, mas defensivo)
                ja_ok += 1
                continue

            # Trecho antes/depois (truncado para legibilidade)
            trecho_antes = desc[:120].replace("\n", " ")
            trecho_depois = nova_desc[:120].replace("\n", " ")

            self.stdout.write(
                f"[{p.slug}]\n"
                f"  antes : {trecho_antes!r}\n"
                f"  depois: {trecho_depois!r}"
            )

            if not dry_run:
                try:
                    p.description = nova_desc
                    p.save(update_fields=["description"])
                    alterados += 1
                except Exception as exc:  # noqa: BLE001
                    self.stderr.write(
                        self.style.ERROR(f"  ERRO ao salvar {p.slug}: {exc}")
                    )
            else:
                alterados += 1

        # --- resumo ---
        self.stdout.write("")
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"dry-run concluído — {alterados} seriam alterados / "
                    f"{ja_ok} já-ok (sem 'WhatsApp') / {total} total"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"concluído — {alterados} alterados / "
                    f"{ja_ok} já-ok / {total} total"
                )
            )
