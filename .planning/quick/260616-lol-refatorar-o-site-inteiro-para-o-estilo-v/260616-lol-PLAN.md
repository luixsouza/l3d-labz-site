---
phase: quick-260616-lol
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - static/css/theme.css
  - apps/core/templates/core/home.html
autonomous: true
requirements: [VIBRANTE-MAKER-STYLE, CARDS-IGUAIS, CTA-INSTAGRAM, NO-BREAK]
must_haves:
  truths:
    - "Em LIGHT e DARK, o site exibe a linguagem visual B (Vibrante Maker): bordas duras na cor de tinta e sombra-offset dura nos CTAs e no hover de cards"
    - "Os cards de produto têm altura igual: thumb quadrado em bloco de cor pastel, nome em 2 linhas, botão 'Adicionar' alinhado na base"
    - "O CTA final da home aponta para o Instagram (@l3d_labz) com visual de degradê IG — não há mais 'Chama no WhatsApp' na home"
    - "Nada quebra: visualizador 3D do detalhe, FAB Instagram, página pública de orçamento, calculadora, editor de litofane, carrinho, checkout e conta continuam funcionando e herdam o novo estilo"
    - "O toggle claro/escuro continua funcionando e ambos os temas usam a mesma linguagem dura/offset"
  artifacts:
    - path: "static/css/theme.css"
      provides: "Apêndice 'Vibrante Maker' no fim do arquivo (tokens --ink/--offset-shadow + overrides de .btn-primary/.product-card/.product-thumb/.badge/.pill/hero/CTA IG), vencendo a cascata"
      contains: "Vibrante Maker"
    - path: "apps/core/templates/core/home.html"
      provides: "CTA final da home apontando para SITE.instagram com classe de degradê IG"
      contains: "SITE.instagram"
  key_links:
    - from: "static/css/theme.css (apêndice Vibrante Maker)"
      to: ".product-card / .product-thumb / .btn-primary / .badge / .pill já existentes"
      via: "seletores de mesma especificidade no fim do arquivo (cascata)"
      pattern: "\\.product-card|\\.btn-primary|--offset-shadow"
    - from: "apps/core/templates/core/home.html (CTA final)"
      to: "config.settings.SITE.instagram"
      via: "{{ SITE.instagram }} via context processor"
      pattern: "SITE\\.instagram"
---

<objective>
Refatorar a identidade visual do site L3D Labz para o estilo "Vibrante Maker" (sketch 002, variante B vencedora), aplicado via `theme.css` + um ajuste de template na home, preservando o toggle claro/escuro e TODAS as funcionalidades já no ar.

Purpose: Dar personalidade maker à marca (bordas duras na cor de tinta, sombra-offset, thumbs em blocos pastel, badges e chips com borda dura, hero degradê verde→azul, CTA Instagram) sem reescrever a arquitetura de tokens/componentes existente e sem quebrar nada.
Output: Apêndice "Vibrante Maker" no fim de `static/css/theme.css` (que vence a cascata sobre os layers v3/v4/Clean & Elegante) + CTA final da home trocado de WhatsApp para Instagram.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

# CONTRATO DE DESIGN — o mockup vencedor (ler antes de tocar em CSS):
@.planning/sketches/002-vitrine-redesign/variant-b-vibrante-maker.html
@.planning/sketches/002-vitrine-redesign/README.md

# Alvos:
@static/css/theme.css
@apps/core/templates/core/home.html
@apps/catalog/templates/catalog/partials/product_card.html

<interfaces>
<!-- Contexto extraído do código. NÃO explorar a base — usar isto direto. -->

