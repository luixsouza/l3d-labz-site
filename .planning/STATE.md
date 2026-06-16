---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
stopped_at: Completed 03-01-PLAN.md
last_updated: "2026-06-07T21:14:10.969Z"
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 10
  completed_plans: 10
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-05)

**Core value:** O cliente consegue visualizar o modelo 3D do produto de forma intuitiva num site bonito e minimalista com a marca L3D Labz.
**Current focus:** Phase 4 — Faça meu Lithophane

## Current Position

Phase: 5
Plan: Not started

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01 P01 | 2 | 2 tasks | 13 files |
| Phase 01 P02 | 2 | 2 tasks | 2 files |
| Phase 02 P01 | 1 | 2 tasks | 4 files |
| Phase 03-visualizador-3d-galeria P01 | 1 | 2 tasks | 2 files |
| Phase 03 P02 | 1 | 2 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Exibir 3D em GLB via `<model-viewer>` (web component, sem build) — casa com a stack vanilla.
- [Roadmap]: Sempre armazenar + oferecer download do STL (arquivo imprimível que o cliente quer).
- [Roadmap]: Rebrand via tokens CSS + dict `SITE` (baixo esforço, alto ROE), não reescrita.
- [Roadmap]: Estética light/clean minimalista como base.
- [Phase 01]: Default de tema mudou para light (data-theme=light) refletindo a estética minimalista; boot script ainda sobrescreve com a preferência salva.
- [Phase 01]: Símbolo #i-koala mantido em icons.html (não referenciado) para não quebrar referências esquecidas.
- [Phase 01]: .grad-text minimalista usa verde solido var(--accent) (sem gradiente/animacao); 5 azuis literais rgba(59,130,246) convertidos para verde.
- [Phase 02]: Validação de upload 3D por extensão (FileExtensionValidator: glb/gltf e stl); MIME/tamanho ficou deferido.
- [Phase 02]: Campos 3D expostos só em ProductMapper.to_detail; to_dict (card/listagem) inalterado.
- [Phase 03-visualizador-3d-galeria]: [Phase 03] AR incluído no model-viewer (ar/ar-modes/ar-scale): 2 atributos, AR Android grátis do GLB, no-op no desktop/iOS.
- [Phase 03-visualizador-3d-galeria]: [Phase 03] model-viewer fixado @4.3.1 via CDN ES module, carregado por página em extra_js gated por has_3d_model; sem nomodule.
- [Phase 03]: Galeria 'Modelos 3D' via with_3d (sem cache) → gallery → models_3d; cards linkam ao detalhe, sem viewer por card.

### Roadmap Evolution

- Phase 4 added: Faça meu Lithophane — editor de upload+ajuste 2D, geração 3D server-side (GLB+STL) com toggle de luz emissivo, e pedido de orçamento no carrinho. Design: docs/superpowers/specs/2026-06-07-faca-meu-lithophane-design.md
- Note: nexora rebrand L3dLabZ + papéis cliente/vendedor + app seller foi mesclado (cherry-pick) na branch merge/nexora-l3dlabz-rebrand antes desta fase.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues que afetam trabalho futuro — ver .planning/codebase/CONCERNS.md]

- [Phase 1] Wordmark do navbar é hand-split (`nex<b>ora</b>`) — não dá pra dirigir por `{{ SITE.name }}` sem mudar markup.
- [Phase 1] Chave localStorage `nexora-theme` deve mudar em DOIS arquivos atomicamente (`base.html` + `app.js`) ou a persistência do tema quebra.
- [Phase 2] Sem validação de upload (extensão/tamanho) no FileField — GLB/STL podem ser grandes; adicionar validators.
- [Phase 3] Serving de media em prod não está endurecido (WhiteNoise só serve static); arquivos 3D grandes precisam de estratégia (lazy/poster; CDN/object storage fica para depois).

## Quick Tasks Completed

