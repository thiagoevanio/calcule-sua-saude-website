#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_exercicios.py — Gera data/exercicios.json a partir dos GIFs.
====================================================================
Coloque os GIFs em  img/exercicios/  e rode este script. Ele lê os nomes
dos arquivos, deduz o grupo muscular e o equipamento por palavras-chave e
monta o catálogo que alimenta a página exercicios.html.

Uso:
  python scripts/build_exercicios.py

Opcional: depois você pode editar data/exercicios.json para acrescentar
'passos', 'musculos' e 'erros' nos exercícios que quiser detalhar.
"""
import re
import json
import unicodedata
from urllib.parse import quote
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GIF_DIR = ROOT / "img" / "exercicios"
OUT = ROOT / "data" / "exercicios.json"

GRUPOS = [
    ("peito", ["supino", "crucifix", "peito", "crossover", "peck", "flexao", "flexão"]),
    ("costas", ["remada", "puxada", "pulldown", "barra fixa", "terra", "pull", "dorsal", "encolhimento"]),
    ("perna", ["agachament", "leg", "extensora", "flexora", "afundo", "avanco", "avanço", "stiff",
               "passada", "hack", "coxa", "perna", "bulgar"]),
    ("gluteo", ["gluteo", "glúteo", "pelvic", "hip thrust", "coice", "abducao", "abdução"]),
    ("panturrilha", ["panturrilha", "gemeos", "gêmeos", "calf"]),
    ("ombro", ["ombro", "desenvolvimento", "elevacao lateral", "elevação lateral", "militar",
               "arnold", "remada alta", "crucifixo inverso", "shoulder"]),
    ("biceps", ["rosca", "biceps", "bíceps", "scott", "concentrada", "martelo", "curl"]),
    ("triceps", ["triceps", "tríceps", "frances", "francês", "coice triceps", "pulley", "testa", "mergulho"]),
    ("abdomen", ["abdomin", "abdômen", "abdomen", "prancha", "crunch", "obliquo", "oblíquo",
                 "elevacao de pernas", "elevação de pernas", "infra"]),
    ("antebraco", ["antebraco", "antebraço", "punho"]),
]

EQUIP = [
    ("halter", ["halter", "dumbbell", "haltere"]),
    ("barra", ["barra", "barbell", "smith"]),
    ("máquina", ["maquina", "máquina", "machine", "cabo", "polia", "cross", "leg press", "hack"]),
    ("peso do corpo", ["peso do corpo", "livre", "flexao", "flexão", "barra fixa", "prancha", "calistenia"]),
    ("kettlebell", ["kettlebell"]),
    ("elastico", ["elastico", "elástico", "band"]),
]


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", text)).strip("-")


def nice_name(stem):
    name = re.sub(r"[_\-]+", " ", stem).strip()
    name = re.sub(r"\s+", " ", name)
    return name[:1].upper() + name[1:] if name else stem


def classify(blob, table, default=""):
    blob = blob.lower()
    for label, kws in table:
        if any(k in blob for k in kws):
            return label
    return default


def main():
    if not GIF_DIR.exists():
        print(f"❌ Pasta não encontrada: {GIF_DIR}")
        print("   Crie a pasta img/exercicios/ e coloque os GIFs lá.")
        return
    # Coleta RECURSIVA (inclui as subpastas por grupo muscular).
    # 1 mídia por exercício, preferindo vídeo (mp4/webm) ao gif.
    by_key = {}
    for p in GIF_DIR.rglob("*"):
        if p.suffix.lower() not in (".gif", ".mp4", ".webm"):
            continue
        key = (str(p.parent), p.stem)
        cur = by_key.get(key)
        if cur is None or (cur.suffix.lower() == ".gif" and p.suffix.lower() in (".mp4", ".webm")):
            by_key[key] = p
    arquivos = [by_key[k] for k in sorted(by_key)]
    if not arquivos:
        print(f"⚠️  Nenhum .gif/.mp4 em {GIF_DIR} (nem nas subpastas).")
        return

    itens = []
    for p in arquivos:
        stem = p.stem
        # grupo = nome da subpasta, sem o contador (ex.: 'Costas (54)' -> 'costas');
        # se o arquivo estiver solto na raiz, deduz pelo nome do arquivo
        if p.parent != GIF_DIR:
            pasta = re.sub(r"\s*\(\d+\)\s*$", "", p.parent.name)
            grupo = slugify(pasta)
        else:
            grupo = classify(stem, GRUPOS, "corpo-todo")
        rel = p.relative_to(ROOT).as_posix()
        itens.append({
            "nome": nice_name(stem),
            "slug": slugify(f"{grupo}-{stem}"),
            "grupo": grupo,
            "equipamento": classify(stem, EQUIP, ""),
            "nivel": "",
            "gif": quote(rel, safe="/"),
            "musculos": [],
            "passos": [],
            "erros": []
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(itens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # resumo por grupo
    from collections import Counter
    c = Counter(i["grupo"] for i in itens)
    print(f"✅ {len(itens)} exercícios gravados em {OUT.relative_to(ROOT)}")
    for g, n in c.most_common():
        print(f"   • {g}: {n}")


if __name__ == "__main__":
    main()
