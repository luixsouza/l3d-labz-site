---
phase: quick-260611-mca
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - apps/catalog/mesh3d.py
  - apps/catalog/management/commands/importar_copa.py
  - apps/catalog/management/commands/importar_makerworld.py
  - apps/catalog/mappers.py
  - apps/catalog/templates/catalog/partials/product_card.html
  - apps/core/templates/base.html
  - static/js/app.js
  - static/css/theme.css
autonomous: true
requirements:
  - MW-IMPORT (comando importar_makerworld)
  - MW-MESH3D (módulo 3D compartilhado)
  - MW-MODAL (modal 3D no catálogo)

must_haves:
  truths:
    - "Rodar importar_makerworld nas fixtures cria 1 Product por pasta (idempotente por slug)"
    - "Produto com modelo.3mf tem foto JPG quadrada, dimensions 'L×A×P cm' e model_3d (GLB) preenchidos"
    - "Produto sem modelo.3mf (aurashell-lamp) é criado foto-only: sem GLB, sem dimensions"
    - "importar_copa continua funcionando (importa de mesh3d, sem duplicação de pipeline)"
    - "Card do catálogo mostra botão 'Ver em 3D' quando o produto tem model_3d"
    - "Clicar 'Ver em 3D' abre modal fullscreen com <model-viewer>, sem navegar; fecha com Esc/backdrop/X"
    - "Página de detalhe exibe chip de dimensões quando há dimensions"
  artifacts:
    - path: "apps/catalog/mesh3d.py"
      provides: "Pipeline 3D compartilhado (coletar/construir mesh, orientar, decimar, finalizar GLB)"
      min_lines: 80
    - path: "apps/catalog/management/commands/importar_makerworld.py"
      provides: "Comando de import MakerWorld → Product"
      min_lines: 120
    - path: "apps/catalog/mappers.py"
      provides: "model_3d_url + has_3d no to_dict do card"
      contains: "has_3d"
  key_links:
    - from: "apps/catalog/management/commands/importar_copa.py"
      to: "apps/catalog/mesh3d.py"
      via: "import do pipeline compartilhado"
      pattern: "from apps.catalog.mesh3d import|from apps.catalog import mesh3d"
    - from: "apps/catalog/management/commands/importar_makerworld.py"
      to: "apps/catalog/mesh3d.py"
      via: "import do pipeline compartilhado"
      pattern: "mesh3d"
    - from: "apps/catalog/templates/catalog/partials/product_card.html"
      to: "static/js/app.js"
      via: "data-viewer-3d / data-viewer-nome no botão"
      pattern: "data-viewer-3d"
    - from: "static/js/app.js"
      to: "apps/core/templates/base.html (modal global)"
      via: "abre/fecha modal, seta/limpa src do model-viewer"
      pattern: "data-viewer-3d|viewer3d"
---

<objective>
Duas entregas no L3D Labz: (A) comando `importar_makerworld` que transforma pastas
scrapadas do MakerWorld em produtos sob demanda (foto quadrada, descrição pt-br
padronizada, dimensões reais via 3mf, GLB pro viewer, categoria automática), e
(B) modal 3D no front que abre o `<model-viewer>` direto do card do catálogo sem
navegar. O pipeline 3D do `importar_copa.py` é extraído para um módulo
compartilhado `apps/catalog/mesh3d.py` e reusado nos dois comandos (sem duplicação).

Purpose: escalar o catálogo real (centenas de modelos no SSD) e deixar o cliente
ver o 3D já na listagem — reforça o core value (visualização 3D intuitiva).
Output: mesh3d.py, importar_makerworld.py, importar_copa refatorado, modal global,
JS+CSS do modal, mapper expondo 3D no card, chip de dimensões no detalhe.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

# Pipeline 3D a refatorar (origem das funções para mesh3d.py)
@apps/catalog/management/commands/importar_copa.py

# Render da foto padronizada + cor PBR (já compartilhado, reusar como está)
@apps/catalog/render3d.py

# Schema dos models (campos de Product e Category)
@apps/catalog/models.py

# Mapper (adicionar model_3d_url/has_3d no to_dict do card)
@apps/catalog/mappers.py

# Templates a tocar
@apps/catalog/templates/catalog/partials/product_card.html
@apps/catalog/templates/catalog/product_detail.html
@apps/core/templates/base.html

# JS IIFE existente (adicionar lógica do modal aqui)
@static/js/app.js

