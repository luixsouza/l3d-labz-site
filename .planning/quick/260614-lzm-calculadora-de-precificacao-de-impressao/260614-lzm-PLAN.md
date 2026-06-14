---
phase: quick-260614-lzm
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - apps/calculator/__init__.py
  - apps/calculator/apps.py
  - apps/calculator/services.py
  - apps/calculator/forms.py
  - apps/calculator/mappers.py
  - apps/calculator/pdf.py
  - apps/calculator/views.py
  - apps/calculator/urls.py
  - apps/calculator/admin.py
  - apps/calculator/templates/calculator/publica.html
  - apps/calculator/templates/calculator/orcamento.html
  - static/js/calculator.js
  - static/css/theme.css
  - config/settings/base.py
  - config/urls.py
  - apps/core/templates/core/partials/navbar.html
  - requirements.txt
autonomous: true
requirements: [CALC-PUB, CALC-PRIV, CALC-PDF]
must_haves:
  truths:
    - "Qualquer visitante abre /calculadora/ e calcula o preço de impressão em tempo real (vanilla JS), vendo o detalhamento completo de custos"
    - "A página pública mostra um CTA para falar com a L3D / pedir orçamento"
    - "Só usuário is_staff acessa /calculadora/orcamento/ (não-staff é redirecionado pro login)"
    - "Admin preenche custos + dados do cliente e baixa um PDF de orçamento com a marca L3D contendo cliente, peça, quantidade, prazo e preço final (e total = preço * quantidade)"
    - "O PDF NÃO expõe nenhum custo interno (filamento/energia/depreciação/mão de obra/margem/taxa de falha)"
    - "A lógica de cálculo é fonte única em services.py e é reusada pela view de orçamento (server-side)"
    - "Há link 'Calculadora' no navbar apontando pra calculadora pública"
  artifacts:
    - path: "apps/calculator/services.py"
      provides: "PricingService.calcular — fórmulas de precificação (stateless, fonte única da verdade) + dataclass de defaults"
      contains: "class PricingService"
    - path: "apps/calculator/pdf.py"
      provides: "Geração do PDF de orçamento com reportlab, sem expor custos internos"
      contains: "def gerar_orcamento_pdf"
    - path: "apps/calculator/forms.py"
      provides: "CalcForm (inputs de custo) e OrcamentoForm (custos + dados do cliente)"
      contains: "class OrcamentoForm"
    - path: "apps/calculator/views.py"
      provides: "View pública (GET) + view de orçamento protegida is_staff (GET/POST -> PDF)"
      contains: "user_passes_test"
    - path: "static/js/calculator.js"
      provides: "Cálculo client-side em tempo real espelhando as fórmulas do services"
      min_lines: 40
    - path: "apps/calculator/templates/calculator/publica.html"
      provides: "Calculadora pública minimalista L3D com detalhamento completo + CTA"
    - path: "apps/calculator/templates/calculator/orcamento.html"
      provides: "Form de orçamento admin (inputs de custo + dados do cliente)"
  key_links:
    - from: "apps/calculator/views.py"
      to: "apps/calculator/services.py"
      via: "PricingService.calcular no fluxo de orçamento (server-side)"
      pattern: "PricingService\\.calcular"
    - from: "apps/calculator/views.py"
      to: "apps/calculator/pdf.py"
      via: "gerar_orcamento_pdf retornando HttpResponse com PDF"
      pattern: "gerar_orcamento_pdf"
    - from: "config/urls.py"
      to: "apps/calculator/urls.py"
      via: "path('calculadora/', include('apps.calculator.urls'))"
      pattern: "apps\\.calculator\\.urls"
    - from: "apps/core/templates/core/partials/navbar.html"
      to: "apps/calculator/urls.py"
      via: "{% url 'calculator:publica' %}"
      pattern: "calculator:publica"
---

<objective>
Criar a Calculadora de Precificação de Impressão 3D da L3D Labz com duas interfaces:
uma pública (aberta, cálculo em vanilla JS em tempo real, mostra todo o detalhamento de
custos + CTA) e uma privada/admin (protegida por is_staff, cálculo server-side, gera um
orçamento em PDF profissional com a marca L3D que esconde os custos internos do cliente).

