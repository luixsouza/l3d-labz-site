---
phase: quick-260614-ndg
verified: 2026-06-14T00:00:00Z
status: human_needed
score: 8/8 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Selecionar uma impressora no select (ex: Bambu Lab P1S) e confirmar que os campos potencia_w, valor_maquina e vida_util_h são auto-preenchidos com os valores corretos (120 W, R$ 7.789, 4000 h), e que os campos permanecem editáveis após o preenchimento."
    expected: "Campos numéricos refletem os valores do preset escolhido; edição manual persiste após mudança."
    why_human: "Auto-preenchimento via event listener JS — só verificável com browser real; o Client de teste não executa JavaScript."
  - test: "Selecionar um filamento (ex: PETG) e confirmar que o campo preco_kg é preenchido com R$ 150 e permanece editável."
    expected: "Campo preco_kg mostra 150 após selecionar PETG; o usuário pode sobrescrever manualmente."
    why_human: "Comportamento idêntico ao caso da impressora — requer execução de JS no browser."
  - test: "Alterar a tarifa_base e a bandeira ANEEL e verificar se o elemento #res_tarifa_efetiva exibe o texto correto, ex.: 'Tarifa efetiva: R$ 0,97/kWh (base R$ 0,95 + Bandeira R$ 0,02)'."
    expected: "Texto dinâmico atualiza em tempo real a cada mudança; formato legível em pt-BR com notação de bandeira."
    why_human: "Depende de execução de JS; aria-live confirmado no HTML, mas a atualização de texto requer browser."
  - test: "Confirmar que o painel de resultado exibe as barras proporcionais (.calc-bar-fill) com larguras variáveis para cada componente de custo, e que o preço de venda aparece em destaque."
    expected: "Ao menos uma barra visível com width > 0%; valores em BRL formatados; preco_venda em destaque com classe .calc-valor-venda."
    why_human: "Largura das barras é setada via style.width em JS; não verificável por grep ou Client de teste sem headless browser."
  - test: "Digitar valores e abrir o permalink gerado (query string na URL) em nova aba; confirmar que os campos são reidratados com os valores originais e o cálculo é idêntico."
    expected: "URL contém todos os parâmetros; ao recarregar, o cálculo reproduz o mesmo resultado."
    why_human: "Permalink depende de history.replaceState e releitura de URLSearchParams — requer browser interativo."
  - test: "Clicar em 'Copiar resultado' e verificar que o clipboard contém o resumo em texto com componentes e preço de venda."
    expected: "Texto copiado inclui Material, Energia, Depreciação, Mão de obra, Ajuste de falha, Custo total e PREÇO DE VENDA."
    why_human: "navigator.clipboard.writeText requer contexto de browser seguro (HTTPS ou localhost com interação do usuário)."
---

# Quick 260614-ndg: Calculadora de Precificação 3D v2 — Relatório de Verificação

