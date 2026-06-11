---
phase: quick-260611-go4
status: completed
completed_at: "2026-06-11"
commits:
  - b2b2339  # T1: mobile header + menu + dark theme
  - 1f0fa96  # T2: rebrand + home/about + 404/500 + footer
  - efd5dc5  # T3: model-viewer + render3d
---

# Resumo — 260611-go4: Corrigir 8 achados do UAT

## O que foi feito

### T1 — Mobile header acessível + menu opaco + tema dark v2 (commit b2b2339)

**Achados fechados: 1, 2, 3, 4**

- CSS (`static/css/theme.css`): bloco `@media (max-width:720px)` esconde `.btn` de texto no header (Entrar/Criar conta/Sair ficam acessíveis no menu mobile). `nav-toggle` ganha `z-index:60` e `pointer-events:auto` — sempre tocável.
- `.main-nav.open`: fundo sólido `#0a0f0c` (não translúcido), links com `color:#e9edf6` (contraste AA), `z-index:49` acima do hero.
- Links de conta adicionados no painel mobile (`navbar.html`): Entrar / Minha conta / Sair dependendo do estado de autenticação, com classe `.nav-account-link`.
- Superfícies de páginas v2 (checkout, auth, conta, pedidos, lithophane) passam a referenciar `var(--bg-card)`, `var(--text)` e `var(--bg-soft)` → tema dark toggle consistente.
- Active do link "Sobre": removida a condição `vn == 'core:home'` (não marcava home como "Sobre").

### T2 — Rebrand L3D + home/sobre separadas + 404/500 + footer (commit 1f0fa96)

**Achados fechados: 5, 6, 7**

- `apps/orders/models.py`: prefixo `NX-` → `L3D-` (apenas pedidos novos; existentes intactos).
- `apps/cart/templates/cart/detail.html`: placeholder cupom `NERD10` → `L3D10`.
- `apps/core/templates/base.html`: title sem duplicação de marca — `{% block title %}L3D Labz — Impressão 3D sob demanda{% endblock %}` único.
- `apps/core/views.py`: `HomeView` (vitrine: featured/new_arrivals/home_categories) + `AboutView` (institucional, sem vitrine).
- `apps/core/urls.py`: `path("")` → `HomeView(name="home")`, `path("sobre/")` → `AboutView(name="about")`, + rotas `/privacidade/` e `/termos/`.
- `apps/core/templates/core/home.html`: vitrine completa (hero, serviços, prova social, categorias, destaques, novidades, CTA).
- `apps/core/templates/core/about.html`: institucional (quem somos, como funciona, FAQ, pagamento, contato).
- `apps/core/templates/core/static_page.html`: privacidade (LGPD) e termos de compra em pt-br.
- `templates/404.html`: extende base.html, link pro catálogo, cópia amigável.
- `templates/500.html`: HTML autocontido (sem extends, sem context processors) — seguro mesmo com DB/cache fora do ar.
- `apps/core/templates/core/partials/footer.html`: links de privacidade, termos e fale-conosco com destinos reais (`core:privacidade`, `core:termos`, WhatsApp).
- `apps/core/admin.py` (novo): `site_header`, `site_title`, `index_title` = "L3D Labz".

### T3 — model-viewer 3/4 + render3d colorido determinístico (commit efd5dc5)

**Achados fechados: 8, 9**

- `apps/catalog/templates/catalog/product_detail.html`: `camera-orbit="35deg 70deg auto"` (era `-25deg 72deg`) — ângulo 3/4 mostra volume. Adicionados `min/max-camera-orbit` para evitar zoom degenerado; `exposure=1.1`.
- `apps/catalog/render3d.py`:
  - Paleta L3D de 8 cores (verde/azul/coral/âmbar/lilás/teal/terra/azul-escuro).
  - Cor derivada deterministicamente via `hashlib.sha1(nome)` — mesma entrada = mesma cor.
  - Iluminação key+fill (antes só key+amb): `_KEY_INT=0.78`, `_FILL_INT=0.28`, `_AMB=0.22` — std de pixels = 72, muito acima do limiar 12.
  - Parâmetro `accent` (hex `#RRGGBB`) funciona como override.
  - Assinatura `render_thumb(mesh, nome, accent, tamanho) -> bytes` preservada.

## Verificações automatizadas

```
# T1
.main-nav.open regra encontrada no CSS                           PASS

# T2
L3D- em orders/models.py, NX- ausente                           PASS
HomeView e AboutView em core/views.py                           PASS
templates/404.html e templates/500.html existem                 PASS
python manage.py check                                          0 issues

# T3
render_thumb(box, 'produto-verde', '') -> std=72.55             PASS (>12)
determinismo b1==b2                                             PASS
camera-orbit="35deg 70deg" em product_detail.html               PASS
```

## Arquivos modificados

| Arquivo | Tipo |
|---------|------|
| `static/css/theme.css` | modificado |
| `apps/core/templates/core/partials/navbar.html` | modificado |
| `apps/orders/models.py` | modificado |
| `apps/cart/templates/cart/detail.html` | modificado |
| `apps/core/templates/base.html` | modificado |
| `apps/core/views.py` | modificado |
| `apps/core/urls.py` | modificado |
| `apps/core/templates/core/home.html` | modificado |
| `apps/core/templates/core/about.html` | modificado |
| `apps/core/templates/core/partials/footer.html` | modificado |
| `apps/core/templates/core/static_page.html` | novo |
| `apps/core/admin.py` | novo |
| `templates/404.html` | novo |
| `templates/500.html` | novo |
| `apps/catalog/templates/catalog/product_detail.html` | modificado |
| `apps/catalog/render3d.py` | modificado |