ESTRUTURA DO theme.css (2644 linhas, token-driven, FORTEMENTE LAYERED):
  O arquivo é uma pilha de "appendices" que se sobrepõem por ordem (cascata):
  - Tokens base dark (:root, ~linha 6) e light ([data-theme="light"], ~747, 1243).
  - Layer v3 (~800): cantos retos + botões outline (`--radius:0`).
  - Layer v4 / v4.1 (~1168, ~1229): cantos suaves de volta (`--r:18px`, `--r-sm:13px`, `--r-pill:999px`), botões preenchidos.
  - Header v2/v3, Busca v2/v3, Footer v2, Refresh "Atelier de Precisão" (~1905).
  - "Clean & Elegante" light-first (~2513): header/footer/hero claros no light.
  - FAB Instagram (~2605) e FIX do split do hero (~2633) ficam no FIM.
  REGRA: o NOVO estilo "Vibrante Maker" entra como APÊNDICE NO FIM DO ARQUIVO
  (depois da linha 2644) para vencer a cascata. NÃO editar/remover os layers
  anteriores nem criar arquivo CSS paralelo (constraint do CLAUDE.md).

TOKENS RELEVANTES já existentes (reaproveitar, não recriar):
  --accent:#2FA84F  --accent-2:#43C266  --accent-strong:#1E8C3E
  --accent-blue:#2BA6E0  --accent-blue-soft:#E6F4FB  --accent-blue-ink:#0E5E84
  --bg --bg-soft --bg-card --bg-elevated --border --border-soft
  --text --text-muted --text-dim
  --r (raio container) --r-sm --r-pill --shadow --shadow-soft --ease
  --font ("Hanken Grotesk") --font-display ("Bricolage Grotesque")  ← MANTER as fontes da marca

CLASSES-ALVO já existentes (mesma especificidade no apêndice):
  .btn / .btn-primary / .btn-ghost / .btn-sm / .btn-block (~91, redefinidos em v4 ~1196 e Atelier ~1951)
  .product-card / .product-thumb / .product-body / .product-name / .product-actions (~253, redefinidos ~1388, ~1959)
  .thumb-mono (placeholder por monograma, usa var(--acc) da categoria; ~606)
  .badge / .badge-discount / .badge-new / .badge-soft (~270, ~1399)
  .pill / .pill.active / .cat-chip (~660, ~2116)  .chip / .spec-chip (~331, ~335)
  .geek-hero--clean (hero da home; ~2004, ~2062, ~2568 light, ~2639 split)
  .shop-cta (CTA final da home; ~948)  .section-head .link (~226)
  .site-header e variações (header já escuro nos dois modos; NÃO precisa virar duro)
  .fab-ig (FAB Instagram global; ~2608) — usa degradê accent; pode ganhar degradê IG opcional

CARD DE PRODUTO (apps/catalog/templates/catalog/partials/product_card.html) — JÁ correto:
  <article class="product-card"> a.product-thumb[style="--ph-accent:..."] > span.thumb-mono[--acc] + img + badge
  > div.product-body (já tem flex:1 herdado) > .product-cat, a.product-name,
    .spec-chip(condicional), .product-rating, .price-row, .product-actions(form > btn-primary btn-block)
  → A altura-igual já está MUITO perto: `.product-body{flex:1}` (linha 274) e
    `.price-row{margin-top:auto}` (279). O botão fica DEPOIS do price-row, então
    para o botão alinhar na base precisamos garantir `.product-actions{margin-top:auto}`
    e tirar o `margin-top:auto` de .price-row OU clampar o nome. Ajustar no apêndice.
  → `.product-name` já tem min-height (~1392 min-height:2.6em). Falta o line-clamp:2.
  → Thumbs em blocos pastel: o card recebe `--ph-accent` (cor da categoria). Usar
    `.product-thumb{ background: cor pastel derivada de --ph-accent }` via color-mix
    (já usado no arquivo, ex. linha 1506/1136), atendendo "blocos de cor pastel rotativos"
    sem precisar de classes c0–c7 nem mexer no template.

