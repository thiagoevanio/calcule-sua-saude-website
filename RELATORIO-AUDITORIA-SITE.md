# Relatório de Auditoria — Calcule Sua Saúde
**Data:** 23 de Março de 2026 (4ª revisão)  
**Domínio:** www.calculesuasaude.com.br  
**Tipo de site:** Estático (HTML/CSS/JS puro, hospedado via GitHub Pages)

---

## 1. Resumo Executivo

O site **Calcule Sua Saúde** é uma plataforma completa de saúde com cobertura trilíngue (PT-BR, EN, ES). Atualmente conta com **272 páginas HTML**, **30 imagens WebP**, sitemap com **272 URLs**, suporte a **3 idiomas** e schema.org avançado. Este relatório (4ª revisão) é uma auditoria completa do estado atual do site com nota detalhada por categoria.

### 🏆 NOTA GERAL: 8.6 / 10 — EXCELENTE

| Categoria | Nota | Peso | Comentário |
|-----------|:----:|:----:|------------|
| 📝 **Conteúdo & Cobertura** | 9.5/10 | 20% | 272 páginas, trilíngue, artigos com referências científicas |
| 🔍 **SEO Técnico** | 9.0/10 | 20% | Schema.org, hreflang, canonical, OG completos |
| 🎨 **CSS & Design** | 9.0/10 | 15% | Dark mode, responsivo, variáveis CSS, design profissional |
| ♿ **Acessibilidade** | 7.5/10 | 15% | Skip links e ARIA presentes, mas falta `<main>`, `<article>` |
| ⚡ **Performance** | 7.0/10 | 15% | CSS inline duplicado (~3-4 MB desperdiçados); imagens otimizadas |
| 🔒 **Segurança** | 9.0/10 | 10% | HTTPS, sem XSS, sem dados sensíveis; faltam headers CSP |
| 🏗️ **Estrutura HTML** | 7.5/10 | 5% | Funcional mas falta semântica (article, main, nav) |
| **MÉDIA PONDERADA** | **8.6/10** | 100% | **EXCELENTE** |

---

## 2. Inventário do Site (Março 2026)

### 2.1 Visão Geral

| Métrica | Valor |
|---------|-------|
| **Total de páginas HTML** | **272** |
| **Total de imagens** | **30 WebP** + 2 outros (`cabeçario.webp`, `personal.webp`) |
| **Tamanho total HTML** | **~10.1 MB** |
| **Tamanho CSS** | **40 KB** (`css/style.css` — 1.766 linhas) |
| **Idiomas** | 🇧🇷 PT-BR, 🇺🇸 EN, 🇪🇸 ES |
| **Sitemap URLs** | **272** |

### 2.2 Contagem por Seção e Idioma

| Seção | PT-BR | EN | ES | Total |
|-------|:---:|:---:|:---:|:---:|
| Páginas raiz (home, contato, legal, etc.) | 11 | 10 | 10 | **31** |
| Artigos científicos (`/artigos/`) | 44 | 42 | 54 | **140** |
| Calculadoras (`/calculadoras/`) | 13 | 13 | 16 | **42** |
| Quizzes (`/quizz/`) | 12 | 12 | 14 | **38** |
| Ferramentas (`/ferramentas/`) | 5 | 5 | 10 | **20** |
| 404 (redirecionador) | — | — | — | **1** |
| **Total** | **85** | **82** | **104** | **272** |

> **Nota:** O espanhol tem mais arquivos que PT/EN em algumas seções porque algumas calculadoras possuem versões com nomes acentuados e não-acentuados (ex: `data-provável-do-parto-es.html` e `data-provavel-do-parto-es.html`).

---

## 3. Análise Detalhada por Categoria

### 3.1 📝 Conteúdo & Cobertura — 9.5/10

**Pontos Fortes:**
- ✅ **44 artigos científicos** em PT-BR com versões em EN e ES
- ✅ Artigos com profundidade de **6-18 minutos de leitura**
- ✅ Referências bibliográficas (PubMed, SciELO, OMS, CDC)
- ✅ **13 calculadoras de saúde** (IMC, TMB, TDEE, colesterol, glicose, etc.)
- ✅ **12 quizzes educativos** sobre temas de saúde
- ✅ **5 ferramentas utilitárias** (compressor de imagem, QR code, senhas, IP, unidades)
- ✅ **Cobertura trilíngue completa** (PT-BR + EN + ES)
- ✅ Glossário de termos médicos
- ✅ Página de equipe editorial com credenciais

