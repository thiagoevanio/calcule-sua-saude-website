#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backfill_covers.py — Gera capa única para artigos ANTIGOS (uma vez).
====================================================================
Reaproveita a geração de capa do robô diário. Para cada artigo em português:
  1. Gera img/covers/<slug>.webp (título + categoria + marca).
  2. Substitui as referências à imagem PADRÃO compartilhada (cabecario.webp)
     pela nova capa — em og:image, twitter:image, schema e imagem no corpo.
  3. Atualiza o card correspondente em artigos.html (se usava a imagem padrão).

Artigos que JÁ têm imagem própria não são alterados (só ganham a capa em
img/covers/, disponível para uso futuro). É seguro rodar mais de uma vez.

Uso:
  python scripts/backfill_covers.py            # gera e aplica
  python scripts/backfill_covers.py --dry-run  # mostra o que faria
"""
import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_daily_article as g  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    arts = [p for p in sorted(g.ARTIGOS_DIR.glob("*.html"))
            if not (p.stem.endswith("-en") or p.stem.endswith("-es"))]
    print(f"Encontrados {len(arts)} artigos em português.\n")

    changed = 0
    for p in arts:
        slug = p.stem
        html = p.read_text(encoding="utf-8")
        m = re.search(r"<title>(.*?)\s*\|", html)
        title = (m.group(1).strip() if m else slug.replace("-", " ").title())
        ms = re.search(r'article:section"\s+content="([^"]+)"', html)
        token = g.category_token(ms.group(1) if ms else "", title)

        data = {"title": title, "h1": title, "excerpt": "", "category": ""}
        cover_rel = g.generate_cover(slug, data, token, args.dry_run)
        if not cover_rel:
            continue
        cover_abs = f"{g.BASE_URL}/{cover_rel}"

        new = html
        new = new.replace(f"{g.BASE_URL}/img/cabecario.webp", cover_abs)
        new = new.replace('content="img/cabecario.webp"', f'content="{cover_abs}"')
        new = new.replace("../img/cabecario.webp", "../" + cover_rel)

        if new != html:
            if not args.dry_run:
                p.write_text(new, encoding="utf-8")
            changed += 1
            print(f"  ✓ {slug} (imagem própria aplicada)")
        else:
            print(f"  · {slug} (já tinha imagem própria; capa gerada)")

    # Atualiza os cards da listagem que ainda usam a imagem padrão
    listing = g.ARTIGOS_LISTING.read_text(encoding="utf-8")

    def repl_card(match):
        block = match.group(0)
        href = re.search(r'href="artigos/([^"/]+)\.html"', block)
        if not href:
            return block
        s = href.group(1)
        if (g.COVERS_DIR / f"{s}.webp").exists() and "img/cabecario.webp" in block:
            block = block.replace("img/cabecario.webp", f"img/covers/{s}.webp")
        return block

    listing2 = re.sub(r'<a [^>]*class="article-card".*?</a>', repl_card, listing, flags=re.S)
    if listing2 != listing:
        if not args.dry_run:
            g.ARTIGOS_LISTING.write_text(listing2, encoding="utf-8")
        print("  ✓ artigos.html (cards atualizados)")

    print(f"\nConcluído: {changed} artigos com imagem própria. "
          f"Capas em img/covers/{'  [dry-run]' if args.dry_run else ''}.")


if __name__ == "__main__":
    main()
