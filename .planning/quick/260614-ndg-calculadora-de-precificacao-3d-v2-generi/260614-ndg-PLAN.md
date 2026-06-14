---
phase: quick-260614-ndg
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - apps/calculator/presets.py
  - apps/calculator/forms.py
  - apps/calculator/views.py
  - apps/calculator/templates/calculator/publica.html
  - apps/calculator/templates/calculator/orcamento.html
  - static/js/calculator.js
  - static/css/theme.css
  - README.md
autonomous: true
requirements: [CALC-V2-PRESETS, CALC-V2-BANDEIRA, CALC-V2-UI, CALC-V2-ORCAMENTO, DOC-README]

must_haves:
  truths:
    - "Selecionar uma impressora no select auto-preenche potência (W), valor da máquina (R$) e vida útil (h); campos continuam editáveis."
    - "Selecionar um filamento auto-preenche o preço/kg sugerido; campo continua editável."
    - "O usuário informa a tarifa base E escolhe a bandeira ANEEL; a tarifa efetiva = base + adicional é exibida e usada no cálculo de energia."
    - "O cálculo client-side em tempo real bate (±R$0,01) com PricingService.calcular para os mesmos inputs."
    - "O painel de resultado mostra cada componente de custo com barra proporcional (% do total) usando só tokens, e preço de venda em destaque."
    - "Inputs são serializados na query string (link compartilhável) e reidratados ao abrir a página."
    - "A calculadora privada (is_staff) usa os mesmos presets/bandeira e gera PDF que NÃO expõe custos internos."
    - "O README descreve o projeto L3D Labz atual (sem qualquer menção a Nexora) incluindo a Calculadora de Precificação 3D."
  artifacts:
    - path: "apps/calculator/presets.py"
      provides: "IMPRESSORAS, FILAMENTOS, BANDEIRAS_ANEEL + helpers de choices e serialização JSON"
      contains: "BANDEIRAS_ANEEL"
    - path: "apps/calculator/forms.py"
      provides: "CalcForm com selects de preset + tarifa_base/bandeira; to_calc_data soma a tarifa efetiva"
      contains: "adicional"
    - path: "static/js/calculator.js"
      provides: "calculo em tempo real espelhando o servico, presets via json_script, breakdown %, permalink"
      contains: "tarifa_efetiva"
    - path: "apps/calculator/templates/calculator/publica.html"
      provides: "UI publica profissional em duas colunas, json_script de presets, breakdown e permalink"
      contains: "json_script"
    - path: "README.md"
      provides: "documentacao alinhada ao L3D Labz atual"
      contains: "L3D Labz"
  key_links:
    - from: "apps/calculator/forms.py to_calc_data()"
      to: "apps/calculator/services.py PricingService.calcular(tarifa_kwh=...)"
      via: "soma tarifa_base + adicional_bandeira ANTES de chamar o servico"
      pattern: "adicional_kwh"
    - from: "publica.html json_script"
      to: "static/js/calculator.js"
      via: "leitura dos presets serializados (sem hardcode duplicado)"
      pattern: "json_script"
    - from: "apps/calculator/presets.py"
      to: "apps/calculator/forms.py"
      via: "choices dos selects de impressora/filamento/bandeira"
      pattern: "from .presets import"
---

<objective>
Reformular a calculadora de precificacao 3D do L3D Labz numa ferramenta GENERICA e profissional (v2): modulo de presets (impressoras, filamentos, bandeiras ANEEL), tarifa efetiva por bandeira, UI em duas colunas com breakdown visual e permalink, orcamento privado reaproveitando a UI, e README atualizado.

Purpose: a v1 era rasa e feia; o usuario quer algo completo, generico e bonito, mantendo a arquitetura em camadas e o PricingService como fonte unica das formulas (sem novos models/migrations).

Output: apps/calculator/presets.py novo; forms/views evoluidos; templates publico e privado redesenhados; calculator.js reescrito; bloco .calc-* do theme.css ampliado; README.md reescrito.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/quick/260614-ndg-calculadora-de-precificacao-3d-v2-generi/260614-ndg-RESEARCH.md
@apps/calculator/services.py
@apps/calculator/forms.py
@apps/calculator/views.py
@apps/calculator/pdf.py
@apps/calculator/mappers.py
@apps/calculator/templates/calculator/publica.html
@apps/calculator/templates/calculator/orcamento.html
@static/js/calculator.js

