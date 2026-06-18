#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_daily_article.py — Robô de artigo diário (Calcule Sua Saúde)
=====================================================================

Fluxo:
  1. Lê content/topics.json e pega o próximo tema 'pending'
     (ou pede um tema inédito à IA se a fila acabar).
  2. Chama a Gemini API (SDK google-genai, modelo gemini-2.5-flash) pedindo
     um artigo estruturado em JSON, em português, baseado em evidências.
  3. Monta o HTML no padrão do site (scripts/templates/article_template.html),
     com schema.org MedicalWebPage + FAQPage, índice, callouts e referências.
  4. Salva em artigos/<slug>.html, insere o card em artigos.html,
     adiciona a URL no sitemap.xml e move o tema para 'published'.

Uso:
  export GEMINI_API_KEY="sua_chave"
  python scripts/generate_daily_article.py

Opções:
  --mock        Gera um artigo de exemplo SEM chamar a API (para testar o pipeline).
  --dry-run     Faz tudo mas NÃO grava nada em disco (mostra o que faria).
  --theme "..." Ignora a fila e usa este tema.
  --model NOME  Modelo Gemini (padrão: env GEMINI_MODEL ou gemini-2.5-flash).

Chave da API: https://aistudio.google.com/app/apikey
"""

import os
import re
import sys
import json
import argparse
import unicodedata
from pathlib import Path
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
ARTIGOS_DIR = ROOT / "artigos"
TEMPLATE = ROOT / "scripts" / "templates" / "article_template.html"
TOPICS = ROOT / "content" / "topics.json"
ARTIGOS_LISTING = ROOT / "artigos.html"
SITEMAP = ROOT / "sitemap.xml"
BASE_URL = "https://www.calculesuasaude.com.br"

MESES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# Categorias aceitas pelos filtros do artigos.html
FILTER_TOKENS = ["Coracao", "Corpo", "Geral", "Longevidade", "Mente", "Metabolismo"]


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return re.sub(r"-{2,}", "-", text)[:70].strip("-")


def category_token(*hints: str) -> str:
    blob = " ".join(h for h in hints if h).lower()
    rules = [
        ("Mente", ["mente", "sono", "mental", "ansied", "depress", "burnout",
                   "mindful", "estresse", "cortisol", "circadian"]),
        ("Coracao", ["cora", "cardio", "press", "colesterol", "circula",
                     "hipertens", "trigliceri", "vascular"]),
        ("Metabolismo", ["metab", "nutri", "diabet", "insulin", "glic", "macro",
                         "vitamina", "omega", "ômega", "fibra", "probi", "jejum",
                         "magnesio", "magnésio", "tireoide", "acido urico",
                         "ácido úrico", "figado", "fígado", "esteatose", "glp"]),
        ("Longevidade", ["longev", "preven", "osso", "inflama", "epigen",
                         "envelhec", "cancer", "câncer", "zonas azuis"]),
        ("Corpo", ["corpo", "movimento", "treino", "forca", "força", "exerc",
                   "muscul", "múscul", "hiit", "mioquina", "creatina"]),
    ]
    for token, kws in rules:
        if any(k in blob for k in kws):
            return token
    return "Geral"


# ----------------------------------------------------------------------------
# Sanitização de HTML (whitelist) — evita tags/atributos inesperados da IA
# ----------------------------------------------------------------------------
ALLOWED_TAGS = {"p", "br", "strong", "em", "b", "i", "ul", "ol", "li",
                "h3", "h4", "a", "table", "thead", "tbody", "tr", "th", "td",
                "blockquote"}
ALLOWED_ATTRS = {"a": {"href"}}


class Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_TAGS:
            return
        allowed = ALLOWED_ATTRS.get(tag, set())
        kept = ""
        for k, v in attrs:
            if k in allowed and v:
                if k == "href" and not re.match(r"^(https?:|#|[\w./-]+\.html)", v):
                    continue
                kept += f' {k}="{escape(v, quote=True)}"'
        self.out.append(f"<{tag}{kept}>")

    def handle_endtag(self, tag):
        if tag in ALLOWED_TAGS:
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        self.out.append(data)

    def result(self):
        return "".join(self.out)


def sanitize(html: str) -> str:
    s = Sanitizer()
    s.feed(html or "")
    html = s.result()
    # tabelas ganham a classe do site
    html = re.sub(r"<table>", '<table class="scientific-table">', html)
    return html.strip()


def clip(text: str, n: int) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


# ----------------------------------------------------------------------------
# Coleta de contexto (artigos existentes) para evitar duplicação
# ----------------------------------------------------------------------------
def existing_slugs() -> set:
    return {p.stem for p in ARTIGOS_DIR.glob("*.html")}


def existing_titles(limit=120) -> list:
    titles = []
    for p in list(ARTIGOS_DIR.glob("*.html"))[:limit]:
        m = re.search(r"<title>(.*?)\s*\|", p.read_text(encoding="utf-8", errors="ignore"))
        if m:
            titles.append(m.group(1).strip())
    return titles


# ----------------------------------------------------------------------------
# JSON Schema esperado da IA
# ----------------------------------------------------------------------------
def response_schema():
    from google.genai import types
    return types.Schema(
        type=types.Type.OBJECT,
        required=["title", "h1", "tag", "meta_description", "og_description",
                  "keywords", "category", "section", "read_time", "excerpt",
                  "intro", "key_points", "sections", "faq", "references"],
        properties={
            "title": types.Schema(type=types.Type.STRING),
            "h1": types.Schema(type=types.Type.STRING),
            "tag": types.Schema(type=types.Type.STRING),
            "meta_description": types.Schema(type=types.Type.STRING),
            "og_description": types.Schema(type=types.Type.STRING),
            "keywords": types.Schema(type=types.Type.STRING),
            "category": types.Schema(type=types.Type.STRING),
            "section": types.Schema(type=types.Type.STRING),
            "read_time": types.Schema(type=types.Type.INTEGER),
            "excerpt": types.Schema(type=types.Type.STRING),
            "intro": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
            "key_points": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
            "sections": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    required=["heading", "content_html"],
                    properties={
                        "heading": types.Schema(type=types.Type.STRING),
                        "content_html": types.Schema(type=types.Type.STRING),
                    },
                ),
            ),
            "faq": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    required=["q", "a"],
                    properties={
                        "q": types.Schema(type=types.Type.STRING),
                        "a": types.Schema(type=types.Type.STRING),
                    },
                ),
            ),
            "references": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        },
    )


def build_prompt(theme: str, avoid_titles: list) -> str:
    avoid = "; ".join(avoid_titles[:80])
    return f"""Você é editor(a) de um portal brasileiro de saúde baseado em evidências