HERO da home (apps/core/templates/core/home.html):
  Usa `.geek-hero.geek-hero--clean` com `.gh-inner` (eyebrow/h1/lead/.hero-cta com .gh-btn)
  e à direita `.gh-viewer` (model-viewer 3D) OU `.gh-deco`. O hero do mockup B é
  degradê verde→azul + textura de pontos + cartão branco com flag. NO LIGHT o hero
  hoje é off-white (Clean). DECISÃO: aplicar o degradê verde→azul + textura de pontos
  na variante B em AMBOS os temas, MANTENDO o `.gh-viewer`/`.gh-deco` como o "cartão"
  à direita (não trocar o conteúdo do hero, só o estilo do container). Texto branco
  sobre o degradê. NÃO remover o model-viewer 3D.

CTA FINAL da home (home.html ~196-209) — ÚNICA mudança de template:
  Hoje: `.shop-cta` com h2 "Ficou com dúvida? Chama no WhatsApp" e
        <a href="https://wa.me/" class="btn btn-primary">...WhatsApp</a> (link FALSO).
  Trocar por bloco Instagram (degradê IG do mockup, classe nova `.ig-cta`):
    h3 "Cola no nosso Instagram!", copy pt-br descontraída, botão "Seguir @l3d_labz"
    apontando para `{{ SITE.instagram }}` (já existe em settings, exposto via context
    processor — confirmar uso de SITE no template; outras telas usam {{ SITE.name }}).
  Ícone: usar `#i-instagram` (existe em icons.html linha 114). NÃO inventar WhatsApp.

SITE config (config/settings/base.py ~225): SITE = { name, tagline, accent,
  instagram:"https://instagram.com/l3d_labz" }. Exposto a templates via context
  processor de apps/core (usado como {{ SITE.name }}). NÃO precisa editar settings.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Apêndice "Vibrante Maker" no theme.css — tokens, botões, cards, badges, chips, hero</name>
  <files>static/css/theme.css</files>
  <action>
Adicionar UM bloco-apêndice no FIM de `static/css/theme.css` (após a linha final, ~2644), com um cabeçalho de comentário pt-br "Vibrante Maker (sketch 002-B) — vence a cascata". NÃO editar nem remover nenhum layer anterior. NÃO criar arquivo CSS novo. Reaproveitar os tokens existentes (`--accent`, `--accent-blue`, `--border`, `--bg-card`, `--font-display`, etc.) — as fontes da marca (Bricolage Grotesque display, Hanken Grotesk corpo) FICAM como estão.

Definir, dentro do apêndice, novos tokens em `:root` e em `[data-theme="light"]`:
  - `--ink`: cor de tinta das bordas duras. No LIGHT (primário) usar um verde-tinta bem escuro (ex. derivado do `#0C1F15` do mockup). No DARK, como bordas pretas somem no fundo escuro, usar uma tinta CLARA (ex. uma versão clara de `--text`/branco-esverdeado) para a mesma linguagem dura/offset ficar legível — conforme decisão travada (light manda; dark coerente com sombra-offset de borda clara).
  - `--offset-shadow`: a sombra-offset dura padrão (ex. `4px 4px 0 var(--ink)`), e uma variante hover maior. Usar essa variável em TODOS os offsets (CTAs e hover de cards) para ficar performático e sem poluir (per decisão 6).

