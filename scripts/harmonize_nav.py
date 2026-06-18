#!/usr/bin/env python3
"""
harmonize_nav.py — Padroniza os ITENS do menu principal em todas as páginas,
por idioma (detectado em <html lang>), com caminhos relativos corretos e o
estado "ativo" conforme a seção da página. Substitui apenas o conteúdo de
<ul id="primary-nav" ...> ... </ul> (deixado por add_mobile_nav.py).

Uso:
  python scripts/harmonize_nav.py            # dry-run
  python scripts/harmonize_nav.py --apply
"""
import argparse, re
from pathlib import Path

UL_RE = re.compile(r'(<ul id="primary-nav"[^>]*>)(.*?)(</ul>)', re.DOTALL | re.IGNORECASE)
LANG_RE = re.compile(r'<html[^>]*\blang="([^"]+)"', re.IGNORECASE)

# Itens por idioma: (chave, rótulo, arquivo, é_botão)
MENUS = {
    "pt": [
        ("inicio", "Início", "index.html", False),
        ("artigos", "Artigos", "artigos.html", False),
        ("receitas", "Receitas", "receitas.html", False),
        ("calculadoras", "Calculadoras", "calculadoras.html", False),
        ("quizzes", "Quizzes", "quizzes.html", False),
        ("ferramentas", "Ferramentas", "ferramentas.html", False),
        ("contato", "Contato", "contato.html", True),
    ],
    "en": [
        ("inicio", "Home", "index-en.html", False),
        ("artigos", "Articles", "artigos-en.html", False),
        ("calculadoras", "Calculators", "calculadoras-en.html", False),
        ("quizzes", "Quizzes", "quizzes-en.html", False),
        ("ferramentas", "Tools", "ferramentas-en.html", False),
        ("contato", "Contact", "contato-en.html", True),
    ],
    "es": [
        ("inicio", "Inicio", "index-es.html", False),
        ("artigos", "Artículos", "artigos-es.html", False),
        ("calculadoras", "Calculadoras", "calculadoras-es.html", False),
        ("quizzes", "Cuestionarios", "quizzes-es.html", False),
        ("ferramentas", "Herramientas", "ferramentas-es.html", False),
        ("contato", "Contacto", "contato-es.html", True),
    ],
}


def detect_lang(text):
    m = LANG_RE.search(text)
    code = (m.group(1).lower() if m else "pt")
    if code.startswith("en"):
        return "en"
    if code.startswith("es"):
        return "es"
    return "pt"


def detect_active(path: Path, root: Path):
    rel = path.relative_to(root)
    folder = rel.parts[0] if len(rel.parts) > 1 else ""
    name = rel.name.lower()
    if folder == "artigos" or name.startswith("artigos"):
        return "artigos"
    if folder == "receitas" or name.startswith("receitas"):
        return "receitas"
    if folder == "calculadoras" or name.startswith("calculadoras"):
        return "calculadoras"
    if folder == "quizz" or name.startswith("quizzes"):
        return "quizzes"
    if folder == "ferramentas" or name.startswith("ferramentas"):
        return "ferramentas"
    if name.startswith("index"):
        return "inicio"
    if name.startswith("contato"):
        return "contato"
    return ""


def build_menu(lang, prefix, active):
    lines = []
    for key, label, fname, is_btn in MENUS[lang]:
        href = prefix + fname
        if is_btn:
            cls = "btn-outline-white"
            extra = ""
            if key == active:
                extra = ' aria-current="page"'
            lines.append(f'            <li><a href="{href}" class="{cls}"{extra}>{label}</a></li>')
        else:
            cls = "nav-link active" if key == active else "nav-link"
            extra = ' aria-current="page"' if key == active else ""
            lines.append(f'            <li><a href="{href}" class="{cls}"{extra}>{label}</a></li>')
    return "\n" + "\n".join(lines) + "\n        "


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    changed = 0
    skipped = 0
    examples = []
    for f in sorted(root.rglob("*.html")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        if 'id="primary-nav"' not in text:
            skipped += 1
            continue
        lang = detect_lang(text)
        active = detect_active(f, root)
        prefix = "../" * (len(f.relative_to(root).parts) - 1)
        new_inner = build_menu(lang, prefix, active)
        new_text = UL_RE.sub(lambda m: m.group(1) + new_inner + m.group(3), text, count=1)
        if new_text != text:
            changed += 1
            if len(examples) < 6:
                examples.append(f"{f.relative_to(root)} [{lang}/{active or '-'}]")
            if args.apply:
                f.write_text(new_text, encoding="utf-8", newline="\n")
        else:
            skipped += 1

    print(f"{'APLICADO' if args.apply else 'DRY-RUN'}")
    print(f"  navs harmonizados: {changed}")
    print(f"  pulados          : {skipped}")
    for e in examples:
        print("   -", e)


if __name__ == "__main__":
    main()
