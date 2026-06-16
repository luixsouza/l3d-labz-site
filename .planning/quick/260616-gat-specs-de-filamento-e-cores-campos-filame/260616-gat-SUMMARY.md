---
phase: quick-260616-gat
plan: "01"
subsystem: catalog
tags: [filament, 3mf, management-command, migration, mapper]
dependency_graph:
  requires: []
  provides:
    - Product.filament_grams
    - Product.color_count
    - ProductMapper.filament_display
    - extrair_specs_3mf command
  affects:
    - apps/catalog/models.py
    - apps/catalog/migrations/0007_product_filament_grams_product_color_count.py
    - apps/catalog/mappers.py
    - apps/catalog/management/commands/extrair_specs_3mf.py
tech_stack:
  added: []
  patterns:
    - parser defensivo com zipfile + xml.etree.ElementTree
    - update_fields parcial idempotente (só filament_grams/color_count)
    - management command estilo importar_makerworld (BaseCommand, pt-br, --dry-run)
key_files:
  created:
    - apps/catalog/migrations/0007_product_filament_grams_product_color_count.py
    - apps/catalog/management/commands/extrair_specs_3mf.py
  modified:
    - apps/catalog/models.py
    - apps/catalog/mappers.py
decisions:
  - filament_display retorna string vazia quando filament_grams==0 (desconhecido), não '0 g'
  - color_count mínimo 1 mesmo quando não há atributo color (max(1, len(elementos)))
  - Fallback project_settings.config retorna gramas=0 (confiabilidade baixa nesse arquivo)
metrics:
  duration: "~25 min"
  completed: "2026-06-16"
  tasks: 2
  files: 4
---

# Quick 260616-gat: Specs de Filamento e Cores — SUMMARY

**One-liner:** Dois campos novos no Product (filament_grams/color_count) + migração 0007 + exposição no mapper + comando extrair_specs_3mf com parser defensivo de .3mf Bambu/Orca.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Campos filament_grams/color_count + migração + mapper | 911d282 | models.py, 0007_*.py, mappers.py |
| 2 | Comando extrair_specs_3mf (parser defensivo do .3mf) | bd6c4e8 | extrair_specs_3mf.py |

## What Was Built

### Task 1 — Campos no Model, Migração, Mapper

**apps/catalog/models.py** — bloco `# Específicos de impressão 3D`:
```python
filament_grams = models.PositiveIntegerField(
    "gramas de filamento", default=0,
    help_text="Consumo total de filamento em gramas extraído do 3MF. 0 = desconhecido.",
)
color_count = models.PositiveSmallIntegerField(
    "número de cores", default=1,
    help_text="Quantidade de cores/filamentos distintos no 3MF.",
)
```

**Migração** `0007_product_filament_grams_product_color_count.py` — `dependencies=[("catalog","0006_productimage")]`, duas `AddField` (PositiveIntegerField default=0; PositiveSmallIntegerField default=1). Aplicada com sucesso.

**apps/catalog/mappers.py** — `ProductMapper.to_dict` expõe:
```python
"filament_grams": instance.filament_grams,
"color_count": instance.color_count,
"filament_display": f"{instance.filament_grams} g" if instance.filament_grams else "",
```
`filament_display` retorna string vazia quando 0 (desconhecido) — não polui a UI com "0 g".

### Task 2 — Comando extrair_specs_3mf

**Localização do .3mf por pasta:**
1. `<pasta>/modelo.3mf` (preferência)
2. Primeiro `*.3mf` por ordem alfabética (fallback)
3. Nenhum → aviso no stderr + `continue` (exit 0)

**Parser `_extrair_specs(tmf_path) -> tuple[int, int] | None`:**

