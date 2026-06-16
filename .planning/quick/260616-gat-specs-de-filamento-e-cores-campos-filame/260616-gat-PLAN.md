---
phase: quick-260616-gat
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - apps/catalog/models.py
  - apps/catalog/migrations/0007_product_filament_grams_product_color_count.py
  - apps/catalog/mappers.py
  - apps/catalog/management/commands/extrair_specs_3mf.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Product tem dois campos novos: filament_grams (int, default 0) e color_count (smallint, default 1)"
    - "ProductMapper.to_dict expõe filament_grams, color_count e filament_display (ex.: '120 g')"
    - "Comando extrair_specs_3mf parseia modelo.3mf de cada pasta <slug>/ e atualiza só filament_grams/color_count"
    - "Comando degrada graciosamente: 3MF ausente/corrompido/sem metadata → warn e segue, nunca quebra"
    - "Comando suporta --base, --only, --limite, --dry-run; idempotente por slugify(pasta.name)"
  artifacts:
    - path: "apps/catalog/models.py"
      provides: "Campos filament_grams e color_count no Product"
      contains: "filament_grams"
    - path: "apps/catalog/management/commands/extrair_specs_3mf.py"
      provides: "Comando de extração de specs do 3MF"
      contains: "class Command"
    - path: "apps/catalog/migrations/0007_product_filament_grams_product_color_count.py"
      provides: "Migração dos dois campos novos"
      contains: "AddField"
  key_links:
    - from: "apps/catalog/management/commands/extrair_specs_3mf.py"
      to: "apps/catalog/models.py (Product.filament_grams/color_count)"
      via: "Product.objects.filter(slug=...).update_fields"
      pattern: "update_fields"
    - from: "apps/catalog/mappers.py (ProductMapper.to_dict)"
      to: "Product.filament_grams/color_count"
      via: "leitura de atributos do model"
      pattern: "filament_grams"
---

<objective>
Adicionar specs de impressão ao catálogo: gramas de filamento e número de cores
por produto, mais um comando de management que extrai esses valores do 3MF
original (Bambu/MakerWorld) e preenche os campos.

Purpose: dar ao cliente dados reais de impressão (consumo de filamento e
multicor) — base de dados para a UI da Parte B e para orçamento.
Output: 2 campos novos no Product + migração + exposição no mapper + comando
extrair_specs_3mf (roda no server, onde estão os 3MF).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md

<interfaces>
<!-- Padrão do importador a espelhar. Executor NÃO precisa explorar o codebase. -->

apps/catalog/models.py — Product (campos de impressão 3D já existentes):
```python
material = models.CharField("material", max_length=60, default="PLA")
dimensions = models.CharField("dimensões", max_length=80, blank=True)
print_time_hours = models.PositiveIntegerField("tempo de impressão (h)", default=4)
```
Os dois campos novos vão neste mesmo bloco "# Específicos de impressão 3D".
Product.slug é único; idempotência usa slugify(pasta.name) == slug.

apps/catalog/management/commands/importar_makerworld.py — padrão a seguir:
- BaseCommand com help pt-br multilinha (docstring + atributo help).
- add_arguments: --base (required), --only (default ""), --limite (type=int default 0).
- handle: valida `base.is_dir()`; `subpastas = sorted(p for p in base.iterdir() if p.is_dir())`;
  filtra por --only; respeita --limite; `slug = slugify(pasta.name)`.
- Usa self.stdout.write / self.stderr.write / self.style.SUCCESS / self.style.ERROR.
- Atualização parcial idempotente: `p.save(update_fields=[...])`.

apps/catalog/mappers.py — ProductMapper.to_dict retorna dict com material/etc.
Adicionar as chaves novas no dict de to_dict (não em to_detail) para ficar
disponível em cards e detalhe.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Campos filament_grams/color_count no Product + migração + mapper</name>
  <files>apps/catalog/models.py, apps/catalog/migrations/0007_product_filament_grams_product_color_count.py, apps/catalog/mappers.py</files>
  <action>
No bloco "# Específicos de impressão 3D" de apps/catalog/models.py (logo após print_time_hours), adicionar dois campos:
filament_grams = PositiveIntegerField("gramas de filamento", default=0, help_text="Consumo total de filamento em gramas extraído do 3MF. 0 = desconhecido.")
e color_count = PositiveSmallIntegerField("número de cores", default=1, help_text="Quantidade de cores/filamentos distintos no 3MF.").
Schema apenas — sem propriedades nem efeito colateral (camada model).

