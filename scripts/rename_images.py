#!/usr/bin/env python3
"""
rename_images.py — Renomeia imagens com espaços/acentos em img/artigos/ para
kebab-case (URLs limpas, melhor SEO de imagem) e atualiza TODAS as referências
nos HTML. Idempotente. Modo dry-run por padrão.

Uso:
  python scripts/rename_images.py            # dry-run
  python scripts/rename_images.py --apply
"""
import argparse, re, unicodedata
from pathlib import Path


def slugify(name: str) -> str:
    stem = name.rsplit(".", 1)[0]
    ext = name.rsplit(".", 1)[1].lower()
    # remove acentos
    stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
    stem = stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return f"{stem}.{ext}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    img_dir = root / "img" / "artigos"

    mapping = {}
    for p in img_dir.iterdir():
        if not p.is_file():
            continue
        new = slugify(p.name)
        if new != p.name:
            mapping[p.name] = new

    print(f"{'APLICADO' if args.apply else 'DRY-RUN'} — {len(mapping)} imagens a renomear")
    for old, new in list(mapping.items())[:6]:
        print(f"   {old}  ->  {new}")

    # atualiza referências nos HTML (substitui o nome do arquivo onde aparecer)
    htmls = list(root.rglob("*.html"))
    refs_updated = 0
    for f in htmls:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        new_txt = txt
        for old, new in mapping.items():
            if old in new_txt:
                new_txt = new_txt.replace(old, new)
        if new_txt != txt:
            refs_updated += 1
            if args.apply:
                f.write_text(new_txt, encoding="utf-8", newline="\n")
    print(f"  HTML com referências atualizadas: {refs_updated}")

    # renomeia os arquivos
    if args.apply:
        for old, new in mapping.items():
            src = img_dir / old
            dst = img_dir / new
            if src.exists() and not dst.exists():
                src.rename(dst)
        print("  imagens renomeadas.")


if __name__ == "__main__":
    main()
