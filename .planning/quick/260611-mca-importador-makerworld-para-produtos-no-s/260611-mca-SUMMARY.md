---
status: complete
---

# Quick Task 260611-mca — Importador MakerWorld + Modal 3D

**Concluída:** 2026-06-11 · **Commits:** 2741089, cf5c837 (merge a02c46e) · **Deploy:** prod (l3dlabz.com.br) no mesmo dia

## O que foi entregue

### T1 — Pipeline 3D compartilhado + comando `importar_makerworld`
- `apps/catalog/mesh3d.py` (novo): pipeline extraído do importar_copa — `coletar_malhas`, `construir_mesh`, `finalizar_glb`, `dimensoes_mm`. Guard MAX_FACES_IN; nunca `force='mesh'`.
- `importar_copa.py` refatorado para consumir o mesh3d (comportamento idêntico).
- `importar_makerworld.py` (novo): pasta scrapada → Product. Foto oficial padronizada (GIF→1º frame, crop quadrado, JPEG q90), categoria automática por keywords (+ `--categoria` fallback), dimensões reais via bbox do 3mf ("L×A×P cm"), GLB no `model_3d`, idempotente por slug, foto-only quando sem 3mf. 3mf NUNCA vai pro `model_stl`.

### T2 — Modal 3D global
- `ProductMapper.to_dict` expõe `model_3d_url`/`has_3d`.
- Card do catálogo: botão "Ver em 3D" (`data-viewer-3d`).
- `base.html`: modal `#viewer3d` único + script model-viewer\@4.3.1 (uma vez, defer).
- `app.js`: abre com src lazy, fecha com X/Esc/backdrop (limpa src → libera GPU/RAM).
- `theme.css`: estilos com tokens; mobile fullscreen.

### T3 — Verificação
- Screenshots MCA-01..04 (card com botão, modal aberto, foto-only sem botão, chips de dimensões).
- E2E prod pós-deploy: 13 produtos importados (0 falhas), 5 com 3D, modal abre/fecha, zero erros de console.

## Notas
- Import em prod roda em container capado por produto (`/home/contta/importar-mw.sh`).
- Nomes dos produtos ficam em inglês (vêm do MakerWorld) — tradução/curadoria de copy é trabalho futuro.
- Modelos multi-parte mostram só o maior componente no GLB (limitação conhecida do pipeline).