(Calcule Sua Saúde). Escreva um artigo COMPLETO, em português do Brasil, sobre o tema:

TEMA: "{theme}"

Requisitos editoriais:
- Tom sério, claro e acolhedor; sem sensacionalismo nem promessas milagrosas.
- Baseado em evidências; cite diretrizes/órgãos (OMS, Ministério da Saúde, sociedades
  médicas, PubMed) quando fizer sentido. NÃO invente estatísticas precisas falsas;
  prefira faixas e linguagem prudente.
- Deixe explícito que é conteúdo educativo e não substitui avaliação médica.
- 8 a 12 seções de profundidade real (não superficiais).
- Use HTML simples em 'content_html': <p>, <ul><li>, <strong>, <em>, <h3>, e no máximo
  UMA <table> quando ajudar (sem atributos de estilo). Não use <script>, <style>, <img>
  nem classes. Não inclua <h2> dentro de content_html (os títulos de seção vêm de 'heading').

Campos:
- title: título curto (<= 60 caracteres), sem o nome do site.
- h1: título de exibição (pode ser igual ao title; pode usar uma quebra com <br>).
- tag: uma linha curta em CAIXA ALTA, ex: "SAÚDE METABÓLICA • CONTEÚDO EDUCATIVO".
- meta_description: <= 155 caracteres, atrativa e precisa.
- og_description: <= 200 caracteres.
- keywords: 8 a 12 palavras-chave separadas por vírgula.
- category: editoria de exibição (ex: "Saúde Mental", "Nutrição Clínica", "Coração e Circulação").
- section: 1 a 2 palavras para schema.org.
- read_time: estimativa em minutos (inteiro).
- excerpt: resumo de 1 frase para o card (<= 150 caracteres).
- intro: 1 a 2 parágrafos de abertura (cada item é HTML de 1 parágrafo, sem a tag <p>).
- key_points: 3 a 4 pontos-chave curtos ("Em resumo").
- sections: lista de {{heading, content_html}}.
- faq: 4 a 6 perguntas frequentes com respostas de 2 a 4 frases.
- references: 4 a 7 referências (texto), preferindo fontes oficiais e revisadas.