<interfaces>
<!-- Contratos que o executor usa diretamente — sem explorar o codebase. -->

Campos de Product (apps/catalog/models.py):
  category (FK PROTECT), name, slug (unique), description, price (Decimal),
  compare_at_price, image (ImageField products/), image_url, model_3d (FileField
  products/models/, ext glb/gltf), model_stl (NÃO usar — ativo protegido),
  stock (default 10), material (default "PLA"), dimensions (CharField max 80, blank),
  print_time_hours (default 4), is_featured, is_active.
  Property: has_3d_model = bool(model_3d).

Campos de Category (apps/catalog/models.py):
  name (unique), slug (unique), icon (CharField default "cube"; NÃO é "icone"),
  accent (hex), description, is_highlighted, order.

Pipeline a extrair de importar_copa.py (vira mesh3d.py):
  _coletar_malhas, _melhor_imagem, _carregar_3mf (Scene → geometrias únicas,
  guard MAX_FACES_IN, NUNCA force='mesh'), _construir_mesh (maior componente +
  pré-decima + orienta), _decimar, _orientar, _finalizar_glb (Y-up + PBR via
  render3d.cor_rgba_por_nome). Constantes: MESH_PREF, MAX_FACES_IN, TARGET_FACES.

render3d (reusar como está):
  render3d.render_thumb(mesh, nome) -> bytes (JPEG quadrado 1000px)
  render3d.cor_rgba_por_nome(nome) -> list[float] RGBA

ProductMapper.to_dict (card) HOJE NÃO expõe 3D. to_detail já expõe
  model_3d_url/has_3d_model/dimensions. O card precisa de model_3d_url + has_3d.

Formato fixture MakerWorld:
  <base>/<slug>/{meta.json, descricao.html, fotos/NN.ext, modelo.3mf?}
  meta.json: { titulo, titulo_en, tags[], licenca, criador, ... }
  fotos ordenadas por nome: "primeira foto" = sorted()[0] (pode ser .gif).
  Fixtures: aurashell-lamp (sem 3mf, foto-only) ;
            mecha-style-self-locking-stackable-drawer-storage (3mf 14MB, 01.gif).
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Extrair mesh3d.py e criar comando importar_makerworld</name>
  <files>apps/catalog/mesh3d.py, apps/catalog/management/commands/importar_copa.py, apps/catalog/management/commands/importar_makerworld.py</files>
  <action>
PASSO 1 — Criar `apps/catalog/mesh3d.py` movendo o pipeline 3D do importar_copa:
mover as funções `_coletar_malhas`, `_carregar_3mf`, `_construir_mesh`, `_decimar`,
`_orientar`, `_finalizar_glb` e as constantes `MESH_PREF`, `MAX_FACES_IN`,
`TARGET_FACES`, `IMG_EXTS` para funções de módulo (sem `self`; trocar
`self.stdout/self.stderr` por um parâmetro opcional `log` callable ou por `print`/
`warnings` — manter os avisos pt-br). Exportar nomes públicos: `coletar_malhas`,
`construir_mesh`, `finalizar_glb`, e helper `dimensoes_mm(mesh) -> tuple[float,float,float]`
que retorna `mesh.extents` (bounding box em mm, já que o 3mf vem em mm). Manter a
lição: NUNCA `force='mesh'` em Scene; usar `scene.geometry.values()` (geometrias
únicas) com guard `MAX_FACES_IN`. Docstring de módulo pt-br.

PASSO 2 — Refatorar `importar_copa.py` para importar de mesh3d (sem duplicar):
remover as funções movidas e chamar `mesh3d.coletar_malhas(...)`,
`mesh3d.construir_mesh(...)`, `mesh3d.finalizar_glb(mesh, nome)`. Comportamento
idêntico ao atual (mesma saída de produtos Copa). NÃO mudar a lista PRODUTOS nem o
fluxo de save.

