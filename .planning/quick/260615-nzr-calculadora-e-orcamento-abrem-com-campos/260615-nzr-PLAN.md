---
phase: quick-260615-nzr
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - apps/calculator/forms.py
  - static/js/calculator.js
autonomous: false
requirements: [QUICK-260615-NZR]

must_haves:
  truths:
    - "A calculadora pública (/calculadora/) abre com TODOS os campos numéricos vazios"
    - "O formulário de orçamento (/calculadora/orcamento/) abre com os campos numéricos de custo vazios"
    - "Com campos vazios, o painel de resultados NÃO mostra 'NaN' nem 'R$ NaN' — mostra R$ 0,00"
    - "Os selects de preset (impressora, filamento) continuam em 'manual' por padrão"
    - "O select de bandeira ANEEL continua em 'amarela' (BANDEIRA_VIGENTE_DEFAULT) por padrão"
    - "Selecionar um preset de impressora/filamento ainda auto-preenche os campos numéricos correspondentes"
  artifacts:
    - path: "apps/calculator/forms.py"
      provides: "CalcForm sem initial= nos FloatField numéricos (OrcamentoForm herda)"
      contains: "class CalcForm"
    - path: "static/js/calculator.js"
      provides: "Cálculo client-side que trata campos vazios sem gerar NaN"
      contains: "function calcular"
  key_links:
    - from: "static/js/calculator.js"
      to: "campos vazios do form"
      via: "num(id, fallback) com fallback 0 + guarda anti-NaN no render"
      pattern: "function num"
---

<objective>
Fazer a calculadora pública e o formulário de orçamento abrirem com os campos numéricos VAZIOS por padrão, para o usuário preencher do zero — sem que o painel de resultados client-side exiba "NaN"/"R$ NaN" enquanto os campos estiverem em branco.

Purpose: O cliente/usuário deve digitar todos os valores do zero (peso, preço, potência, tempo etc.) em vez de partir de defaults pré-preenchidos que ele precisaria apagar.
Output: forms.py sem `initial=` nos campos numéricos do CalcForm; calculator.js tratando vazio/NaN para mostrar R$ 0,00.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@apps/calculator/forms.py
@static/js/calculator.js
@apps/calculator/templates/calculator/publica.html
@apps/calculator/templates/calculator/orcamento.html

<notes>
Investigação concluída — fatos confirmados que o executor DEVE usar (não re-explorar):

1. **forms.py é a fonte única dos defaults.** Campos numéricos do `CalcForm` com `initial=`:
   `peso_g` (50.0), `preco_kg` (120.0), `potencia_w` (_DEF.potencia_w), `valor_maquina`
   (_DEF.valor_maquina), `vida_util_h` (_DEF.vida_util_h), `tempo_h` (4.0), `tarifa_base`
   (0.95), `custo_maoobra` (10.0), `taxa_falha_pct` (_DEF.taxa_falha_pct), `margem_pct`
   (_DEF.margem_pct). `OrcamentoForm(CalcForm)` herda tudo automaticamente.

2. **MANTER (não mexer):**
   - `impressora` ChoiceField `initial="manual"` (UX preset)
   - `filamento` ChoiceField `initial="manual"` (UX preset)
   - `bandeira` ChoiceField `initial=BANDEIRA_VIGENTE_DEFAULT` ("amarela") — é select, não número
   - `OrcamentoForm.quantidade` IntegerField `initial=1` (não está no escopo de zerar)
   - O parâmetro `min_value=` de cada FloatField (validação server-side) — só remover `initial=`.

3. **Templates NÃO precisam de edição.**
   - `publica.html` usa `value="{{ form.X.field.initial|unlocalize }}"`. Sem `initial`,
     `field.initial` é `None` → `|unlocalize` de None → string vazia → `value=""`. Campo abre vazio. Confirmar visualmente mesmo assim.
   - `orcamento.html` usa `{% include "core/partials/field.html" with field=form.X %}`,
     que renderiza o widget Django (sem `initial` → input vazio).
   - O campo `quantidade_pub` em publica.html tem `value="1"` literal (hardcoded, não vem do
     form) — MANTER como está (quantidade não está no escopo).

