---
quick_id: 260626-o3a
status: complete
date: 2026-06-26
---

# Quick 260626-o3a — Zerar catálogo + admin de cadastro manual

## Objetivo
Apagar todos os produtos do site (decisão do dono: cadastrar manualmente, pois as fotos do import eram lixão/loremflickr — ver memória `fotos-produto-loremflickr-lixao`) e turbinar o admin de Produto para cadastro manual visual.

## O que foi feito

### Task 1 — `apps/catalog/management/commands/limpar_catalogo.py` (novo)
- **Dry-run por padrão** (sem flag não apaga nada; imprime contagem + aviso).
- `--confirmar`: gera `backups/catalogo-<timestamp>.json` (UTF-8) via `dumpdata` capturado em `StringIO`, depois `Product.objects.all().delete()`.
- Segurança documentada na docstring: `OrderItem.product=SET_NULL` (pedidos intactos), `ProductImage`=CASCADE (galeria cai junto), `Category` PROTECT (categorias nunca apagadas).
- Imprime contagens antes/depois e o comando de restore (`loaddata`).
- Bug corrigido na verificação: `--output` do dumpdata no Windows gera CP1252 e quebra o `loaddata`; solução = capturar stdout e gravar com `encoding="utf-8"`.

### Task 2 — `apps/catalog/admin.py` (turbinado)
- Helper `_thumb_html()` com `format_html` (escape seguro).
- `ProductImageInline` com coluna `preview` (60px) por foto.
- `ProductAdmin.list_display` com `thumb` (48px) no início; `image_preview` readonly (200px) no form.
- Fieldsets ordenados para cadastro manual; blocos "Modelos 3D" e "Automação / scraper" colapsados (`classes: collapse`).
- `CategoryAdmin` inalterado.

## Verificação local (SQLite seed)
- `manage.py check` — sem erros.
- `limpar_catalogo` (dry-run) — não apaga, mostra contagem.
- `limpar_catalogo --confirmar` — backup 18.9 KB gerado, `Product.objects.count()==0`, `Category.objects.count()==7`, `loaddata` restaura 23 produtos.

## Commits
- `a563d02` feat: comando limpar_catalogo (backup JSON + delete seguro com guard)
- `796d86c` feat: admin de Produto turbinado para cadastro manual visual
- `c06dd7c` fix: backup JSON em UTF-8 (dumpdata stdout + write_text encoding=utf-8)
- `ee93502` chore: adicionar /backups/ ao .gitignore

## Pendente (orquestrador)
- Deploy (push na main) + rodar `limpar_catalogo --confirmar` em prod via `manage.yml`.
- Verificar catálogo vazio e admin no browser.
