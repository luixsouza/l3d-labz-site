---
phase: quick-260617-mrl
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - apps/calculator/presets.py
  - apps/calculator/forms.py
  - apps/calculator/services.py
  - static/js/calculator.js
  - apps/calculator/templates/calculator/publica.html
  - apps/calculator/templates/calculator/orcamento.html
  - apps/core/templates/core/partials/navbar.html
  - apps/core/templates/core/partials/footer.html
  - static/css/theme.css
autonomous: false
requirements: [calc-enxuto, calc-mockup, navbar-footer-skin]
must_haves:
  truths:
    - "A calculadora pública recalcula em tempo real só com material, energia, mão de obra, custos fixos e margem (sem depreciação/vida útil nem taxa de falha)."
    - "O cliente vê 3 cards (Filamento, Energia e Tempo, Opcionais) no layout do mockup, com chips de potência, chips de bandeira e chips de margem que preenchem os campos."
    - "Os botões 'Puxar preço do site' e 'Restaurar preço automático' preenchem o R$/kg com o preço de referência L3D do material selecionado."
    - "PricingService.calcular e calculator.js produzem o mesmo preço de venda com a fórmula enxuta."
    - "O fluxo staff de orçamento + PDF continua funcionando (PDF só com dados públicos)."
    - "Navbar e footer usam o skin maker: brand-badge com logo.png, 'Labz' em verde, footer-brand-block com mascot-name/mascot-sub — nos temas claro e escuro."
  artifacts:
    - path: "apps/calculator/services.py"
      provides: "PricingService.calcular enxuto (5 chaves de custo)"
      contains: "custos_fixos"
    - path: "apps/calculator/forms.py"
      provides: "CalcForm enxuto + to_calc_data simplificado"
      contains: "custos_fixos"
    - path: "static/js/calculator.js"
      provides: "espelho client-side da fórmula enxuta + botões de preço + chips"
    - path: "apps/calculator/templates/calculator/publica.html"
      provides: "layout 3 cards do mockup"
    - path: "apps/core/templates/core/partials/navbar.html"
      provides: "marca skin maker (brand-badge + brand-labz)"
    - path: "apps/core/templates/core/partials/footer.html"
      provides: "footer-brand-block (mascot-name/mascot-sub)"
  key_links:
    - from: "static/js/calculator.js"
      to: "apps/calculator/services.py"
      via: "fórmula espelhada (preço de venda idêntico)"
      pattern: "custos_fixos"
    - from: "apps/calculator/forms.py"
      to: "apps/calculator/services.py"
      via: "to_calc_data() -> PricingService.calcular(**...)"
      pattern: "valor_kwh|custos_fixos"
---

<objective>
Redesenhar a calculadora de custos pública para bater fielmente com o mockup (image.png, estilo 3dprime), trocar o modelo de cálculo pela versão enxuta (remover depreciação automática e taxa de falha; adicionar custos_fixos manual e valor_kwh único), e sincronizar navbar/footer com o skin maker já presente no CSS.

Purpose: Entregar a calculadora simples e bonita que o usuário aprovou no mockup, mantendo a arquitetura em camadas (PricingService = fonte única, forms alimenta o service, calculator.js só espelha) e o fluxo staff/PDF intacto.

Output: presets/forms/services/JS no modelo enxuto; template público no layout de 3 cards; navbar/footer no skin maker; CSS de suporte; validação visual por screenshot nos temas claro e escuro.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@image.png

# Backend calc atual (a enxugar)
@apps/calculator/presets.py
@apps/calculator/forms.py
@apps/calculator/services.py
@apps/calculator/views.py
@apps/calculator/pdf.py

# Frontend calc (a redesenhar / espelhar)
@static/js/calculator.js
@apps/calculator/templates/calculator/publica.html
@apps/calculator/templates/calculator/orcamento.html

# Skin maker de referência (já existe no CSS)
@apps/core/templates/core/partials/navbar.html
@apps/core/templates/core/partials/footer.html
@apps/core/templates/core/home.html

