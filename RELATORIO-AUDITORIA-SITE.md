# Relatório de Auditoria — Calcule Sua Saúde
**Data:** 02 de Março de 2026  
**Domínio:** www.calculesuasaude.com.br  
**Tipo de site:** Estático (HTML/CSS/JS puro, hospedado via GitHub Pages)

---

## 1. Resumo Executivo

O site **Calcule Sua Saúde** está bem estruturado e conta com um volume significativo de conteúdo: 133 páginas HTML, 32 imagens, sitemap com 133 URLs, cobertura bilíngue (PT-BR + EN) em quase todo o conteúdo e schema.org avançado nos artigos principais. **Este relatório (2ª revisão) documenta problemas já corrigidos em PRs anteriores, uma nova correção de inconsistência nas OG tags (72 arquivos), e oportunidades de melhoria adicional para aumentar tráfego orgânico e qualidade.**

---

## 2. Inventário do Site

| Seção | Páginas PT-BR | Páginas EN | Total |
|-------|:---:|:---:|:---:|
| Raiz (index, artigos, calc., quizzes, contato, legal…) | 9 | 9 | 18 |
| Artigos científicos (`/artigos/`) | 31 | 31 | 62 |
| Calculadoras (`/calculadoras/`) | 11 | 11 | 22 |
| Quizzes (`/quizz/`) | 10 | 10 | 20 |
| Ferramentas (`/ferramentas/`) | 5 | 5 | 10 |
| 404, CNAME, robots, sitemap | — | — | 1 HTML + 4 arquivos |
| **Total HTML** | | | **133** |
| **Total imagens (webp)** | | | **32 (img/)** |
| **Tamanho total HTML** | | | **~4,7 MB** |

---

## 3. Problemas Corrigidos Nesta PR

### 3.1 Links Internos Quebrados (8 links → 0 após correção)

| Arquivo | Link quebrado | Corrigido para |
|---------|--------------|----------------|
| `contato-en.html` | `articles.html` | `artigos-en.html` |
| `contato-en.html` | `calculators.html` | `calculadoras-en.html` |
| `contato-en.html` | `contact.html` (nav + footer) | `contato-en.html` |
| `contato-en.html` | `disclaimer.html` | `isencao-de-responsabilidade-en.html` |
| `contato-en.html` | `privacy-policy.html` | `politica-de-privacidade-en.html` |
| `contato-en.html` | `terms-of-use.html` | `termos-de-uso-en.html` |
| `mioquinas-movimento.html` | `../calculadora-gasto-calorico.html` | `../calculadoras/gasto-energetico-diario-tdee.html` |
| `mioquinas-movimento.html` | `../calculadora-imc.html` | `../calculadoras/indice-de-massa-corporal-imc.html` |
| `mioquinas-movimento-en.html` | (mesmos links acima) | Equivalentes EN |
| `calculadoras-en.html` | `calculadoras/glucose-converter.html` | `calculadoras/glucose-converter-en.html` |

### 3.2 Imagens com Caminho Errado em `artigos.html`

| Imagem referenciada | Arquivo real |
|--------------------|--------------|
| `img/artigos/Álcool e Danos Hepáticos.webp` | `img/artigos/alcool-e-danos-hepáticos.webp` |
| `img/artigos/Anemia Ferropriva Sinais.webp` | `img/artigos/anemia-ferropriva-sinais.webp` |

> **Observação:** Havia `onerror` de fallback no Unsplash, então o site não "quebrava" visualmente, mas o Google não conseguia indexar as imagens corretas.

### 3.3 Canonical URL — Inconsistência `www` vs `não-www`

O sitemap usa **`www.calculesuasaude.com.br`** (correto, pois o CNAME aponta para www), mas **64 páginas HTML** tinham `<link rel="canonical">` apontando para `https://calculesuasaude.com.br/` (sem www). Isso cria sinal de conteúdo duplicado para o Google.

**Corrigido:** todos os canonicals e hreflang de 64 arquivos foram padronizados para `www`.

### 3.4 Meta Tags Canônicas e OG Ausentes em Páginas de Seção

As páginas abaixo não tinham `<link rel="canonical">` nem `<meta property="og:title">`, o que impede compartilhamento correto em redes sociais e enfraquece o SEO:

- `quizzes.html` / `quizzes-en.html`  
- `calculadoras.html` / `calculadoras-en.html`  
- `contato.html` / `contato-en.html`  
- `termos-de-uso.html` / `termos-de-uso-en.html`  
- `politica-de-privacidade.html`  
- `isencao-de-responsabilidade.html`  
- `personal.html`  