<interfaces>
<!-- Contratos ja existentes que o executor deve respeitar - NAO alterar assinaturas. -->

PricingService.calcular (apps/calculator/services.py) - FONTE UNICA, manter assinatura:
  calcular(*, peso_g, preco_kg, potencia_w=110, tempo_h, tarifa_kwh=0.95,
           valor_maquina=2000, vida_util_h=2000, custo_maoobra,
           taxa_falha_pct=10, margem_pct=150) -> dict[str, float]
  Retorna 8 chaves: custo_material, custo_energia, custo_depreciacao,
  custo_maoobra, subtotal, ajuste_falha, custo_total, preco_venda.
  Formulas (espelhar no JS):
    custo_material    = (peso_g/1000) * preco_kg
    custo_energia     = (potencia_w/1000) * tempo_h * tarifa_kwh
    custo_depreciacao = (valor_maquina/vida_util_h) * tempo_h
    subtotal          = material + energia + depreciacao + maoobra
    ajuste_falha      = subtotal * (taxa_falha_pct/100)
    custo_total       = subtotal + ajuste_falha
    preco_venda       = custo_total * (1 + margem_pct/100)

gerar_orcamento_pdf(dados: dict) -> bytes (apps/calculator/pdf.py) - recebe SOMENTE
  {cliente_nome, peca_descricao, quantidade, prazo_entrega, observacoes,
   preco_venda, total}. PROIBIDO passar qualquer custo interno. NAO alterar este modulo.

Tokens CSS disponiveis (usar SO estes, sem cores literais novas):
  Superficies: --bg, --bg-soft, --bg-card, --bg-elevated, --border, --border-soft
  Texto: --text, --text-muted, --text-dim
  Accent: --accent, --accent-2, --accent-strong, --accent-soft, --accent-glow
  Geometria/fonte: --radius, --radius-sm, --radius-lg, --shadow, --header-h,
                   --font, --font-display, --font-mono, --ease
  Bloco .calc-* JA existe em theme.css a partir da linha ~2150 (ampliar, nao duplicar).

Padroes JS do projeto: vanilla ES, IIFE, "use strict", carregado com defer.
  Ler presets via {{ presets_json|json_script:"calc-presets" }} (Django json_script).
  Navbar ja tem o link 'calculator:publica'; nao precisa adicionar.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: presets.py + tarifa efetiva por bandeira (forms/services/views)</name>
  <files>apps/calculator/presets.py, apps/calculator/forms.py, apps/calculator/views.py</files>
  <action>
Criar `apps/calculator/presets.py` com docstring pt-br e os dicts EXATAMENTE como preparados no RESEARCH.md (secao 1 IMPRESSORAS, secao 2 BANDEIRAS_ANEEL + BANDEIRA_VIGENTE_DEFAULT="amarela", secao 3 FILAMENTOS). Comentar no topo a data de vigencia (2026-06-14) e a fonte ANEEL das bandeiras, e a nota "potencia = media de impressao, nao pico da fonte". Adicionar a chave manual em cada dict de presets: IMPRESSORAS["manual"] = {"label": "Outra / manual", "potencia_w": 0, "valor_maquina": 0, "vida_util_h": 0} e FILAMENTOS["manual"] = {"label": "Outro / manual", "preco_kg_default": 0, "densidade_g_cm3": 0}. Expor helpers de namespace (funcoes module-level, sem estado): `impressora_choices()`, `filamento_choices()`, `bandeira_choices()` retornando listas de tuplas (value, label) com "manual" no fim das impressoras/filamentos e "verde" primeiro nas bandeiras; e `presets_json()` retornando um dict serializavel {"impressoras": IMPRESSORAS, "filamentos": FILAMENTOS, "bandeiras": BANDEIRAS_ANEEL} para o json_script (sem duplicar numeros no JS).