<interfaces>
<!-- Fórmula ENXUTA (decisão travada — não revisitar): -->
<!-- custo_material = (peso_g/1000) * preco_kg -->
<!-- custo_energia  = (potencia_w/1000) * tempo_h * valor_kwh -->
<!-- subtotal       = custo_material + custo_energia + custo_maoobra + custos_fixos -->
<!-- preco_venda    = subtotal * (1 + margem_pct/100) -->
<!-- REMOVER: vida_util_h/valor_maquina/custo_depreciacao E taxa_falha_pct/ajuste_falha. -->
<!-- valor_kwh é UM campo único (R$/kWh); chips de bandeira apenas PREENCHEM esse campo no client. -->

<!-- CSS do skin maker já existe — NÃO recriar, apenas usar o markup esperado: -->
<!-- navbar: <span class="brand-badge"><img src="{% static 'img/logo.png' %}" alt=""></span>
            <span class="brand-word">L3D <span class="brand-labz">Labz</span></span>
     (.brand-badge linha ~129; .brand-word linha ~154; .brand-labz linha ~160; skin header linha ~1591) -->
<!-- footer: 1ª coluna do .footer-grid vira .footer-brand-block com
            <span class="mascot-name">L3D <b>Labz</b></span> + <p class="mascot-sub">...</p>
     (.footer-brand-block .mascot-name linha ~1675; .mascot-sub linha ~1678;
      NOTA linha ~1695 força mascot-name uniforme sem verde — comportamento atual a preservar) -->
<!-- Componentes de chip/botão maker existentes: .pill / .pill.active (linha ~660),
     .btn / .btn-primary / .btn-ghost / .btn-block (linha ~91-112, skin ~1197), .icon-btn (~187). -->
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Modelo de cálculo enxuto (presets + forms + service + staff template)</name>
  <files>apps/calculator/presets.py, apps/calculator/forms.py, apps/calculator/services.py, apps/calculator/templates/calculator/orcamento.html</files>
  <behavior>
    - PricingService.calcular(peso_g=130, preco_kg=120, potencia_w=200, tempo_h=6, valor_kwh=1.00, custo_maoobra=20, custos_fixos=0, margem_pct=100) retorna:
      custo_material=15.60, custo_energia=1.20, custo_maoobra=20.00, custos_fixos=0.00, subtotal=36.80, preco_venda=73.60.
    - O dict retornado tem EXATAMENTE estas chaves: custo_material, custo_energia, custo_maoobra, custos_fixos, subtotal, preco_venda (sem custo_depreciacao, custo_total, ajuste_falha).
    - CalcForm.to_calc_data() devolve dict com chaves: peso_g, preco_kg, potencia_w, tempo_h, valor_kwh, custo_maoobra, custos_fixos, margem_pct (sem valor_maquina, vida_util_h, tarifa_base, bandeira, taxa_falha_pct).
    - OrcamentoForm (herda CalcForm) continua válido com os campos de cliente; OrcamentoService.criar e a view orcamento POST seguem funcionando (preco_venda do dict enxuto).
  </behavior>
  <action>
    Em presets.py: simplificar PARA O ESCOPO ENXUTO. Adicionar CONSUMO_CHIPS = lista de 3 chips fixos do mockup [{"label":"Ender 3 (~120W)","w":120},{"label":"Bambu A1 (~200W)","w":200},{"label":"Bambu X1C (~350W)","w":350}] e BANDEIRA_KWH = {"verde":0.95,"amarela":0.97,"vermelha":1.02} com docstring documentando a origem (tarifa base BR 2025 ≈ R$0,95 + adicional ANEEL aproximado por bandeira). Manter FILAMENTOS (preco_kg_default é a fonte do botão "puxar preço"). presets_json() deve passar a expor "filamentos", "consumo_chips" e "bandeira_kwh" (remover dependência de "impressoras"/"bandeiras" antigas no JS — pode manter as constantes legadas se outro código usar, mas o json para o JS é o enxuto). Remover/parar de usar impressora_choices e bandeira_choices se ninguém mais consome (confira com grep antes de apagar).
    Em forms.py: CalcForm passa a ter campos: filamento (ChoiceField UX), peso_g, preco_kg, potencia_w, tempo_h, valor_kwh (FloatField min 0.01, label "Valor do kWh (R$)"), custo_maoobra (min 0), custos_fixos (FloatField min 0, required False default 0, label "Custos Fixos (R$)", help "Desgaste da impressora, acabamento, etc."), margem_pct. REMOVER os campos impressora, valor_maquina, vida_util_h, tarifa_base, bandeira, taxa_falha_pct. Reescrever to_calc_data() para o dict enxuto (sem soma de bandeira — valor_kwh vai direto). custos_fixos vazio = 0.0.
    Em services.py: reescrever PricingService.calcular para a assinatura/fórmula enxuta (keyword-only): peso_g, preco_kg, potencia_w, tempo_h, valor_kwh, custo_maoobra, custos_fixos=0.0, margem_pct. Remover custo_depreciacao, ajuste_falha, custo_total e os params valor_maquina/vida_util_h/tarifa_kwh/taxa_falha_pct. Atualizar CustoDefaults (remover valor_maquina/vida_util_h/taxa_falha_pct; tarifa_kwh -> valor_kwh; manter margem_pct default). Atualizar a docstring do módulo com a fórmula enxuta. NÃO mexer em OrcamentoService (já só recebe dados públicos).
    Em orcamento.html (staff): remover o card "Impressora" inteiro (potencia_w fica num card próprio ou junto de tempo/energia), remover valor_maquina/vida_util_h, remover taxa_falha_pct; trocar o card "Energia" (tarifa_base+bandeira) por um único campo valor_kwh; adicionar custos_fixos no card de trabalho/opcionais; manter o select de filamento e o painel de dados do cliente intactos. Garantir que a view orcamento POST recompute preco_venda pelo dict enxuto (a view já faz resultado["preco_venda"] — confirmar que a chave existe).
    Atualizar pdf.py SOMENTE se houver referência a custo interno (não deve haver — ele já recebe só o dict público; apenas confirme, não altere a lógica pública).
  </action>
  <verify>
    <automated>cd C:/dev/l3d-labz-site && python manage.py shell -c "from apps.calculator.services import PricingService as P; r=P.calcular(peso_g=130,preco_kg=120,potencia_w=200,tempo_h=6,valor_kwh=1.00,custo_maoobra=20,custos_fixos=0,margem_pct=100); assert set(r)=={'custo_material','custo_energia','custo_maoobra','custos_fixos','subtotal','preco_venda'}, r; assert r['preco_venda']==73.60, r; print('OK', r)"</automated>
    <automated>cd C:/dev/l3d-labz-site && python manage.py check</automated>
  </verify>
  <done>PricingService e CalcForm.to_calc_data usam a fórmula enxuta (5 custos + preço); o staff orcamento.html não referencia mais campos removidos; manage.py check passa; o cálculo de exemplo do mockup bate (preço 73,60).</done>