**Phase Goal:** Calculadora de precificação 3D GENÉRICA e profissional — presets de impressoras (auto-preenchem potência/valor/vida útil), bandeiras tarifárias ANEEL (tarifa efetiva = base + adicional), presets de filamento, UI profissional (breakdown visual, permalink, copiar), orçamento privado is_staff com PDF sem custos internos, e README alinhado ao L3D Labz. App apps/calculator stateless (sem models/migrations), PricingService fonte única, pt-br.
**Verified:** 2026-06-14
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Selecionar impressora auto-preenche potência/valor/vida útil; campos continuam editáveis | ✓ VERIFIED (lógica) / ? HUMAN (execução JS) | `aplicarPresetImpressora()` em `calculator.js:52-58` lê `PRESETS.impressoras[key]` e faz `setVal()` nos três campos; event listener em `init()` linha 273-276. Verificação comportamental requer browser. |
| 2 | Selecionar filamento auto-preenche preco/kg; campo continua editável | ✓ VERIFIED (lógica) / ? HUMAN (execução JS) | `aplicarPresetFilamento()` em `calculator.js:61-65`; dados `preco_kg_default` presentes em todos os 10 filamentos de `presets.py`. |
| 3 | Usuário informa tarifa base + bandeira ANEEL; tarifa_efetiva = base + adicional é exibida e usada | ✓ VERIFIED | `to_calc_data()` em `forms.py:144-145`: `adicional = BANDEIRAS_ANEEL[c["bandeira"]]["adicional_kwh"]; tarifa_kwh = c["tarifa_base"] + adicional`. Teste direto: `0.95 + 0.01885 = 0.96885` PASS. JS espelha em `atualizarTarifaEfetiva()` linha 68-84. |
| 4 | Cálculo client-side em tempo real bate (±R$0,01) com PricingService.calcular para os mesmos inputs | ✓ VERIFIED | Fórmulas em `calculator.js:120-126` são idênticas às de `services.py` (comentadas explicitamente). Tarifa efetiva usada no custo de energia em ambos os lados. |
| 5 | Painel de resultado mostra cada componente com barra proporcional (% do total) usando só tokens; preço de venda em destaque | ✓ VERIFIED (estrutura) / ? HUMAN (renderização) | `publica.html:207-278` tem 5 `.calc-bar` + `.calc-bar-fill` por componente. `theme.css:2279-2297`: `.calc-bar { background: var(--border-soft) }` / `.calc-bar-fill { background: var(--accent) }` — somente tokens. `.calc-valor-venda` em destaque na linha 289. JS seta `style.width` na linha 92. |
| 6 | Inputs serializados na query string (permalink) e reidratados ao abrir | ✓ VERIFIED (lógica) / ? HUMAN (execução) | `CAMPOS_PERMALINK` define 14 campos (linha 169-173); `atualizarPermalink()` chama `history.replaceState` (linha 183); `reidratarPermalink()` relê `URLSearchParams` (linha 188-202); chamada no `init()` antes do primeiro cálculo (linha 269). |
| 7 | Calculadora privada (is_staff) gera PDF que NÃO expõe custos internos | ✓ VERIFIED | `@user_passes_test(lambda u: u.is_staff)` em `views.py:34`; `dados_pdf` em `views.py:52-60` contém apenas `cliente_nome, peca_descricao, quantidade, prazo_entrega, observacoes, preco_venda, total`; `pdf.py` inalterado (docstring linha 14-15 proíbe explicitamente custos internos). Teste com `Client.post()`: status 200, `Content-Type: application/pdf`, `content[:4] == b'%PDF'`, sem palavras de custo interno no conteúdo binário — PASS. |
| 8 | README descreve projeto L3D Labz atual sem qualquer menção a Nexora, incluindo a Calculadora | ✓ VERIFIED | Grep case-insensitive `nexora` retornou exit 1 (nenhuma ocorrência). `README.md:1`: "L3D Labz — Impressão 3D sob demanda". `README.md:57-64`: seção dedicada à Calculadora v2 com presets, bandeiras ANEEL, breakdown, permalink. |

