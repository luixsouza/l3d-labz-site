# Sketch Manifest

## Design Direction
Tirar o ar "sombrio" do L3D Labz migrando o default visual pra uma estética
**Clean & Elegante** (light-first, estilo Apple/Linear): fundo off-white quente
(`#FAFBF9`), cards brancos, sombras difusas em vez de bordas duras. As "cores do
Luigi" entram contidas — **verde** (`#2FA84F`) só em CTAs/detalhes/foco e **azul**
(`#2BA6E0`) como cor secundária (links, badges, prova social). Tipografia da marca
mantida (display Bricolage Grotesque, corpo Hanken Grotesk). O diferencial — o
visualizador 3D (`<model-viewer>`) — sobe pro hero como protagonista.

## Reference Points
- Apple / Linear (clareza, respiro, sombras suaves)
- Tokens reais do projeto: `static/css/theme.css` (paleta light já existente, reequilibrada)
- Marca: cores do Luigi (verde + branco + azul)

## Sketches

| # | Name | Design Question | Winner | Tags |
|---|------|----------------|--------|------|
| 001 | home-clean-elegante | A direção clara tira o ar sombrio e coloca o 3D como protagonista? | **B — hero split** | home, palette, light-theme, hero, model-viewer |
| 002 | vitrine-redesign | Que personalidade visual dá vida à loja (cards alinhados, contato via Instagram)? | **B — Vibrante Maker** | home, catalog, product-card, palette, personality, maker |

## Decisão de estilo vigente (002 → B "Vibrante Maker")
A vitrine adota a direção **Vibrante Maker**: bordas duras (`2.5–3px solid --ink`),
sombra-offset nos CTAs/hovers (`Npx Npx 0 --ink`), thumbs em blocos de cor pastel,
hero degradê verde→azul com textura de pontos, badges NOVO/TOP, CTA Instagram
(degradê IG, no lugar de WhatsApp). Mantém a paleta do Luigi e as fontes da marca.
Resolve o bug de cards com alturas diferentes (altura igual + botão no rodapé +
nome clamp 2 linhas). Light é primário; dark adaptado.