Purpose: dar ao maker uma ferramenta de custo transparente e à L3D uma forma rápida de
emitir orçamentos sem revelar a estrutura de custos/margem.

Output: novo app `apps/calculator` seguindo o padrão do `apps/lithophane` (services finos,
views finas, mappers/formatting, templates pt-br), reportlab pinado no requirements, link
no navbar, e estilos no theme.css usando os design tokens existentes.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

# Análogo de arquitetura (COPIE este padrão: app stateless, services @staticmethod, views finas)
@apps/lithophane/services.py
@apps/lithophane/views.py
@apps/lithophane/urls.py
@apps/lithophane/apps.py
@apps/lithophane/mappers.py
@apps/lithophane/admin.py
@apps/lithophane/templates/lithophane/editor.html

# Formatação BRL e form->dict
@apps/core/formatting.py
@apps/orders/forms.py

# Templates / tokens / JS vanilla (padrão IIFE, defer, CSRF helper)
@apps/core/templates/base.html
@apps/core/templates/core/partials/navbar.html
@apps/core/templates/core/partials/field.html
@static/js/app.js

# Montagem do app
@config/urls.py
@requirements.txt

<interfaces>
<!-- Contratos já existentes no codebase — use diretamente, sem explorar. -->

apps/core/formatting.py:
```python
def format_brl(value: Decimal | float | int | None) -> str:  # 1234.5 -> 'R$ 1.234,50'
```

apps/core/layers.py:
```python
class BaseService: ...          # marcador de intenção (classe base vazia)
class BaseMapper[M]: ...        # provê to_list(); subclasse implementa to_dict()
```

config/settings/base.py — LOCAL_APPS (linhas ~47-54): apps.core, apps.accounts, apps.catalog,
apps.promotions, apps.cart, apps.orders, apps.lithophane. Adicionar "apps.calculator".

Padrão de proteção staff (Django): `from django.contrib.auth.decorators import user_passes_test`
e decorar a view com `@user_passes_test(lambda u: u.is_staff)`.

