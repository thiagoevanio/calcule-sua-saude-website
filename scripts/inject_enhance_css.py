#!/usr/bin/env python3
"""Injeta <link> do css/enhance.css por último no <head> de todas as paginas.
Idempotente: nao duplica se ja existir. Calcula o prefixo relativo correto
(paginas na raiz usam 'css/...', paginas em subpastas usam '../css/...')."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = '<link rel="stylesheet" href="{p}css/enhance.css">'

def main(apply=True):
    changed = skipped = noenhance = 0
    for f in ROOT.rglob('*.html'):
        rel = f.relative_to(ROOT)
        txt = f.read_text(encoding='utf-8', errors='ignore')
        if 'css/enhance.css' in txt:
            skipped += 1
            continue
        if '</head>' not in txt:
            noenhance += 1
            continue
        depth = len(rel.parts) - 1            # 0 = raiz, 1 = subpasta
        prefix = '../' * depth
        link = '    ' + LINK.format(p=prefix) + '\n'
        new = txt.replace('</head>', link + '</head>', 1)
        if apply:
            f.write_text(new, encoding='utf-8')
        changed += 1
    print(f"injetado: {changed} | ja tinha: {skipped} | sem <head>: {noenhance}")

if __name__ == '__main__':
    main(apply='--dry-run' not in sys.argv)