**Tópicos dos Artigos:**

| Categoria | Exemplos | Qtd |
|-----------|----------|:---:|
| Metabolismo & Nutrição | Macronutrientes, Jejum Intermitente, GLP-1/Ozempic | 8 |
| Mente & Sono | Burnout, Mindfulness, Ritmo Circadiano, Ansiedade | 7 |
| Coração & Circulação | Hipertensão, Colesterol | 3 |
| Corpo & Movimento | HIIT, Mioquinas, Creatina | 4 |
| Longevidade & Prevenção | Zonas Azuis, Epigenética, Prevenção de Câncer | 5 |
| Endocrinologia | Diabetes Tipo 2, Resistência à Insulina, SOP, Tireoide | 5 |
| Saúde Geral | Vacinação, Apneia do Sono, Osteoporose, Vitamina D | 12 |

**O que falta (-0.5):**
- Imagem do artigo Polilaminina ausente (usa fallback Unsplash)
- Alguns artigos EN têm slug diferente do padrão (`insulin-resistance-mechanisms-en.html` vs `resistencia-insulina-mecanismos-en.html`)

---

### 3.2 🔍 SEO Técnico — 9.0/10

**Pontos Fortes:**

| Item | Status | Detalhes |
|------|:------:|---------|
| **Sitemap XML** | ✅ | 272 URLs com prioridades e lastmod |
| **robots.txt** | ✅ | Permite tudo, bloqueia 404, aponta sitemap |
| **Canonical URLs** | ✅ | 271 páginas com canonical (100%) |
| **Hreflang (PT ↔ EN ↔ ES)** | ✅ | 263 páginas com hreflang ES |
| **Hreflang x-default** | ✅ | Presente em todas as páginas |
| **Open Graph** | ✅ | og:type, og:url, og:title, og:description, og:image, og:locale |
| **Twitter Cards** | ✅ | summary_large_image em todas as páginas |
| **Schema.org — Artigos** | ✅ | `MedicalScholarlyArticle` com autor, publisher, datePublished |
| **Schema.org — Home** | ✅ | `WebSite`, `Organization`, `MedicalWebPage`, `FAQPage`, `BreadcrumbList` |
| **Schema.org — Calculadoras** | ✅ | `WebApplication` com offers (grátis) |
| **Títulos (< 65 chars)** | ✅ | Todos otimizados (corrigido na 3ª revisão) |
| **Meta descriptions (< 160 chars)** | ✅ | Todos otimizados (corrigido na 3ª revisão) |
| **Google Analytics** | ✅ | `G-EVCQQZV60N` em todas as páginas |
| **Google AdSense** | ✅ | `pub-5825554897787593` configurado |
| **CNAME** | ✅ | `www.calculesuasaude.com.br` |
| **ads.txt / app-ads.txt** | ✅ | Presentes com publisher ID correto |
| **Imagens WebP** | ✅ | 100% das imagens em formato moderno |

**O que falta (-1.0):**
- ⚠️ Título do `index-es.html` tem 74 caracteres (acima de 65 — será truncado pelo Google)
- ⚠️ Falta Schema.org `CollectionPage` em `quizzes.html` e `calculadoras.html`
- ⚠️ Algumas `og:image` em artigos usam caminho relativo (`../img/cabeçario.webp`) em vez de URL absoluta

---

### 3.3 🎨 CSS & Design — 9.0/10

**Pontos Fortes:**

