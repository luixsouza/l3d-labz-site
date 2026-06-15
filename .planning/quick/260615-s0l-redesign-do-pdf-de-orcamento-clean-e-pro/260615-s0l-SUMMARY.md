---
quick_id: 260615-s0l
title: Redesign do PDF de orçamento — clean e profissional
status: complete
date: 2026-06-15
tags: [pdf, calculator, reportlab, branding]
key-files:
  modified:
    - apps/calculator/pdf.py
decisions:
  - Monograma L3D desenhado em canvas (sem logo.png) para evitar risco de marca
  - Layout letterhead com canvas hooks (onFirstPage/onLaterPages) no lugar de flowables de cabeçalho
  - Nº de orçamento determinístico ORC-YYYYMMDD-XXXX via hash MD5 do nome do cliente
  - Contatos/marca lidos de settings.SITE com fallbacks seguros
metrics:
  duration: "~5 min"
  completed: 2026-06-15
  tasks_completed: 1
  tasks_total: 1
  files_modified: 1
---

# Quick 260615-s0l — Redesign do PDF de orçamento (clean & profissional) Summary

Substituição completa de `apps/calculator/pdf.py` pelo layout clean/profissional com letterhead (monograma L3D em canvas + wordmark), card de dados 2x2, tabela de itens com header verde, caixa de total verde-claro e rodapé com contatos via `settings.SITE`.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Substituir apps/calculator/pdf.py pelo módulo redesenhado | 99a404b | apps/calculator/pdf.py |

## Verification

```
PDF OK 3135
```

Comando de verificação executado com sucesso: `b[:4] == b'%PDF'` e `len(b) > 2000` (3135 bytes).

## Deviations from Plan

None — plano executado exatamente como escrito. O arquivo temp já estava completamente validado; apenas porte verbatim + verificação.

## Known Stubs

None.

## Threat Flags

None. O módulo continua sem custos internos — apenas dados públicos do cliente conforme decisão D-03 / T-calc-02.

## Self-Check: PASSED

- apps/calculator/pdf.py: FOUND, modificado (177 ins, 195 del)
- Commit 99a404b: FOUND
- Verificação PDF: PASSED (3135 bytes, header %PDF presente)