NÃO repita temas já publicados: {avoid}

Responda APENAS com o JSON no formato solicitado."""


# ----------------------------------------------------------------------------
# Geração (real e mock)
# ----------------------------------------------------------------------------
def generate_with_gemini(theme: str, model: str) -> dict:
    from google import genai
    from google.genai import types
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        sys.exit("❌ Defina GEMINI_API_KEY (ou GOOGLE_API_KEY) no ambiente.")
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model,
        contents=build_prompt(theme, existing_titles()),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema(),
            temperature=0.7,
            max_output_tokens=8192,
        ),
    )
    return json.loads(resp.text)


def generate_mock(theme: str) -> dict:
    """Artigo de exemplo determinístico para testar o pipeline sem API."""
    return {
        "title": clip(theme.split(":")[0], 58),
        "h1": escape(theme.split(":")[0]),
        "tag": "CONTEÚDO EDUCATIVO • BASEADO EM EVIDÊNCIAS",
        "meta_description": clip(f"Guia educativo sobre {theme.lower()}: o que é, "
                                 f"por que importa e o que dizem as evidências.", 150),
        "og_description": clip(f"Entenda {theme.lower()} de forma clara e baseada em evidências.", 190),
        "keywords": "saúde, prevenção, bem-estar, evidências, " + slugify(theme).replace("-", ", "),
        "category": "Saúde Geral",
        "section": "Saúde",
        "read_time": 8,
        "excerpt": clip(f"O que você precisa saber sobre {theme.split(':')[0].lower()}.", 145),
        "intro": [
            f"Este artigo apresenta uma visão geral, <strong>educativa e baseada em evidências</strong>, sobre {escape(theme.split(':')[0].lower())}. (Conteúdo de exemplo gerado em modo de teste.)",
            "As informações aqui não substituem a avaliação de um profissional de saúde.",
        ],
        "key_points": [
            "Este é um texto de exemplo para validar o pipeline.",
            "Em produção, o conteúdo é gerado pela Gemini.",
            "A estrutura, o índice e as referências são montados automaticamente.",
        ],
        "sections": [
            {"heading": "Visão geral", "content_html":
                "<p>Parágrafo de exemplo descrevendo o panorama do tema, com linguagem "
                "clara e sem alarmismo. <strong>Pontos importantes</strong> aparecem em destaque.</p>"
                "<ul><li>Primeiro aspecto relevante.</li><li>Segundo aspecto relevante.</li></ul>"},
            {"heading": "Como prevenir e cuidar", "content_html":
                "<p>Estratégias gerais costumam incluir hábitos de vida, acompanhamento "
                "periódico e atenção aos sinais de alerta.</p>"
                "<table><thead><tr><th>Hábito</th><th>Benefício</th></tr></thead>"
                "<tbody><tr><td>Atividade física</td><td>Melhora metabólica e cardiovascular</td></tr>"
                "<tr><td>Sono adequado</td><td>Recuperação e equilíbrio hormonal</td></tr></tbody></table>"},
            {"heading": "Quando procurar ajuda", "content_html":
                "<p>Diante de sintomas persistentes ou sinais de alerta, procure um "
                "profissional de saúde para avaliação individualizada.</p>"},
        ],
        "faq": [
            {"q": "Este conteúdo substitui o médico?", "a": "Não. É material educativo e não substitui avaliação, diagnóstico ou tratamento profissional."},
            {"q": "Com que frequência o site publica?", "a": "Um novo artigo por dia, de forma automatizada, com curadoria de temas."},
        ],
        "references": [
            "Organização Mundial da Saúde (OMS) — materiais educativos.",
            "Ministério da Saúde (Brasil) — diretrizes e campanhas.",
            "PubMed — literatura científica revisada por pares.",
        ],
    }


# ----------------------------------------------------------------------------
# Montagem do corpo do artigo
# ----------------------------------------------------------------------------
def build_body(data: dict) -> str:
    parts = []

    # Aviso médico (sempre)
    parts.append(
        '            <div class="clinical-pearl" style="border-left-color:#D97706">\n'
        '                <h4><i data-lucide="alert-triangle"></i> Aviso médico importante</h4>\n'
        '                <p style="margin-bottom:0">Este conteúdo é <strong>educativo e informativo</strong> '
        'e <strong>não substitui</strong> a consulta, o diagnóstico ou o tratamento de um profissional de '
        'saúde. Em caso de sintomas, procure orientação médica.</p>\n'
        '            </div>\n'
    )

    # Índice
    toc = ['            <div class="toc-integrated">',
           '                <h4 class="toc-title">Índice do Artigo</h4>',
           '                <ul class="toc-list">']
    sec_ids = []
    for i, s in enumerate(data["sections"], 1):
        sid = slugify(s["heading"]) or f"secao-{i}"
        sec_ids.append(sid)
        toc.append(f'                    <li><a href="#{sid}">{i}. {escape(s["heading"])}</a></li>')
    if data.get("faq"):
        toc.append(f'                    <li><a href="#faq">{len(data["sections"])+1}. Perguntas frequentes</a></li>')
    toc += ['                </ul>', '            </div>\n']
    parts.append("\n".join(toc) + "\n")

    # Introdução
    for p in data.get("intro", []):
        parts.append(f"            <p>{sanitize_inline(p)}</p>\n")

    # Em resumo
    if data.get("key_points"):
        lis = "".join(f"<li>{sanitize_inline(k)}</li>" for k in data["key_points"])
        parts.append(
            '            <div class="clinical-pearl">\n'
            '                <h4><i data-lucide="info"></i> Em resumo</h4>\n'
            f'                <ul style="margin-bottom:0">{lis}</ul>\n'
            '            </div>\n'
        )

    # Seções
    for i, s in enumerate(data["sections"], 1):
        sid = sec_ids[i - 1]
        parts.append(f'            <h2 id="{sid}">{i}. {escape(s["heading"])}</h2>\n')
        parts.append("            " + sanitize(s["content_html"]) + "\n")

    # FAQ
    if data.get("faq"):
        parts.append(f'            <h2 id="faq">{len(data["sections"])+1}. Perguntas frequentes</h2>\n')
        for qa in data["faq"]:
            parts.append(f'            <p><strong>{escape(qa["q"])}</strong><br>{sanitize_inline(qa["a"])}</p>\n')

    # Referências
    refs = ['            <div class="references-section">',
            '                <h3 id="referencias">Referências e Fontes</h3>']
    for i, r in enumerate(data.get("references", []), 1):
        refs.append(f'                <p class="ref-item">{i}. {sanitize_inline(r)}</p>')
    refs.append('            </div>')
    parts.append("\n".join(refs) + "\n")

    return "".join(parts)


def sanitize_inline(text: str) -> str:
    """Permite formatação leve em trechos de 1 linha (strong/em/a/br)."""
    s = Sanitizer()
    s.feed(text or "")
    return s.result().strip()


# ----------------------------------------------------------------------------
# Schemas JSON-LD
# ----------------------------------------------------------------------------
def schema_article(data, canonical, date_iso, date_only):
    obj = {
        "@context": "https://schema.org",
        "@type": "MedicalWebPage",
        "headline": data["title"],
        "image": f"{BASE_URL}/img/cabecario.webp",
        "author": {"@type": "Organization", "name": "Calcule Sua Saúde - Corpo Editorial"},
        "publisher": {"@type": "Organization", "name": "Calcule Sua Saúde",
                      "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/img/logo.png"}},
        "datePublished": date_only, "dateModified": date_only,
        "description": data["meta_description"],
        "reviewedBy": {"@type": "Organization", "name": "Calcule Sua Saúde - Corpo Editorial"},
        "mainEntityOfPage": canonical,
    }
    return json.dumps(obj, ensure_ascii=False)


def schema_faq(data):
    obj = {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": qa["q"],
                           "acceptedAnswer": {"@type": "Answer",
                                              "text": re.sub("<[^>]+>", "", qa["a"])}}
                          for qa in data.get("faq", [])]}
    return json.dumps(obj, ensure_ascii=False)


# ----------------------------------------------------------------------------
# Inserções (listagem + sitemap + topics)
# ----------------------------------------------------------------------------
def insert_card(slug, data, token, dry):
    html = ARTIGOS_LISTING.read_text(encoding="utf-8")
    anchor = '<div class="articles-grid" id="articles-grid">'
    if anchor not in html:
        print("⚠️  Não encontrei a grade de artigos; card não inserido.")
        return
    card = (
        f'\n\n                <!-- AUTO -->\n'
        f'                <a class="article-card" href="artigos/{slug}.html" '
        f'data-category="{token}" data-title="{escape(data["title"], quote=True)}" '
        f'data-excerpt="{escape(data["excerpt"], quote=True)}" data-read="{data["read_time"]}" '
        f'aria-label="Ler artigo: {escape(data["title"], quote=True)}">\n'
        f'                    <div class="card-img-container">\n'
        f'                        <img loading="lazy" decoding="async" src="img/cabecario.webp" '
        f'class="card-img" alt="{escape(data["title"], quote=True)}" width="800" height="450">\n'
        f'                    </div>\n'
        f'                    <div class="card-content">\n'
        f'                        <span class="card-category">{escape(data["category"])}</span>\n'
        f'                        <h3 class="card-title">{escape(data["title"])}</h3>\n'
        f'                        <p class="card-excerpt">{escape(data["excerpt"])}</p>\n'
        f'                        <div class="card-footer"><span class="meta-chip">'
        f'<i data-lucide="clock" size="14"></i> {data["read_time"]} min</span>'
        f'<span>Equipe Editorial</span></div>\n'
        f'                    </div>\n'
        f'                </a>'
    )
    new = html.replace(anchor, anchor + card, 1)
    if not dry:
        ARTIGOS_LISTING.write_text(new, encoding="utf-8")
    print(f"   • card inserido em artigos.html ({token})")


def insert_sitemap(canonical, date_only, dry):
    xml = SITEMAP.read_text(encoding="utf-8")
    if canonical in xml:
        print("   • sitemap já continha a URL")
        return
    entry = (f'  <url><loc>{canonical}</loc><lastmod>{date_only}</lastmod>'
             f'<changefreq>monthly</changefreq><priority>0.82</priority></url>\n')
    new = xml.replace("</urlset>", entry + "</urlset>", 1)
    if not dry:
        SITEMAP.write_text(new, encoding="utf-8")
    print("   • URL adicionada ao sitemap.xml")


def update_topics(topics_data, used_theme, slug, date_only, from_queue, dry):
    if from_queue:
        for t in topics_data["queue"]:
            if t.get("theme") == used_theme and t.get("status") == "pending":
                t["status"] = "published"
                break
        topics_data["queue"] = [t for t in topics_data["queue"] if t.get("status") != "published"]
    topics_data.setdefault("published", []).append(
        {"theme": used_theme, "slug": slug, "date": date_only})
    if not dry:
        TOPICS.write_text(json.dumps(topics_data, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Robô de artigo diário (Gemini).")
    ap.add_argument("--mock", action="store_true", help="Gera exemplo sem chamar a API.")
    ap.add_argument("--dry-run", action="store_true", help="Não grava nada em disco.")
    ap.add_argument("--theme", type=str, default=None, help="Tema específico (ignora a fila).")
    ap.add_argument("--model", type=str,
                    default=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    date_only = now.strftime("%Y-%m-%d")
    date_iso = now.strftime("%Y-%m-%dT08:00:00+00:00")
    date_human = f"{now.day} de {MESES[now.month]}, {now.year}"

    # 1. escolher tema
    topics_data = json.loads(TOPICS.read_text(encoding="utf-8")) if TOPICS.exists() else {"queue": [], "published": []}
    from_queue = False
    if args.theme:
        theme = args.theme
    else:
        pend = next((t for t in topics_data.get("queue", []) if t.get("status") == "pending"), None)
        if pend:
            theme = pend["theme"]; from_queue = True
        else:
            theme = None  # IA escolhe (apenas no modo real)

    print(f"📝 Tema: {theme or '(IA irá sugerir um tema inédito)'}")
    print(f"🤖 Modo: {'MOCK' if args.mock else args.model}{'  [dry-run]' if args.dry_run else ''}")

    # 2. gerar
    if args.mock:
        data = generate_mock(theme or "Tema de saúde de exemplo")
    else:
        if theme is None:
            theme = suggest_theme(args.model)
            print(f"💡 Tema sugerido pela IA: {theme}")
        data = generate_with_gemini(theme, args.model)

    # 3. normalizar/validar
    data["title"] = clip(data["title"], 60)
    data["meta_description"] = clip(data["meta_description"], 158)
    data["excerpt"] = clip(data["excerpt"], 150)
    data["read_time"] = int(data.get("read_time") or 8)
    if not data.get("h1"):
        data["h1"] = escape(data["title"])

    slug = slugify(data.get("title") or theme)
    used = existing_slugs()
    base = slug; n = 2
    while slug in used:
        slug = f"{base}-{n}"; n += 1

    canonical = f"{BASE_URL}/artigos/{slug}.html"
    token = category_token(data.get("category"), data.get("section"), theme)

    # 4. montar HTML
    body = build_body(data)
    tpl = TEMPLATE.read_text(encoding="utf-8")
    page = tpl
    repl = {
        "{{TITLE}}": escape(data["title"]),
        "{{H1}}": data["h1"],
        "{{TAG}}": escape(data["tag"]),
        "{{META_DESCRIPTION}}": escape(data["meta_description"], quote=True),
        "{{KEYWORDS}}": escape(data.get("keywords", ""), quote=True),
        "{{CANONICAL}}": canonical,
        "{{OG_TITLE}}": escape(data["title"], quote=True),
        "{{OG_DESCRIPTION}}": escape(data.get("og_description", data["meta_description"]), quote=True),
        "{{SECTION}}": escape(data.get("section", "Saúde"), quote=True),
        "{{PUBLISHED_ISO}}": date_iso,
        "{{PUBLISHED_HUMAN}}": date_human,
        "{{READ_TIME}}": str(data["read_time"]),
        "{{SLUG}}": slug,
        "{{SCHEMA_ARTICLE}}": schema_article(data, canonical, date_iso, date_only),
        "{{SCHEMA_FAQ}}": schema_faq(data),
        "{{BODY}}": body,
    }
    for k, v in repl.items():
        page = page.replace(k, v)

    out = ARTIGOS_DIR / f"{slug}.html"
    print(f"\n✅ Artigo: {out.relative_to(ROOT)}  ({len(page)//1024} KB)")
    if not args.dry_run:
        out.write_text(page, encoding="utf-8")

    # 5. listagem + sitemap + topics
    insert_card(slug, data, token, args.dry_run)
    insert_sitemap(canonical, date_only, args.dry_run)
    update_topics(topics_data, theme, slug, date_only, from_queue, args.dry_run)

    print(f"\n🎉 Concluído: {data['title']}")
    print(f"   Seções: {len(data['sections'])} | FAQ: {len(data.get('faq', []))} | "
          f"Refs: {len(data.get('references', []))} | Categoria: {token}")


def suggest_theme(model: str) -> str:
    """Pede à IA um tema inédito quando a fila acaba."""
    from google import genai
    from google.genai import types
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    prompt = ("Sugira UM tema inédito de artigo de saúde em português (brasileiro), "
              "baseado em evidências, com bom volume de busca, que NÃO esteja nesta "
              "lista de temas já publicados: " + "; ".join(existing_titles()) +
              ". Responda apenas com o título do tema, sem aspas.")
    resp = client.models.generate_content(
        model=model, contents=prompt,
        config=types.GenerateContentConfig(temperature=0.9, max_output_tokens=60))
    return resp.text.strip().strip('"').splitlines()[0]


if __name__ == "__main__":
    main()