Em `forms.py`: importar de `.presets`. Adicionar a CalcForm tres campos de selecao: `impressora` (ChoiceField, choices=impressora_choices(), required=False, initial="manual"), `filamento` (ChoiceField, choices=filamento_choices(), required=False, initial="manual"). Para energia: manter um campo `tarifa_base` (FloatField, label "Tarifa base da distribuidora (R$/kWh)", initial 0.95, min_value 0.01, help_text com a nota do RESEARCH) e adicionar `bandeira` (ChoiceField, choices=bandeira_choices(), initial=BANDEIRA_VIGENTE_DEFAULT). Remover o campo `tarifa_kwh` como input direto do usuario (ele passa a ser derivado). Atualizar o help_text de `potencia_w` para a nota do RESEARCH (potencia ativa media durante impressao, nao a potencia da fonte; usar wattimetro para valor exato). Em `to_calc_data()`: calcular `adicional = BANDEIRAS_ANEEL[c["bandeira"]]["adicional_kwh"]` e `tarifa_kwh = c["tarifa_base"] + adicional`, passando esse `tarifa_kwh` efetivo ao dict que o PricingService espera (a assinatura do servico NAO muda - continua recebendo um unico tarifa_kwh). Os campos de preset (impressora/filamento) NAO entram em to_calc_data - sao apenas UX de auto-preenchimento; os valores reais usados sao os campos numericos editaveis.

Em `views.py`: na view `publica`, injetar `"presets_json": presets_json()` no contexto (para o json_script) alem do form e defaults. Manter a view `orcamento` server-side fina; ela ja chama PricingService via form.to_calc_data(), entao a soma da bandeira passa a valer no orcamento automaticamente. Nao engrossar as views alem de passar contexto.

Respeitar camadas: presets em modulo proprio, logica de soma da tarifa no form (to_calc_data), views finas, servico inalterado.
  </action>
  <verify>
    <automated>.venv/Scripts/python.exe manage.py check</automated>
    <automated>.venv/Scripts/python.exe -c "import os,django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev'); django.setup(); from apps.calculator.forms import CalcForm; f=CalcForm(data={'peso_g':50,'preco_kg':120,'potencia_w':110,'tempo_h':4,'tarifa_base':0.95,'bandeira':'amarela','valor_maquina':2000,'vida_util_h':2000,'custo_maoobra':10,'taxa_falha_pct':10,'margem_pct':150,'impressora':'manual','filamento':'manual'}); assert f.is_valid(), f.errors; d=f.to_calc_data(); assert abs(d['tarifa_kwh']-0.96885)<1e-6, d['tarifa_kwh']; print('OK tarifa efetiva', d['tarifa_kwh'])"</automated>
    <automated>.venv/Scripts/python.exe manage.py makemigrations --check --dry-run calculator</automated>
  </verify>
  <done>presets.py existe com os 3 dicts + helpers + opcao manual; CalcForm valida com tarifa_base+bandeira e to_calc_data soma o adicional (0.95+0.01885=0.96885) no tarifa_kwh efetivo; PricingService inalterado; sem novas migrations.</done>
</task>

<task type="auto">
  <name>Task 2: UI publica profissional + JS (presets, breakdown %, permalink) + CSS</name>
  <files>apps/calculator/templates/calculator/publica.html, static/js/calculator.js, static/css/theme.css</files>
  <action>
Reescrever `publica.html` mantendo `{% extends "base.html" %}` e o layout `.calc-layout` (form a esquerda, resultado sticky a direita; single-column no mobile ja vem do CSS). Secoes claras em cards: Impressora, Filamento, Tempo, Energia (com bandeira), Trabalho, Margem/Risco. Adicionar selects de Impressora e Filamento (montar a partir dos choices ja disponiveis em form.impressora / form.filamento) que, via JS, auto-preenchem os campos numericos correspondentes (impressora -> potencia/valor/vida util; filamento -> preco/kg); "manual" libera os campos para edicao. Secao Energia: campo tarifa_base + select de bandeira, com um elemento com id fixo (ex. res_tarifa_efetiva) que exibe "Tarifa efetiva: R$ X (base R$ Y + Bandeira R$ Z)". Adicionar campo `quantidade` na publica (number, default 1, min 1) para mostrar total quando >1. Serializar os presets para o JS com `{{ presets_json|json_script:"calc-presets" }}` (sem hardcode de numeros no JS). Manter o CTA "Pedir orcamento com a L3D" (placeholder de contato WhatsApp, comentado no template). Adicionar botao "Copiar resultado". Acessibilidade: cada input com `<label for>`, aria-live no painel de resultado, foco visivel, mobile-first. NAO colocar numeros de preset literais no HTML/JS - eles vem do json_script.