#### Tentativa 1: `Metadata/slice_info.config` (XML do Bambu/Orca Slicer)
- Membro localizado por `name.lower().endswith("slice_info.config")` (case-insensitive)
- Todos os elementos com `tag.lower() == "filament"` em qualquer profundidade via `.iter()`
- **Gramas:** atributo `used_g` → float acumulado; fallback para qualquer atributo cujo nome contenha `"used"` e `"g"`
- **Cores:** atributo `color` (ou `colour`) normalizado `.lower()` — conjunto de valores distintos; se ausente, conta elementos `<filament>`
- `filament_grams = round(soma)` — `color_count = max(1, len(cores_distintas))`

**XML exemplo parseado com sucesso:**
```xml
<config>
  <plate>
    <filament id="1" used_g="12.34" color="#FF0000" type="PLA"/>
    <filament id="2" used_g="20.00" color="#00FF00" type="PLA"/>
  </plate>
</config>
```
→ `filament_grams=32`, `color_count=2`

#### Tentativa 2: `*project_settings.config` (fallback)
- Membro localizado por `name.lower().endswith("project_settings.config")`
- Tenta parsear como XML: procura elementos/atributos com chave `filament_colour` ou `filament_color` — conta valores distintos
- Se XML falhar (ET.ParseError): regex `"filament_colou?r"\s*:\s*\[([^\]]*)\]` para JSON-ish — divide por vírgula, conta strings distintas
- Retorna `(0, color_count)` — gramas ficam 0 (esse arquivo não tem used_g confiável)

#### Proteção total
Toda lógica dentro de `try/except Exception` — `BadZipFile`, `OSError`, `ET.ParseError`, `ValueError` e qualquer outra → retorna `None` → aviso no stderr → próxima pasta.

**Flags suportadas:**
- `--base BASE` (obrigatório)
- `--only NOME` — filtra por nome exato da pasta
- `--limite N` — processa no máximo N pastas (0 = sem limite)
- `--dry-run` — imprime valores mas NÃO salva; confirmado via assert no banco

**Atualização parcial idempotente:**
```python
prod.filament_grams = g
prod.color_count = c
prod.save(update_fields=["filament_grams", "color_count"])
```

## Verificação Executada

### 1. Migração e check

```
manage.py makemigrations catalog --check --dry-run  -> "No changes detected" (migração já criada)
manage.py migrate catalog                           -> "Applying catalog.0007...OK"
manage.py check                                     -> "System check identified no issues (0 silenced)"
```

### 2. .3mf fake (2 filamentos, cores distintas)

XML criado dentro de `Metadata/slice_info.config` num ZIP:
```xml
<config><plate>
  <filament id="1" used_g="12.34" color="#FF0000" type="PLA"/>
  <filament id="2" used_g="20.00" color="#00FF00" type="PLA"/>
</plate></config>
```

| Passo | Comando | Resultado |
|-------|---------|-----------|
| Dry-run | `extrair_specs_3mf --base <tmp> --dry-run` | `filament_grams=32 color_count=2 (dry-run — sem salvar)` |
| Verificar banco (dry-run) | assert filament_grams==0 | PASSED — banco inalterado |
| Real | `extrair_specs_3mf --base <tmp>` | `filament_grams=32 g, color_count=2 — atualizado` |
| Verificar banco (real) | assert filament_grams==32 and color_count==2 | PASSED |

### 3. Degradação graciosa

| Cenário | Resultado |
|---------|-----------|
| Pasta sem .3mf | aviso stderr + pula / exit 0 |
| ZIP inválido (bytes aleatórios) | aviso stderr + pula / exit 0 |

## Tags/Atributos Exatos Parseados (para validação no server)

### slice_info.config (formato primário — Bambu Studio / Orca Slicer)

```
Caminho ZIP: Metadata/slice_info.config  (ou qualquer membro com sufixo slice_info.config, case-insensitive)
```

Elemento alvo: qualquer elemento cujo `tag.lower() == "filament"` em qualquer profundidade.

| Atributo | Lido como | Propósito |
|----------|-----------|-----------|
| `used_g` | float (ex: `"12.34"`) | gramas acumulados — SUM de todos os filamentos |
| `color` | string hex (ex: `"#FF0000"`) | identidade de cor distinta — SET para dedup |
| `colour` | string hex (fallback de `color`) | identidade de cor distinta |