Classes CSS de tokens já disponíveis no theme.css: `.section`, `.container`, `.page-head`,
`.eyebrow`, `.card`, `.field` (label+input+help+errors), `.grid-2`, `.form-grid` (+ `.col-2`),
`.btn .btn-primary .btn-ghost .btn-block .btn-sm`, `.text-muted`, `.text-dim`.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Scaffold do app + fórmulas de cálculo (services) + forms</name>
  <files>apps/calculator/__init__.py, apps/calculator/apps.py, apps/calculator/services.py, apps/calculator/forms.py, apps/calculator/mappers.py, apps/calculator/admin.py, config/settings/base.py</files>
  <behavior>
    PricingService.calcular(...) recebe os inputs de custo e devolve um dict com TODAS as
    chaves de saída (decisão D-01): custo_material, custo_energia, custo_depreciacao,
    custo_maoobra, subtotal, ajuste_falha, custo_total, preco_venda. Casos a fixar via cálculo manual:
    - custo_material = (peso_g/1000) * preco_kg → ex.: 50g a R$120/kg = R$6,00
    - custo_energia = (potencia_w/1000) * tempo_h * tarifa_kwh → ex.: 110W, 4h, R$0,95 = R$0,418
    - custo_depreciacao = (valor_maquina/vida_util_h) * tempo_h → ex.: R$2000/2000h * 4h = R$4,00
    - custo_maoobra = valor fixo informado (R$) → passthrough
    - subtotal = soma dos quatro custos acima
    - ajuste_falha = subtotal * (taxa_falha/100); custo_total = subtotal + ajuste_falha
    - preco_venda = custo_total * (1 + margem/100)
    Arredondar valores monetários para 2 casas no dict de saída.
  </behavior>
  <action>
    Criar o app `apps/calculator` espelhando `apps/lithophane`. Em `apps.py`: AppConfig com
    name="apps.calculator", default_auto_field BigAutoField, verbose_name="Calculadora".
    Registrar "apps.calculator" em LOCAL_APPS no config/settings/base.py (após "apps.lithophane").

    Em `services.py` criar `PricingService(BaseService)` com `@staticmethod calcular(...)` que é a
    FONTE ÚNICA DA VERDADE das fórmulas (decisão D-01, modelo de custo COMPLETO). Centralizar os
    defaults num dataclass `CustoDefaults` (frozen) — decisão D-05: tarifa_kwh=0.95, margem_pct=150,
    taxa_falha_pct=10, potencia_w=110 (Ender 3; comentar Prusa i3 MK3=180W como exemplo),
    valor_maquina, vida_util_h. Usar Decimal nas contas monetárias e devolver floats arredondados
    a 2 casas (consistente com format_brl). Não tocar no banco (cálculo stateless por D-05).

    Em `forms.py`: `CalcForm` (forms.Form) com os inputs de custo (peso_g, preco_kg, potencia_w,
    tempo_h, tarifa_kwh, valor_maquina, vida_util_h, custo_maoobra, taxa_falha_pct, margem_pct) —
    todos com defaults sensatos (initial=CustoDefaults) e help_text em pt-br. `OrcamentoForm` herda/
    estende com os campos do cliente (decisão D-03): cliente_nome, peca_descricao, quantidade
    (IntegerField min=1), prazo_entrega (CharField), observacoes (CharField textarea, required=False).
    Adicionar `to_calc_data()` em CalcForm convertendo cleaned_data no dict que PricingService espera
    (padrão `to_*_data()` do apps/orders/forms.py).

    Em `mappers.py`: `PricingMapper(BaseMapper)` com `to_display(resultado: dict)` que aplica
    format_brl em cada valor monetário do resultado (custo_material..preco_venda) devolvendo strings
    prontas pro template. Em `admin.py`: deixar só o docstring pt-br (sem models a registrar — app stateless).
    Toda copy/docstrings em pt-br (convenção CLAUDE.md).
  </action>
  <verify>
    <automated>cd /c/dev/l3d-labz-site && python -c "import django,os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev');django.setup();from apps.calculator.services import PricingService;r=PricingService.calcular(peso_g=50,preco_kg=120,potencia_w=110,tempo_h=4,tarifa_kwh=0.95,valor_maquina=2000,vida_util_h=2000,custo_maoobra=10,taxa_falha_pct=10,margem_pct=150);print(r);assert abs(r['custo_material']-6.0)<0.01 and abs(r['custo_depreciacao']-4.0)<0.01 and set(['custo_material','custo_energia','custo_depreciacao','custo_maoobra','subtotal','ajuste_falha','custo_total','preco_venda'])<=set(r)"</automated>
  </verify>
  <done>App registrado em INSTALLED_APPS; `python manage.py check` passa; PricingService.calcular devolve as 8 chaves de saída com os valores corretos do exemplo; forms validam com defaults.</done>
</task>

<task type="auto">
  <name>Task 2: Calculadora pública (rota aberta + template + JS vanilla + CSS + navbar)</name>
  <files>apps/calculator/views.py, apps/calculator/urls.py, apps/calculator/templates/calculator/publica.html, static/js/calculator.js, static/css/theme.css, config/urls.py, apps/core/templates/core/partials/navbar.html</files>
  <action>
    Implementar a calculadora PÚBLICA (decisão D-02): rota aberta em /calculadora/.

    Em `views.py`: view fina `publica(request)` que renderiza `calculator/publica.html` passando os
    defaults (CustoDefaults) pro template (initial dos inputs). Em `urls.py`: app_name="calculator",
    `path("", views.publica, name="publica")`. Em config/urls.py montar
    `path("calculadora/", include("apps.calculator.urls"))` (espelhando a linha do lithophane).

    Em `publica.html` (extends base.html): cabeçalho com `.page-head` + `.eyebrow` em pt-br;
    formulário com os campos de custo agrupados em seções (Filamento / Energia / Máquina / Trabalho /
    Margem) usando `.card`, `.field` e `.form-grid`. Painel de RESULTADO mostrando o DETALHAMENTO
    COMPLETO (custo_material, custo_energia, custo_depreciacao, custo_maoobra, subtotal, ajuste_falha,
    custo_total e preco_venda em destaque) — é ferramenta de maker, revela tudo. Incluir um CTA
    `.btn .btn-primary` "Pedir orçamento com a L3D" — usar placeholder de contato (link WhatsApp
    wa.me ou mailto) já que não há página de contato dedicada; comentar no template que é placeholder.
    Mobile-first, usa os tokens do tema (claro/escuro automático). Carregar o JS em extra_js com defer.

    Em `static/js/calculator.js`: IIFE vanilla (espelha static/js/app.js — "use strict", defer) que
    lê os inputs, RECALCULA EM TEMPO REAL no input/change espelhando EXATAMENTE as fórmulas do
    PricingService (mesmas operações da Task 1) e escreve os resultados formatados em R$ nos elementos
    de saída (formatação BRL simples em JS: pt-BR via toLocaleString('pt-BR',{style:'currency',
    currency:'BRL'})). Sem framework, sem build. Nenhum fetch — cálculo 100% client-side aqui.

    Em `theme.css`: adicionar um pequeno bloco de estilos da calculadora (ex.: `.calc-grid`,
    `.calc-result`, `.calc-row`, `.calc-total`) usando SÓ os tokens existentes (--bg-card, --border,
    --accent, --radius, --text-muted etc.), incluindo a regra de impressão se necessário. Não
    introduzir cores literais novas (convenção de tokens). Adicionar link "Calculadora" no navbar.html
    (dentro de .main-nav, padrão dos outros links com classe active via vn == 'calculator:publica').
  </action>
  <verify>
    <automated>cd /c/dev/l3d-labz-site && python -c "import os,django;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev');django.setup();from django.test import Client;c=Client();r=c.get('/calculadora/');print('status',r.status_code);b=r.content.decode();assert r.status_code==200 and 'calculator.js' in b and ('preco' in b.lower() or 'preço' in b.lower())" && python manage.py check</automated>
  </verify>
  <done>GET /calculadora/ retorna 200 com o form e o JS; o detalhamento completo de custos aparece na página; CTA presente; link "Calculadora" no navbar; `python manage.py check` passa.</done>