4. **calculator.js — comportamento atual e o problema:**
   - `num(id, fallback)`: `parseFloat('')` → NaN → retorna `fallback`. HOJE os fallbacks são
     valores NÃO-zero hardcoded (50, 120, 110, 4, 0.95, 2000, 2000, 10, 10, 150). Resultado:
     com campos vazios, a calculadora AINDA calcula um preço usando esses fallbacks — o painel
     mostraria um preço "fantasma" em vez de R$ 0,00. Isso contraria o objetivo.
   - `atualizarTarifaEfetiva()` usa fallback `0.95` para `tarifa_base`.
   - `calcular()` lê todos os campos via `num(...)`, calcula e escreve via `escrever()`/`brl()`.
     `brl(NaN)` → "R$ NaN" se algum valor escapar como NaN.
</notes>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Remover initial= dos campos numéricos do CalcForm</name>
  <files>apps/calculator/forms.py</files>
  <action>
    No `CalcForm`, remover APENAS o argumento `initial=...` de cada um dos 10 FloatField numéricos:
    `peso_g`, `preco_kg`, `potencia_w`, `valor_maquina`, `vida_util_h`, `tempo_h`,
    `tarifa_base`, `custo_maoobra`, `taxa_falha_pct`, `margem_pct`. Manter `label=`,
    `min_value=`, `max_value=` e `help_text=` intactos em todos.

    NÃO tocar (manter exatamente como estão): os ChoiceField `impressora` (initial="manual"),
    `filamento` (initial="manual") e `bandeira` (initial=BANDEIRA_VIGENTE_DEFAULT). Em
    `OrcamentoForm`, NÃO tocar `quantidade` (initial=1) nem os campos de texto. `OrcamentoForm`
    herda de `CalcForm`, então o comportamento de campos vazios propaga sozinho.

    Manter o import `from .services import CustoDefaults` e a linha `_DEF = CustoDefaults()`
    se `_DEF` ainda for referenciado em algum lugar do arquivo após a edição; se `_DEF` deixar
    de ser usado em qualquer ponto, remover a linha `_DEF = CustoDefaults()` e o import de
    `CustoDefaults` para não deixar import morto (convenção: sem código morto). Verificar com grep
    antes de remover.
  </action>
  <verify>
    <automated>cd /c/dev/l3d-labz-site && python -c "import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev'); django.setup(); from apps.calculator.forms import CalcForm, OrcamentoForm; cf=CalcForm(); assert cf.fields['peso_g'].initial is None, 'peso_g ainda tem initial'; assert cf.fields['margem_pct'].initial is None, 'margem_pct ainda tem initial'; assert cf.fields['tarifa_base'].initial is None; assert cf.fields['impressora'].initial=='manual', 'impressora deve manter manual'; assert cf.fields['bandeira'].initial=='amarela', 'bandeira deve manter amarela'; of=OrcamentoForm(); assert of.fields['potencia_w'].initial is None, 'OrcamentoForm herdou initial'; assert of.fields['quantidade'].initial==1, 'quantidade deve manter 1'; print('OK')"</automated>
  </verify>
  <done>
    Todos os 10 FloatField numéricos do CalcForm têm `initial is None`; `impressora`/`filamento`
    seguem "manual"; `bandeira` segue "amarela"; `OrcamentoForm.quantidade` segue 1; sem import
    morto de CustoDefaults se _DEF não for mais usado.
  </done>
</task>