| ID | Descrição | Data | Commits |
|----|-----------|------|---------|
| 260611-go4 | Corrigir 9 achados do UAT 2026-06-11 (mobile nav, rebrand L3D-, 404/500, home/sobre, viewer 3/4, fotos coloridas) | 2026-06-11 | b2b2339, 1f0fa96, efd5dc5, fbe51aa |
| 260611-mca | Importador MakerWorld (mesh3d.py compartilhado, fotos reais, dimensões do 3MF) + modal 3D no catálogo | 2026-06-11 | 2741089, cf5c837 |
| 260611-n3w | Catálogo sem 3D na UI + galeria de fotos em carrossel + tradução pt-br dos nomes no import | 2026-06-11 | 9822c50, 0ebcb88 |
| 260612-gf7 | Hero da home ligado ao PromotionService (promo hero dinâmica com fallback hardcoded) | 2026-06-12 | a31106d, 3dd7fb6 |
| 260614-lzm | Calculadora de precificação 3D: pública (vanilla JS, detalhamento completo + CTA) e privada is_staff (orçamento em PDF reportlab, sem custos internos) | 2026-06-14 | 253eb86, 436f4b6, 3b94df7 |
| 260614-ndg | Calculadora 3D v2 genérica: presets de 14 impressoras + 10 filamentos, bandeiras tarifárias ANEEL (tarifa efetiva), UI profissional (breakdown/permalink/copiar) e README reescrito. Verificada 8/8 must-haves | 2026-06-14 | f1f70f6, 27b0133, 0cea257, c351d63 |
| 260614-q6g | Redesign "Clean & Elegante" light-first (sketch 001 variante B): paleta light reconciliada (3 blocos divergentes), azul secundário, sombras difusas, moldura clara (header/footer/hero off-white) e hero 3D lado a lado. Hero virou VITRINE geek: modelo-vitrine astronauta auto-hospedado (`static/models/astronaut.glb`) via `HERO_3D_MODEL_URL`, com fallback p/ produto curado (`HERO_3D_PRODUCT_SLUG`); viewer polido (luz neutra, sombra suave, 3/4, poster, sem barra). Fix do split (`1fr !important` herdado do hero do Sobre atropelava). Deployado em prod e confirmado no navegador | 2026-06-14 | 0a9d35b, 8faed13, d64ff57, 289cd36, 4ca96fb |
| 260615-gfa | Catálogo limpo: cap de 3 fotos/produto no importador MakerWorld (1 principal + 2 extras, `MAX_EXTRAS`), comando `podar_galeria` (poda idempotente da galeria existente — dry-run/limit, mantém Product.image + 2 primeiras) e comando `gerar_descricoes` (Claude Vision `claude-opus-4-8` reescreve descrições pt-br únicas a partir da foto principal — dry-run/limit/model). `anthropic==0.109.1` no requirements. NADA executado contra prod — runbook de deploy no SUMMARY (rodar os 2 comandos NO SERVER com --dry-run antes) | 2026-06-15 | a224a8e, 4959a2f, 39e10a7 |
| 260615-nzr | Calculadora pública (`/calculadora/`) e orçamento (`/calculadora/orcamento/`) abrem com os 10 campos numéricos VAZIOS (removido `initial=` dos FloatField do `CalcForm`; `OrcamentoForm` herda). `calculator.js` com fallbacks `0` e `brl()` à prova de `NaN` (sem preço fantasma). Selects (impressora/filamento/bandeira) e quantidade=1 preservados. Verificação no navegador pendente. | 2026-06-15 | 2353c73, 0f6e756 |
| 260615-s0l | Redesign clean/profissional do `apps/calculator/pdf.py` (PDF de orçamento): letterhead com monograma "L3D" desenhado em canvas (escolhido vs logo.png Luigi), card 2×2 de dados, tabela de itens header verde, total em destaque (box verde-claro, total não quebra linha), rodapé com contatos do `settings.SITE`, nº `ORC-YYYYMMDD-XXXX`. Mantida a trava de segurança (só dados públicos) e a assinatura `gerar_orcamento_pdf`. Verificado render no contexto Django real (rasterizado p/ inspeção visual). | 2026-06-15 | 99a404b |
| 260615-sf7 | PDF de orçamento PREMIUM (evolução do s0l): header full-bleed com gradiente verde + monograma branco + pill do nº, marca d'água "L3D", blocos "Faturar para"/"Detalhes" (emissão/validade+7d/prazo), tabela de itens, resumo com Subtotal + card TOTAL verde-escuro (largura aguenta 6 dígitos sem quebrar), bloco "Condições & Observações", faixa de rodapé escura com contatos. Trava de segurança e assinatura preservadas. Verificado visualmente no Django real (rasterizado, vários casos). | 2026-06-15 | c04f3b2 |
| 260616-e8v | 3D na página do produto: `<model-viewer>` embutido no detalhe com toggle Fotos↔3D (progressive enhancement, painel Fotos `active` por padrão p/ no-JS), `camera-controls`/`auto-rotate`/`ar` (AR mobile "Ver no seu espaço"), `reveal="interaction"`+poster (GLB só baixa ao abrir a aba — atende constraint de performance), botão "Baixar STL" condicional. Tudo gated por `product.has_3d`/`has_stl` (produtos sem 3D mantêm layout atual). Camada de dados já existia no `ProductMapper.to_detail`; tocou só template + `app.js` + `theme.css` + ícone `#i-download`. **VERIFICADO em navegador real (Playwright/WebGL renderiza)** — e na verificação 2 bugs foram corrigidos (c7a67fd): (1) `reveal="interaction"` é inválido na v4 → o modelo NUNCA carregava; trocado por `reveal="manual"`+`loading="lazy"`+`dismissPoster()` ao abrir a aba (GLB só baixa sob demanda, confirmado); (2) painel Fotos nascia sem `.active` → foto escondida no load (e sumiria em produto sem 3D); adicionado `.active`. Confirmado: lazy-load OK, modelo renderiza, toggle e STL OK. | 2026-06-16 | 9839146, 53ce2d4, c7a67fd |
| 260616-gat | Specs de impressão no catálogo (Parte A de "loja mais rica"): campos `filament_grams` (PositiveInteger, 0=desconhecido) e `color_count` (PositiveSmallInteger, default 1) no `Product` + migração `0007` + expostos no `ProductMapper.to_dict` (`filament_grams`, `color_count`, `filament_display` ex "120 g"). Comando `extrair_specs_3mf` (espelha `importar_makerworld`: `--base/--only/--limite/--dry-run`, idempotente por slug, parser defensivo zipfile+ElementTree do `Metadata/slice_info.config` → soma `used_g`, conta `color` distintos; fallback `project_settings.config`; degradação graciosa). Verificado com 3MF fake (grams=32, colors=2). ⚠️ **RODA NO SERVER** (3MF lá): `--dry-run` primeiro. Tags exatas parseadas documentadas no SUMMARY p/ validar contra 3MF real. | 2026-06-16 | 911d282, bd6c4e8 |
| 260616-fma | Página pública de orçamento: novo modelo `Orcamento` na app calculator (`TimeStampedModel`, token UUID4, **só os 7 campos públicos** — espelho da trava do PDF, Decimal pra dinheiro) + migração `0001_initial`. Camadas: `OrcamentoService.criar` (`@transaction.atomic`, único write), `OrcamentoQuery.by_token`, `OrcamentoMapper.to_public` (Model→dict, `format_brl`). Rotas públicas sem auth: `/calculadora/orcamento/<uuid:token>/` (HTML read-only elegante c/ identidade L3D, total destaque, pagamento 50/50, CTA Instagram, botão Baixar PDF) e `/.../pdf/` (reusa `gerar_orcamento_pdf` dos dados persistidos). Staff POST agora **persiste + mostra link copiável** (não baixa mais o PDF direto). Admin registrado. **VERIFICADO no browser**: HTML 200 c/ dados, PDF route `%PDF`, token inválido 404, allowlist negativa (nenhum custo interno no HTML). ⚠️ **DEPLOY: rodar `migrate` no server**. | 2026-06-16 | b86452e, 0ff68a1, 5b3edce |
| 260616-f2c | Conversão leve: (A) **FAB de Instagram** flutuante global (canto inf. direito, `base.html` gated por `SITE.instagram`, gradiente accent, offset seguro no mobile) — verificado por screenshot headless (Playwright) desktop+mobile; (B) **AR no editor de litofane** (`ar`/`ar-modes` + botão "Ver no seu espaço" injetados no `<model-viewer>` dinâmico do `lithophane-editor.js`, reusando `.detail-ar-btn` do e8v). ⚠️ Os commits da branch do worktree foram **descartados** (o "fix" da duplicata removeu por engano o bloco CSS do e8v); aplicado cirurgicamente na main. AR real depende de device. | 2026-06-16 | c02fec3 |
| 260616-eii | PDF de orçamento turbinado (4 melhorias sobre o premium sf7, tudo em `pdf.py`, zero dependência nova): (1) **QR code → Instagram** via `reportlab.graphics.barcode.qr` ao lado do CTA; (2) **CTA "PARA APROVAR"** pt-br com `@l3d_labz` (sem WhatsApp no settings); (3) **política de pagamento** "Sinal de 50% para iniciar a produção, saldo na entrega" somada ao bloco Condições (preserva validade 7d + obs do cliente, sem bloco órfão quando não há obs); (4) **selo gráfico "L3D"** antes da descrição na tabela de itens (shapes, sempre renderiza, sem input externo — corrigido clipping/overflow do Drawing + respiro de 8pt). Trava de segurança (só dados públicos) e assinatura `gerar_orcamento_pdf(dados)->bytes` preservadas. **Verificado visualmente** (rasterizado: QR, CTA, selo, pagamento e os 2 casos com/sem obs OK). | 2026-06-16 | 0a35f33, 9d4f035, b21f5c9 |

## Session Continuity

Last session: 2026-06-15 (quick 260615-sf7 — PDF de orçamento PREMIUM; antes: 260615-s0l redesign clean do PDF; 260615-nzr campos vazios na calculadora; pacote Shopee dos 669 modelos MakerWorld; superusuário l3dlabzz@gmail.com em prod)
Stopped at: Quick task 260615-gfa completa (3 commits em main: a224a8e, 4959a2f, 39e10a7) — código LOCAL, NÃO deployado/executado. PENDENTE: deploy + rodar `podar_galeria` e `gerar_descricoes` NO SERVER (runbook no SUMMARY 260615-gfa). gerar_descricoes precisa de ANTHROPIC_API_KEY no ambiente do server. Anterior: 260614-q6g em prod (hero astronauta).
NOTAS: (1) headless do Chrome NÃO renderiza WebGL aqui — verificação do 3D depende de olho no navegador real, não de screenshot. (2) modelo-vitrine do hero é trocável por env (`HERO_3D_MODEL_URL` / `HERO_3D_PRODUCT_SLUG`). (3) dev DB precisava da migração catalog.0006_productimage (aplicada local; prod roda no deploy via entrypoint).
Resume file: None