</task>

<task type="auto">
  <name>Task 3: Calculadora privada (is_staff) + geração do PDF de orçamento + requirements</name>
  <files>requirements.txt, apps/calculator/pdf.py, apps/calculator/views.py, apps/calculator/urls.py, apps/calculator/templates/calculator/orcamento.html</files>
  <action>
    Implementar a calculadora PRIVADA / ORÇAMENTO (decisões D-03 e D-04).

    Em `requirements.txt`: adicionar reportlab pinado com `==` (decisão D-04 — pura-python, sem deps
    de sistema, funciona Windows dev + Docker Linux prod; NÃO usar WeasyPrint). Numa seção pt-br
    ("# --- Geração de PDF (orçamentos) ---"). Instalar no venv: `pip install reportlab==<versao>`.

    Em `apps/calculator/pdf.py` (módulo isolado, análogo ao apps/lithophane/generation.py):
    `def gerar_orcamento_pdf(dados: dict) -> bytes` usando reportlab (canvas ou platypus/SimpleDocTemplate).
    O PDF é o ORÇAMENTO do cliente com a marca L3D Labz e contém SOMENTE (decisão D-03):
    cabeçalho/título "L3D Labz — Orçamento", nome do cliente, descrição da peça, quantidade, prazo de
    entrega, observações, PREÇO FINAL (preco_venda) e TOTAL = preco_venda * quantidade (format BRL).
    PROIBIDO incluir custo_material/energia/depreciacao/maoobra/subtotal/margem/taxa_falha — o cliente
    NÃO vê custos internos. Valores em R$ formatados pt-br.

    Em `views.py`: adicionar `@user_passes_test(lambda u: u.is_staff)` na view `orcamento(request)`.
    GET renderiza `calculator/orcamento.html` (OrcamentoForm com defaults). POST: valida o OrcamentoForm;
    se válido, calcula SERVER-SIDE via `PricingService.calcular(**form.to_calc_data())` (reuso da fonte
    única — key_link), monta o dict de dados do cliente (preco_venda, quantidade, total, nome, peça,
    prazo, obs) e retorna `HttpResponse(gerar_orcamento_pdf(dados), content_type='application/pdf')`
    com `Content-Disposition: attachment; filename="orcamento-<cliente>.pdf"`. Em `urls.py`:
    `path("orcamento/", views.orcamento, name="orcamento")`.

    Em `orcamento.html` (extends base.html): form POST com csrf_token, os mesmos inputs de custo da
    pública MAIS os campos do cliente (cliente_nome, peca_descricao, quantidade, prazo_entrega,
    observacoes), usando `.card`/`.field`/`.form-grid` e `{% include "core/partials/field.html" %}`.
    Botão "Gerar orçamento (PDF)" `.btn .btn-primary`. Copy 100% pt-br. (Pode reaproveitar/parcializar
    o markup da pública, mas mantenha a separação: esta página é só pra staff e foca em emitir o PDF.)
  </action>
  <verify>
    <automated>cd /c/dev/l3d-labz-site && python -c "import os,django;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev');django.setup();from apps.calculator.pdf import gerar_orcamento_pdf;b=gerar_orcamento_pdf({'cliente_nome':'Fulano','peca_descricao':'Vaso','quantidade':2,'prazo_entrega':'5 dias','observacoes':'','preco_venda':50.0,'total':100.0});assert b[:5]==b'%PDF-' and len(b)>800;from django.test import Client;c=Client();r=c.get('/calculadora/orcamento/');print('anon redirect',r.status_code);assert r.status_code in (302,301)" && python manage.py check && python manage.py makemigrations --check --dry-run</automated>
  </verify>
  <done>reportlab pinado e instalado; gerar_orcamento_pdf devolve bytes de PDF válido (%PDF-) sem custos internos; acesso anônimo a /calculadora/orcamento/ redireciona (is_staff exigido); POST de staff devolve PDF; cálculo do orçamento roda via PricingService (server-side); `python manage.py check` e `makemigrations --check` passam (sem models novos).</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| visitante anônimo → /calculadora/ | rota pública: inputs numéricos não confiáveis chegam só ao JS client-side; nada persiste |
