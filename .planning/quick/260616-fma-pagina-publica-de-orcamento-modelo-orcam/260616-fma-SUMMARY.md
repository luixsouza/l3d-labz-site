---
phase: quick-260616-fma
plan: "01"
subsystem: calculator
tags: [orcamento, persistencia, publico, pdf, token, seguranca]
dependency_graph:
  requires: [apps.core.models.TimeStampedModel, apps.core.layers, apps.core.formatting, apps.calculator.pdf.gerar_orcamento_pdf]
  provides: [Orcamento model, OrcamentoService.criar, OrcamentoQuery.by_token, OrcamentoMapper.to_public, /calculadora/orcamento/<token>/, /calculadora/orcamento/<token>/pdf/]
  affects: [apps/calculator/views.py, apps/calculator/urls.py, apps/calculator/admin.py]
tech_stack:
  added: []
  patterns: [TimeStampedModel inheritance, BaseService/@transaction.atomic, BaseQuery/ORM-only, BaseMapper/allowlist-explícita, UUID token público]
key_files:
  created:
    - apps/calculator/models.py
    - apps/calculator/migrations/__init__.py
    - apps/calculator/migrations/0001_initial.py
    - apps/calculator/queries.py
    - apps/calculator/templates/calculator/orcamento_publico.html
  modified:
    - apps/calculator/services.py
    - apps/calculator/mappers.py
    - apps/calculator/views.py
    - apps/calculator/urls.py
    - apps/calculator/admin.py
    - apps/calculator/templates/calculator/orcamento.html
decisions:
  - Orcamento persiste SOMENTE os 7 campos públicos — espelho da allowlist do pdf.py; nenhum campo de custo no schema
  - OrcamentoMapper._CAMPOS_PUBLICOS é allowlist explícita e documentada (defesa em profundidade além do model)
  - orcamento_pdf serve inline (não attachment) para o cliente ver no browser e baixar
  - Sem cache no OrcamentoQuery (dado individual/mutável, sem ganho de cache)
metrics:
  duration: ~20 min
  completed: 2026-06-16
  tasks: 3
  files: 11
---

# Phase quick-260616-fma Plan 01: Página Pública de Orçamento — Persistência + Link Compartilhável

**One-liner:** Orçamento persistido por token UUID com página pública read-only (HTML + PDF) que o cliente abre sem login — nenhum custo interno em nenhuma camada.

## Tasks Completed

| # | Task | Commit | Arquivos-chave |
|---|------|--------|---------------|
| 1 | Modelo Orcamento + migração + service/query/mapper | b86452e | models.py, 0001_initial.py, queries.py, services.py, mappers.py |
| 2 | Rotas públicas + views finas + staff POST persiste | 0ff68a1 | urls.py, views.py |
| 3 | Template público + card link staff + admin | 5b3edce | orcamento_publico.html, orcamento.html, admin.py |

## Verification Results

Todos os verify steps do plano passaram (executados automaticamente):

1. **makemigrations + migrate**: `No changes detected` / `No migrations to apply` — tabela Orcamento criada na primeira run (0001_initial.py). PASS.

2. **OrcamentoService.criar + OrcamentoMapper.to_public + OrcamentoQuery.by_token**:
   - `d['total_display'] == 'R$ 103,38'` — PASS
   - `'custo_material' not in d and 'margem_pct' not in d and 'subtotal' not in d` — PASS
   - `OrcamentoQuery.by_token(o.token).id == o.id` — PASS

3. **GET /calculadora/orcamento/<token>/ = 200** com dados corretos (nome, peça, total BRL), zero termos de custo interno no HTML. PASS.

4. **GET /calculadora/orcamento/<token>/pdf/ = 200**, `Content-Type: application/pdf`, primeiros bytes `%PDF`. PASS.

5. **Token inexistente = 404** (HTML e PDF). PASS.

6. **manage.py check**: `System check identified no issues (0 silenced)`. PASS.

7. **Templates carregam + admin registrado**: `templates+admin OK`. PASS.

## Deviations from Plan

Nenhum — plano executado exatamente como escrito.

## Known Stubs

Nenhum — todos os dados renderizados vêm do DB via OrcamentoMapper.to_public.

## Threat Surface Scan

Nenhuma surface nova não coberta pelo threat_model do plano:
- Rotas /orcamento/<token>/ e /pdf/ já mapeadas como T-fma-01 e T-fma-02
- Escrita coberta por T-fma-03 (gate is_staff mantido)

## Self-Check: PASSED

Arquivos criados/modificados verificados:
- apps/calculator/models.py — presente
- apps/calculator/migrations/0001_initial.py — presente
- apps/calculator/queries.py — presente
- apps/calculator/templates/calculator/orcamento_publico.html — presente (124 linhas)
- apps/calculator/admin.py — registra Orcamento (verificado via admin.site.is_registered)
- Commits b86452e, 0ff68a1, 5b3edce — presentes em git log