</task>

<task type="auto">
  <name>Task 2: Calculadora pública no layout do mockup (template + JS + CSS)</name>
  <files>apps/calculator/templates/calculator/publica.html, static/js/calculator.js, static/css/theme.css</files>
  <action>
    publica.html: reescrever o formulário para os 3 cards do mockup (cada card com ícone redondo + título usando o sprite #icons existente):
    1) "Filamento": field "Material de referência" (select id_filamento); field "Preço do Filamento" (id_preco_kg, sufixo "R$/kg"); field "Quantidade Utilizada (g)" (id_peso_g, sufixo "g", help "Consulte o fatiador para saber a gramagem"). Abaixo do material, dois botões estilo ghost com ícone: id="btnPuxarPreco" "Puxar preço do site" e id="btnRestaurarPreco" "Restaurar preço automático" (usar .btn .btn-ghost .btn-sm).
    2) "Energia e Tempo": field "Consumo da Impressora (W)" (id_potencia_w, sufixo "W") com 3 chips .pill abaixo (data-w=120/200/350, textos "Ender 3 (~120W)","Bambu A1 (~200W)","Bambu X1C (~350W)") renderizados a partir de presets consumo_chips; field "Tempo de Impressão (horas)" (id_tempo_h); field "Valor do kWh (R$)" (id_valor_kwh, sufixo "R$") com 3 chips .pill (data-kwh) "Bandeira verde/amarela/vermelha" renderizados de presets bandeira_kwh.
    3) "Opcionais": field "Mão de Obra (R$)" (id_custo_maoobra, help "Valor fixo por peça (preparação, acabamento, etc.)"); field "Custos Fixos (R$)" (id_custos_fixos, help "Desgaste da impressora, acabamento, etc."); field "Margem de Lucro (%)" (id_margem_pct) com chips .pill 30/50/80/100 (data-margem).
    Rodapé do form: botão primário largo type=button id="btnCalcular" .btn .btn-primary .btn-block "Calcular Custo" + botão secundário id="btnLimpar" .btn .btn-ghost "Limpar". Título "Calculadora de Custos" / sub "Calcule o custo real da sua impressão 3D".
    Manter o painel de resultado/breakdown adaptado à fórmula enxuta: linhas material, energia, mão de obra, custos fixos, subtotal, preço de venda. REMOVER as linhas/barras de depreciação e ajuste de falha e seus ids. Manter o botão "Copiar resultado" (#btnCopiar). Todos os inputs numéricos usam |unlocalize nos initials e ids id_<campo> (o JS depende deles).
    calculator.js: atualizar o espelho para a fórmula enxuta (remover custo_depreciacao, ajuste_falha, custo_total, valor_maquina, vida_util_h, tarifa_base/bandeira; ler valor_kwh direto). Ler presets {filamentos, consumo_chips, bandeira_kwh}. Implementar: clique nos chips .pill[data-w] preenche id_potencia_w (+ marca .active e recalcula); .pill[data-kwh] preenche id_valor_kwh; .pill[data-margem] preenche id_margem_pct. btnPuxarPreco e btnRestaurarPreco preenchem id_preco_kg com FILAMENTOS[material].preco_kg_default (ambos usam a mesma referência). btnLimpar reseta o form e recalcula. Atualizar CAMPOS_PERMALINK (remover ids mortos, incluir valor_kwh, custos_fixos). Atualizar copiarResultado para as linhas enxutas. Recalcular em input/change e ao clicar Calcular.
    theme.css: NO FIM do arquivo (vencendo light/dark/!important como o resto do skin maker), adicionar só o que faltar para reproduzir o mockup: ícone redondo dos títulos de seção (.calc-card-ic ou similar), sufixo de unidade dentro do input (.calc-suffix, ex.: "R$/kg","g","W","R$","%"), espaçamento dos chips, e ajustes de grid das 3 colunas por card. Reaproveitar .card/.field/.pill/.btn existentes; não duplicar tokens. Comparar contra image.png e iterar (memória "theme-css-especificidade": especificidade igual/maior).
  </action>
  <verify>
    <automated>cd C:/dev/l3d-labz-site && python manage.py check && python -c "import re,io; s=open('static/js/calculator.js',encoding='utf-8').read(); assert 'custo_depreciacao' not in s and 'ajuste_falha' not in s and 'taxa_falha' not in s, 'JS ainda tem campos mortos'; assert 'valor_kwh' in s and 'custos_fixos' in s, 'JS sem campos novos'; print('JS OK')"</automated>
    <automated>cd C:/dev/l3d-labz-site && grep -v '^[[:space:]]*#' apps/calculator/templates/calculator/publica.html | grep -c "id_valor_kwh\|id_custos_fixos\|btnPuxarPreco\|btnCalcular"</automated>
  </verify>
  <done>publica.html mostra os 3 cards do mockup com chips e botões funcionais; calculator.js espelha a fórmula enxuta e implementa chips/botões/limpar; CSS reproduz o visual do mockup; manage.py check passa; sem referências a campos removidos no JS.</done>
</task>

<task type="auto">
  <name>Task 3: Navbar/footer no skin maker</name>
  <files>apps/core/templates/core/partials/navbar.html, apps/core/templates/core/partials/footer.html, static/css/theme.css</files>
  <action>
    navbar.html: trocar a marca antiga (svg #i-l3d-mark + "<b>L3D</b> Labz") pelo markup que o CSS espera:
      <span class="brand-badge"><img src="{% static 'img/logo.png' %}" alt=""></span>
      <span class="brand-word">L3D <span class="brand-labz">Labz</span></span>
    (manter o <a class="brand" ...> e o aria-label). Não tocar na nav nem em header-actions.
    footer.html: na 1ª coluna do .footer-grid, trocar o bloco antigo por .footer-brand-block:
      <a href="{% url 'core:home' %}" class="brand footer-brand"><span class="brand-badge"><img src="{% static 'img/logo.png' %}" alt=""></span></a>
      <div class="footer-brand-block"><span class="mascot-name">L3D <b>Labz</b></span><p class="mascot-sub">Peças impressas em 3D com capricho de maker: action figures, réplicas, utensílios e gadgets — produzidos sob demanda, do seu jeito.</p></div>
    (confira o markup exato esperado pelo CSS antes de escrever; preservar a NOTA da linha ~1695 que mantém o mascot-name uniforme). Não alterar as outras 3 colunas nem o footer-bottom.
    theme.css: adicionar regra SÓ se faltar para o footer receber o skin maker (borda/sombra dura coerente com o resto do site) — no fim do arquivo, vencendo light/dark. Não quebrar tema claro/escuro nem links existentes.
  </action>
  <verify>
    <automated>cd C:/dev/l3d-labz-site && python manage.py check && grep -c "brand-badge\|brand-labz" apps/core/templates/core/partials/navbar.html && grep -c "footer-brand-block\|mascot-name" apps/core/templates/core/partials/footer.html</automated>
  </verify>
  <done>navbar e footer usam brand-badge/brand-labz e footer-brand-block/mascot-name; manage.py check passa; nenhum link existente removido.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Validação visual por screenshot (Chrome headless / Playwright+SwiftShader) — regra do projeto: não cantar "pronto" de UI sem screenshot real. Capturar a calculadora pública (/calculadora/), a navbar e o footer nos DOIS temas (claro e escuro), comparando contra image.png.</what-built>
  <how-to-verify>
    1. Subir o server local: `python manage.py runserver` (ou usar o ambiente de validação headless da memória "verificar-ui-no-browser").
    2. Abrir http://127.0.0.1:8000/calculadora/ e tirar screenshot em tema ESCURO (default) e tema CLARO (toggle de tema). Conferir contra image.png: 3 cards (Filamento / Energia e Tempo / Opcionais), chips de potência, chips de bandeira, chips de margem, botões "Puxar preço do site" e "Restaurar preço automático", botão largo "Calcular Custo" + "Limpar", e o painel de resultado sem depreciação/falha.
    3. Interagir: clicar um chip de potência (preenche W), um chip de bandeira (preenche kWh), "Puxar preço do site" (preenche R$/kg do material), e verificar que o preço de venda recalcula. Conferir o exemplo do mockup (peso 130g, preço 120, 200W, 6h, kWh 1,00, mão de obra 20, margem 100% => preço de venda R$ 73,60).
    4. Screenshot da navbar (logo em badge + "L3D Labz" com Labz verde) e do footer (marca + colunas) nos dois temas.
    5. Confirmar que tema claro e escuro não estão quebrados em nenhuma das telas.
  </how-to-verify>
  <resume-signal>Digite "aprovado" ou descreva os ajustes visuais necessários (itero até bater com o mockup).</resume-signal>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| visitante → calculadora pública | inputs numéricos não confiáveis no client (só preview; sem escrita no banco) |
| staff → orçamento/PDF | dados do cliente persistidos; PDF público por token |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-mrl-01 | Information disclosure | PDF/orçamento público | mitigate | manter contrato: pdf.py e OrcamentoService só recebem os 7 campos públicos; nenhum custo interno (custos_fixos, mão de obra, margem) entra no banco/PDF — inalterado por este plano |
| T-mrl-02 | Tampering | inputs da calculadora | accept | cálculo é só preview client-side; orçamento formal é recomputado server-side via PricingService (fonte única) |
| T-mrl-SC | Tampering | npm/pip/cargo installs | accept | sem novas dependências (web component/vanilla; reportlab já presente) |
</threat_model>

<verification>
- `python manage.py check` passa.
- PricingService enxuto retorna 6 chaves e bate o exemplo do mockup (preço 73,60).
- calculator.js sem campos mortos (depreciação/falha) e com valor_kwh/custos_fixos.
- publica.html com 3 cards, chips e botões do mockup; sem depreciação/falha no breakdown.
- navbar/footer com markup do skin maker; temas claro/escuro intactos.
- Screenshot real (claro + escuro) aprovado contra image.png.
</verification>

<success_criteria>
- Calculadora pública idêntica ao mockup (3 cards, chips, botões de preço, Calcular/Limpar), com a fórmula enxuta recalculando em tempo real.
- Backend (presets/forms/service) e JS espelhados na fórmula enxuta; fluxo staff/orçamento/PDF funcionando.
- Navbar e footer no skin maker (brand-badge + brand-labz; footer-brand-block) nos dois temas.
- Validação visual por screenshot aprovada.
</success_criteria>

<output>
Create `.planning/quick/260617-mrl-calc-mockup-navbar-footer/260617-mrl-SUMMARY.md` when done.
</output>