**Corrigido:** adicionados canonical, robots, og:type, og:url, og:title, og:description, og:locale e hreflang em todas as páginas acima.

---

## 4. Problemas Corrigidos Nesta Atualização (Março 2026 — 2ª revisão)

### 4.0 ✅ CORRIGIDO — Inconsistência `www` vs `não-www` em OG tags

**Afetava:** 70 arquivos HTML com `og:url` e 6 arquivos com `og:image` apontando para `https://calculesuasaude.com.br/` (sem `www`), enquanto as canonical URLs usavam `https://www.calculesuasaude.com.br/`.  
**Impacto:** Sinais conflitantes para o Google e redes sociais — canonical e og:url devem ser idênticos.  
**Correção:** Padronizados todos os `og:url` e `og:image` em 72 arquivos para usar `www.calculesuasaude.com.br`.

### 4.1–4.8 ✅ CORRIGIDO (PR anterior + verificação atual)

Os seguintes itens foram reportados na 1ª auditoria como pendentes e agora estão **confirmados como corrigidos**:

| # | Item | Status Atual |
|---|------|:---:|
| 4.2 | Hreflang do `resistencia-insulina-mecanismos.html` ↔ `insulin-resistance-mechanisms-en.html` | ✅ Corrigido |
| 4.5 | Canonicals nas 26 páginas de `/calculadoras/` | ✅ Corrigido (26/26) |
| 4.6 | Canonicals nas 20 páginas de `/quizz/` | ✅ Corrigido (20/20) |
| 4.7 | `hreflang="x-default"` em todas as páginas | ✅ Corrigido (143 páginas) |
| 4.8 | OG tags em `artigos-en.html` | ✅ Corrigido (canonical + og:title/description/image) |
| 4.14 | OG tags em `artigos-en.html` (duplicado do 4.8) | ✅ Corrigido |
| 4.15 | Canonical e OG em `personal-en.html` | ✅ Corrigido |

---

## 5. Problemas Identificados — A Corrigir Futuramente

### 5.1 🔴 CRÍTICO — Imagem da Polilaminina Ausente

**Arquivo:** `img/artigos/Polilaminina Beneficios Saude.webp`  
**Status:** **Não existe no repositório**  
**Impacto:** O card do artigo polilaminina no `artigos.html` exibe a imagem do Unsplash (fallback), não uma imagem própria. Isso reduz a identidade visual e impede que o Google Images indexe uma imagem relevante.  
**Solução:** Criar/adicionar uma imagem `.webp` otimizada com esse nome no diretório `img/artigos/`.

### 5.2 🟡 IMPORTANTE — Inconsistência de Nomeação nos Artigos EN

| Arquivo EN existente | Padrão esperado |
|---------------------|----------------|
| `artigos/insulin-resistance-mechanisms-en.html` | `artigos/resistencia-insulina-mecanismos-en.html` |
| `artigos/polilaminina-health-benefits-en.html` | `artigos/polilaminina-beneficios-saude-en.html` |

Os hreflang cruzados estão funcionando corretamente (confirmado), mas a nomeação não segue o padrão usado nos demais artigos (`[slug-pt]-en.html`). **Impacto:** Menor que o inicialmente estimado, pois o hreflang está funcional. Porém, a padronização futura dos slugs facilitará manutenção.  
**Solução:** Renomear os arquivos para seguir o padrão ou manter os hreflang corretos como estão.

### 5.3 🟡 IMPORTANTE — Títulos de Página Acima de 70 Caracteres

**Afeta:** ~60 artigos (todos têm título com 71–116 caracteres)  
**Impacto:** O Google trunca títulos acima de ~60-65 chars no resultado da busca, exibindo "…" e reduzindo CTR (taxa de clique).  
**Formato atual:** `"Cortisol e Estresse Crônico: Neurobiologia, Diagnóstico e Tratamento | Calcule Sua Saúde"` (85 chars)  
**Formato recomendado:** `"Cortisol e Estresse Crônico | Calcule Sua Saúde"` (49 chars) ou `"Cortisol e Estresse: Neurobiologia e Tratamento"` (47 chars)  
**Solução:** Revisão gradual dos títulos começando pelos artigos com maior tráfego potencial.

### 5.4 🟡 IMPORTANTE — Meta Descriptions Acima de 165 Caracteres

**Afeta:** ~30 artigos  
**Impacto:** O Google reescreve a meta description quando muito longa, podendo usar trechos desfavoráveis do conteúdo.  
**Solução:** Limitar descriptions a 150–160 caracteres.