Painel de resultado com breakdown visual: para cada componente (material, energia, depreciacao, mao de obra, ajuste de falha) uma linha com rotulo, valor em R$, e uma BARRA proporcional (% do total) - a barra e um elemento cuja largura (style.width = pct + '%') usa tokens (fundo --border-soft, preenchimento --accent / --accent-soft); sem cores literais novas. Mostrar subtotal, custo total, "custo por hora" (custo_total / tempo_h), preco de venda em destaque (reusar .calc-preco-venda), e total (preco_venda * quantidade) exibido somente quando quantidade > 1.

Reescrever `static/js/calculator.js` (IIFE, "use strict", funciona com defer): (a) ler os presets do `#calc-presets` via JSON.parse(textContent); (b) ao mudar o select de impressora/filamento, preencher os inputs numericos a partir do preset (exceto "manual", que nao sobrescreve); (c) calcular tarifa_efetiva = tarifa_base + adicional da bandeira selecionada (adicional vem dos presets) e exibir no elemento de tarifa efetiva; (d) calculo em tempo real espelhando EXATAMENTE PricingService.calcular, com as formulas comentadas e identicas ao Python, usando tarifa_efetiva no custo de energia; (e) breakdown: calcular o % de cada componente sobre custo_total e setar a largura das barras; custo por hora; total por quantidade quando >1; (f) permalink: a cada input, serializar os campos relevantes na query string com history.replaceState; no init, se location.search tiver params, reidratar os campos ANTES do primeiro calculo; (g) botao "Copiar resultado": montar um resumo em texto (componentes + preco de venda) e usar navigator.clipboard.writeText com fallback (textarea + execCommand) e feedback visual. Formatacao BRL via toLocaleString("pt-BR", {style:"currency", currency:"BRL"}). Comentar que e apenas preview client-side (servidor e a fonte da verdade; aceitar +-R$0,01).

Ampliar o bloco `.calc-*` em theme.css a partir de ~linha 2150 (NAO duplicar regras existentes - elas ja cobrem .calc-layout, .calc-section-title, .calc-rows, .calc-preco-venda, @media print). Adicionar: `.calc-bar` (trilho, fundo --border-soft, altura pequena, --radius-sm) e `.calc-bar-fill` (preenchimento --accent/--accent-soft com transition width usando --ease); estilo da linha de tarifa efetiva; badge de custo/hora; estilo do botao "Copiar resultado" e do select de preset. Usar SOMENTE tokens existentes. Garantir que o @media print existente continue ocultando inputs/CTA.
  </action>
  <verify>
    <automated>.venv/Scripts/python.exe -c "import os,django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev'); django.setup(); from django.test import Client; c=Client(); r=c.get('/calculadora/', HTTP_HOST='localhost'); body=r.content.decode(); assert r.status_code==200, r.status_code; assert 'calc-presets' in body, 'json_script ausente'; assert 'Tarifa efetiva' in body or 'tarifa_efetiva' in body or 'res_tarifa_efetiva' in body; print('OK publica render', r.status_code)"</automated>
    <automated>.venv/Scripts/python.exe -c "f=open('static/js/calculator.js',encoding='utf-8').read(); assert 'calc-presets' in f and 'tarifa_efetiva' in f and 'replaceState' in f and 'clipboard' in f, 'JS faltando peca'; print('OK calculator.js')"</automated>
  </verify>
  <done>publica.html renderiza 200 com json_script de presets, selects de impressora/filamento, tarifa efetiva, breakdown com barras, custo/hora, permalink e botao copiar; calculator.js le presets do JSON, espelha as formulas, faz auto-preenchimento, breakdown %, permalink e copiar; CSS .calc-bar/.calc-bar-fill adicionados so com tokens; sem regras duplicadas.</done>