PASSO 3 — Criar `apps/catalog/management/commands/importar_makerworld.py`:
Flags: `--base` (required), `--only <slug>`, `--limite N`, `--sem3d`,
`--categoria "Nome"`. Para cada subpasta de `<base>` (ou só `--only`, respeitando
`--limite`):
  a) Ler `meta.json` (titulo, titulo_en, tags). Nome do produto = `titulo_en` ou
     `titulo`. Slug = `slugify(nome do diretório)` (estável por pasta).
  b) Categoria automática por keywords em `(titulo_en + ' ' + ' '.join(tags))`.lower():
     airplane|jet|plane→"Aviões"; star wars|pokemon|dragon|anime|geek→"Geek";
     valentine|love|heart→"Presentes"; kitchen|organizer|desk|home→"Casa & Organização";
     toy|fidget|kids→"Brinquedos". Sem match → usa `--categoria`; se também ausente,
     pular com aviso pt-br e continuar. `Category.objects.get_or_create(slug=slugify(nome),
     defaults={name, icon:"cube", accent:"#2FA84F", order, is_highlighted:True, description})`.
  c) Foto principal = `sorted(fotos/*)[0]`. Abrir com Pillow; se GIF, `img.seek(0)`
     (primeiro frame). Converter para quadrado: crop/pad central, fundo branco
     (RGBA→RGB sobre branco), salvar JPEG quality=90. (NÃO usar render3d aqui — a
     foto principal do MakerWorld é a foto real da pasta, padronizada para quadrado.)
  d) Descrição padronizada pt-br por template (NÃO copiar descricao.html):
     "{nome} ({categoria}) impresso sob demanda em PLA pela L3D Labz. Orçamento e
     prazo pelo WhatsApp." + " Dimensões: {dimensions}." quando houver. Em pt-br.
  e) 3D (pulável via `--sem3d`): localizar `modelo.3mf`. Se existe e não `--sem3d`:
     `malhas = mesh3d.coletar_malhas(pasta, prefs=['.3mf'])`; `mesh =
     mesh3d.construir_mesh(malhas, ...)`; dimensões via `mesh3d.dimensoes_mm(mesh)`
     ANTES do finalizar (bbox original em mm) → `dimensions` = "L×A×P cm"
     (mm→cm = /10, 1 casa decimal, formato "{:.1f}×{:.1f}×{:.1f} cm"); GLB =
     `mesh3d.finalizar_glb(mesh, nome)` salvo em `model_3d`. NUNCA salvar o 3mf em
     model_stl. Se não há 3mf → produto foto-only (sem dimensions, sem model_3d).
  f) Idempotente por slug (padrão importar_copa): `p = existente or Product(slug=...)`;
     setar campos (category, name, description, price=Decimal("0"),
     compare_at_price=None, stock=10, material="PLA+", is_featured=False,
     is_active=True); `p.save()`; `p.image.save(f"{slug}.jpg", ContentFile(jpg),
     save=False)`; se GLB: `p.model_3d.save(f"{slug}.glb", ContentFile(glb),
     save=False)`; `p.save(update_fields=[...])`. Mensagens de progresso pt-br
     (estilo importar_copa). Docstring de módulo pt-br com exemplo de uso.
  </action>
  <verify>
    <automated>.venv\Scripts\python.exe manage.py importar_makerworld --base .uat\fixtures-mw 2>&1 | Select-String -Pattern "importados|atualizados|foto-only" ; .venv\Scripts\python.exe manage.py shell -c "from apps.catalog.models import Product; m=Product.objects.get(slug='mecha-style-self-locking-stackable-drawer-storage'); a=Product.objects.get(slug='aurashell-lamp'); assert m.image and m.model_3d and m.dimensions, ('mecha', m.image, bool(m.model_3d), m.dimensions); assert a.image and not a.model_3d and not a.dimensions, ('aura', bool(a.model_3d), a.dimensions); print('OK', m.dimensions)"</automated>
  </verify>
  <done>
    importar_makerworld nas fixtures cria 2 produtos: mecha (foto JPG + dimensions
    "L×A×P cm" + model_3d GLB) e aurashell (foto-only, sem GLB/dimensions).
    importar_copa importa de mesh3d (grep confirma) sem duplicar o pipeline.
    Rodar de novo é idempotente (não duplica, atualiza por slug).
  </done>
</task>

<task type="auto">
  <name>Task 2: Modal 3D global no front + 3D no card + chip de dimensões</name>
  <files>apps/catalog/mappers.py, apps/catalog/templates/catalog/partials/product_card.html, apps/core/templates/base.html, static/js/app.js, static/css/theme.css</files>
  <action>
PASSO 1 — Mapper (`apps/catalog/mappers.py`): em `ProductMapper.to_dict` (o que o
card recebe), adicionar `"model_3d_url": instance.model_3d.url if instance.model_3d
else ""` e `"has_3d": instance.has_3d_model`. Não remover nada existente. (to_detail
herda de to_dict, segue funcionando.)

