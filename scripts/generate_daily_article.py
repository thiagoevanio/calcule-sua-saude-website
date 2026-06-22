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
import time
import argparse
import unicodedata
import urllib.request
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
ARTIGOS_DIR = ROOT / "artigos"
TEMPLATE = ROOT / "scripts" / "templates" / "article_template.html"
TOPICS = ROOT / "content" / "topics.json"
ARTIGOS_LISTING = ROOT / "artigos.html"
INDEX = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"
COVERS_DIR = ROOT / "img" / "covers"
DEFAULT_IMG = "img/cabecario.webp"          # fallback (caminho relativo à raiz)
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
# Limpeza de URLs das referências (resolve o redirect do grounding da Gemini)
# ----------------------------------------------------------------------------
_URL_RE = re.compile(r'https?://[^\s<>"\)\]]+')
_REDIRECT_HOST = "vertexaisearch.cloud.google.com"
_url_cache = {}


def resolve_url(url: str) -> str:
    """Segue redirecionamentos e devolve a URL final (limpa). Tolerante a falhas."""
    if url in _url_cache:
        return _url_cache[url]
    final = url
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(
                url, method=method, headers={"User-Agent": "Mozilla/5.0 (compatible; CalculeSuaSaudeBot/1.0)"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                final = resp.geturl()
            break
        except Exception:
            continue
    _url_cache[url] = final
    return final


def clean_domain(url: str) -> str:
    try:
        net = urlparse(url).netloc.lower()
        return net[4:] if net.startswith("www.") else net
    except Exception:
        return url


def tidy_references(text: str) -> str:
    """Troca a URL de redirecionamento do grounding por um link limpo (domínio) clicável."""
    def repl(m):
        u = m.group(0).rstrip(".,;")
        if _REDIRECT_HOST in u:
            u = resolve_url(u)
        dom = clean_domain(u) or u
        return f'<a href="{u}">{dom}</a>'
    return _URL_RE.sub(repl, text or "")


# ----------------------------------------------------------------------------
# Coleta de contexto (artigos existentes) para evitar duplicação
# ----------------------------------------------------------------------------
def existing_slugs() -> set:
    return {p.stem for p in ARTIGOS_DIR.glob("*.html")}


def existing_titles(limit=160) -> list:
    titles = []
    for p in list(ARTIGOS_DIR.glob("*.html"))[:limit]:
        m = re.search(r"<title>(.*?)\s*\|", p.read_text(encoding="utf-8", errors="ignore"))
        if m:
            titles.append(m.group(1).strip())
    return titles


def existing_articles(limit=200) -> list:
    """Lista (titulo, slug) dos artigos PT existentes — para links internos (SEO)."""
    arts = []
    for p in sorted(ARTIGOS_DIR.glob("*.html")):
        slug = p.stem
        if slug.endswith("-en") or slug.endswith("-es"):
            continue  # só versões em português
        m = re.search(r"<title>(.*?)\s*\|", p.read_text(encoding="utf-8", errors="ignore"))
        title = m.group(1).strip() if m else slug.replace("-", " ").title()
        arts.append((title, slug))
        if len(arts) >= limit:
            break
    return arts


def pick_related(token: str, current_slug: str, n: int = 4) -> list:
    """Escolhe até n artigos relacionados (mesma editoria), com preenchimento."""
    arts = [(t, s) for (t, s) in existing_articles() if s != current_slug]
    same = [(t, s) for (t, s) in arts if category_token(t) == token]
    others = [(t, s) for (t, s) in arts if (t, s) not in same]
    return (same + others)[:n]


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


def build_research_prompt(theme: str) -> str:
    """Prompt da 1ª passada: pesquisa com Google Search (grounding)."""
    return f"""Você é pesquisador(a) médico(a). Pesquise na web fontes CONFIÁVEIS e ATUAIS
sobre o tema de saúde abaixo e produza um BRIEFING factual, em português do Brasil,
que servirá de base para um artigo. Use somente informações que você realmente
encontrar nas fontes pesquisadas.

TEMA: "{theme}"

Priorize fontes de alta autoridade: Organização Mundial da Saúde (OMS/WHO),
Ministério da Saúde do Brasil, ANVISA, sociedades médicas brasileiras (SBC, SBD, SBEM,
SBP, etc.), CDC, NIH, Mayo Clinic, Cochrane, e estudos revisados por pares (PubMed).

No briefing, inclua:
- Definição e conceitos-chave (com números/faixas APENAS se confirmados nas fontes).
- Causas, fatores de risco, sintomas e diagnóstico, conforme as diretrizes.
- Prevenção e tratamentos com respaldo de evidência (e o nível dessa evidência).
- Mitos comuns vs. o que a ciência diz.
- Dados epidemiológicos do Brasil quando houver.
- Uma lista final "FONTES:" com as referências usadas (nome da fonte, título e URL real).

Seja rigoroso: se não encontrar um dado, diga que não há evidência clara em vez de
estimar. NÃO invente estatísticas, nomes de estudos, autores nem URLs."""


def build_writer_prompt(theme: str, brief: str, sources: list,
                        avoid_titles: list, internal: list) -> str:
    """Prompt da 2ª passada: redação do artigo em JSON estruturado."""
    avoid = "; ".join(avoid_titles[:90])
    src_block = "\n".join(f"- {t} — {u}" for t, u in sources[:20]) or "(sem fontes coletadas)"
    links_block = "\n".join(f'- "{t}" → {s}.html' for t, s in internal[:40]) or "(nenhum)"
    research_block = (brief.strip()[:14000] if brief else
                      "(Sem briefing de pesquisa — seja EXTRA cauteloso: só afirme o que "
                      "for consensual e bem estabelecido; prefira faixas e linguagem prudente.)")
    return f"""Você é editor(a)-chefe de um portal brasileiro de saúde baseado em evidências
(Calcule Sua Saúde), nicho YMYL. Escreva um artigo LONGO, APROFUNDADO e CIENTÍFICO,
em português do Brasil, sobre o tema:

TEMA: "{theme}"

============ BRIEFING DE PESQUISA (use como base factual) ============
{research_block}

============ FONTES PESQUISADAS (cite as reais; não invente outras) ============
{src_block}

REGRA DE OURO — NADA INVENTADO: este é um site de saúde. Baseie TODA afirmação factual
no briefing acima e no conhecimento médico consolidado. É PROIBIDO inventar estatísticas,
percentuais, nomes de estudos, autores, datas ou URLs. Se um dado não estiver no briefing
e você não tiver certeza, use linguagem prudente ("estudos sugerem", "em geral", faixas
aproximadas) em vez de números falsos. Nunca prometa cura nem resultados garantidos.

REQUISITOS DE TAMANHO E PROFUNDIDADE:
- Artigo LONGO: 2.500 a 4.000 palavras no total.
- 12 a 16 seções de profundidade real, cada uma com vários parágrafos substanciais
  (não escreva seções de uma frase). Inclua subtópicos com <h3> dentro das seções.
- Use ao menos 1 e no máximo 3 <table> (ex.: comparativos, faixas de referência, sinais
  de alerta) onde realmente ajudem a entender.
- Tom sério, claro e acolhedor; rigor científico sem sensacionalismo.

SEO PROFISSIONAL E E-E-A-T:
- O title e o h1 devem conter a palavra-chave principal de forma natural.
- Distribua palavras-chave e termos semânticos (LSI) ao longo do texto, sem encher.
- Estruture para "featured snippets": parágrafos-resposta diretos e listas claras.
- LINKS INTERNOS (importante p/ SEO): inclua de 3 a 6 links para artigos JÁ existentes
  do site que sejam realmente relacionados, usando href RELATIVO só com o slug, assim:
  <a href="SLUG.html">texto âncora descritivo</a>. Escolha SOMENTE desta lista:
{links_block}
  Não invente slugs fora dessa lista. Insira os links naturalmente no corpo do texto.
- Sinais de E-E-A-T: linguagem técnica precisa, citação de diretrizes/órgãos, e deixar
  explícito que é conteúdo educativo que não substitui avaliação médica.

HTML em 'content_html': use apenas <p>, <ul><li>, <ol><li>, <strong>, <em>, <h3>,
<a href="...">, <blockquote> e <table>/<thead>/<tbody>/<tr>/<th>/<td> (sem atributos de
estilo nem classes). NÃO use <script>, <style>, <img>. NÃO inclua <h2> em content_html
(os títulos de seção vêm de 'heading').

Campos do JSON:
- title: título curto (<= 60 caracteres), com a palavra-chave, sem o nome do site.
- h1: título de exibição (pode usar <br>).
- tag: uma linha curta em CAIXA ALTA, ex: "SAÚDE METABÓLICA • CONTEÚDO EDUCATIVO".
- meta_description: <= 155 caracteres, atrativa, precisa e com a palavra-chave.
- og_description: <= 200 caracteres.
- keywords: 10 a 14 palavras-chave separadas por vírgula.
- category: editoria (ex: "Saúde Mental", "Nutrição Clínica", "Coração e Circulação").
- section: 1 a 2 palavras para schema.org.
- read_time: estimativa em minutos (inteiro; artigo longo costuma dar 12-18).
- excerpt: resumo de 1 frase para o card (<= 150 caracteres).
- intro: 2 a 3 parágrafos de abertura (cada item é HTML de 1 parágrafo, sem a tag <p>).
- key_points: 4 a 6 pontos-chave ("Em resumo").
- sections: lista de {{heading, content_html}} — 12 a 16 itens, aprofundados.
- faq: 6 a 8 perguntas frequentes com respostas de 2 a 4 frases.
- references: 6 a 10 referências REAIS no formato "Fonte. Título. Ano. Disponível em: URL",
  priorizando as FONTES PESQUISADAS acima e órgãos oficiais. Não invente referências.

NÃO repita temas já publicados: {avoid}

Responda APENAS com o JSON no formato solicitado."""


# ----------------------------------------------------------------------------
# Geração (real e mock)
# ----------------------------------------------------------------------------
def _client():
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        sys.exit("❌ Defina GEMINI_API_KEY (ou GOOGLE_API_KEY) no ambiente.")
    return genai.Client(api_key=api_key)


# Modelos de fallback: se o principal estiver sobrecarregado (503), tenta o próximo.
# (gemini-2.5-flash-lite costuma ter cota grátis e fica menos sobrecarregado)
FALLBACK_MODELS = ["gemini-2.5-flash-lite"]
_TRANSIENT = ("503", "UNAVAILABLE", "500", "INTERNAL", "RESOURCE_EXHAUSTED",
              "429", "deadline", "DEADLINE", "timeout", "overloaded")


def _gen(client, model, contents, config, label="geração", tries=4, base=8):
    """Chama a Gemini com novas tentativas + espera crescente em erros temporários (503/429/500)."""
    last = None
    for i in range(tries):
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as e:
            last = e
            msg = str(e)
            if i < tries - 1 and any(t in msg for t in _TRANSIENT):
                wait = base * (2 ** i)
                print(f"   ⚠️  {label}: instável ({msg[:70]}…) — nova tentativa em {wait}s")
                time.sleep(wait)
                continue
            raise
    raise last


def _gen_with_fallback(client, model, contents, config, label="geração"):
    """Tenta o modelo principal e, se persistir falha temporária, troca de modelo."""
    modelos = [model] + [m for m in FALLBACK_MODELS if m != model]
    last = None
    for mdl in modelos:
        try:
            return _gen(client, mdl, contents, config, label=f"{label} [{mdl}]")
        except Exception as e:
            last = e
            print(f"   ⚠️  modelo {mdl} indisponível; tentando alternativa…")
    raise last


def research_theme(theme: str, model: str):
    """1ª passada: pesquisa fontes reais com Google Search grounding.
    Retorna (briefing_texto, lista_de_fontes[(titulo, url)]). Tolerante a falhas."""
    from google.genai import types
    try:
        client = _client()
        resp = _gen(
            client, model, build_research_prompt(theme),
            types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.25,
                max_output_tokens=8192,
            ),
            label="pesquisa", tries=2,
        )
        brief = resp.text or ""
        sources = []
        try:
            gm = resp.candidates[0].grounding_metadata
            for ch in (getattr(gm, "grounding_chunks", None) or []):
                web = getattr(ch, "web", None)
                if web and getattr(web, "uri", None):
                    sources.append((getattr(web, "title", "") or web.uri, web.uri))
        except Exception:
            pass
        # remove duplicadas e resolve o redirect → URL real (limpa)
        seen, uniq = set(), []
        for t, u in sources:
            if u in seen:
                continue
            seen.add(u)
            uniq.append((t, resolve_url(u) if _REDIRECT_HOST in u else u))
            if len(uniq) >= 15:
                break
        print(f"   • pesquisa: {len(brief)} chars de briefing, {len(uniq)} fontes")
        return brief, uniq
    except Exception as e:
        print(f"   ⚠️  pesquisa (grounding) indisponível ({e}); seguindo sem briefing.")
        return "", []


def generate_with_gemini(theme: str, model: str) -> dict:
    from google.genai import types
    client = _client()
    # 1ª passada — pesquisa com fontes reais
    brief, sources = research_theme(theme, model)
    # 2ª passada — redação estruturada em JSON
    prompt = build_writer_prompt(theme, brief, sources,
                                 existing_titles(), existing_articles())
    resp = _gen_with_fallback(
        client, model, prompt,
        types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema(),
            temperature=0.4,
            max_output_tokens=32768,
        ),
        label="escrita do artigo",
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
# Geração da imagem de capa (única por artigo) — Pillow
# ----------------------------------------------------------------------------
# Paleta (gradiente topo→base) por editoria/token
COVER_PALETTE = {
    "Coracao":     ((183, 41, 41), (120, 22, 22)),
    "Corpo":       ((191, 87, 0), (120, 55, 4)),
    "Metabolismo": ((17, 120, 132), (10, 70, 96)),
    "Mente":       ((91, 58, 142), (54, 34, 92)),
    "Longevidade": ((30, 132, 73), (18, 86, 52)),
    "Geral":       ((10, 77, 104), (6, 48, 66)),
}
COVER_LABEL = {
    "Coracao": "Coração & Circulação", "Corpo": "Corpo & Movimento",
    "Metabolismo": "Metabolismo & Nutrição", "Mente": "Mente & Sono",
    "Longevidade": "Longevidade & Prevenção", "Geral": "Saúde Geral",
}
# Classe CSS de cor da tag de categoria (definida no <style> de index.html/artigos.html)
CAT_CLASS = {
    "Coracao": "cat-coracao", "Corpo": "cat-corpo", "Metabolismo": "cat-metab",
    "Mente": "cat-mente", "Longevidade": "cat-long", "Geral": "cat-geral",
}


def cat_class(token: str) -> str:
    return CAT_CLASS.get(token, "cat-geral")


def _cover_font(size: int, bold: bool = True):
    from PIL import ImageFont
    cands = ([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ] if bold else [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ])
    for c in cands:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def generate_cover(slug: str, data: dict, token: str, dry: bool):
    """Cria img/covers/<slug>.webp (1200x675) com título + categoria + marca.
    Retorna o caminho relativo à raiz, ou None se falhar (usa fallback)."""
    rel = f"img/covers/{slug}.webp"
    if dry:
        return rel
    try:
        from PIL import Image, ImageDraw
    except Exception as e:
        print(f"   ⚠️  Pillow indisponível ({e}); usando imagem padrão.")
        return None
    try:
        W, H, PAD = 1200, 675, 80
        c1, c2 = COVER_PALETTE.get(token, COVER_PALETTE["Geral"])
        img = Image.new("RGB", (W, H), c1)
        draw = ImageDraw.Draw(img)
        # gradiente vertical (uma linha por y)
        for y in range(H):
            t = y / H
            draw.line([(0, y), (W, y)],
                      fill=(int(c1[0]*(1-t)+c2[0]*t),
                            int(c1[1]*(1-t)+c2[1]*t),
                            int(c1[2]*(1-t)+c2[2]*t)))
        # categoria + barra de destaque
        f_cat = _cover_font(30, bold=True)
        draw.text((PAD, 205), COVER_LABEL.get(token, "Saúde").upper(),
                  font=f_cat, fill=(255, 255, 255))
        draw.rectangle([PAD, 258, PAD + 90, 270], fill=(255, 255, 255))
        # título (usa o título curto; encolhe e centraliza no espaço útil)
        title = re.sub(r"<[^>]+>", " ", data.get("title") or data.get("h1") or "")
        title = re.sub(r"\s+", " ", title).strip()
        area_top, area_bot = 300, 560
        size = 80
        while size >= 40:
            f_title = _cover_font(size, bold=True)
            lines = _wrap(draw, title, f_title, W - 2 * PAD)
            lh = int(size * 1.16)
            if len(lines) <= 4 and len(lines) * lh <= (area_bot - area_top):
                break
            size -= 4
        lines = lines[:4]
        lh = int(size * 1.16)
        y = area_top + ((area_bot - area_top) - len(lines) * lh) // 2
        for ln in lines:
            draw.text((PAD, y), ln, font=f_title, fill=(255, 255, 255))
            y += lh
        # marca (rodapé)
        f_brand = _cover_font(34, bold=True)
        draw.ellipse([PAD, H - PAD - 4, PAD + 26, H - PAD + 22], fill=(255, 255, 255))
        draw.text((PAD + 40, H - PAD - 4), "Calcule Sua Saúde",
                  font=f_brand, fill=(255, 255, 255))
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        img.save(COVERS_DIR / f"{slug}.webp", "WEBP", quality=82, method=6)
        print(f"   • capa gerada: {rel}")
        return rel
    except Exception as e:
        print(f"   ⚠️  falha ao gerar capa ({e}); usando imagem padrão.")
        return None


# ----------------------------------------------------------------------------
# Montagem do corpo do artigo
# ----------------------------------------------------------------------------
def build_body(data: dict, cover_rel: str = None, related: list = None) -> str:
    parts = []

    # Imagem de capa (única do artigo) — bom para Google Imagens e visual
    if cover_rel:
        parts.append(
            f'            <img src="../{cover_rel}" alt="{escape(data["title"], quote=True)}" '
            f'width="1200" height="675" fetchpriority="high" decoding="async" '
            f'style="width:100%;height:auto;border-radius:14px;margin-bottom:26px;display:block">\n'
        )

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

    # Leia também (artigos relacionados)
    if related:
        lis = "".join(
            f'<li><a href="{escape(s, quote=True)}.html">{escape(t)}</a></li>'
            for t, s in related)
        parts.append(
            '            <div class="clinical-pearl">\n'
            '                <h4><i data-lucide="link"></i> Leia também</h4>\n'
            f'                <ul style="margin-bottom:0">{lis}</ul>\n'
            '            </div>\n'
        )

    # Referências
    refs = ['            <div class="references-section">',
            '                <h3 id="referencias">Referências e Fontes</h3>']
    for i, r in enumerate(data.get("references", []), 1):
        refs.append(f'                <p class="ref-item">{i}. {sanitize_inline(tidy_references(r))}</p>')
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
def schema_article(data, canonical, date_iso, date_only, image_url=None):
    obj = {
        "@context": "https://schema.org",
        "@type": "MedicalWebPage",
        "headline": data["title"],
        "image": image_url or f"{BASE_URL}/{DEFAULT_IMG}",
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
def insert_card(slug, data, token, dry, cover_rel=None):
    html = ARTIGOS_LISTING.read_text(encoding="utf-8")
    anchor = '<div class="articles-grid" id="articles-grid">'
    if anchor not in html:
        print("⚠️  Não encontrei a grade de artigos; card não inserido.")
        return
    img_src = cover_rel or DEFAULT_IMG
    card = (
        f'\n\n                <!-- AUTO -->\n'
        f'                <a class="article-card" href="artigos/{slug}.html" '
        f'data-category="{token}" data-title="{escape(data["title"], quote=True)}" '
        f'data-excerpt="{escape(data["excerpt"], quote=True)}" data-read="{data["read_time"]}" '
        f'aria-label="Ler artigo: {escape(data["title"], quote=True)}">\n'
        f'                    <div class="card-img-container">\n'
        f'                        <img loading="lazy" decoding="async" src="{img_src}" '
        f'class="card-img" alt="{escape(data["title"], quote=True)}" width="800" height="450">\n'
        f'                    </div>\n'
        f'                    <div class="card-content">\n'
        f'                        <span class="card-category cat-tag {cat_class(token)}">{escape(data["category"])}</span>\n'
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


def insert_home(slug, data, token, cover_rel, dry, max_sidebar=5):
    """Promove o novo artigo a destaque principal (hero) na home (index.html);
    o hero anterior vira um card lateral e a lista lateral é aparada. Tolerante a falhas."""
    try:
        if not INDEX.exists():
            return
        html = INDEX.read_text(encoding="utf-8")
        m = re.search(r'<a\s+href="[^"]*"\s+class="featured-article-hero">.*?</a>', html, re.S)
        if not m:
            print("   ⚠️  seção de destaque não encontrada na home; pulando.")
            return
        old_hero = m.group(0)
        href_old = (re.search(r'href="([^"]+)"', old_hero) or [None, "artigos.html"])[1]
        mt = re.search(r'<h3>(.*?)</h3>', old_hero, re.S)
        title_old = re.sub(r"\s+", " ", mt.group(1)).strip() if mt else "Artigo"
        mc = re.search(r'card-category">(.*?)<', old_hero, re.S)
        cat_old = mc.group(1).strip() if mc else "Saúde"
        mi = re.search(r'src="([^"]+)"', old_hero)
        img_old = mi.group(1) if mi else DEFAULT_IMG

        cover = cover_rel or DEFAULT_IMG
        title = escape(data["title"])
        # novo hero
        new_hero = (
            f'<a href="artigos/{slug}.html" class="featured-article-hero">\n'
            f'                        <img src="{cover}" class="featured-article-hero-img" '
            f'alt="{escape(data["title"], quote=True)}" loading="lazy" decoding="async" '
            f'width="800" height="500" onerror="this.onerror=null;this.src=\'{DEFAULT_IMG}\';">\n'
            f'                        <div class="featured-article-hero-overlay"></div>\n'
            f'                        <div class="featured-article-hero-content">\n'
            f'                            <span class="badge-novo"><i data-lucide="sparkles" size="12"></i> Novo</span>\n'
            f'                            <span class="card-category cat-tag {cat_class(token)}">{escape(data.get("category", "Saúde"))}</span>\n'
            f'                            <h3>{title}</h3>\n'
            f'                            <p>{escape(data["excerpt"])}</p>\n'
            f'                        </div>\n'
            f'                    </a>'
        )
        # hero antigo vira card lateral
        old_card = (
            f'<a href="{href_old}" class="new-article-card">\n'
            f'                            <img src="{img_old}" class="new-article-thumb" '
            f'alt="{escape(title_old, quote=True)}" loading="lazy" decoding="async" '
            f'width="200" height="160" onerror="this.onerror=null;this.src=\'{DEFAULT_IMG}\';">\n'
            f'                            <div class="new-article-info">\n'
            f'                                <span class="badge-novo"><i data-lucide="sparkles" size="10"></i> Novo</span>\n'
            f'                                <h4>{escape(title_old)}</h4>\n'
            f'                                <span class="cat-tag {cat_class(category_token(cat_old))}">{escape(cat_old)}</span>\n'
            f'                            </div>\n'
            f'                        </a>'
        )
        html = html.replace(old_hero, new_hero, 1)
        html = html.replace('<div class="new-articles-sidebar">',
                            '<div class="new-articles-sidebar">\n                        ' + old_card, 1)
        # apara a lista lateral para no máximo max_sidebar cards
        cards = re.findall(r'<a\s+href="[^"]*"\s+class="new-article-card">.*?</a>', html, re.S)
        for extra in cards[max_sidebar:]:
            html = html.replace("\n                        " + extra, "", 1)
            html = html.replace(extra, "", 1)
        if not dry:
            INDEX.write_text(html, encoding="utf-8")
        print("   • destaque atualizado na home (index.html)")
    except Exception as e:
        print(f"   ⚠️  falha ao atualizar a home ({e}); seguindo.")


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

    # 4. gerar a capa única do artigo
    cover_rel = generate_cover(slug, data, token, args.dry_run)
    cover_abs = f"{BASE_URL}/{cover_rel}" if cover_rel else f"{BASE_URL}/{DEFAULT_IMG}"

    # 5. montar HTML
    related = pick_related(token, slug)
    body = build_body(data, cover_rel, related)
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
        "{{SCHEMA_ARTICLE}}": schema_article(data, canonical, date_iso, date_only, cover_abs),
        "{{SCHEMA_FAQ}}": schema_faq(data),
        "{{BODY}}": body,
    }
    for k, v in repl.items():
        page = page.replace(k, v)

    # capa única também no Open Graph / Twitter (substitui a imagem padrão fixa)
    if cover_rel:
        page = page.replace(f"{BASE_URL}/{DEFAULT_IMG}", cover_abs)

    out = ARTIGOS_DIR / f"{slug}.html"
    print(f"\n✅ Artigo: {out.relative_to(ROOT)}  ({len(page)//1024} KB)")
    if not args.dry_run:
        out.write_text(page, encoding="utf-8")

    # 6. listagem + destaque na home + sitemap + topics
    insert_card(slug, data, token, args.dry_run, cover_rel)
    insert_home(slug, data, token, cover_rel, args.dry_run)
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
    resp = _gen_with_fallback(
        client, model, prompt,
        types.GenerateContentConfig(temperature=0.9, max_output_tokens=60),
        label="sugestão de tema")
    return resp.text.strip().strip('"').splitlines()[0]


if __name__ == "__main__":
    main()