</task>

<task type="auto">
  <name>Task 3: orcamento privado reaproveitando a UI nova + presets/bandeira</name>
  <files>apps/calculator/templates/calculator/orcamento.html</files>
  <action>
Atualizar `orcamento.html` (continua POST server-side, area is_staff) para reaproveitar o markup novo: selects de Impressora e Filamento (de form.impressora / form.filamento), campos tarifa_base + select de bandeira (de form.bandeira) na secao Energia, e o restante dos custos via `{% include "core/partials/field.html" %}` como ja faz. Manter as duas colunas: esquerda = custos de producao (com os mesmos cards/secoes da publica), direita = dados do cliente + botao "Gerar orcamento (PDF)". O calculo do preco final continua 100% server-side via PricingService (a view ja faz isso e a soma da bandeira ja vem de to_calc_data apos a Task 1). NAO incluir o json_script nem o calculator.js de preview aqui se nao for necessario para o fluxo server-side; se reaproveitar o auto-preenchimento JS, incluir o json_script e o script, mas garantir que o submit continua mandando os campos numericos reais (os presets sao so UX). NAO expor custos internos no template do cliente nem no fluxo - o PDF (apps/calculator/pdf.py) ja recebe so {cliente_nome, peca_descricao, quantidade, prazo_entrega, observacoes, preco_venda, total} e NAO deve ser alterado. Manter pt-br e acessibilidade.
  </action>
  <verify>
    <automated>.venv/Scripts/python.exe -c "import os,django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev'); django.setup(); from django.test import Client; from django.contrib.auth import get_user_model; U=get_user_model(); u,_=U.objects.get_or_create(email='staff-ndg@l3d.test', defaults={'is_staff':True}); u.is_staff=True; u.set_password('x'); u.save(); c=Client(); c.force_login(u); g=c.get('/calculadora/orcamento/', HTTP_HOST='localhost'); assert g.status_code==200, g.status_code; p=c.post('/calculadora/orcamento/', data={'peso_g':50,'preco_kg':120,'potencia_w':110,'tempo_h':4,'tarifa_base':0.95,'bandeira':'amarela','valor_maquina':2000,'vida_util_h':2000,'custo_maoobra':10,'taxa_falha_pct':10,'margem_pct':150,'impressora':'manual','filamento':'manual','cliente_nome':'Cliente Teste','peca_descricao':'Peca X','quantidade':2,'prazo_entrega':'3 dias','observacoes':''}, HTTP_HOST='localhost'); assert p.status_code==200 and p['Content-Type']=='application/pdf', (p.status_code, p.get('Content-Type')); assert p.content[:4]==b'%PDF'; print('OK orcamento PDF gerado')"</automated>
  </verify>
  <done>GET /calculadora/orcamento/ retorna 200 (is_staff) com a UI nova (presets + tarifa_base/bandeira); POST valido gera um PDF (%PDF) usando a tarifa efetiva da bandeira; pdf.py inalterado e sem custos internos no documento.</done>
</task>

<task type="auto">
  <name>Task 4: reescrever README.md alinhado ao L3D Labz atual</name>
  <files>README.md</files>
  <action>
