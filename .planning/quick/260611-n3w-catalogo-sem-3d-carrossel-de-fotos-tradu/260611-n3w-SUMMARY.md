---
phase: quick-260611-n3w
status: done
commits:
  - 9822c50 feat(catalogo): ProductImage + galeria no importador + tradução via OpenAI
  - 0ebcb88 feat(ui): remove visualização 3D + carrossel de fotos no detalhe
screenshots:
  - C:\dev\l3d-labz-site\.uat\screenshots\N3W-01-catalogo-sem3d.png
  - C:\dev\l3d-labz-site\.uat\screenshots\N3W-02-detalhe-carrossel.png
  - C:\dev\l3d-labz-site\.uat\screenshots\N3W-02b-detalhe-carrossel-slide2.png
---

# 260611-N3W — Catálogo sem 3D + Carrossel de Fotos + Tradução: SUMMARY

## O que foi feito

### Task 1 — Model ProductImage + migration + admin + mapper/query + importador

**Model e migration:**
- `ProductImage(TimeStampedModel)` adicionado em `apps/catalog/models.py` com FK `product` (`related_name="gallery"`), `image`, `order`. Migration `0006_productimage.py` criada e aplicada.

**Admin:**
- `ProductImageInline(TabularInline)` adicionado; registrado em `ProductAdmin.inlines`.

**Mapper (`apps/catalog/mappers.py`):**
- `to_dict`: removidas chaves `model_3d_url` e `has_3d` (3D fora da UI).
- `to_detail`: adicionada chave `gallery` (foto principal + extras ordenadas por `order`); removidas `model_3d_url`, `stl_url`, `has_3d_model`, `has_stl`.

**Query (`apps/catalog/queries.py`):**
- `detail_by_slug`: adicionado `.prefetch_related("gallery")` no producer.

**Importador (`importar_makerworld.py`):**
- `def traduzir_nome(titulo_en)`: POST para OpenAI gpt-4o-mini via urllib stdlib; sem `OPENAI_API_KEY` → retorna título em inglês + aviso no stdout (chave nunca logada); qualquer exceção → fallback com aviso.
- Cache anti-retradução: se o produto existe e o nome atual difere do título original, reutiliza o nome sem chamar a API.
- Flag `--sem3d` substituída por `--com3d` (default: NÃO gera GLB). Dimensões coletadas do 3mf sempre que disponível, mesmo sem `--com3d`.
- Galeria: após salvar a foto principal, `p.gallery.all().delete()` + recria `ProductImage` para cada `fotos[1:]` (idempotente). Falha em foto individual → warning, continua.
- Import de `ProductImage` adicionado no topo.

### Task 2 — Remover 3D da UI + carrossel no detalhe

**`product_card.html`:** Removido bloco `{% if product.has_3d %}...btn-3d...{% endif %}`.

**`base.html`:** Removidos modal `<div class="viewer3d">` e `<script type="module" ... model-viewer ...>` global.

**`product_detail.html`:**
- `.detail-media` substituído: carrossel `.carousel` com setas e dots quando `gallery|length > 1`; imagem estática quando 1 foto; fallback picsum com `onerror`.
- Bloco `{% if product.has_stl %}...Baixar STL...{% endif %}` removido.
- `{% block extra_js %}` com model-viewer removido.

**`app.js`:** IIFE `viewer3d()` (modal 3D) removida (~56 linhas). Carrossel genérico (linhas 78-107) não alterado — já suporta o detalhe do produto.

**`theme.css`:** Blocos `.viewer3d*` (~68 linhas) e `.btn-3d` (~14 linhas) removidos. Adicionado escopo `.detail-media .carousel/.slide/img` para fotos quadradas inteiras no detalhe.

## Verificações executadas

| Verificação | Resultado |
|---|---|
| `makemigrations --check --dry-run` | sem mudanças pendentes |
| `migrate` | 0006_productimage aplicada OK |
| AST parse (models, admin, mappers, queries, importador) | OK |
| Asserts UI: model-viewer/viewer3d/btn-3d/Baixar STL ausentes | OK |
| Assert: carousel presente no product_detail.html | OK |
| Import fixtures sem OPENAI_API_KEY | aviso no stdout, nomes em inglês mantidos |
| `gallery: p.gallery.count()` mecha | **5** (6 fotos − 1 principal) |
| `gallery: p.gallery.count()` aurashell | 1 (2 fotos − 1 principal) |
| Screenshot N3W-01: catálogo sem botão "Ver em 3D" | OK |
| Screenshot N3W-02: detalhe mecha com carrossel (setas + dots) | OK |
| Screenshot N3W-02b: carrossel navegado para slide 2 | OK |

## Checklist must_haves

- [x] Nenhum botão "Ver em 3D", nenhum `<model-viewer>` e nenhum "Baixar STL" aparecem na UI
- [x] O detalhe do produto mostra carrossel quando há 2+ fotos, imagem estática quando 1
- [x] O importador salva TODAS as fotos na galeria (principal + galeria) de forma idempotente
- [x] Sem OPENAI_API_KEY o import mantém o nome em inglês e emite aviso no stdout
- [x] O produto "mecha" importado das fixtures tem **5** imagens na galeria

## Arquivos alterados

- `apps/catalog/models.py` — adicionado `ProductImage`
- `apps/catalog/migrations/0006_productimage.py` — criado
- `apps/catalog/admin.py` — `ProductImageInline` adicionado
- `apps/catalog/mappers.py` — `gallery` em `to_detail`; chaves 3D removidas
- `apps/catalog/queries.py` — `prefetch_related("gallery")` em `detail_by_slug`
- `apps/catalog/management/commands/importar_makerworld.py` — galeria, `traduzir_nome`, `--com3d`
- `apps/catalog/templates/catalog/product_detail.html` — carrossel, sem 3D/STL
- `apps/catalog/templates/catalog/partials/product_card.html` — sem btn-3d
- `apps/core/templates/base.html` — sem modal viewer3d / model-viewer
- `static/js/app.js` — sem IIFE viewer3d
- `static/css/theme.css` — sem .viewer3d*/.btn-3d; escopo carrossel no detalhe
