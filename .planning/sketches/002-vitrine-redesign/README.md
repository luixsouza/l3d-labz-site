---
sketch: 002
name: vitrine-redesign
question: "Que personalidade visual a vitrine da L3D Labz deve ter, com cards alinhados e contato via Instagram?"
winner: "B"
tags: [home, catalog, product-card, palette, personality, maker]
---

# Sketch 002: Vitrine Redesign

## Design Question
A home/catálogo da L3D Labz parecia genérica e "vazia", com cards de produto de
alturas diferentes (botão "Adicionar" desalinhado) e um CTA "Chama no WhatsApp"
que não existe (o contato real é Instagram). Que direção de estilo dá personalidade
à loja e resolve esses problemas?

## How to View
- `.planning/sketches/002-vitrine-redesign/variant-a-clean-premium.html`
- `.planning/sketches/002-vitrine-redesign/variant-b-vibrante-maker.html`  ★ vencedor
- `.planning/sketches/002-vitrine-redesign/variant-c-editorial-showcase.html`

## Variants
- **A: Clean Premium** — Apple/Linear, off-white, cards brancos, sombra suave, verde só nos CTAs. Sóbrio e atemporal.
- **B: Vibrante Maker ★** — bordas pretas marcantes, hero degradê verde→azul com textura de pontos, thumbs em blocos de cor pastel, badges (NOVO/TOP), botões com sombra-offset dura, Instagram chamativo. Energia geek/maker.
- **C: Editorial Showcase** — revista/galeria: hero assimétrico numerado, produto em destaque grande, grid com fios finos. Sofisticado e curado.

## Winner: B — Vibrante Maker
Escolhido pelo dono ("ficou top"). Dá personalidade à marca sem perder a paleta
do Luigi (verde #2FA84F + azul #2BA6E0 + branco). Decisões a levar pro site real:
- **Cards de altura igual** (flex-column + `margin-top:auto` no botão; nome `-webkit-line-clamp:2`).
- **Bordas duras** (`2.5–3px solid --ink`) e **sombra-offset** nos hovers/CTAs (`Npx Npx 0 --ink`).
- **Thumbs em blocos de cor pastel** rotativos (c0–c7) por card.
- **Hero** com degradê verde→azul + textura de pontos + cartão do produto com "flag" NOVO.
- **CTA Instagram** (degradê IG) no lugar do WhatsApp; copy descontraída ("Cola no nosso Instagram").
- Badges NOVO/TOP com borda dura; chips/categorias como pílulas com borda.
- Manter suporte light/dark (light é primário).

## What to Look For
Personalidade vs. sobriedade; legibilidade dos thumbs coloridos; consistência das
bordas duras em escala (muitas cards); como o estilo se traduz pro tema escuro.