Gerar a migração via management (NÃO escrever à mão se makemigrations rodar): o orquestrador roda
`DJANGO_SETTINGS_MODULE=config.settings.dev .venv/Scripts/python.exe manage.py makemigrations catalog`.
Se preferir determinismo, criar manualmente apps/catalog/migrations/0007_product_filament_grams_product_color_count.py com dependencies=[("catalog","0006_productimage")] e duas migrations.AddField (filament_grams PositiveIntegerField default=0; color_count PositiveSmallIntegerField default=1). COMMITAR a migração gerada.

Em apps/catalog/mappers.py, dentro de ProductMapper.to_dict, adicionar ao dict retornado:
"filament_grams": instance.filament_grams,
"color_count": instance.color_count,
"filament_display": (f"{instance.filament_grams} g" if instance.filament_grams else "") (display-ready, pt-br; vazio quando 0 = desconhecido).
Não duplicar em to_detail (to_detail já chama to_dict).
  </action>
  <verify>
    <automated>DJANGO_SETTINGS_MODULE=config.settings.dev .venv/Scripts/python.exe manage.py makemigrations catalog --check --dry-run; DJANGO_SETTINGS_MODULE=config.settings.dev .venv/Scripts/python.exe manage.py migrate catalog; DJANGO_SETTINGS_MODULE=config.settings.dev .venv/Scripts/python.exe manage.py check</automated>
  </verify>
  <done>migrate aplica a 0007 sem erro; `manage.py check` limpo; to_dict retorna filament_grams, color_count e filament_display.</done>
</task>

<task type="auto">
  <name>Task 2: Comando extrair_specs_3mf (parser defensivo do 3MF)</name>
  <files>apps/catalog/management/commands/extrair_specs_3mf.py</files>
  <action>
Criar comando novo espelhando o estilo de importar_makerworld (docstring pt-br multilinha + help; self.stdout/self.stderr/self.style).

Imports: zipfile, xml.etree.ElementTree as ET, from pathlib import Path, from django.core.management.base import BaseCommand, from django.utils.text import slugify, from apps.catalog.models import Product.

add_arguments: --base (required), --only (default ""), --limite (type=int default 0), --dry-run (action="store_true").

handle: validar base.is_dir() (erro + return se não). subpastas = sorted(p for p in base.iterdir() if p.is_dir()); filtra por --only (p.name == only); respeita --limite. Para cada pasta: slug = slugify(pasta.name); localizar o 3MF: tmf = pasta / "modelo.3mf"; se não existir, tentar primeiro *.3mf via sorted(pasta.glob("*.3mf")) → se vazio, self.stderr.write aviso "sem 3MF" e continue (NÃO quebrar).

Parser defensivo — função-helper module-level `_extrair_specs(tmf_path) -> tuple[int, int] | None` retornando (gramas_arredondado, num_cores) ou None se nada parseável:
- Abrir o 3MF como zip (try zipfile.ZipFile; except BadZipFile/OSError → return None).
- Tentar nesta ordem de membros (case-insensitive, pois alguns escrevem "Metadata/slice_info.config"): primeiro qualquer nome que termine em "slice_info.config", depois qualquer "project_settings.config". Usar zf.namelist() e casar por .lower().endswith(...).
- slice_info.config (XML do Bambu/Orca): parsear com ET.fromstring(bytes). O schema típico tem elementos <filament .../> com atributos. PARSEAR DEFENSIVAMENTE — varrer todos os elementos cujo tag.lower() == "filament" (em qualquer profundidade via .iter()). Para gramas: ler atributo "used_g" (Bambu) com fallback para qualquer atributo cujo nome.lower() contenha "used" e "g" (ex.: used_g); converter float e somar. Para cores: contar elementos <filament> distintos; se houver atributo "color"/"colour", contar cores distintas (normalizadas .lower()); senão contar o nº de elementos filament. color_count = max(1, distintas).
- Fallback project_settings.config: costuma ser JSON-ish ou XML com chaves tipo "filament_colour" (lista) e sem gramas confiáveis. Tentar: se for parseável como XML, procurar texto/atributos com "filament_colour"/"filament_color" e contar entradas distintas → color_count. Gramas geralmente indisponível aqui → manter 0. Try/except envolvendo TUDO; qualquer falha → seguir para o próximo membro/return None.
- Arredondar gramas com round() para int (campo é PositiveIntegerField).

