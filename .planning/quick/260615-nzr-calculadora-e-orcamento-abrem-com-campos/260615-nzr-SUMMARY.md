---
quick_id: 260615-nzr
status: complete
date: 2026-06-15
commits: [2353c73, 0f6e756]
---

# Quick 260615-nzr — Calculadora e orçamento com campos vazios

## Objetivo
Calculadora pública (`/calculadora/`) e formulário de orçamento (`/calculadora/orcamento/`) devem abrir com os campos numéricos **vazios**, pro usuário preencher do zero.

## O que foi feito

### `apps/calculator/forms.py` (commit 2353c73)
- Removidos os `initial=` dos 10 `FloatField` numéricos do `CalcForm`: `peso_g`, `preco_kg`, `potencia_w`, `valor_maquina`, `vida_util_h`, `tempo_h`, `tarifa_base`, `custo_maoobra`, `taxa_falha_pct`, `margem_pct`. `min_value`/`max_value`/`help_text` preservados.
- `OrcamentoForm` herda de `CalcForm` → pega o comportamento automaticamente.
- **Preservados** (não zerados): selects `impressora`/`filamento` (`initial="manual"`), `bandeira` (`initial=BANDEIRA_VIGENTE_DEFAULT`) e `OrcamentoForm.quantidade` (`initial=1`).
- Removido import morto `CustoDefaults`/`_DEF` que só servia aos `initial`.

### `static/js/calculator.js` (commit 0f6e756)
- Fallbacks de `num(id, X)` em `calcular()` e `atualizarTarifaEfetiva()` trocados de valores não-zero (50/120/110/4/0.95/2000/2000/10/10/150) para **`0`** — com campos vazios o painel mostra **R$ 0,00** em vez de um preço fantasma calculado sobre defaults.
- Guarda `if (isNaN(n)) n = 0;` em `brl()` — nunca renderiza "R$ NaN".
- Presets (auto-preenchimento ao escolher impressora/filamento) e permalink intactos.

## Templates
Nenhuma edição necessária: `publica.html` usa `value="{{ form.X.field.initial|unlocalize }}"` (vira `value=""` sem initial) e `orcamento.html` renderiza via `field.html` (widget vazio). Nenhum `json_script` pré-popula campos numéricos.

## ⚠️ Verificação humana pendente (regra do Luix: UI não se canta "pronto" sem navegador real)
Após deploy em prod (`l3dlabz.com.br`) ou local (`localhost:8000`):
1. **`/calculadora/`** — todos os campos numéricos abrem **vazios**; o painel de preço mostra **R$ 0,00** (não um valor calculado, não "R$ NaN").
2. Escolher um preset de impressora/filamento ainda **auto-preenche** os campos correspondentes.
3. Preencher peso + tempo + preço → o preview recalcula normalmente.
4. **`/calculadora/orcamento/`** (logado como staff) — mesmos campos vazios; preencher tudo + dados do cliente → POST gera o **PDF** de download.