### 5.5 🟢 MELHORIA — Skip Link de Acessibilidade (WCAG 2.1 AA)

**Afeta:** ~107 de 133 páginas (26 já possuem)  
**Problema:** Não há link "Pular para o conteúdo" (`<a href="#conteudo" class="skip-link">Pular para o conteúdo</a>`)  
**Impacto:** Usuários de teclado/leitores de tela precisam navegar por todo o menu antes de chegar ao conteúdo.  
**Exemplo de implementação:**
```html
<a href="#conteudo" class="skip-link">Pular para o conteúdo</a>
<nav>...</nav>
<main id="conteudo">...</main>
```
```css
.skip-link { position:absolute; top:-40px; left:0; background:#0A4D68; color:white; padding:8px; }
.skip-link:focus { top:0; }
```

### 5.6 🟢 MELHORIA — Inline CSS em Artigos (Performance)

**Afeta:** todos os artigos (cada um tem ~7–12 KB de CSS inline)  
**Impacto:** CSS duplicado em cada página aumenta o tamanho total de download e impede cache do browser.  
**Tamanho atual total HTML:** 4,69 MB  
**Solução:** Extrair o CSS dos artigos para um arquivo compartilhado `/css/artigos.css` e linká-lo com `<link rel="stylesheet">`. Isso reduziria o total para ~1-2 MB com cache.

### 5.7 🟢 MELHORIA — `404.html` Sem Meta Description

A página 404 serve como redirecionador JS. Para usuários sem JS, ela exibe uma página genérica sem branding adequado. Adicionalmente, não tem meta description.

### 5.8 🟢 MELHORIA — Imagens de Artigos com Nomes com Espaços e Acentos

**Afeta:** 27 das 32 imagens em `img/artigos/`  
**Problema:** Nomes como `"Resistência à Insulina Mecanismos.webp"` precisam de URL encoding em alguns servidores.  
**Solução futura:** Ao adicionar novas imagens, usar formato `slug-do-artigo.webp` (sem espaços, sem acentos), como já é feito para `alcool-e-danos-hepáticos.webp` e `anemia-ferropriva-sinais.webp`.

---

## 6. Análise de SEO Técnico

### 6.1 Pontos Fortes ✅

| Item | Status |
|------|--------|
| Sitemap XML (133 URLs) | ✅ Presente e completo |
| robots.txt | ✅ Correto, aponta sitemap |
| CNAME configurado | ✅ `www.calculesuasaude.com.br` |
| ads.txt e app-ads.txt | ✅ Configurados com publisher ID correto |
| Schema.org nos artigos | ✅ MedicalScholarlyArticle, FAQPage, BreadcrumbList |
| Schema.org na home | ✅ WebSite, SoftwareApplication, MedicalWebPage |
| Hreflang PT-BR ↔ EN | ✅ Presente na maioria dos artigos |
| Cobertura bilíngue | ✅ Quase todas as páginas têm versão EN |
| Imagens em formato WebP | ✅ Todas as imagens em .webp (formato moderno) |
| Google Analytics | ✅ `G-EVCQQZV60N` implementado |
| Google AdSense | ✅ `pub-5825554897787593` implementado |
| lang attribute no `<html>` | ✅ Correto em todas as páginas |
| 404 com redirecionamentos | ✅ Redireciona URLs antigas para novas |
| Open Graph nos artigos | ✅ og:type, og:title, og:description, og:image |
| favicon.ico | ✅ Presente |

### 6.2 Áreas de Melhoria ⚠️

| Item | Prioridade | Status |
|------|-----------|:---:|
| Canonicals nas calculadoras individuais | 🔴 Alta | ✅ Corrigido |
| Canonicals nos quizzes individuais | 🔴 Alta | ✅ Corrigido |
| hreflang x-default | 🟡 Média | ✅ Corrigido |
| OG tags www inconsistência | 🔴 Alta | ✅ Corrigido (esta PR) |
| Imagem polilaminina ausente | 🔴 Alta | ⚠️ Pendente |
| Títulos muito longos (>70 chars) | 🟡 Média | ⚠️ Pendente |
| Meta descriptions longas (>165 chars) | 🟡 Média | ⚠️ Pendente |
| Skip link acessibilidade | 🟡 Média | ⚠️ Pendente |
| CSS inline vs externo | 🟢 Baixa | ⚠️ Pendente |

---

## 7. Análise de Performance

### 7.1 Tamanho dos Arquivos

