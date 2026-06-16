"""Extrai specs de filamento de arquivos .3mf e preenche Product.filament_grams/color_count.

Para cada subpasta de --base que contenha um arquivo .3mf (preferência: modelo.3mf),
o comando abre o arquivo como ZIP, localiza o membro Metadata/slice_info.config (XML
do Bambu/Orca Slicer) e extrai:
  - filament_grams: soma de used_g de todos os elementos <filament>.
  - color_count: número de cores distintas (atributo "color") ou nº de elementos <filament>.

Fallback: se slice_info.config não existir, tenta project_settings.config (lê cor de
filament_colour/filament_color como contagem de entradas distintas; gramas = 0).

O parser é totalmente defensivo: qualquer falha (ZIP corrompido, XML malformado,
membro ausente) emite um aviso no stderr e pula a pasta — nunca levanta exceção.

O comando é idempotente por slug: slugify(pasta.name) deve casar com Product.slug.
Só atualiza filament_grams e color_count via update_fields — nunca toca outros campos.

Uso:
    python manage.py extrair_specs_3mf --base /ssd/modelos
    python manage.py extrair_specs_3mf --base /ssd/modelos --only meu-produto
    python manage.py extrair_specs_3mf --base /ssd/modelos --limite 10
    python manage.py extrair_specs_3mf --base /ssd/modelos --dry-run
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import Product


# ---------------------------------------------------------------------------
# Parser defensivo do .3mf
# ---------------------------------------------------------------------------

def _extrair_specs(tmf_path: Path) -> tuple[int, int] | None:
    """Abre um .3mf e retorna (filament_grams, color_count) ou None se não parseável.

    Estratégia de leitura (em ordem):
    1. Membro cujo nome termine em 'slice_info.config' (XML do Bambu/Orca Slicer).
       - Varre todos os elementos cujo tag.lower() == 'filament' (em qualquer profundidade).
       - Atributo 'used_g' → float somado para filament_grams.
       - Atributo 'color' → normalizado .lower() para contar cores distintas.
       - color_count = max(1, len(cores_distintas)) — ou nº de elementos se sem atributo.
    2. Membro cujo nome termine em 'project_settings.config' (fallback, formato XML ou JSON-ish).
       - Conta entradas distintas em 'filament_colour' / 'filament_color'; gramas = 0.
    3. Qualquer outra falha → return None.
    """
    try:
        zf = zipfile.ZipFile(tmf_path, "r")
    except (zipfile.BadZipFile, OSError):
        return None

    with zf:
        nomes = zf.namelist()
        # Normaliza casing para busca case-insensitive
        nomes_lower = [n.lower() for n in nomes]

        # --- tentativa 1: slice_info.config ---
        slice_idx = next(
            (i for i, n in enumerate(nomes_lower) if n.endswith("slice_info.config")),
            None,
        )
        if slice_idx is not None:
            try:
                data = zf.read(nomes[slice_idx])
                raiz = ET.fromstring(data)
                elementos_filament = [el for el in raiz.iter() if el.tag.lower() == "filament"]
                if elementos_filament:
                    gramas_total = 0.0
                    cores: set[str] = set()
                    for el in elementos_filament:
                        # Gramas: atributo 'used_g' (Bambu/Orca) com fallback para
                        # qualquer atributo cujo nome contenha 'used' e 'g'.
                        g_val = el.get("used_g")
                        if g_val is None:
                            g_val = next(
                                (v for k, v in el.attrib.items()
                                 if "used" in k.lower() and "g" in k.lower()),
                                None,
                            )
                        if g_val is not None:
                            try:
                                gramas_total += float(g_val)
                            except ValueError:
                                pass

                        # Cor: atributo 'color' ou 'colour' (normalizado para lowercase).
                        cor = el.get("color") or el.get("colour")
                        if cor:
                            cores.add(cor.strip().lower())

                    filament_grams = round(gramas_total)
                    color_count = max(1, len(cores)) if cores else max(1, len(elementos_filament))
                    return filament_grams, color_count
            except Exception:
                # XML malformado ou leitura falhou — tenta fallback
                pass

        # --- tentativa 2: project_settings.config ---
        proj_idx = next(
            (i for i, n in enumerate(nomes_lower) if n.endswith("project_settings.config")),
            None,
        )
        if proj_idx is not None:
            try:
                data = zf.read(nomes[proj_idx]).decode("utf-8", errors="replace")
                # Pode ser XML com múltiplos elementos filament_colour/filament_color,
                # ou JSON-ish. Tentamos XML primeiro.
                try:
                    raiz = ET.fromstring(data)
                    cores: set[str] = set()
                    for el in raiz.iter():
                        chave = el.tag.lower()
                        valor = (el.text or "").strip()
                        if ("filament_colour" in chave or "filament_color" in chave) and valor:
                            cores.add(valor.lower())
                        for attr_k, attr_v in el.attrib.items():
                            if ("filament_colour" in attr_k.lower()
                                    or "filament_color" in attr_k.lower()):
                                cores.add(attr_v.strip().lower())
                    if cores:
                        return 0, max(1, len(cores))
                except ET.ParseError:
                    # Não é XML válido — tenta heurística de texto plano
                    import re
                    padrao = re.compile(
                        r'"filament_colou?r"\s*:\s*\[([^\]]*)\]', re.IGNORECASE
                    )
                    m = padrao.search(data)
                    if m:
                        entradas = [
                            e.strip().strip('"').lower()
                            for e in m.group(1).split(",")
                            if e.strip().strip('"')
                        ]
                        if entradas:
                            return 0, max(1, len(set(entradas)))
            except Exception:
                pass

    return None


# ---------------------------------------------------------------------------
# Comando principal
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = (
        "Extrai specs de filamento (.3mf Bambu/Orca) e atualiza Product.filament_grams e "
        "Product.color_count. Parser defensivo: 3MF ausente, corrompido ou sem metadata "
        "emite aviso e pula — nunca interrompe o lote. Idempotente por slug de pasta."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--base", required=True,
            help="Diretório raiz com as subpastas de produto (ex.: /ssd/modelos).",
        )
        parser.add_argument(
            "--only", default="",
            help="Processa só a pasta com este nome exato (ex.: meu-produto).",
        )
        parser.add_argument(
            "--limite", type=int, default=0,
            help="Processa no máximo N pastas (0 = sem limite).",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Simula a extração e exibe os valores, mas NÃO salva no banco.",
        )

    def handle(self, *args, **options):
        base = Path(options["base"])
        if not base.is_dir():
            self.stderr.write(self.style.ERROR(f"diretório não encontrado: {base}"))
            return

        only = options["only"].strip()
        limite = options["limite"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("modo dry-run ativo — nada será salvo no banco"))

        # --- coleta subpastas ordenadas ---
        subpastas = sorted(p for p in base.iterdir() if p.is_dir())
        if only:
            subpastas = [p for p in subpastas if p.name == only]

        atualizados = 0
        pulados = 0
        processados = 0

        for pasta in subpastas:
            if limite and processados >= limite:
                break
            processados += 1

            slug = slugify(pasta.name)

            # --- localizar o .3mf ---
            tmf = pasta / "modelo.3mf"
            if not tmf.exists():
                candidatos = sorted(pasta.glob("*.3mf"))
                if not candidatos:
                    self.stderr.write(f"  ! {pasta.name}: sem arquivo .3mf — pulando")
                    pulados += 1
                    continue
                tmf = candidatos[0]

            # --- parsear ---
            resultado = _extrair_specs(tmf)
            if resultado is None:
                self.stderr.write(
                    f"  ! {pasta.name}: não foi possível extrair specs de {tmf.name} — pulando"
                )
                pulados += 1
                continue

            g, c = resultado

            if dry_run:
                self.stdout.write(
                    f"  · {slug}: filament_grams={g} color_count={c} (dry-run — sem salvar)"
                )
                continue

            # --- localizar o produto ---
            prod = Product.objects.filter(slug=slug).first()
            if prod is None:
                self.stderr.write(f"  ! produto não encontrado para slug '{slug}' — pulando")
                pulados += 1
                continue

            prod.filament_grams = g
            prod.color_count = c
            prod.save(update_fields=["filament_grams", "color_count"])
            self.stdout.write(f"  · {slug}: filament_grams={g} g, color_count={c} — atualizado")
            atualizados += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"dry-run concluído — {processados} pastas analisadas, {pulados} puladas"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"extrair_specs_3mf: {atualizados} atualizados, {pulados} pulados"
                f" — total analisado: {processados}"
            ))