No handle, para cada pasta: chamar _extrair_specs; se None → self.stderr.write aviso e continue. Se ok: localizar o produto por Product.objects.filter(slug=slug).first(); se não existir, aviso "produto não encontrado p/ slug" e continue. Se --dry-run: self.stdout.write(f"  · {slug}: filament_grams={g} color_count={c} (dry-run — sem salvar)") e NÃO salvar. Senão: prod.filament_grams = g; prod.color_count = c; prod.save(update_fields=["filament_grams", "color_count"]) e log de sucesso. Contar atualizados/pulados e imprimir resumo final com self.style.SUCCESS.

CRÍTICO p/ validação do orquestrador: documentar no SUMMARY EXATAMENTE quais tags/atributos o parser lê (ex.: elemento <filament used_g="12.34" color="#FF0000"/> dentro de slice_info.config; fallback project_settings.config chave filament_colour), pois o formato real será validado contra um 3MF de verdade no server.
  </action>
  <verify>
    <automated>DJANGO_SETTINGS_MODULE=config.settings.dev .venv/Scripts/python.exe manage.py help extrair_specs_3mf; DJANGO_SETTINGS_MODULE=config.settings.dev .venv/Scripts/python.exe -c "import importlib; importlib.import_module('apps.catalog.management.commands.extrair_specs_3mf'); print('import ok')"</automated>
  </verify>
  <done>Comando importa sem erro e aparece em `manage.py help`. Parser é totalmente envolvido em try/except (3MF ausente/corrompido/sem metadata nunca levanta exceção). --dry-run não salva. Atualiza só filament_grams/color_count via update_fields.</done>
</task>

</tasks>

<verification>
Verificação automática (orquestrador executa, sem checkpoint humano):

1. Migração + check:
   `manage.py makemigrations catalog --check --dry-run` (deve estar limpo após Task 1), `migrate catalog`, `check`.

2. 3MF fake de teste (orquestrador constrói): criar pasta temp `<temp>/produto-x/` contendo `modelo.3mf` = um zip com membro `Metadata/slice_info.config` cujo XML contém 2 filamentos distintos, ex.:
   ```
   <config><plate>
     <filament id="1" used_g="12.34" color="#FF0000" type="PLA"/>
     <filament id="2" used_g="20.00" color="#00FF00" type="PLA"/>
   </plate></config>
   ```
   Criar um Product com slug "produto-x" no banco de teste. Rodar:
   - `manage.py extrair_specs_3mf --base <temp> --dry-run` → imprime filament_grams=32 color_count=2, NÃO salva (valores no banco permanecem default).
   - `manage.py extrair_specs_3mf --base <temp>` → após rodar, Product(slug="produto-x").filament_grams == 32 e color_count == 2.

3. Degradação graciosa: rodar contra uma pasta sem 3MF e contra um zip inválido → comando emite aviso e termina com exit 0 (não levanta exceção).
</verification>

<success_criteria>
- Product tem filament_grams (PositiveIntegerField default 0) e color_count (PositiveSmallIntegerField default 1), com migração 0007 commitada.
- ProductMapper.to_dict expõe filament_grams, color_count, filament_display.
- extrair_specs_3mf existe, parseia slice_info.config (fallback project_settings.config), é idempotente por slug, suporta --base/--only/--limite/--dry-run, atualiza só os dois campos via update_fields e degrada graciosamente.
- SUMMARY documenta as tags/atributos exatos parseados (para validação contra 3MF real no server) + RUNBOOK: no server rodar `--dry-run` primeiro, conferir, depois rodar de verdade (NÃO contra prod neste quick).
</success_criteria>

<output>
Create `.planning/quick/260616-gat-specs-de-filamento-e-cores-campos-filame/260616-gat-SUMMARY.md` when done.

O SUMMARY DEVE conter:
1. Tags/atributos exatos que o parser lê (slice_info.config e fallback).
2. RUNBOOK do server: `--dry-run` primeiro → conferir saída → rodar de verdade. NÃO rodar contra prod neste quick.
</output>
