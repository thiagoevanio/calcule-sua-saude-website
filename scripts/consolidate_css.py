#!/usr/bin/env python3
"""
consolidate_css.py — Une arquivos css/generated/inline-*.css que têm REGRAS
idênticas (ignorando apenas comentários) em um único arquivo canônico, repara
as referências nos HTML e remove os redundantes. ZERO mudança visual: só
arquivos com as mesmas regras são unificados, melhorando o cache entre páginas.

Uso:
  python scripts/consolidate_css.py            # dry-run
  python scripts/consolidate_css.py --apply
"""
import argparse, re, hashlib
from pathlib import Path
from collections import Counter, defaultdict

REF = re.compile(r'css/generated/(inline-[0-9a-f]+\.css)')


def rules_hash(txt: str) -> str:
    no_comments = re.sub(r'/\*.*?\*/', '', txt, flags=re.DOTALL)
    return hashlib.md5(re.sub(r'\s+', ' ', no_comments).strip().encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    gen = root / "css" / "generated"

    htmls = list(root.rglob("*.html"))
    ref_count = Counter()
    for f in htmls:
        for m in REF.findall(f.read_text(encoding="utf-8", errors="ignore")):
            ref_count[m] += 1

    # agrupa por regras
    groups = defaultdict(list)
    for name in ref_count:
        p = gen / name
        if p.exists():
            groups[rules_hash(p.read_text(encoding="utf-8", errors="ignore"))].append(name)

    # mapping redundante -> canônico (canônico = mais usado, desempate alfabético)
    mapping = {}
    for names in groups.values():
        if len(names) < 2:
            continue
        canonical = sorted(names, key=lambda n: (-ref_count[n], n))[0]
        for n in names:
            if n != canonical:
                mapping[n] = canonical

    print(f"{'APLICADO' if args.apply else 'DRY-RUN'}")
    print(f"  arquivos redundantes a unificar: {len(mapping)}")

    # 1) repara referências nos HTML
    changed_files = 0
    for f in htmls:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        new = txt
        for old, canon in mapping.items():
            if old in new:
                new = new.replace(old, canon)
        if new != txt:
            changed_files += 1
            if args.apply:
                f.write_text(new, encoding="utf-8", newline="\n")
    print(f"  HTML atualizados: {changed_files}")

    # 2) remove arquivos redundantes (agora sem referências)
    if args.apply:
        removed = 0
        for old in mapping:
            p = gen / old
            if p.exists():
                p.unlink()
                removed += 1
        print(f"  arquivos CSS removidos: {removed}")
    else:
        print(f"  arquivos CSS que seriam removidos: {len(mapping)}")


if __name__ == "__main__":
    main()