PASSO 2 — Card (`product_card.html`): dentro de `.product-thumb` (ou em
`.product-body`, escolha que não quebre o layout existente), quando `product.has_3d`,
adicionar um botão "Ver em 3D" com ícone, que NÃO é link de navegação:
`<button type="button" class="btn-3d" data-viewer-3d="{{ product.model_3d_url }}"
data-viewer-nome="{{ product.name }}"><svg class="icon"><use href="#i-cube"></use></svg>
Ver em 3D</button>`. O botão deve abrir o modal (não navegar) — garantir
`type="button"` e que o clique não dispare o link `<a>` do card (colocar o botão
FORA do `<a class="product-thumb">`, ex.: como overlay posicionado ou no
`.product-body`, e/ou usar `stopPropagation` no JS). Copy pt-br.

PASSO 3 — Modal global (`base.html`): incluir UMA vez, antes de `</main>` ou após
o footer, um modal fullscreen oculto por padrão:
`<div class="viewer3d" id="viewer3d" hidden aria-hidden="true">` com backdrop,
`<header>` (título `<span data-viewer-title></span>` + botão X
`<button class="viewer3d-close" data-viewer-close aria-label="Fechar">` usando
`#i-x`), e um `<model-viewer data-viewer-mv ...>` SEM `src` inicial, com os MESMOS
atributos do detail: `camera-controls auto-rotate touch-action="pan-y"
environment-image="neutral" tone-mapping="commerce" exposure="1.1"
shadow-intensity="1" shadow-softness="0.8" camera-orbit="35deg 75deg auto"
interaction-prompt="none" loading="lazy" reveal="auto" style="background:#fbfbfd"
ar ar-modes="webxr scene-viewer quick-look" ar-scale="auto"`. Também em base.html,
carregar o script do model-viewer UMA vez com defer (mesmo CDN/versão do detail:
`https://cdn.jsdelivr.net/npm/@google/model-viewer@4.3.1/dist/model-viewer.min.js`
como `<script type="module" defer>`), logo após o `app.js`, para o modal do
catálogo funcionar. (O detail já carrega o seu via extra_js; aceitável — module
carrega uma vez por página.)

PASSO 4 — JS (`static/js/app.js`, dentro da IIFE existente): novo bloco comentado
`/* ----- modal 3D ----- */`. Selecionar `#viewer3d`, `[data-viewer-mv]`,
`[data-viewer-title]`. `document.addEventListener("click", ...)`: se
`e.target.closest("[data-viewer-3d]")` → `e.preventDefault(); e.stopPropagation();`
ler `data-viewer-3d` (url) e `data-viewer-nome`; setar título, setar
`mv.setAttribute("src", url)` (LAZY: só seta ao abrir), remover `hidden`, setar
`aria-hidden="false"`, adicionar classe `.open`, `document.body.style.overflow =
"hidden"`. Fechar (função `closeViewer`): `mv.removeAttribute("src")` (libera
memória), `hidden`, `aria-hidden="true"`, remover `.open`, restaurar overflow.
Fechar em: clique em `[data-viewer-close]`, clique no backdrop (target === o
container ou `.viewer3d-backdrop`), e tecla Esc (`keydown` global quando aberto).
Guardar contra ausência dos elementos (if !modal return).

PASSO 5 — CSS (`static/css/theme.css`): estilos do modal usando tokens existentes.
`.viewer3d[hidden]{display:none}`. `.viewer3d`: position fixed, inset 0, z-index
alto, display flex centralizado, backdrop escuro com blur
(`background:rgba(10,12,16,.6); backdrop-filter:blur(8px)`), fade-in. Conteúdo:
card elevado (`--bg-elevated`, `--border`, `--radius-lg`, `--shadow`), header com
título (`--font-display`) e botão X (`--text-muted` → `--text` no hover).
`[data-viewer-mv]`: width 100%, flex:1, min-height. Mobile (`@media max-width`):
fullscreen (inset 0, radius 0). Botão `.btn-3d` do card: discreto, com ícone, cores
de token. Manter estética minimalista/clean.

