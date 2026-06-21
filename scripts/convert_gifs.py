#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_gifs.py — Converte os GIFs de exercícios em MP4 (bem mais leves).
=========================================================================
GIF é pesado; MP4 (H.264) costuma ficar 80–90% menor e roda perfeito na web.
Este script lê img/exercicios/*.gif e gera img/exercicios/<nome>.mp4.

Pré-requisito (instala sozinho o ffmpeg, não precisa instalar à mão):
    pip install imageio imageio-ffmpeg

Uso:
    python scripts/convert_gifs.py                # converte, mantém os GIFs
    python scripts/convert_gifs.py --delete-gifs  # converte e apaga os .gif
    python scripts/convert_gifs.py --update-json  # troca .gif por .mp4 no catálogo

Depois rode  python scripts/build_exercicios.py  (ou use --update-json) e
faça commit apenas dos .mp4 (mais leves) + data/exercicios.json.
"""
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GIF_DIR = ROOT / "img" / "exercicios"
CATALOG = ROOT / "data" / "exercicios.json"


def human(n):
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delete-gifs", action="store_true", help="Apaga o .gif após converter.")
    ap.add_argument("--update-json", action="store_true", help="Atualiza data/exercicios.json (.gif -> .mp4).")
    ap.add_argument("--fps", type=int, default=0, help="Forçar FPS (0 = detectar do GIF).")
    args = ap.parse_args()

    try:
        import imageio.v2 as imageio
    except Exception:
        print("❌ Falta a biblioteca. Rode:  pip install imageio imageio-ffmpeg")
        sys.exit(1)

    if not GIF_DIR.exists():
        print(f"❌ Pasta não encontrada: {GIF_DIR}  (crie e coloque os GIFs lá)")
        sys.exit(1)

    gifs = sorted(GIF_DIR.rglob("*.gif"))  # inclui subpastas (grupos musculares)
    if not gifs:
        print(f"⚠️  Nenhum .gif em {GIF_DIR} (nem nas subpastas).")
        return

    total_in = total_out = 0
    ok = 0
    for p in gifs:
        mp4 = p.with_suffix(".mp4")
        try:
            reader = imageio.get_reader(str(p))
            meta = reader.get_meta_data()
            dur = meta.get("duration")  # ms por frame
            fps = args.fps or (round(1000.0 / dur) if dur else 15)
            fps = max(8, min(int(fps), 30))
            writer = imageio.get_writer(
                str(mp4), fps=fps, codec="libx264", quality=7,
                macro_block_size=None, pixelformat="yuv420p",
                output_params=["-movflags", "+faststart"],
            )
            for frame in reader:
                writer.append_data(frame)
            writer.close()
            reader.close()
            si, so = p.stat().st_size, mp4.stat().st_size
            total_in += si
            total_out += so
            ok += 1
            print(f"  ✓ {p.name}  {human(si)} -> {human(so)}")
            if args.delete_gifs:
                p.unlink()
        except Exception as e:
            print(f"  ✗ {p.name}: {e}")

    print(f"\n✅ {ok}/{len(gifs)} convertidos.  Total: {human(total_in)} -> {human(total_out)}"
          + (f"  (economia de {100 - total_out * 100 / total_in:.0f}%)" if total_in else ""))

    if args.update_json and CATALOG.exists():
        from urllib.parse import unquote, quote
        data = json.loads(CATALOG.read_text(encoding="utf-8"))
        for it in data:
            raw = unquote(it.get("gif", ""))
            if raw.endswith(".gif"):
                mp4rel = raw[:-4] + ".mp4"
                if (ROOT / mp4rel).exists():
                    it["gif"] = quote(mp4rel, safe="/")
        CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("   • data/exercicios.json atualizado (.gif -> .mp4)")


if __name__ == "__main__":
    main()