Reescrever `README.md` inteiro em pt-br, enxuto e correto, removendo qualquer resquicio de "Nexora" e secoes obsoletas (ex.: cupons de demo so se ainda existirem; nao inventar). Conteudo: titulo e descricao do projeto L3D Labz (fabrica/loja de impressao 3D sob demanda, identidade visual inspirada no Luigi, minimalista, tema claro/escuro). Features REAIS atuais: catalogo (categorias/produtos), visualizador 3D com `<model-viewer>` + galeria, "Faca meu Lithophane", carrinho em sessao, checkout/pedidos com pagamento simulado isolado, contas/enderecos, e a Calculadora de Precificacao 3D (publica em /calculadora/ + orcamento PDF privado is_staff em /calculadora/orcamento/). NAO inventar features que nao existem - verificar contra o codebase antes de listar. Stack: Django 5.2, DRF (serializers como scaffolding), HTML+CSS por design tokens sem framework, JS vanilla sem build, SQLite dev / PostgreSQL prod, LocMem dev / Redis prod opcional, Pillow, reportlab (PDF), whitenoise, gunicorn. Manter a tabela de camadas (Model/Queries/Services/Mappers/Serializers/Views/Templates) que ja esta correta. Como rodar localmente: venv + `pip install -r requirements.txt`, migrate, (seed se o comando ainda existir), createsuperuser, runserver; settings dev/prod. Deploy: citar Docker + Cloudflare Tunnel + CI (apenas mencionar, apontar para .planning, sem detalhar segredos). Substituir titulo "Nexora - E-commerce de Impressao 3D" por algo como "L3D Labz - Impressao 3D sob demanda". Remover env vars com nome "nexora" dos exemplos (usar nomes genericos/l3d).
  </action>
  <verify>
    <automated>.venv/Scripts/python.exe -c "t=open('README.md',encoding='utf-8').read(); low=t.lower(); assert 'nexora' not in low, 'ainda menciona Nexora'; assert 'l3d labz' in low; assert 'calculadora' in low; assert 'model-viewer' in low or 'visualizador 3d' in low; print('OK README')"</automated>
  </verify>
  <done>README.md nao contem "nexora" (case-insensitive), menciona L3D Labz, a Calculadora de Precificacao 3D e o visualizador 3D; descreve stack e como rodar corretamente sem inventar features.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| visitante anonimo -> calculadora publica | inputs numericos nao confiaveis no form publico (so client-side preview + validacao Django no orcamento) |
| usuario is_staff -> orcamento/PDF | custos internos passam pelo servidor; PDF nao pode vazar custos ao cliente final |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-calc-01 | Information Disclosure | gerar_orcamento_pdf / orcamento.html | mitigate | PDF recebe so {cliente, peca, qtd, prazo, obs, preco_venda, total}; pdf.py NAO alterado; nenhum custo interno no template do cliente |
| T-calc-02 | Tampering | inputs da calculadora (client-side) | accept | calculo JS e so preview; orcamento formal recalcula server-side via PricingService com validacao do Django form |
| T-calc-03 | Elevation of Privilege | view orcamento | mitigate | @user_passes_test(is_staff) mantido; verificado no teste (GET 200 com staff) |
| T-calc-04 | Tampering | nenhum install de pacote novo | accept | nao ha instalacao npm/pip/cargo nesta task; reportlab/model-viewer ja presentes no projeto |
</threat_model>

<verification>
- `.venv/Scripts/python.exe manage.py check` sem erros.
- `.venv/Scripts/python.exe manage.py makemigrations --check --dry-run calculator` sem mudancas (app stateless).
- to_calc_data soma a tarifa efetiva (0.95 + 0.01885 = 0.96885) conferido por calculo manual.
- /calculadora/ retorna 200 com json_script de presets, tarifa efetiva e breakdown.
- /calculadora/orcamento/ gera PDF valido (%PDF) com is_staff e sem custos internos.
- README sem "nexora" e com L3D Labz + Calculadora.
</verification>

<success_criteria>
- presets.py com IMPRESSORAS/FILAMENTOS/BANDEIRAS_ANEEL + opcao manual + helpers de choices/json.
- Bandeira aplicada como tarifa_efetiva = tarifa_base + adicional ANTES do calculo de energia (no form), PricingService inalterado.
- UI publica profissional em duas colunas: presets auto-preenchem, breakdown com barras %, custo/hora, total por quantidade, permalink e copiar resultado, so com tokens.
- Orcamento privado reaproveita a UI e gera PDF sem expor custos internos.
- README alinhado ao L3D Labz atual, pt-br, sem Nexora, sem inventar features.
- Sem novos models/migrations; camadas respeitadas; copy em pt-br.
</success_criteria>

<output>
Create `.planning/quick/260614-ndg-calculadora-de-precificacao-3d-v2-generi/260614-ndg-SUMMARY.md` when done
</output>