<task type="auto">
  <name>Task 2: Tratar campos vazios no calculator.js (sem NaN, mostra R$ 0,00)</name>
  <files>static/js/calculator.js</files>
  <action>
    Garantir que, com os campos numéricos vazios, o painel de resultados mostre R$ 0,00 em vez
    de NaN ou de um preço fantasma baseado em fallbacks não-zero.

    Mudanças:
    1. Em `num(id, fallback)`: manter a assinatura, mas mudar TODAS as chamadas dentro de
       `calcular()` e `atualizarTarifaEfetiva()` para passar `0` como fallback (em vez dos atuais
       50, 120, 110, 4, 0.95, 2000, 2000, 10, 10, 150). Assim campo vazio → 0, e o cálculo
       naturalmente resulta em 0,00 enquanto não houver valores.
    2. Manter a guarda existente de `custo_depreciacao` (`vida_util_h > 0 ? ... : 0`) — com
       vida_util_h=0 a divisão é evitada.
    3. Em `brl(valor)`: blindar contra NaN — se `Number(valor)` for NaN, formatar como 0 (ex.:
       tratar `var n = Number(valor); if (isNaN(n)) n = 0;` antes do `toLocaleString`). Isso
       garante que NENHUM caminho renderize "R$ NaN".
    4. `atualizarBarra` já trata `total > 0 ? ... : 0` — manter; com total 0 as barras ficam 0%.
    5. NÃO alterar o comportamento dos presets: `aplicarPresetImpressora`/`aplicarPresetFilamento`
       continuam preenchendo os campos via `setVal` quando o usuário escolhe um preset != manual.
    6. NÃO mexer no permalink nem na reidratação — eles já só setam valores quando presentes.

    Não inserir números literais de default no JS — o objetivo é exatamente que vazio signifique 0.
  </action>
  <verify>
    <automated>cd /c/dev/l3d-labz-site && node -e "const fs=require('fs');const s=fs.readFileSync('static/js/calculator.js','utf8'); if(/num\(\"id_peso_g\",\s*50\)/.test(s)) throw new Error('fallback nao-zero ainda em peso_g'); if(/num\(\"id_preco_kg\",\s*120\)/.test(s)) throw new Error('fallback nao-zero ainda em preco_kg'); if(!/isNaN\(n\)/.test(s) && !/isNaN\([^)]*\)\s*\)?\s*n\s*=\s*0/.test(s)) console.warn('confirme guarda NaN em brl manualmente'); console.log('OK fallbacks zerados');"</automated>
  </verify>
  <done>
    Todas as chamadas `num(...)` em `calcular()`/`atualizarTarifaEfetiva()` usam fallback 0;
    `brl()` nunca produz "R$ NaN"; presets e permalink intactos.
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
    forms.py sem initial nos campos numéricos do CalcForm/OrcamentoForm, e calculator.js
    tratando campos vazios (fallback 0 + guarda anti-NaN).
  </what-built>
  <how-to-verify>
    A regra do Luix: não cantar "pronto" de UI sem verificação real no navegador. O cálculo
    é DOM/JS, então um browser real é necessário.

    1. Rodar o servidor: `python manage.py runserver`
    2. Abrir http://localhost:8000/calculadora/ no navegador.
       - Conferir que TODOS os campos numéricos (peso, preço/kg, potência, valor da máquina,
         vida útil, tempo, tarifa base, mão de obra, taxa de falha, margem) aparecem VAZIOS.
       - Conferir que os selects "Modelo da impressora" e "Material" estão em "Outra / manual"
         e "Outro / manual"; e que a "Bandeira ANEEL" está em "Amarela".
       - Conferir que o painel de resultados à direita NÃO mostra "NaN"/"R$ NaN" — deve mostrar
         R$ 0,00 (ou —) nos valores enquanto tudo está vazio. A linha "Tarifa efetiva" não deve
         conter NaN.
       - Digitar alguns valores (ex.: peso 50, preço 120, tempo 4) e confirmar que o preço
         atualiza em tempo real sem erros.
       - Selecionar uma impressora do preset (ex.: Bambu Lab A1 Mini) e confirmar que potência/
         valor/vida útil são auto-preenchidos.
    3. Abrir http://localhost:8000/calculadora/orcamento/ (logado como staff).
       - Conferir que os campos numéricos de custo aparecem VAZIOS.
       - Conferir que "Quantidade" continua em 1.
    4. (Opcional) Preencher tudo no /orcamento/ e gerar o PDF para confirmar que o cálculo
       server-side ainda funciona.
  </how-to-verify>
  <resume-signal>Digite "aprovado" ou descreva os problemas encontrados (ex.: campo X ainda preenchido, NaN aparecendo, preset quebrou).</resume-signal>
</task>

</tasks>

<verification>
- CalcForm/OrcamentoForm: todos os campos numéricos com `initial is None`; selects de preset e bandeira preservados; quantidade=1.
- /calculadora/ abre com campos vazios e sem NaN no painel.
- /calculadora/orcamento/ abre com campos de custo vazios.
- Presets de impressora/filamento ainda auto-preenchem.
- Cálculo server-side do PDF de orçamento intacto.
</verification>

<success_criteria>
- Campos numéricos vazios por padrão em ambas as telas.
- Zero ocorrências de "NaN"/"R$ NaN" no painel de resultados com campos vazios.
- Selects (impressora/filamento/bandeira) e quantidade mantêm seus padrões.
- Nenhuma regressão no auto-preenchimento por preset nem no cálculo server-side.
</success_criteria>

<output>
Create `.planning/quick/260615-nzr-calculadora-e-orcamento-abrem-com-campos/260615-nzr-SUMMARY.md` when done
</output>