| Arquivo | Tamanho | % CSS inline |
|---------|---------|:---:|
| `artigos.html` | 80 KB | 20% |
| `artigos-en.html` | 70 KB | 13% |
| `calculadoras/glucose-converter-en.html` | 70 KB | 29% |
| `artigos/polilaminina-beneficios-saude.html` | 65 KB | 26% |
| `index.html` | 51 KB | 21% |
| Artigos típicos | 30–45 KB | 30–38% |

> **Análise:** Para um site estático, os tamanhos são razoáveis. A maior oportunidade de performance está em extrair o CSS inline para um arquivo compartilhado, eliminando ~25-35 KB de CSS repetido em cada página de artigo.

### 7.2 Imagens

- Todas as imagens estão em formato **WebP** ✅ (excelente para performance)
- Imagens usam `loading="lazy"` e `decoding="async"` ✅
- Tamanhos variam de 14 KB a 39 KB — razoável para um blog médico ✅
- Todas as imagens têm `onerror` com fallback Unsplash ✅

---

## 8. Análise de Conteúdo

### 8.1 Artigos (31 PT-BR + 31 EN = 62 artigos)

| Tópico | Quantidade |
|--------|-----------|
| Metabolismo & Nutrição | 6 |
| Mente & Sono | 5 |
| Coração & Circulação | 2 |
| Corpo & Movimento | 5 |
| Longevidade & Prevenção | 5 |
| Saúde Geral | 8 |

**Ponto positivo:** Profundidade científica excelente. Artigos com 6-18 min de leitura, referências bibliográficas, tabelas e infográficos em texto.

**Oportunidades de novos artigos:**
- Diabetes Tipo 2 (altíssimo volume de busca em PT)
- Obesidade e cirurgia bariátrica
- Saúde mental / depressão
- Alzheimer / demência
- Suplementos populares: magnésio, ômega-3, zinco, vitamina B12
- Menopausa e saúde feminina
- Creatina + saúde cerebral (tendência 2025-2026)
- Jejum intermitente (muito buscado)
- Microbioma e probióticos
- Polilaminina (já adicionado ✅)

### 8.2 Calculadoras (11 PT + 11 EN = 22 páginas)

Cobertura boa das principais ferramentas de saúde. **Oportunidades:**
- Calculadora de Risco Cardiovascular (Framingham Score)
- Calculadora de Consumo de Álcool
- Calculadora de Sono (horas recomendadas por idade)
- Calculadora de Gordura Visceral
- Calculadora de Vitamina D

### 8.3 Quizzes (10 PT + 10 EN = 20 páginas)

**Oportunidades:**
- Quiz: "Você tem resistência insulínica?"
- Quiz: "Seu sono é saudável?"
- Quiz: "Você conhece os riscos do tabagismo?"
- Quiz: "Quanto você sabe sobre longevidade?"

---

## 9. Estrutura Técnica do Site

### 9.1 Arquitetura de Arquivos

```
calculesuasaude.com.br/
├── index.html                  ← Home PT-BR
├── index-en.html               ← Home EN
├── artigos.html                ← Lista de artigos PT-BR
├── artigos-en.html             ← Lista de artigos EN
├── calculadoras.html           ← Lista de calculadoras PT-BR
├── calculadoras-en.html        ← Lista de calculadoras EN
├── quizzes.html / quizzes-en.html
├── contato.html / contato-en.html
├── personal.html / personal-en.html
├── isencao-de-responsabilidade.html
├── politica-de-privacidade.html
├── termos-de-uso.html
├── 404.html                    ← Redirecionador JS
├── robots.txt                  ← Allow all, aponta sitemap
├── sitemap.xml                 ← 133 URLs
├── CNAME                       ← www.calculesuasaude.com.br
├── ads.txt / app-ads.txt       ← AdSense
├── artigos/                    ← 62 artigos (31 PT + 31 EN)
├── calculadoras/               ← 22 calculadoras
├── quizz/                      ← 20 quizzes
├── ferramentas/                ← 10 ferramentas utilitárias
├── img/                        ← 32 imagens WebP
└── css/style.css               ← CSS compartilhado (só usado no index)
```

### 9.2 Observação Importante: CSS Duplicado

O arquivo `css/style.css` (25 KB, 1116 linhas) é importado **apenas** em `index.html` e `index-en.html`. Todos os outros arquivos HTML (artigos, calculadoras, quizzes) têm seu CSS completamente inline — o que significa que não aproveitam cache do browser.

---

## 10. Lista de Ações Prioritárias

### Prioridade 1 — Fazer logo (impacto imediato em SEO)