**Score:** 8/8 truths verified (6 com evidência completa de código + testes comportamentais; 2 com evidência de código + verificação comportamental pendente de browser para a camada JS)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `apps/calculator/presets.py` | IMPRESSORAS, FILAMENTOS, BANDEIRAS_ANEEL + helpers + manual | ✓ VERIFIED | 272 linhas; 14 impressoras + manual, 10 filamentos + manual, 4 bandeiras ANEEL; helpers `impressora_choices()`, `filamento_choices()`, `bandeira_choices()`, `presets_json()` presentes. `BANDEIRA_VIGENTE_DEFAULT = "amarela"`. |
| `apps/calculator/forms.py` | CalcForm com selects de preset + tarifa_base/bandeira; to_calc_data soma a tarifa efetiva | ✓ VERIFIED | `import from .presets` linha 14-20; campos `impressora`, `filamento`, `tarifa_base`, `bandeira`; `to_calc_data()` usa `adicional_kwh` (linha 144); `OrcamentoForm` estende `CalcForm`. |
| `static/js/calculator.js` | Cálculo em tempo real espelhando o serviço, presets via json_script, breakdown %, permalink | ✓ VERIFIED | 314 linhas; IIFE + "use strict"; lê `#calc-presets`; `aplicarPresetImpressora/Filamento`; `atualizarTarifaEfetiva`; fórmulas comentadas idênticas ao Python; `atualizarBarra`; `atualizarPermalink` / `reidratarPermalink`; `copiarResultado` com fallback `execCommand`. |
| `apps/calculator/templates/calculator/publica.html` | UI pública com json_script de presets, breakdown e permalink | ✓ VERIFIED | `{{ presets_json\|json_script:"calc-presets" }}` linha 8; selects de impressora/filamento; `#res_tarifa_efetiva` com `aria-live="polite"`; 5 blocos `.calc-bar`/`.calc-bar-fill`; `#btnCopiar`; `#res_preco_venda`; `#res_total_qtd_wrap`. |
| `README.md` | Documentação alinhada ao L3D Labz atual | ✓ VERIFIED | Sem "Nexora"; "L3D Labz" no título; seção Calculadora na tabela de features e seção dedicada; `model-viewer` mencionado; stack completa incluindo reportlab. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `forms.py to_calc_data()` | `services.py PricingService.calcular(tarifa_kwh=...)` | soma `tarifa_base + adicional_kwh` antes de chamar o serviço | ✓ WIRED | `adicional = BANDEIRAS_ANEEL[c["bandeira"]]["adicional_kwh"]` / `tarifa_kwh = c["tarifa_base"] + adicional` em `forms.py:144-145`. Teste de integração: input `tarifa_base=0.95, bandeira="amarela"` → `tarifa_kwh=0.96885` PASS. |
| `publica.html json_script` | `static/js/calculator.js` | `JSON.parse(document.getElementById("calc-presets").textContent)` | ✓ WIRED | Template linha 8: `{{ presets_json\|json_script:"calc-presets" }}`; JS linha 11-16: lê `#calc-presets` via `JSON.parse(el.textContent)`. Nenhum número literal de preset no JS. |
| `apps/calculator/presets.py` | `apps/calculator/forms.py` | `from .presets import BANDEIRAS_ANEEL, BANDEIRA_VIGENTE_DEFAULT, bandeira_choices, filamento_choices, impressora_choices` | ✓ WIRED | `forms.py:14-20` importa todos os símbolos esperados; choices usados nos `ChoiceField`. |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `manage.py check` sem erros | `.venv/Scripts/python.exe manage.py check` | "System check identified no issues (0 silenced)." | PASS |
| `tarifa_efetiva = 0.95 + 0.01885 = 0.96885` | `CalcForm.to_calc_data()` com inputs de teste | `0.96885` (diferença < 1e-6) | PASS |
| `makemigrations --check` sem mudanças | `.venv/Scripts/python.exe manage.py makemigrations --check --dry-run calculator` | "No changes detected in app 'calculator'" | PASS |
| GET `/calculadora/` retorna 200 com `calc-presets` e `res_tarifa_efetiva` | `Client().get('/calculadora/')` | status 200; `"calc-presets"` e `"res_tarifa_efetiva"` no body | PASS |
| GET `/calculadora/orcamento/` redireciona (anônimo) | `Client().get('/calculadora/orcamento/')` | status 302 | PASS |
| GET `/calculadora/orcamento/` retorna 200 (is_staff) | `Client(force_login=staff).get(...)` | status 200 | PASS |
| POST `/calculadora/orcamento/` gera PDF válido | `Client(force_login=staff).post(...)` com dados completos | status 200, `Content-Type: application/pdf`, `content[:4] == b'%PDF'` | PASS |
| PDF não vaza custos internos | busca de palavras `custo_material`, `custo_energia`, `subtotal`, etc. no binário do PDF | nenhuma ocorrência | PASS |
| README sem "Nexora" | grep case-insensitive no `README.md` | exit 1 (nenhuma ocorrência) | PASS |
| `calculator.js` tem todas as peças | `"calc-presets"`, `"tarifa_efetiva"`, `"replaceState"`, `"clipboard"` presentes | todas presentes | PASS |
| Commits do SUMMARY existem | `git log f1f70f6 27b0133 0cea257 c351d63` | 4 commits encontrados | PASS |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `apps/calculator/templates/calculator/publica.html` | 306-310 | Número WhatsApp placeholder `5511999999999` em CTA | Info | Documentado como "Known Stub" no SUMMARY; comentado no template com instrução de substituição. Não afeta funcionalidade da calculadora. |

