---
phase: quick-260616-eii
plan: "01"
subsystem: apps/calculator
tags: [pdf, reportlab, qr-code, branding, orcamento]
dependency_graph:
  requires: [apps/calculator/pdf.py (260615-sf7 — PDF premium base)]
  provides: [PDF de orcamento com QR, CTA, politica de pagamento e selo grafico]
  affects: [apps/calculator/views.py (gerar_orcamento_pdf chamada inalterada)]
tech_stack:
  added: []
  patterns: [reportlab.graphics.barcode.qr (ja incluso no reportlab 4.5.1), Drawing como Flowable em celula de tabela platypus, colwidth-gap-pattern]
key_files:
  modified:
    - apps/calculator/pdf.py
decisions:
  - "QR code posicionado no bloco CTA (nao no rodape) — um QR so, sem poluicao visual"
  - "Selo L3D implementado como Drawing (Flowable) em sub-tabela, nao como _monograma (canvas) — mais robusto em platypus"
  - "Politica de pagamento inserida em negrito dentro do bloco CONDICOES existente (ordem: obs -> pagamento -> validade)"
  - "Gap badge->texto via colWidth (_SELO_LADO + 8pt) em vez de RIGHTPADDING — RIGHTPADDING comprime o Drawing abaixo do tamanho declarado no reportlab"
  - "_SUB_CW = _DESCR_CW - 2*_ITENS_PAD para descontar os paddings externos da tabela itens (10pt cada lado)"
metrics:
  duration: "~2h (tasks + ajuste pos-aprovacao)"
  completed: "2026-06-16"
  tasks_completed: 3
  files_modified: 1
---

# Quick 260616-eii: PDF de Orcamento Turbinado — QR Code + CTA + Pagamento + Selo L3D

**One-liner:** PDF de orcamento premium turbinado com QR Instagram, CTA "PARA APROVAR" pt-br, politica "sinal de 50%" em negrito e selo grafico "L3D" com 8pt de gap na tabela de itens — tudo via reportlab.graphics sem dependencia nova.

## O que foi entregue

4 melhorias no `apps/calculator/pdf.py`, todas dentro do modulo, reaproveitando paleta e helpers existentes:

| # | Melhoria | Implementacao |
|---|----------|---------------|
| 1 | **QR code Instagram** | Helper `_qr_drawing(url, lado)` usando `reportlab.graphics.barcode.qr.QrCodeWidget`; retorna `None` se `_IG_URL` vazio |
| 2 | **CTA "PARA APROVAR"** | Bloco com tabela 2 colunas [texto pt-br com @l3d_labz, QR 2.4cm] inserido entre resumo e condicoes; degrada para texto puro sem QR |
| 3 | **Politica de pagamento** | "Sinal de 50% para iniciar a producao, saldo na entrega." em negrito antes da validade de 7 dias no bloco CONDICOES; obs do cliente mantida no topo |
| 4 | **Selo L3D na tabela** | Helper `_selo_drawing(lado)` retorna `Drawing` com `Rect` arredondado verde + `String` "L3D" branca; celula DESCRICAO virou sub-tabela com gap de 8pt entre badge e texto |

## Commits

| Task | Commit | Descricao |
|------|--------|-----------|
| Task 1 | `0a35f33` | feat(quick-260616-eii): QR Instagram + CTA "Para aprovar" no PDF de orcamento |
| Task 2 | `9d4f035` | feat(quick-260616-eii): politica de pagamento 50% + selo L3D na tabela de itens |
| Task 3 (ajuste) | `b21f5c9` | fix(quick-260616-eii): respiro 8pt entre badge L3D e texto da descricao |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Overflow silencioso do Drawing do selo na sub-tabela**
- **Found during:** Task 3 (ajuste pos-aprovacao do checkpoint)
- **Issue:** O calculo original de `_TEXTO_CW = _DESCR_CW - _SELO_LADO - 0.2*cm` nao descontava os paddings externos da tabela `itens` (10pt left + 10pt right = 20pt totais). A sub-tabela tentava ocupar `_DESCR_CW` inteiro mas o espaco real disponivel era `_DESCR_CW - 20pt`. O reportlab truncava o Drawing silenciosamente — badge sumia na renderizacao visual mas o texto "L3D" aparecia no texto extraido do PDF.
- **Fix:** Introduzido `_SUB_CW = _DESCR_CW - 2 * _ITENS_PAD` como base real. Gap de 8pt incorporado no `colWidth` da coluna do badge (`_BADGE_COL = _SELO_LADO + _GAP_BADGE`) em vez de `RIGHTPADDING`: `RIGHTPADDING` em celula de sub-tabela comprime o conteudo da coluna sem alterar o `colWidth` declarado, fazendo o Drawing ficar menor que seu tamanho nominal e ser clipado.
- **Files modified:** apps/calculator/pdf.py
- **Commit:** b21f5c9

## Verificacao

- PDF 1 (com obs, R$ 269,70): `%PDF`, >4KB — OK
- PDF 2 (sem obs, R$ 1.499,00): `%PDF`, >4KB — OK
- Badge "L3D" visivel com gap 8pt verificado via fitz clip 4x zoom (ambos os casos)
- Descricao longa (multi-linha): badge alinhado verticalmente, wrap correto
- Colunas QTD/PRECO UNIT./TOTAL alinhadas em ambos os exemplos
- Trava T-calc-02: docstring "PROIBIDO incluir" intacta, nenhum campo de custo novo
- Assinatura `gerar_orcamento_pdf(dados: dict) -> bytes` inalterada
- Zero dependencia nova no requirements.txt
- Aprovacao visual humana confirmada (checkpoint 260616-eii)

## Threat Surface Scan

Nenhuma superficie nova de seguranca introduzida. As 4 melhorias usam somente:
- Strings fixas de marca (`_IG_URL`, `_IG` — lidos de `settings.SITE` em modulo-load)
- Dados publicos do dict `dados` ja usados anteriormente
- Zero leitura de filesystem, zero HTTP request no modulo

Trava T-calc-02 preservada: docstring "PROIBIDO incluir" intacta.

## Self-Check: PASSED

- [x] apps/calculator/pdf.py modificado
- [x] Commits 0a35f33, 9d4f035, b21f5c9 existem no worktree
- [x] PDF gera bytes validos para casos com e sem observacoes
- [x] Badge "L3D" visivel com gap elegante (verificado via fitz 4x)
- [x] Sem campo de custo interno
