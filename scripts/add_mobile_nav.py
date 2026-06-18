#!/usr/bin/env python3
"""
add_mobile_nav.py — Injeta o menu hambúrguer mobile (nav.css + nav.js + botão)
em todas as páginas HTML de forma IDEMPOTENTE e ADITIVA.

O que faz em cada arquivo:
  1. Adiciona <link rel="stylesheet" href="{prefix}css/nav.css"> antes de </head>
  2. Adiciona <script defer src="{prefix}js/nav.js"></script> antes de </head>
  3. Insere o <button class="nav-toggle"> antes do primeiro <ul ...nav-menu...>
     e dá id="primary-nav" ao <ul> (para aria-controls)
  4. Unifica o ícone do logo: data-lucide="zap" -> "microscope" dentro de .logo

Nunca remove conteúdo. Se 'css/nav.css' já existir no arquivo, pula (idempotente).

Uso:
  python scripts/add_mobile_nav.py            # simulação (dry-run)
  python scripts/add_mobile_nav.py --apply    # aplica de verdade
"""
import argparse
import re
from pathlib import Path

SKIP_FILES = {"404.html"}

NAV_MENU_RE = re.compile(r'<ul((?:(?!>).)*?\bclass="(?:(?!").)*?\bnav-menu\b(?:(?!").)*?"(?:(?!>).)*?)>', re.IGNORECASE | re.DOTALL)

BUTTON_HTML = ('<button class="nav-toggle" aria-label="Abrir menu" '
               'aria-expanded="false" aria-controls="primary-nav">'
               '<span></span><span></span><span></span></button>\n            ')


def prefix_for(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    depth = len(rel.parts) - 1  # número de pastas acima do arquivo
    return "../" * depth


def process(path: Path, root: Path):
    text = path.read_text(encoding="utf-8")
    if "css/nav.css" in text:
        return "skip (já tem)", text, False

    if "</head>" not in text or "nav-menu" not in text:
        return "skip (sem head/nav)", text, False

    p = prefix_for(path, root)
    original = text

    # 1+2. links no <head>
    head_inject = (f'    <link rel="stylesheet" href="{p}css/nav.css">\n'
                   f'    <script defer src="{p}js/nav.js"></script>\n')
    text = text.replace("</head>", head_inject + "</head>", 1)

    # 3. botão hambúrguer + id no <ul>
    m = NAV_MENU_RE.search(text)
    if m:
        ul_attrs = m.group(1)
        new_attrs = ul_attrs if re.search(r'\bid=', ul_attrs, re.IGNORECASE) else ' id="primary-nav"' + ul_attrs
        replacement = BUTTON_HTML + "<ul" + new_attrs + ">"
        text = text[:m.start()] + replacement + text[m.end():]

    # 4. unifica ícone do logo
    text = text.replace('class="logo"><i data-lucide="zap"', 'class="logo"><i data-lucide="microscope"')

    changed = text != original
    return ("ok" if changed else "sem mudança"), text, changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="aplica as mudanças (sem isso é dry-run)")
    ap.add_argument("--root", default=".", help="raiz do site")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    files = sorted(root.rglob("*.html"))
    stats = {"ok": 0, "skip": 0, "no-change": 0}
    changed_examples = []

    for f in files:
        if f.name in SKIP_FILES:
            continue
        status, new_text, changed = process(f, root)
        if status == "ok" and changed:
            stats["ok"] += 1
            if len(changed_examples) < 5:
                changed_examples.append(str(f.relative_to(root)))
            if args.apply:
                f.write_text(new_text, encoding="utf-8", newline="\n")
        elif status.startswith("skip"):
            stats["skip"] += 1
        else:
            stats["no-change"] += 1

    print(f"{'APLICADO' if args.apply else 'DRY-RUN'} — raiz: {root}")
    print(f"  alterados : {stats['ok']}")
    print(f"  pulados   : {stats['skip']}")
    print(f"  sem mudança: {stats['no-change']}")
    print("  exemplos  :", ", ".join(changed_examples))


if __name__ == "__main__":
    main()
