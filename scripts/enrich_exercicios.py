#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enrich_exercicios.py — Preenche descrições dos exercícios com a IA (Gemini).
============================================================================
Para cada exercício em data/exercicios.json sem 'passos', gera com a Gemini:
  nivel, musculos[], passos[] (execução correta) e erros[] (erros comuns).

É resumível: salva a cada item e pula os que já têm conteúdo. Se a cota
estourar, é só rodar de novo depois que continua de onde parou.

Pré-requisito:
    pip install google-genai
    export GEMINI_API_KEY="sua_chave"     (mesma chave do robô de artigos)

Uso:
    python scripts/enrich_exercicios.py            # preenche os que faltam
    python scripts/enrich_exercicios.py --limit 50 # só 50 por vez
    python scripts/enrich_exercicios.py --force    # refaz todos
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "exercicios.json"


def schema():
    from google.genai import types
    return types.Schema(
        type=types.Type.OBJECT,
        required=["nivel", "musculos", "passos", "erros"],
        properties={
            "nivel": types.Schema(type=types.Type.STRING),
            "musculos": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
            "passos": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
            "erros": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        },
    )


def prompt(it):
    return (
        "Você é educador físico. Descreva, em português do Brasil, o exercício de "
        f"musculação a seguir, de forma EDUCATIVA e SEGURA.\n\n"
        f"Exercício: {it.get('nome')}\n"
        f"Grupo muscular: {it.get('grupo')}\n"
        f"Equipamento: {it.get('equipamento') or 'não informado'}\n\n"
        "Gere um JSON com:\n"
        "- nivel: 'iniciante', 'intermediário' ou 'avançado'.\n"
        "- musculos: 3 a 4 músculos principais trabalhados.\n"
        "- passos: 4 a 6 passos curtos e claros da execução correta.\n"
        "- erros: 3 a 5 erros comuns a evitar.\n"
        "Não invente nomes de aparelhos; se não souber o equipamento, descreva o movimento padrão."
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", default=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
    ap.add_argument("--sleep", type=float, default=1.5)
    args = ap.parse_args()

    if not CATALOG.exists():
        sys.exit("❌ data/exercicios.json não existe. Rode build_exercicios.py primeiro.")
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        sys.exit("❌ Defina GEMINI_API_KEY no ambiente (a mesma chave do robô).")

    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)

    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    pend = [i for i in data if args.force or not i.get("passos")]
    if args.limit:
        pend = pend[: args.limit]
    print(f"📋 {len(pend)} exercício(s) para preencher (de {len(data)}).")

    done = 0
    for it in pend:
        try:
            resp = client.models.generate_content(
                model=args.model,
                contents=prompt(it),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema(),
                    temperature=0.4,
                    max_output_tokens=4096,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            out = json.loads(resp.text)
            it["nivel"] = out.get("nivel", it.get("nivel", ""))
            it["musculos"] = out.get("musculos", [])
            it["passos"] = out.get("passos", [])
            it["erros"] = out.get("erros", [])
            done += 1
            CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"  ✓ {it.get('nome')}")
            time.sleep(args.sleep)
        except Exception as e:
            print(f"  ✗ {it.get('nome')}: {e}")
            time.sleep(3)

    print(f"\n✅ {done} preenchidos. Catálogo salvo em {CATALOG.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