Aplicar a linguagem B sobrescrevendo as classes JÁ existentes (mesma especificidade, com `!important` só onde os layers v4/Atelier também usam `!important`):
  - Bordas duras: `.btn-primary`, `.product-card`, `.product-thumb` (borda inferior dura entre thumb e body), `.badge`, `.pill`, `.cat-chip`, `.chip` ganham `border: 2.5px solid var(--ink)`. (Raio: manter o arredondado do mockup B — o mockup usa `--r:20px` nos cards e botões com `border-radius:12px`; não voltar a cantos retos do v3.)
  - Sombra-offset dura: `.btn-primary` ganha `box-shadow: var(--offset-shadow)`; `:hover` translada `-1px,-1px` e aumenta o offset; `:active` translada `2px,2px` e reduz (efeito "pressionado" do mockup). `.product-card:hover` translada `-2px,-2px` + `box-shadow: 6px 6px 0 var(--ink)`. Substituir os hovers suaves (translateY + shadow difusa) dos layers anteriores.
  - Thumbs em blocos de cor pastel: `.product-thumb { background: color-mix(in srgb, var(--ph-accent, var(--accent)) 16%, #fff); }` (derivar pastel da cor da categoria que o card já recebe via `--ph-accent`) — atende "blocos pastel rotativos" sem tocar no template. No DARK, usar uma mistura adequada para não estourar (ex. misturar com `--bg-card`). O `.thumb-mono` continua usando `--acc`.
  - Badges NOVO/TOP com borda dura: `.badge-new`/`.badge-discount` com `border:2px solid var(--ink)`, mantendo as cores on-brand (verde/azul); `.badge-soft` legível.
  - Chips/categorias como pílulas com borda: `.pill`, `.cat-chip` com borda dura; `.pill.active`/`.cat-chip:hover` com fundo de tinta e texto claro (estilo `.chip.on` do mockup), preservando contraste.

Hero da home (`.geek-hero--clean`) em AMBOS os temas: aplicar o degradê verde→azul do mockup (`linear-gradient(135deg, var(--accent) 0%, #27a07a 45%, var(--accent-blue) 100%)`) + textura de pontos via `::before` (`radial-gradient(rgba(255,255,255,.18) 2px, transparent 2px); background-size:26px 26px`) + borda dura `3px solid var(--ink)` + `--r` grande. Texto/eyebrow/lead em branco. Botões `.gh-btn.primary` brancos com offset, `.gh-btn.ghost` outline branco. Sobrescrever a regra light "off-white" do Clean (linha ~2568) — como o apêndice vem depois, ele vence; usar a MESMA especificidade `[data-theme="light"] .geek-hero--clean`. MANTER `.gh-viewer`/`.gh-deco` (model-viewer 3D NÃO sai). Garantir que `.gh-viewer model-viewer` continue visível sobre o degradê (cartão branco com borda dura, estilo `.hero-card` do mockup).

Acessibilidade/perf (decisão 6): garantir contraste do texto sobre o degradê; preservar `:focus-visible` (já existe regra ~2000 — não remover); a sombra-offset é estática (sem animação custosa); respeitar `prefers-reduced-motion` (a regra global ~594 já zera transições — não anular). Não introduzir animações novas pesadas.

NÃO tocar em: `.site-header`/navbar (header já é escuro nos dois modos e funciona — pode receber só a borda inferior dura se ficar coerente, mas sem quebrar o sticky/blur), `.fab-ig` (FAB Instagram), `.detail-3d-panel`/`.detail-ar-btn`/`.detail-stl-btn`/`.detail-media-tab` (viewer 3D do detalhe), `.spec-chip` (só herda borda se fizer sentido), calculadora (`.calc-*`), litofane (`.litho-*`), checkout/conta — essas telas herdam tokens e os componentes base (`.btn`, `.card`, `.product-card`, `.badge`, `.pill`) que já estamos estilizando. NÃO remover os FIX finais (split do hero ~2639, FAB ~2605); colocar o apêndice DEPOIS deles e re-afirmar o split do hero se o novo estilo do hero precisar (manter `grid-template-columns:1.15fr .85fr` no desktop, 1fr no mobile ≤820px).
  </action>
  <verify>
    <automated>grep -q "Vibrante Maker" static/css/theme.css && grep -q -- "--offset-shadow" static/css/theme.css && grep -q -- "--ink" static/css/theme.css && python -c "import sys; s=open('static/css/theme.css',encoding='utf-8').read(); sys.exit(0 if s.count('{')==s.count('}') else 1)"</automated>
  </verify>
  <done>