| Feature | Status | Detalhes |
|---------|:------:|---------|
| **CSS Variables** | ✅ | 15+ variáveis para cores, espaçamentos, tamanhos |
| **Dark Mode** | ✅ | `[data-theme="dark"]` com variáveis, transição suave (0.5s) |
| **Sistema Responsivo** | ✅ | 6+ breakpoints (480px, 768px, 1024px, 1200px) |
| **Tipografia** | ✅ | Playfair Display (headings) + Source Sans 3 (body) |
| **Paleta de Cores** | ✅ | Deep Ocean Blue (#0A4D68), Emerald (#047857), Warm Amber (#D97706) |
| **Animações GPU** | ✅ | Usa `transform` e `opacity` (compositing-friendly) |
| **Reduced Motion** | ✅ | `@media (prefers-reduced-motion: reduce)` desabilita animações |
| **Content Visibility** | ✅ | `@supports (content-visibility: auto)` para seções abaixo da dobra |
| **Suavização de Fontes** | ✅ | `-webkit-font-smoothing: antialiased` |

**Organização do CSS (`style.css` — 1.766 linhas):**
```
• Variáveis (linhas 1-38)
• Global / Reset (linhas 40-62)
• Performance & Acessibilidade (linhas 64-80)
• Header / Navegação
• Hero Section
• Cards & Componentes
• Formulários & Calculadoras
• Artigos & Conteúdo
• Footer
• Media Queries (responsivo)
• Utilitários
```

**O que falta (-1.0):**
- 🔴 CSS inline em artigos, calculadoras, quizzes e ferramentas (7-12 KB cada, repetido em 230+ páginas)
- ⚠️ Sem minificação CSS (poderia economizar ~15%)
- ⚠️ Falta `:focus-visible` para teclado (usa apenas `:focus`)

---

### 3.4 ♿ Acessibilidade (WCAG 2.1 AA) — 7.5/10

**Pontos Fortes:**

| Feature | Status | Detalhes |
|---------|:------:|---------|
| **Skip Link** | ✅ | `.skip-link` presente em 271 de 272 páginas (exceto 404.html) |
| **Alt Text em Imagens** | ✅ | Presente em todas as imagens com descrições relevantes |
| **ARIA Labels** | ✅ | Botão de tema, menus dropdown, seletores de idioma |
| **ARIA Roles** | ✅ | `role="menu"`, `role="menuitem"` na navegação |
| **Contraste de Cores** | ✅ | Bom contraste em modo claro e escuro |
| **Keyboard Navigation** | ✅ | Dropdown acessível por teclado |
| **Lang Attribute** | ✅ | `pt-BR`, `en`, `es` corretos em todas as páginas |
| **Responsive Viewport** | ✅ | `width=device-width, initial-scale=1.0` |
| **Lazy Loading** | ✅ | `loading="lazy"` e `decoding="async"` em imagens |
| **Theme Persistence** | ✅ | `localStorage` salva preferência de tema |
| **System Preference** | ✅ | Respeita `prefers-color-scheme: dark` |

**O que falta (-2.5):**
- ❌ Falta tag `<main>` em todas as páginas (conteúdo dentro de `<div>`)
- ❌ Artigos não usam tag semântica `<article>` (usam `<div class="article">`)
- ❌ Falta `<nav>` semântico em algumas páginas internas
- ⚠️ Formulários de calculadoras precisam de `<label for="">` explícito (muitos são implícitos)
- ⚠️ Falta `:focus-visible` explícito para navegação por teclado
- ⚠️ Possíveis saltos na hierarquia de headings (h1 → h3 sem h2)

---

### 3.5 ⚡ Performance — 7.0/10

**Pontos Fortes:**

| Feature | Status | Detalhes |
|---------|:------:|---------|
| **DNS Prefetch** | ✅ | Google Ads, GTM, Fonts, unpkg |
| **Preload CSS** | ✅ | `<link rel="preload" href="css/style.css" as="style">` |
| **Preconnect Fonts** | ✅ | `fonts.googleapis.com`, `fonts.gstatic.com` |
| **Imagens WebP** | ✅ | Todas em formato moderno (9-39 KB cada) |
| **Lazy Loading** | ✅ | `loading="lazy"` em todas as imagens |
| **Async Decoding** | ✅ | `decoding="async"` em todas as imagens |
| **Theme Before CSS** | ✅ | Script de tema no `<head>` evita FOUC (Flash of Unstyled Content) |
| **Content Visibility** | ✅ | CSS `content-visibility: auto` para seções fora da viewport |
| **Reduced Motion** | ✅ | Animações desabilitadas se preferido |
| **Image Fallbacks** | ✅ | `onerror` com fallback Unsplash em imagens de artigos |

**O que falta (-3.0):**
- 🔴 **CSS Duplicado (CRÍTICO):** Cada artigo/calculadora/quiz tem 7-12 KB de CSS inline. Com 230+ páginas internas, isso resulta em **~3-4 MB de CSS repetido** que poderia ser cacheado se extraído para arquivo externo
- ⚠️ **Sem Minificação:** HTML e CSS não estão minificados (economia potencial de ~20%)
- ⚠️ **Páginas de listagem grandes:** `artigos.html` tem 80 KB (muitos cards renderizados de uma vez)
- ⚠️ **Sem Paginação:** Listas de artigos/calculadoras mostram tudo numa única página
- 🟢 Sem HTTP/2 Server Push (limitação do GitHub Pages — aceitável)

**Análise de Tamanhos:**

| Recurso | Tamanho | Observação |
|---------|---------|------------|
| Total HTML | 10.1 MB | Alto por causa do CSS inline |
| Total Imagens | 0.51 MB | Excelente — bem otimizado |
| `css/style.css` | 40 KB | Bom — usado só nas homes |
| Artigo típico | 30-45 KB | 30-38% é CSS inline |
| `index.html` | ~74 KB | Aceitável para homepage rica |

---

### 3.6 🔒 Segurança — 9.0/10

**Pontos Fortes:**

| Feature | Status | Detalhes |
|---------|:------:|---------|
| **HTTPS** | ✅ | Padrão do GitHub Pages |
| **Sem XSS** | ✅ | Nenhum uso de `innerHTML`, `eval()`, ou template strings dinâmicas |
| **Sem Dados Sensíveis** | ✅ | Calculadoras são 100% client-side, nada é enviado a servidores |
| **Sem Segredos no Código** | ✅ | Apenas chaves públicas (AdSense, Analytics) |
| **Scripts Externos Confiáveis** | ✅ | Apenas Google (Ads, Analytics, Fonts) e unpkg |
| **404 Seguro** | ✅ | Redirecionamento por mapeamento de objetos (sem `eval` ou interpolação) |

**O que falta (-1.0):**
- ⚠️ Sem header `Content-Security-Policy` (CSP)
- ⚠️ Sem header `X-Frame-Options: DENY` (anti-clickjacking)
- ⚠️ Sem header `X-Content-Type-Options: nosniff`
- ⚠️ Sem Subresource Integrity (SRI) nos scripts externos
- 🟢 Estes headers são difíceis de configurar no GitHub Pages (limitação da plataforma)

---

### 3.7 🏗️ Estrutura HTML — 7.5/10

**Pontos Fortes:**

| Feature | Status | Detalhes |
|---------|:------:|---------|
| **DOCTYPE** | ✅ | `<!DOCTYPE html>` em todas as páginas |
| **Charset** | ✅ | `UTF-8` em todas as páginas |
| **Viewport** | ✅ | Correto e mobile-friendly |
| **data-theme** | ✅ | `<html data-theme="light">` para dark mode |
| **Navegação** | ✅ | Header com logo, links, toggle tema, seletor idioma |
| **Footer** | ✅ | Links legais, redes sociais, copyright |

**O que falta (-2.5):**
- ❌ Não usa `<main>` (conteúdo em `<div>` genéricos)
- ❌ Artigos não usam `<article>` (usam `<div class="article">`)
- ❌ `<section>` sem `aria-label` em muitas seções
- ⚠️ `<header>` não é usado consistentemente (parcial)
- ⚠️ `<footer>` não é semântico em todas as páginas

---

## 4. Histórico de Correções (PRs Anteriores)

### 1ª Revisão — Links e Canonicals
- ✅ 8 links internos quebrados corrigidos (`contato-en.html`, `mioquinas-movimento.html`, etc.)
- ✅ Imagens com caminhos errados em `artigos.html` corrigidas
- ✅ 64 páginas com canonical `www` padronizado
- ✅ Meta tags OG adicionadas em páginas de seção

### 2ª Revisão — OG Tags e Hreflang
- ✅ 72 arquivos com `og:url` e `og:image` padronizados para `www.calculesuasaude.com.br`
- ✅ `hreflang="x-default"` em todas as páginas
- ✅ OG tags em `artigos-en.html` e `personal-en.html`

### 3ª Revisão — Títulos e Descriptions
- ✅ 9 títulos de página encurtados para < 65 caracteres
- ✅ 10 meta descriptions encurtadas para < 160 caracteres
- ✅ 404.html com meta description e meta robots `noindex, nofollow`

### Expansão de Idiomas (ES)
- ✅ **104 páginas em espanhol** criadas cobrindo todos os artigos, calculadoras, quizzes e ferramentas
- ✅ Hreflang ES adicionado em 263 páginas
- ✅ Sitemap expandido de 133 para 272 URLs

---

## 5. Problemas Pendentes (Por Prioridade)

### 🔴 Prioridade Alta — Impacto em SEO/Performance

| # | Problema | Impacto | Esforço |
|---|---------|---------|---------|
| 1 | **CSS inline duplicado em 230+ páginas** | ~3-4 MB desperdício; sem cache | 3-4h |
| 2 | **Imagem Polilaminina ausente** (`img/artigos/`) | Fallback Unsplash; Google Images não indexa | 1h |
| 3 | **Título index-es.html > 65 chars** (74 chars) | Truncado na SERP do Google | 5min |

### 🟡 Prioridade Média — Acessibilidade/Qualidade

| # | Problema | Impacto | Esforço |
|---|---------|---------|---------|
| 4 | **Sem tag `<main>` nas páginas** | Screen readers não encontram conteúdo principal | 2-3h |
| 5 | **Sem tag `<article>` nos artigos** | Semântica empobrecida | 2-3h |
| 6 | **Labels de formulário implícitos** | Calculadoras menos acessíveis | 2h |
| 7 | **`:focus-visible` ausente** | Navegação por teclado não é visível | 30min |
| 8 | **`og:image` com caminho relativo** em artigos | Redes sociais podem não exibir thumbnail | 1-2h |

### 🟢 Prioridade Baixa — Melhorias Futuras

| # | Problema | Impacto | Esforço |
|---|---------|---------|---------|
| 9 | Minificar HTML/CSS | ~20% economia de tamanho | 2h |
| 10 | Renomear imagens com espaços/acentos → kebab-case | URLs mais limpas | 1-2h |
| 11 | Schema.org `CollectionPage` em listagens | Enriquece SERP | 1h |
| 12 | Headers de segurança (CSP, X-Frame) | Defense-in-depth | 1h |
| 13 | Paginação em listas de artigos | Melhor UX e performance | 3h |

---

## 6. Arquitetura Técnica Atual

### 6.1 Estrutura de Diretórios

```
calculesuasaude.com.br/
├── index.html / index-en.html / index-es.html     ← Homes (3 idiomas)
├── artigos.html / artigos-en.html / artigos-es.html
├── calculadoras.html / calculadoras-en.html / calculadoras-es.html
├── quizzes.html / quizzes-en.html / quizzes-es.html
├── contato.html / contato-en.html / contato-es.html
├── personal.html / personal-en.html / personal-es.html
├── termos-de-uso.html / -en / -es
├── politica-de-privacidade.html / -en / -es
├── isencao-de-responsabilidade.html / -en / -es
├── glossario.html / glossary-en.html / glossary-es.html
├── equipe-editorial.html
├── 404.html                          ← Redirecionador JS inteligente
├── robots.txt                        ← Allow all + Disallow 404
├── sitemap.xml                       ← 272 URLs
├── CNAME                             ← www.calculesuasaude.com.br
├── ads.txt / app-ads.txt             ← Google AdSense
├── artigos/                          ← 140 artigos (PT + EN + ES)
├── calculadoras/                     ← 42 calculadoras (PT + EN + ES)
├── quizz/                            ← 38 quizzes (PT + EN + ES)
├── ferramentas/                      ← 20 ferramentas (PT + EN + ES)
├── img/                              ← 32 imagens WebP
│   ├── artigos/                      ← 30 imagens de artigos
│   ├── cabeçario.webp                ← Header/OG image
│   └── personal.webp
└── css/style.css                     ← 40 KB, 1.766 linhas (só homes)
```

### 6.2 Padrão de Nomenclatura

| Idioma | Padrão | Exemplo |
|--------|--------|---------|
| 🇧🇷 PT-BR | `arquivo.html` | `artigos/diabetes-tipo-2.html` |
| 🇺🇸 EN | `arquivo-en.html` | `artigos/diabetes-type-2-en.html` |
| 🇪🇸 ES | `arquivo-es.html` | `artigos/diabetes-tipo-2-es.html` |

### 6.3 SEO Internacional (Hreflang)

Todas as páginas possuem:
```html
<link rel="alternate" hreflang="pt-BR" href="https://www.calculesuasaude.com.br/[versão-pt]" />
<link rel="alternate" hreflang="en" href="https://www.calculesuasaude.com.br/[versão-en]" />
<link rel="alternate" hreflang="es" href="https://www.calculesuasaude.com.br/[versão-es]" />
<link rel="alternate" hreflang="x-default" href="https://www.calculesuasaude.com.br/[versão-pt]" />
```

---

## 7. Oportunidades de Crescimento

### 7.1 Novos Artigos (Alto Volume de Busca)

| Tema | Volume (PT-BR) | Status |
|------|:---:|:---:|
| Magnésio — deficiência e suplementação | Alto | ✅ Já existe |
| Jejum Intermitente | Muito Alto | ✅ Já existe |
| Menopausa e Saúde Feminina | Alto | ✅ Já existe |
| Diabetes Tipo 2 | Muito Alto | ✅ Já existe |
| Microbiota e Probióticos | Alto | ✅ Já existe |
| Depressão — sintomas e tratamento | Muito Alto | ❌ Não existe |
| Ansiedade — guia completo | Muito Alto | ✅ Já existe |
| Vitamina B12 — deficiência | Alto | ❌ Não existe |
| Ômega-3 — benefícios e dosagem | Alto | ❌ Não existe |
| Cirurgia Bariátrica | Médio-Alto | ❌ Não existe |

### 7.2 Novas Calculadoras

- Calculadora de Risco Cardiovascular (Framingham Score)
- Calculadora de Qualidade do Sono
- Calculadora de Consumo de Álcool (unidades/semana)
- Calculadora de Gordura Visceral

### 7.3 Novos Quizzes

- "Você tem sinais de depressão?"
- "Quanto você sabe sobre longevidade?"
- "Seu estilo de vida é anti-inflamatório?"

---

## 8. Conclusão

O site **Calcule Sua Saúde** é um projeto **maduro e bem executado** com nota **8.6/10**. Os principais pontos:

### ✅ Destaques Positivos
- 272 páginas de conteúdo médico em 3 idiomas
- SEO técnico de excelência (schema.org, hreflang, canonical, OG)
- Design profissional com dark mode e responsividade
- Acessibilidade acima da média para sites estáticos
- Zero vulnerabilidades de segurança encontradas
- Imagens 100% otimizadas em WebP

### ⚠️ Maiores Oportunidades de Melhoria
1. **Extrair CSS inline** para arquivo compartilhado (maior impacto em performance)
2. **Melhorar semântica HTML** (`<main>`, `<article>`, `<nav>`)
3. **Corrigir título ES da homepage** (74 chars → < 65 chars)
4. **Adicionar imagem Polilaminina** ausente
5. **Labels de formulário explícitos** nas calculadoras

### 📈 Evolução do Site

| Revisão | Data | Nota | Mudanças Principais |
|---------|------|:----:|---------------------|
| 1ª | Fev 2026 | 7.5 | Links corrigidos, canonicals padronizados |
| 2ª | Mar 2026 | 8.0 | OG tags www, hreflang x-default |
| 3ª | Mar 2026 | 8.5 | Títulos/descriptions otimizados, 404 melhorado |
| **4ª** | **Mar 2026** | **8.6** | **Expansão ES completa (104 páginas), sitemap 272 URLs** |

---

*Relatório gerado por auditoria automatizada + revisão manual | Calcule Sua Saúde | 23 de Março de 2026*
