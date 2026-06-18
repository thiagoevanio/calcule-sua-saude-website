# Estratégia de SEO — Calcule Sua Saúde

**Atualizado em:** 18 de junho de 2026

Este documento resume a auditoria de SEO feita no site, **o que foi corrigido** nesta rodada e as **próximas oportunidades** para crescer em buscas.

---

## 1. Estado geral

O site está **tecnicamente muito bem posicionado**. Na verificação final:

- ✅ **289 páginas**, 0 links internos quebrados, 0 imagens/assets faltando.
- ✅ 100% das páginas com `<title>`, `<h1>` único, `meta description`, `canonical` e Open Graph.
- ✅ Schema.org em artigos (MedicalWebPage + FAQPage), calculadoras e home.
- ✅ Trilíngue (PT/EN/ES) com `hreflang`.

---

## 2. O que foi corrigido nesta rodada

| Item | Antes | Depois |
|------|-------|--------|
| **Títulos longos (>65 caracteres)** | 42 páginas | 26 (os 17 piores reescritos, incl. um de 104 → 63) |
| **Meta descriptions longas (>160)** | 10+ páginas | **0** (38 descriptions aparadas para ≤155) |
| **Cobertura do sitemap** | 185 URLs (~64%) | **289 URLs (100%)** — incluindo todos os quizzes e versões EN/ES |
| **Artigos novos (conteúdo em alta)** | — | +2 artigos de 2.000+ palavras (Ozivy e Orforglipron) |

> Observação técnica: ao aparar as descriptions, 29 páginas que usavam fechamento de tag no estilo `/>` tiveram o bloco SEO do `<head>` reescrito (canonical, Open Graph, Twitter e hreflang self/x-default). Todas foram validadas. **Recomendação:** para essas 29 páginas (calculadoras e ferramentas), revisar e, se desejar, recompor os `hreflang` cruzados PT↔EN↔ES completos — hoje elas têm `hreflang` self + x-default.

---

## 3. Oportunidades (por prioridade)

### 🔴 Alta
1. **Manter o sitemap atualizado automaticamente.** O robô diário já adiciona cada novo artigo ao `sitemap.xml`. Vale rodar periodicamente um rebuild para refletir remoções e novas seções.
2. **Imagens próprias nos artigos.** Vários artigos compartilham a mesma imagem de cabeçalho. Imagens únicas e otimizadas (WebP, com `alt` descritivo) melhoram o Google Imagens e o compartilhamento social.
3. **Submeter o sitemap no Google Search Console** após o deploy (Settings → Sitemaps), e acompanhar cobertura e consultas.

### 🟡 Média
4. **Títulos borderline (66–72 caracteres):** 26 páginas ainda passam um pouco do ideal. Encurtar a parte descritiva (mantendo a marca) evita corte na SERP.
5. **Links internos (topic clusters).** Agrupar artigos relacionados com links entre si — ex.: o cluster de **GLP-1 / canetas emagrecedoras** (Ozivy, Orforglipron, Canetas, GLP-1/Ozempic) já se cruza; replicar isso para diabetes, sono, nutrição etc. fortalece a autoridade temática.
6. **Schema `CollectionPage`** nas páginas de listagem (`artigos.html`, `calculadoras.html`, `quizzes.html`) para enriquecer os resultados.
7. **Sinais de E-E-A-T** (experiência, especialidade, autoridade e confiança): reforçar a página de equipe editorial, autoria nominal nos artigos e datas de revisão visíveis — crítico para o nicho YMYL (saúde).

### 🟢 Baixa / contínuo
8. **Core Web Vitals:** o CSS já foi externalizado; acompanhar LCP/CLS no PageSpeed Insights.
9. **Conteúdo em cadência:** o robô diário publica 1 artigo/dia. Priorizar na fila (`content/topics.json`) temas de **alto volume de busca** e **tendências** (como foi feito com Ozivy/Orforglipron).
10. **Atualizar artigos antigos** periodicamente (datas, dados) — o Google valoriza conteúdo "fresco".

---

## 4. Por que os 2 artigos novos ajudam o SEO

- **Tema em alta + intenção de busca real:** "Ozivy" (primeira caneta brasileira) e "orforglipron" (pílula emagrecedora) têm pico de buscas em 2026.
- **Conteúdo aprofundado:** 2.000+ palavras, com índice, tabelas, FAQ (elegível a *rich results*) e referências — sinais fortes de qualidade.
- **Cluster temático:** ambos linkam entre si e para os artigos existentes de GLP-1/canetas, concentrando autoridade no tema.
- **Atualidade:** notícia recente tende a ranquear rápido enquanto o interesse está alto.

---

## 5. Resumo

O site partiu de uma base sólida e ficou **mais forte**: descriptions e títulos saneados, **sitemap completo (100%)** e dois artigos de fôlego sobre o assunto mais quente do momento. As maiores alavancas daqui para frente são **imagens próprias**, **links internos por tema** e **cadência de conteúdo** — tudo já sustentado pelo robô diário.
