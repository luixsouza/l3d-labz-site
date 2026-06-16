---
phase: quick-260616-m6a
plan: "01"
subsystem: templates, catalog-commands
tags: [rebrand, whatsapp-cleanup, instagram, management-command]
dependency_graph:
  requires: []
  provides: [corrigir_contato_descricoes]
  affects: [home, about, footer, static_page, calculadora-publica, importadores]
tech_stack:
  added: []
  patterns: [management-command-pattern, regex-idempotent-rewrite]
key_files:
  created:
    - apps/catalog/management/commands/corrigir_contato_descricoes.py
  modified:
    - apps/core/templates/core/home.html
    - apps/core/templates/core/about.html
    - apps/core/templates/core/partials/footer.html
    - apps/core/templates/core/static_page.html
    - apps/calculator/templates/calculator/publica.html
    - apps/catalog/management/commands/importar_makerworld.py
    - apps/catalog/management/commands/importar_copa.py
    - apps/catalog/management/commands/seed_makerworld.py
    - apps/catalog/mappers.py
decisions:
  - "Canal de contato consolidado: apenas Instagram @l3d_labz via SITE.instagram; sem WhatsApp/telefone"
  - "Frase canônica em prod: 'Orçamento e prazo pelo Instagram @l3d_labz.'"
metrics:
  duration: 12
  completed_date: "2026-06-16"
---

# Phase quick-260616-m6a Plan 01: Varredura WhatsApp -> Instagram

**One-liner:** Substituição completa de WhatsApp/wa.me por Instagram @l3d_labz nos templates, importadores e mapper; comando `corrigir_contato_descricoes` idempotente para corrigir descrições já no Postgres de prod.

## What Was Built

### Task 1 — Templates (5 arquivos)

Todas as menções de WhatsApp e links `wa.me` foram substituídas por Instagram:

- **home.html**: bloco "Precisa de ajuda?" — "WhatsApp" -> "Instagram" (texto puro)
- **about.html**: (4 ocorrências)
  - Hero CTA ghost: `wa.me` -> `{{ SITE.instagram }}`, `#i-whats` -> `#i-instagram`, adicionados `target="_blank" rel="noopener"`
  - Bloco "Precisa de ajuda?": texto "WhatsApp" -> "Instagram"
  - h2 contato: "Chama no WhatsApp" -> "Chama no Instagram"
  - CTA contato: `wa.me` -> `{{ SITE.instagram }}`, `#i-whats` -> `#i-instagram`, rotulo "WhatsApp" -> "Instagram"
- **footer.html**: link "Fale conosco" `wa.me` -> `{{ SITE.instagram }}`
- **static_page.html**: secoes privacidade (5) e termos (6) — `wa.me` -> `{{ SITE.instagram }}`, copy "Fale conosco pelo WhatsApp" -> "Fale com a gente no Instagram"
- **publica.html**: removido numero fake `5511999999999` e parametro `?text=` (especifico de WhatsApp); href -> `{{ SITE.instagram }}`; comentario atualizado

### Task 2 — Importadores e mapper (4 arquivos)

Frases de contato nas descricoes geradas por import:

- **importar_makerworld.py**: "Orcamento e prazo pelo WhatsApp." -> "Orcamento e prazo pelo Instagram @l3d_labz."
- **importar_copa.py**: idem (variante concatenada)
- **seed_makerworld.py**: "preco e prazo combinados no WhatsApp." -> "preco e prazo combinados no Instagram @l3d_labz."
- **mappers.py**: comentario `(orcamento no WhatsApp)` -> `(orcamento no Instagram)`

### Task 3 — Comando `corrigir_contato_descricoes` (1 arquivo novo)

Comando de management idempotente para reescrever `Product.description` no banco de prod:

- Filtra `Product.objects.filter(description__icontains="whatsapp")` (lote eficiente)
- Aplica 3 padroes regex case-insensitive em ordem (mais especifico primeiro) + fallback generico:
  1. `[Oo]rcamento e prazo pelo WhatsApp.` -> frase canonica
  2. `[Pp]reco e prazo combinados no WhatsApp.` -> frase canonica
  3. `\bWhatsApp\b` (avulso) -> `Instagram @l3d_labz`
- Frase canonica: `"Orcamento e prazo pelo Instagram @l3d_labz."`
- Flags: `--dry-run` (mostra antes/depois, nao salva) e `--limite N` (processa no max N produtos)
- Escrita via `p.save(update_fields=["description"])` — nunca em dry-run
- Saida: slug + trecho antes/depois por produto + resumo (N alterados / N ja-ok / N total)
- Idempotente: 2a execucao encontra 0 produtos no filtro icontains

## Verification Results

**`manage.py check`:** 0 issues.

**Grep final:**
```
grep -riE "whatsapp|wa\.me" apps/
```
Retorna APENAS linhas dentro de `corrigir_contato_descricoes.py` (strings de input do regex de correcao) — conforme esperado e aceitavel pelo plano.

**Teste local do comando (SQLite dev com produto de teste):**

```
# dry-run:
[test-produto-whatsapp]
  antes : 'Produto Teste impresso em 3D pela L3D Labz. Orcamento e prazo pelo WhatsApp.'
  depois: 'Produto Teste impresso em 3D pela L3D Labz. Orcamento e prazo pelo Instagram @l3d_labz.'
dry-run concluido — 1 seriam alterados / 0 ja-ok / 1 total

# run real: 1 alterado / 0 ja-ok / 1 total
# 2a execucao: 0 alterados / 0 ja-ok / 0 total (idempotencia confirmada)
```

## Runbook — corrigir descricoes no SERVER (Postgres de prod)

As descricoes de ~669 produtos importados pelo MakerWorld (via `importar_makerworld` e `seed_makerworld`) ainda citam "WhatsApp". Rodar este comando no server para corrigir:

**Passo 1 — dry-run (obrigatorio primeiro)**

```bash
# Via Docker (deploy atual):
docker exec -it l3d-web python manage.py corrigir_contato_descricoes --dry-run 2>&1 | head -100
# Confirmar que as substituicoes fazem sentido (antes/depois)
```

**Passo 2 — run de verdade**

```bash
docker exec -it l3d-web python manage.py corrigir_contato_descricoes
# Saida esperada: N alterados / 0 ja-ok / N total
```

**Passo 3 — verificar idempotencia**

```bash
docker exec -it l3d-web python manage.py corrigir_contato_descricoes
# Saida esperada: 0 alterados / 0 ja-ok / 0 total
```

## Deviations from Plan

None — plano executado exatamente como escrito.

## Known Stubs

None.

## Self-Check: PASSED

- [x] `apps/catalog/management/commands/corrigir_contato_descricoes.py` — criado e verificado
- [x] `apps/core/templates/core/about.html` — contem `{{ SITE.instagram }}` (4 ocorrencias corrigidas)
- [x] Commits b3dc752, 7ee3c96, cc78571 — existem no git log
- [x] `manage.py check` — 0 issues
- [x] Grep final limpo (exceto strings de input no comando de correcao)