Fallback de gramas: qualquer atributo cujo nome (lowercase) contenha `"used"` e `"g"` (ex: `used_grams`).

**color_count = max(1, len(cores_distintas))** — se nenhum atributo color encontrado, usa o número de elementos `<filament>`.

### project_settings.config (fallback — gramas sempre 0)

```
Caminho ZIP: qualquer membro com sufixo project_settings.config, case-insensitive
```

Chave XML ou JSON procurada: `filament_colour` ou `filament_color` (case-insensitive).
- XML: elemento `<filament_colour>valor</filament_colour>` ou atributo `filament_colour="valor"`
- JSON: `"filament_colour": ["#FF0000", "#00FF00", ...]`

Retorna sempre `filament_grams=0` para este fallback (confiabilidade baixa).

## Deviations from Plan

None — plano executado exatamente como especificado.

## RUNBOOK — Executar no Server

**IMPORTANTE: NÃO rodar contra prod neste quick. Rodar NO SERVER, onde estão os .3mf.**

### Pré-condições

```bash
# 1. Deploy + aplicar migração:
python manage.py migrate catalog
# deve aparecer: Applying catalog.0007_product_filament_grams_product_color_count... OK

# 2. Confirmar que o comando existe:
python manage.py help extrair_specs_3mf
```

### Execução

```bash
# Passo 1 — dry-run (verificar output antes de salvar):
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py extrair_specs_3mf \
    --base /caminho/para/pasta/dos/modelos \
    --dry-run

# Conferir output: cada linha deve mostrar "filament_grams=X color_count=Y (dry-run — sem salvar)"
# Verificar se os valores fazem sentido (ex: gramas típicas PLA: 10-300g por modelo)
# Pastas com "! sem arquivo .3mf" são normais para produtos foto-only

# Passo 2 — rodar de verdade (só após conferir dry-run):
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py extrair_specs_3mf \
    --base /caminho/para/pasta/dos/modelos

# Opcional — testar só um produto antes do lote:
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py extrair_specs_3mf \
    --base /caminho/para/pasta/dos/modelos \
    --only nome-da-pasta-do-produto \
    --dry-run
```

### O que esperar no output

- `! X: sem arquivo .3mf — pulando` → produto foto-only, normal
- `! X: não foi possível extrair specs de modelo.3mf — pulando` → .3mf sem slice_info.config legível
- `· slug: filament_grams=0 g, color_count=2 — atualizado` → 3MF com cores mas sem used_g (project_settings fallback)
- `! produto não encontrado para slug 'X' — pulando` → pasta no SSD não tem produto no banco ainda

### Idempotência

O comando é seguro de rodar múltiplas vezes. Cada execução sobrescreve apenas `filament_grams` e `color_count` — sem afetar nome, foto, preço, modelo 3D ou qualquer outro campo.

## Known Stubs

None — campos populados com defaults (filament_grams=0, color_count=1) que são valores legítimos representando "desconhecido" e "1 cor". `filament_display` retorna string vazia quando 0, portanto não aparece na UI enquanto não for preenchido pelo comando.

## Threat Flags

None — comando de management (sem endpoint HTTP, sem input do usuário na web, sem acesso a dados sensíveis).

## Self-Check: PASSED

- apps/catalog/models.py contém `filament_grams` e `color_count`: FOUND
- apps/catalog/migrations/0007_product_filament_grams_product_color_count.py: FOUND
- apps/catalog/mappers.py contém `filament_display`: FOUND
- apps/catalog/management/commands/extrair_specs_3mf.py contém `class Command`: FOUND
- Commit 911d282 (Task 1): FOUND
- Commit bd6c4e8 (Task 2): FOUND
- manage.py check: 0 issues
- migrate catalog 0007: OK
- dry-run filament_grams=32 color_count=2: PASSED
- real run assert filament_grams==32 color_count==2: PASSED
- degradacao graceful (sem .3mf, zip invalido): exit 0: PASSED