| usuário → /calculadora/orcamento/ | rota protegida is_staff: inputs chegam ao servidor, geram PDF |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-calc-01 | Elevation of Privilege | view `orcamento` | mitigate | `@user_passes_test(lambda u: u.is_staff)` — não-staff é redirecionado pro login (verificado no teste anônimo→302) |
| T-calc-02 | Information Disclosure | PDF do cliente | mitigate | `gerar_orcamento_pdf` recebe SÓ {cliente, peça, qtd, prazo, obs, preco_venda, total}; custos internos nunca entram no dict do PDF (decisão D-03) |
| T-calc-03 | Tampering | inputs numéricos do form de orçamento | mitigate | OrcamentoForm valida tipos (DecimalField/IntegerField); cálculo server-side ignora qualquer "preço" vindo do cliente e recalcula via PricingService |
| T-calc-SC | Tampering | pip install reportlab | mitigate | reportlab é pacote consolidado e amplamente usado; pinado com `==`; verificar legitimidade em pypi.org/project/reportlab antes do install |
</threat_model>

<verification>
- `python manage.py check` sem erros após todas as tarefas.
- `python manage.py makemigrations --check --dry-run` não detecta migrations pendentes (app é stateless, sem models).
- GET /calculadora/ → 200 com form + JS de cálculo em tempo real + detalhamento completo + CTA.
- GET /calculadora/orcamento/ anônimo → redirect (302) pro login.
- gerar_orcamento_pdf devolve bytes começando com %PDF- e sem nenhum custo interno.
- PricingService.calcular é chamado pela view de orçamento (cálculo server-side, fonte única).
- Link "Calculadora" presente no navbar.
- NÃO rodar `runserver` de forma bloqueante (usar django.test.Client para checar rotas).
</verification>

<success_criteria>
- App `apps/calculator` segue o padrão em camadas do CLAUDE.md: views finas, lógica em services
  (@staticmethod, stateless), forms com `to_calc_data()`, mappers/formatting pra exibição, PDF isolado.
- Calculadora pública funciona client-side em tempo real e revela todos os custos + CTA (D-02).
- Calculadora privada exige is_staff e gera PDF de orçamento da marca L3D sem expor custos (D-03, D-04).
- Fórmulas de custo COMPLETAS (material, energia, depreciação, mão de obra, taxa de falha, margem)
  com defaults centralizados e editáveis (D-01, D-05); cálculo do orçamento roda server-side.
- reportlab pinado com `==` no requirements.txt (D-04); toda copy em pt-br.
- Cada tarefa é commitável atomicamente.
</success_criteria>

<output>
Crie `.planning/quick/260614-lzm-calculadora-de-precificacao-de-impressao/260614-lzm-SUMMARY.md` ao concluir.
</output>