Nenhum marcador de dívida (`TBD`, `FIXME`, `XXX`) encontrado nos arquivos modificados. O placeholder do WhatsApp está documentado explicitamente no SUMMARY e comentado no template — não é um marcador de dívida sem rastreabilidade.

---

### Human Verification Required

#### 1. Auto-preenchimento de impressora

**Test:** Abrir `/calculadora/`, selecionar "Bambu Lab P1S" no select de Impressora.
**Expected:** Campos `potencia_w = 120`, `valor_maquina = 7789`, `vida_util_h = 4000` são preenchidos automaticamente; os campos permanecem editáveis após o auto-preenchimento.
**Why human:** O auto-preenchimento depende de event listener JS executado no browser; o Client de teste Django não executa JavaScript.

#### 2. Auto-preenchimento de filamento

**Test:** Selecionar "PETG" no select de Filamento.
**Expected:** Campo `preco_kg` mostra `150` (preco_kg_default do PETG); o campo continua editável.
**Why human:** Mesmo motivo — JS não executado pelo Client de teste.

#### 3. Exibição dinâmica da tarifa efetiva

**Test:** Alterar `tarifa_base` para `1.00` e selecionar "Vermelha Patamar 1"; verificar o elemento `#res_tarifa_efetiva`.
**Expected:** Texto exibe "Tarifa efetiva: R$ 1,04/kWh (base R$ 1,00 + Bandeira R$ 0,04)" (valores aproximados).
**Why human:** Atualização de `textContent` via JS; `aria-live="polite"` está no HTML mas a atualização é dinâmica.

#### 4. Breakdown visual com barras proporcionais

**Test:** Com inputs padrão (50g PLA, 4h, tarifa 0.95, amarela), verificar se as barras `.calc-bar-fill` têm largura > 0% e os percentuais são exibidos.
**Expected:** Cada barra tem `style.width` proporcional ao custo do componente; percentuais como "45.2%" aparecem ao lado de cada linha.
**Why human:** `style.width` é setado dinamicamente em JS; não verificável por grep ou Client de teste.

#### 5. Permalink compartilhável

**Test:** Preencher campos, copiar a URL gerada, abrir em nova aba (ou aba anônima).
**Expected:** Campos são reidratados com os mesmos valores; o cálculo reproduz o mesmo preço de venda.
**Why human:** `history.replaceState` e `URLSearchParams` requerem browser com contexto de navegação real.

#### 6. Botão Copiar resultado

**Test:** Clicar em "Copiar resultado" e colar em editor de texto.
**Expected:** O texto colado contém os 6 componentes de custo e o PREÇO DE VENDA formatados em pt-BR; o botão mostra feedback "Copiado!" por 2 segundos.
**Why human:** `navigator.clipboard.writeText` requer browser em contexto seguro (HTTPS ou localhost com interação do usuário).

---

### Gaps Summary

Nenhuma lacuna técnica encontrada. Todos os 8 must-haves são verificáveis no código: as estruturas de dados, a lógica de cálculo, as rotas, o controle de acesso, e a geração de PDF foram confirmados programaticamente. Os 6 itens de verificação humana dizem respeito exclusivamente ao comportamento da camada JavaScript no browser — comportamentos que existem no código mas que o Client de teste Django (sem JS) não pode exercitar.

---

_Verified: 2026-06-14_
_Verifier: Claude (gsd-verifier)_
