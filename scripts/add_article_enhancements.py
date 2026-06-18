#!/usr/bin/env python3
"""
add_article_enhancements.py — Injeta a experiência de leitura (article.css +
article.js) em todas as páginas que contêm um artigo (class="article-body").
Idempotente e aditivo. Pula se 'css/article.css' já estiver referenciado.

Uso:
  python scripts/add_article_enhancements.py            # dry-run
  python scripts/add_article_enhancements.py --apply
"""
import argparse
from pathlib import Path


def prefix_for(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    return "../" * (len(rel.parts) - 1)


def process(path: Path, root: Path):
    text = path.read_text(encoding="utf-8")
    if 'class="article-body"' not in text:
        return "skip (não é artigo)", text, False
    if "css/article.css" in text:
        return "skip (já tem)", text, False
    if "</head>" not in text:
        return "skip (sem head)", text, False

    p = prefix_for(path, root)
    inject = (f'    <link rel="stylesheet" href="{p}css/article.css">\n'
              f'    <script defer src="{p}js/article.js"></script>\n')
    new_text = text.replace("</head>", inject + "</head>", 1)
    return "ok", new_text, new_text != text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    stats = {"ok": 0, "skip": 0}
    examples = []
    for f in sorted(root.rglob("*.html")):
        status, new_text, changed = process(f, root)
        if status == "ok" and changed:
            stats["ok"] += 1
            if len(examples) < 6:
                examples.append(str(f.relative_to(root)))
            if args.apply:
                f.write_text(new_text, encoding="utf-8", newline="\n")
        else:
            stats["skip"] += 1

    print(f"{'APLICADO' if args.apply else 'DRY-RUN'}")
    print(f"  artigos alterados: {stats['ok']}")
    print(f"  pulados          : {stats['skip']}")
    print("  exemplos         :", ", ".join(examples))


if __name__ == "__main__":
    main()