O apêndice "Vibrante Maker" existe no fim de theme.css; define `--ink` e `--offset-shadow` em `:root` e `[data-theme="light"]`; sobrescreve `.btn-primary`, `.product-card`, `.product-thumb`, `.badge`, `.pill`/`.cat-chip` com bordas duras + sombra-offset; aplica degradê+pontos+borda dura no `.geek-hero--clean` nos dois temas mantendo `.gh-viewer`; nenhum layer anterior foi removido; chaves `{` e `}` balanceadas; FIX do split do hero preservado/reafirmado.
  </done>
</task>

<task type="auto">
  <name>Task 2: Card de produto com altura igual + CTA Instagram na home</name>
  <files>static/css/theme.css, apps/core/templates/core/home.html</files>
  <action>
PARTE A — Altura igual dos cards (no MESMO apêndice "Vibrante Maker" do theme.css, decisão 3):
  - Garantir `.product-card { display:flex; flex-direction:column; }` (já é, reafirmar).
  - `.product-body { display:flex; flex-direction:column; flex:1; }` (reafirmar flex:1).
  - `.product-name`: aplicar clamp de 2 linhas — `display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;` + `min-height:2.4em` (≈ 2 linhas no tamanho atual). Isso normaliza a altura do bloco de título entre cards com nomes curtos e longos.
  - Empurrar a ação para a base: `.product-actions { margin-top:auto; }`. ATENÇÃO: hoje `.price-row` tem `margin-top:auto` (linha 279) — com dois `margin-top:auto` na mesma coluna flex o primeiro consome o espaço e o botão NÃO alinha. Resolver re-zerando `.price-row{margin-top:0}` no apêndice e deixando só `.product-actions{margin-top:auto}`, OU mantendo `.price-row` com margin pequena e movendo o auto para `.product-actions`. O objetivo final: em uma fileira de cards (nomes de 1 e de 2 linhas, com e sem `.spec-chip`, com e sem desconto), os botões "Adicionar" ficam todos na mesma linha de base. Thumb quadrado consistente já garantido por `aspect-ratio:1/1` + bloco pastel da Task 1.
  - `.product-thumb` borda inferior dura (`border-bottom: 2.5px solid var(--ink)`) separando thumb do body, como no mockup.

PARTE B — CTA Instagram na home (apps/core/templates/core/home.html, decisão 4):
  Substituir o bloco `<section>` do CTA final (atualmente "Ficou com dúvida? Chama no WhatsApp" com link `https://wa.me/`, linhas ~196-209) por um bloco Instagram no estilo do mockup (degradê IG `linear-gradient(120deg,#F58529,#DD2A7B 55%,#515BD4)`, borda dura, sombra-offset, texto branco):
    - Usar uma classe nova `ig-cta` (definida no apêndice do theme.css, Parte C abaixo).
    - Conteúdo pt-br: ícone `#i-instagram`, título "Cola no nosso Instagram!", subtítulo curto descontraído (ex. "Timelapse das impressões, drops e novidades. @l3d_labz"), e botão "Seguir @l3d_labz" apontando para `href="{{ SITE.instagram }}"` com `target="_blank" rel="noopener"`.
    - NÃO inventar número/link de WhatsApp. Remover o `<a href="https://wa.me/">`. Pode manter um link secundário "Ver catálogo" para `{% url 'catalog:product_list' %}` se fizer sentido visual, mas o foco é o Instagram.
  Manter o resto da home (hero, serviços, prova social, categorias, destaques, novidades) intacto — só o CTA final muda.

PARTE C — Estilo `.ig-cta` (no apêndice do theme.css):
  `.ig-cta { background: linear-gradient(120deg,#F58529,#DD2A7B 55%,#515BD4); color:#fff; border:3px solid var(--ink); box-shadow: 7px 7px 0 var(--ink); display:flex; align-items:center; gap:... }` com layout responsivo (empilha no mobile), título em `--font-display`, e o botão interno branco com offset. Garantir contraste do texto branco sobre o degradê IG (já alto). No DARK, manter o degradê IG (cores fixas da marca Instagram) com `--ink` claro na borda/offset para coerência.