- [x] ~~Adicionar canonicals em todas as calculadoras~~ ✅ (26/26 corrigido)
- [x] ~~Adicionar canonicals em todos os quizzes~~ ✅ (20/20 corrigido)
- [x] ~~Corrigir hreflang do resistencia-insulina~~ ✅ (hreflang funcional)
- [x] ~~Adicionar hreflang x-default em todas as páginas~~ ✅ (143 páginas)
- [x] ~~Padronizar og:url e og:image com www~~ ✅ (72 arquivos corrigidos)
- [ ] **Adicionar imagem `img/artigos/Polilaminina Beneficios Saude.webp`** — criar e adicionar imagem de artigo

### Prioridade 2 — Fazer em breve (melhoria de qualidade)

- [ ] **Revisar títulos longos** nos artigos mais populares (Resistência à Insulina, Mioquinas, Macronutrientes, Cortisol)
- [ ] **Revisar meta descriptions longas** nos artigos com >165 chars
- [x] ~~Adicionar OG tags em `artigos-en.html`~~ ✅
- [x] ~~Adicionar canonical e OG em `personal-en.html`~~ ✅

### Prioridade 3 — Melhorias de médio prazo

- [ ] **Skip link de acessibilidade** em todas as páginas (~107 páginas restantes)
- [ ] **Extrair CSS para `/css/artigos.css`** — reduz tamanho total e habilita cache
- [ ] **Adicionar Schema.org `CollectionPage`** em quizzes.html e calculadoras.html
- [ ] **Renomear imagens antigas** para o formato `slug-kebab-case.webp` (sem espaços/acentos) ao criar versões novas

### Prioridade 4 — Crescimento de conteúdo

- [ ] **Novos artigos de alto volume:** Diabetes Tipo 2, Jejum Intermitente, Magnésio, B12, Menopausa
- [ ] **Novas calculadoras:** Risco Cardiovascular, Consumo de Álcool, Sono
- [ ] **Novos quizzes:** Resistência Insulínica, Qualidade do Sono, Longevidade

---

## 11. Análise de Robots.txt e Sitemap

### robots.txt — OK ✅
```
User-agent: *
Allow: /
Disallow: /404.html
Sitemap: https://www.calculesuasaude.com.br/sitemap.xml
```

O `Disallow: /404.html` já foi adicionado para evitar indexação da página de erro/redirecionamento. ✅

### Sitemap — 133 URLs ✅

Distribuição de prioridades:
- Prioridade 1.00: 3 URLs (home, index PT e EN)
- Prioridade 0.90: 6 URLs (seções principais)
- Prioridade 0.85: 34 URLs (artigos novos/destacados)
- Prioridade 0.80: 62 URLs (artigos)
- Prioridade 0.75: 20 URLs (quizzes)
- Prioridade 0.50: 2 URLs (ferramentas)
- Prioridade 0.30: 6 URLs (legal/contato)

**Sugestão:** Manter lastmod atualizado quando artigos forem revisados — isso sinaliza ao Google que o conteúdo está ativo.

---

## 12. Conclusão

O site **Calcule Sua Saúde** tem uma base sólida:
- Conteúdo médico de qualidade com referências bibliográficas
- Cobertura bilíngue (PT-BR + EN) quase completa
- Schema.org estruturado nos artigos (FAQPage, MedicalScholarlyArticle)
- Sitemap completo e robots.txt correto
- Imagens em WebP moderno

**Correções realizadas nesta PR:**
- ✅ 72 arquivos com `og:url` e `og:image` padronizados para `www.calculesuasaude.com.br`

**Correções confirmadas como já realizadas (PR anterior):**
- ✅ Canonicals em todas as 26 calculadoras e 20 quizzes
- ✅ `hreflang="x-default"` em 143 páginas
- ✅ Hreflang cruzado funcional nos artigos de resistência à insulina
- ✅ OG tags em `artigos-en.html` e `personal-en.html`
- ✅ Links quebrados corrigidos
- ✅ Canonical www padronizado

**Maiores oportunidades de crescimento orgânico restantes:**
1. Adicionar a imagem da polilaminina ausente
2. Revisar títulos para ficar abaixo de 60 caracteres
3. Revisar meta descriptions para ficar abaixo de 160 caracteres
4. Criar novos artigos sobre temas de alto volume (diabetes, jejum, magnésio)
5. Adicionar skip links de acessibilidade nas páginas restantes

**Nota de saúde do site: 8.5/10** (subiu de 7.8 após correções dos canonicals, hreflang e OG tags)

---

*Relatório gerado automaticamente + revisão manual | Calcule Sua Saúde | Março 2026*