PASSO 6 — Detalhe (`product_detail.html`): o chip de dimensões JÁ EXISTE
(`{% if product.dimensions %}<span class="chip">...#i-ruler... {{ product.dimensions }}`).
Confirmar que continua presente; se faltar o ícone/chip, garantir o chip
"📏 {{ product.dimensions }}" usando `#i-ruler`. (Nenhuma mudança necessária se já
está como no template lido — apenas validar.)
  </action>
  <verify>
    <automated>.venv\Scripts\python.exe manage.py check 2>&1 | Select-String -Pattern "no issues|System check" ; Select-String -Path apps\catalog\mappers.py -Pattern "has_3d" ; Select-String -Path apps\core\templates\base.html -Pattern "viewer3d|model-viewer" ; Select-String -Path static\js\app.js -Pattern "data-viewer-3d" ; Select-String -Path apps\catalog\templates\catalog\partials\product_card.html -Pattern "data-viewer-3d"</automated>
  </verify>
  <done>
    to_dict do card expõe model_3d_url + has_3d. Card mostra botão "Ver em 3D"
    (type=button, data-viewer-3d) quando has_3d. base.html tem modal global único +
    script model-viewer carregado uma vez. app.js abre modal (seta src lazy) e fecha
    (limpa src) via Esc/backdrop/X. CSS do modal com tokens. `manage.py check` limpo.
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
    Comando importar_makerworld (rodado nas fixtures, criou produtos mecha + aurashell)
    e modal 3D no catálogo (botão "Ver em 3D" no card abrindo model-viewer fullscreen).
  </what-built>
  <how-to-verify>
    1. Garantir que a Task 1 já rodou o import nas fixtures (mecha + aurashell criados).
    2. Subir o servidor: `.venv\Scripts\python.exe manage.py runserver`
    3. Abrir http://127.0.0.1:8000/catalogo/ — localizar o card do produto
       "Mecha-style self-locking stackable drawer storage box".
       Esperado: foto quadrada real (não placeholder) + botão "Ver em 3D".
    4. Clicar "Ver em 3D" → modal fullscreen abre SEM trocar de página, backdrop
       escuro com blur, model-viewer girando o modelo. Título do produto no topo.
    5. Fechar com X, depois reabrir e fechar com Esc, depois reabrir e fechar
       clicando no backdrop. Em todos, a página de catálogo continua atrás (sem reload).
    6. Card do aurashell-lamp: foto-only, SEM botão "Ver em 3D".
    7. Abrir o detalhe do mecha (/catalogo/mecha-style-.../): viewer embutido +
       chip de dimensões "📏 L×A×P cm" presente.
    8. (Opcional) Capturar screenshot do modal aberto via Playwright do venv para registro.
  </how-to-verify>
  <resume-signal>Digite "approved" ou descreva os problemas (foto, modal, dimensões).</resume-signal>
</task>

</tasks>

<verification>
- `importar_copa` e `importar_makerworld` compartilham `mesh3d.py` (grep: ambos
  importam mesh3d; nenhuma das funções do pipeline aparece duplicada nos comandos).
- Import nas fixtures: mecha = foto JPG quadrada + dimensions "L×A×P cm" + GLB;
  aurashell = foto-only. Re-rodar é idempotente (mesma contagem de produtos).
- `manage.py check` sem erros.
- Modal 3D abre/fecha no catálogo sem navegar (Esc/backdrop/X), src setado ao abrir
  e limpo ao fechar (lazy + libera memória). Botão só aparece com has_3d.
- Chip de dimensões no detalhe quando há dimensions.
</verification>

<success_criteria>
- mesh3d.py existe e é a única fonte do pipeline 3D (DRY entre os dois comandos).
- importar_makerworld: categoria automática, foto quadrada (GIF→1º frame, fundo
  branco, q90), descrição pt-br por template (não o HTML cru), dimensões reais via
  3mf (geometrias únicas, sem force='mesh'), GLB no model_3d (3mf nunca em model_stl),
  flags --base/--only/--limite/--sem3d/--categoria, idempotente por slug, foto-only
  quando sem 3mf.
- Card expõe e usa model_3d_url/has_3d; modal global único; JS vanilla na IIFE;
  CSS com tokens; copy pt-br; chip de dimensões no detalhe.
- Fixtures NÃO commitadas.
</success_criteria>

<output>
Create `.planning/quick/260611-mca-importador-makerworld-para-produtos-no-s/260611-mca-SUMMARY.md` when done.
Commit em pt-br, conventional, SEM trailer Co-Authored-By (regra do dono do repo).
</output>