OBS: o WhatsApp no `core/about.html` (linhas 16/128) NÃO faz parte deste escopo (a decisão 4 fala da HOME). Deixar `about.html` como está — não tocar.
  </action>
  <verify>
    <automated>grep -q "SITE.instagram" apps/core/templates/core/home.html && ! grep -q "wa.me" apps/core/templates/core/home.html && grep -q "ig-cta" apps/core/templates/core/home.html && grep -q "ig-cta" static/css/theme.css && grep -q "line-clamp" static/css/theme.css</automated>
  </verify>
  <done>
Os cards de produto têm `.product-name` com `-webkit-line-clamp:2` + min-height e `.product-actions{margin-top:auto}` (sem conflito de duplo margin-top), de modo que os botões alinham na base entre cards de alturas naturais diferentes. A home não tem mais `wa.me`; o CTA final é o bloco `.ig-cta` (degradê IG, borda dura, offset) com botão "Seguir @l3d_labz" → `{{ SITE.instagram }}`. `about.html` intocado.
  </done>
</task>

</tasks>

<verification>
Verificação CRÍTICA feita pelo ORQUESTRADOR no navegador (Playwright + dev server — HTTP/render/WebGL funcionam aqui). Subir o server com:
`DJANGO_SETTINGS_MODULE=config.settings.dev .venv/Scripts/python.exe manage.py runserver`

Screenshotar em LIGHT e DARK, desktop e mobile, confirmando (a) estilo B aplicado, (b) cards de altura igual, (c) nada quebrado, (d) CTA Instagram:
- `/` (home) — hero degradê+pontos+borda dura, model-viewer 3D vivo, CTA Instagram no fim (sem WhatsApp), cards alinhados nas seções Mais vendidos / Novidades.
- `/catalogo/` — grid de cards altura-igual (botões na base), filtros funcionando, badges/pills com borda dura.
- `/catalogo/modelos-3d/` — mesmo grid parametrizado, filtros de specs (se `specs_ready`), paginação preserva filtros.
- detalhe de produto (com aba 3D) — toggle Fotos↔3D, `.detail-3d-panel`/`.detail-ar-btn`/`.detail-stl-btn` OK, model-viewer renderiza.
- carrinho `/carrinho/`, checkout, `/calculadora/`, login `/conta/entrar/`, e a página pública de orçamento (`/calculadora/orcamento/<token>/`) — herdam o novo estilo sem quebrar layout/contraste.
- FAB Instagram (`.fab-ig`) presente e clicável; toggle de tema alterna light/dark e ambos usam a linguagem dura/offset.
Acessibilidade: foco visível preservado; `prefers-reduced-motion` respeitado.
</verification>

<success_criteria>
- Estilo "Vibrante Maker" (variante B) visível em LIGHT e DARK: bordas duras `--ink`, sombra-offset `--offset-shadow` nos CTAs e hover de cards, thumbs em blocos pastel, badges/chips com borda dura, hero degradê verde→azul com textura de pontos.
- Cards de produto com altura igual: thumb quadrado pastel, nome em 2 linhas (clamp), botão "Adicionar" alinhado na base em toda a fileira.
- CTA final da home aponta para `SITE.instagram` com visual de degradê IG; sem `wa.me` na home.
- Paleta do Luigi (verde #2FA84F + azul #2BA6E0) e fontes da marca (Bricolage Grotesque / Hanken Grotesk) MANTIDAS.
- Tudo que estava no ar continua funcionando (viewer 3D, FAB, orçamento público, calculadora, litofane, carrinho/checkout/conta); toggle claro/escuro OK.
- Apêndice único no fim de theme.css; nenhum layer anterior removido; sem arquivo CSS paralelo.
</success_criteria>

<output>
Create `.planning/quick/260616-lol-refatorar-o-site-inteiro-para-o-estilo-v/260616-lol-SUMMARY.md` when done
</output>
