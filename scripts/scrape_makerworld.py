#!/usr/bin/env python3
"""Scraper de curadoria do MakerWorld — top modelos em pastas prontas p/ import.

Para cada modelo: pasta `<dest>/<slug>/` com:
  meta.json        — id, título, descrição (html), licença, tags, criador, contagens, url
  descricao.html   — resumo/descrição original (pra moldar a copy do site)
  fotos/NN.jpg     — capa + galeria oficial (fotos REAIS das peças impressas)
  modelo.3mf       — arquivo de impressão (REQUER token de login — cookie `token`)

Uso:
  python3 scrape_makerworld.py --top 20 --dest ./makerworld
  python3 scrape_makerworld.py --top 50 --keyword dragon --order downloadCount
  MAKERWORLD_TOKEN=eyJ... python3 scrape_makerworld.py --top 10 --dest ./mw

Sem token: baixa meta+fotos e pula o 3MF (dá pra baixar depois com --so-arquivos).
Licença de cada modelo fica no meta.json — CONFIRA antes de vender impressões
("Standard Digital File License" NÃO permite uso comercial; prefira CC-BY etc.).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://makerworld.com/api/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PAUSA = 1.5  # segundos entre requests — educado com o servidor deles


def _req(url: str, token: str = "") -> bytes:
    """GET com timeout curto e 3 tentativas — CDN/API às vezes pendura a conexão."""
    h = {"User-Agent": UA, "Accept": "application/json"}
    if token:
        # SOMENTE o cookie — mandar Authorization junto faz a API responder 403
        h["Cookie"] = f"token={token}"
    ultimo: Exception | None = None
    for tentativa in range(3):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read()
        except Exception as e:  # timeout, reset, 5xx...
            ultimo = e
            time.sleep(3 * (tentativa + 1))
    raise RuntimeError(f"3 tentativas falharam p/ {url[:80]}: {ultimo}")


def _json(url: str, token: str = "") -> dict:
    return json.loads(_req(url, token))


def listar_top(n: int, keyword: str, order: str) -> list[dict]:
    """Busca paginada ordenada por popularidade."""
    hits, offset = [], 0
    while len(hits) < n:
        lote = min(50, n - len(hits))
        q = urllib.parse.urlencode({
            "keyword": keyword, "orderBy": order, "limit": lote, "offset": offset,
        })
        d = _json(f"{API}/search-service/select/design2?{q}")
        page = d.get("hits", [])
        if not page:
            break
        hits.extend(page)
        offset += len(page)
        time.sleep(PAUSA)
    return hits[:n]


def baixar_modelo(design_id: int, dest: Path, token: str, so_arquivos: bool) -> str:
    d = _json(f"{API}/design-service/design/{design_id}")
    slug = d.get("slug") or f"design-{design_id}"
    slug = re.sub(r"[^a-z0-9-]", "", slug.lower())[:80] or f"design-{design_id}"
    pasta = dest / slug
    pasta.mkdir(parents=True, exist_ok=True)

    # ---- meta + descrição ----
    if not so_arquivos:
        criador = (d.get("designCreator") or {})
        meta = {
            "id": d["id"],
            "url": f"https://makerworld.com/en/models/{d['id']}-{d.get('slug', '')}",
            "titulo": d.get("title"),
            "titulo_en": d.get("titleTranslated"),
            "licenca": d.get("license"),
            "tags": d.get("tags") or [],
            "criador": criador.get("name"),
            "criador_handle": criador.get("handle"),
            "downloads": d.get("downloadCount"),
            "likes": d.get("likeCount"),
            "prints": d.get("printCount"),
            "scrape_em": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        (pasta / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        desc = (d.get("summary") or "") + "\n" + (d.get("summaryTranslated") or "")
        (pasta / "descricao.html").write_text(desc.strip(), encoding="utf-8")

        # ---- fotos: capa + galerias das instances (dedup, ordem estável) ----
        urls, vistos = [], set()
        if d.get("coverUrl"):
            urls.append(d["coverUrl"])
        for inst in d.get("instances") or []:
            for p in inst.get("pictures") or []:
                u = p.get("url")
                if u and u not in vistos:
                    vistos.add(u)
                    urls.append(u)
        fotos = pasta / "fotos"
        fotos.mkdir(exist_ok=True)
        for i, u in enumerate(urls, 1):
            ext = os.path.splitext(urllib.parse.urlparse(u).path)[1] or ".jpg"
            alvo = fotos / f"{i:02d}{ext}"
            if alvo.exists():
                continue
            try:
                alvo.write_bytes(_req(u))
            except Exception as e:  # foto quebrada não derruba o modelo
                print(f"    ! foto {i}: {e}")
            time.sleep(0.4)

    # ---- arquivo de impressão (3MF) — precisa de token ----
    arq = pasta / "modelo.3mf"
    if arq.exists():
        return f"{slug} (3mf já existia)"
    if not token:
        return f"{slug} (SEM 3MF — rode com token)"
    inst = (d.get("instances") or [{}])[0]
    iid = inst.get("id")
    if not iid:
        return f"{slug} (sem instance p/ download)"
    try:
        resp = _json(f"{API}/design-service/instance/{iid}/f3mf?type=download", token)
        url = resp.get("url") or (resp.get("data") or {}).get("url")
        if not url:
            return f"{slug} (download negado: {str(resp)[:80]})"
        arq.write_bytes(_req(url))
        return f"{slug} OK ({arq.stat().st_size // 1024} KB)"
    except urllib.error.HTTPError as e:
        return f"{slug} (HTTP {e.code} no download — token expirado?)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=20, help="quantos modelos (padrão 20)")
    ap.add_argument("--keyword", default="", help="busca opcional (vazio = geral)")
    ap.add_argument("--order", default="hotScore",
                    help="hotScore (padrão) | downloadCount | likeCount")
    ap.add_argument("--dest", default="./makerworld", help="pasta de saída")
    ap.add_argument("--so-arquivos", action="store_true",
                    help="só baixa 3MF faltantes (meta/fotos já salvos)")
    args = ap.parse_args()

    token = os.environ.get("MAKERWORLD_TOKEN", "").strip()
    if not token:
        tf = Path.home() / ".makerworld_token"
        if tf.exists():
            token = tf.read_text().strip()
    if not token:
        print("AVISO: sem MAKERWORLD_TOKEN — baixando só meta+fotos (3MF pulado).")

    dest = Path(args.dest)
    hits = listar_top(args.top, args.keyword, args.order)
    print(f"{len(hits)} modelos (order={args.order}, keyword={args.keyword!r})\n")
    licencas: dict[str, int] = {}
    for i, h in enumerate(hits, 1):
        lic = h.get("license") or "?"
        licencas[lic] = licencas.get(lic, 0) + 1
        print(f"[{i}/{len(hits)}] {h.get('titleTranslated') or h.get('title')}  [{lic}]")
        try:
            print("   ", baixar_modelo(h["id"], dest, token, args.so_arquivos))
        except Exception as e:
            print(f"    FALHOU: {e}")
        time.sleep(PAUSA)

    print("\n--- licenças encontradas (confira antes de vender impressões!) ---")
    for lic, n in sorted(licencas.items(), key=lambda x: -x[1]):
        print(f"  {n:3d}x {lic}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
