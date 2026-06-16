# Scripts de Automação SEO - calculesuasaude.com.br

Este diretório contém scripts Python para resolver os 3 problemas principais do Google Search Console:

## 📋 Conteúdo

- **fix_sitemap_404s.py** - Missão 1: Limpar erros 404 do sitemap
- **generate_internal_links.py** - Missão 2: Resolver páginas órfãs
- **generate_seo_content.py** - Missão 3: Adicionar conteúdo SEO com IA

## 🚀 Quick Start

### Missão 1: Limpar Erros 404 do Sitemap (61 URLs)

```bash
# Fazer backup e remover URLs com 404 do sitemap
python scripts/fix_sitemap_404s.py --sitemap sitemap.xml --backup --verbose
```

**O que faz:**
- Lê o `sitemap.xml`
- Verifica se cada URL tem arquivo `.html` correspondente
- Remove URLs que apontam para arquivos deletados
- Salva o sitemap limpo
- Cria backup automático

**Saída esperada:**
```
📂 Lendo sitemap de: sitemap.xml
🔍 Encontradas 89 URLs no sitemap
Verificadas 89/89 URLs... ✓

🗑️  Removendo 61 URLs com 404...
   - https://calculesuasaude.com.br/calculadora-antiga1.html
   - https://calculesuasaude.com.br/calculadora-antiga2.html
   ...

✅ Sitemap salvo com sucesso!

📊 Resumo:
   Total de URLs originais: 89
   URLs removidas (404):    61
   URLs válidas:            28
```

---

### Missão 2: Gerar Links Internos (114 Páginas Órfãs)

```bash
# Gerar lista de links para o footer
python scripts/generate_internal_links.py --html-dir . --output links.html
```

**O que faz:**
- Lê todos os arquivos `.html`
- Extrai a tag `<title>` de cada um
- Gera um bloco HTML com lista `<ul>` de links
- Salva em `links.html`

**Próximos passos:**
1. Copie TODO o conteúdo de `links.html`
2. Abra seu `index.html`
3. Cole antes de `</body>` para que o Google rastreie todas as páginas
4. Commit, push, deploy
5. Submeta o sitemap no Google Search Console

**Resultado esperado em index.html:**
```html
<!-- ANTES DE FECHAR </body> -->

<!-- LINKS INTERNOS PARA RASTREAMENTO -->
<div class="internal-links-footer" style="...">
    <h3>Ferramentas e Calculadoras</h3>
    <ul>
        <li><a href="https://calculesuasaude.com.br/calculadora-imc.html">Calculadora de IMC</a></li>
        <li><a href="https://calculesuasaude.com.br/calculadora-peso.html">Calculadora de Peso Ideal</a></li>
        ...
    </ul>
</div>
<!-- FIM DOS LINKS INTERNOS -->

</body>
```

---

### Missão 3: Gerar Conteúdo SEO com IA (137 Páginas Thin Content)

**Pré-requisitos:**
```bash
# Instalar a biblioteca do Gemini
pip install google-generativeai
```

**Configurar API Key:**
```bash
# Linux/Mac
export GOOGLE_API_KEY="sua_chave_aqui"

# Windows (PowerShell)
$env:GOOGLE_API_KEY="sua_chave_aqui"
```

**Usar o script:**
```bash
# Processar um arquivo HTML
python scripts/generate_seo_content.py --input calculadora-imc.html --api-key sua_chave_aqui

# Processar múltiplos arquivos
python scripts/generate_seo_content.py --input calculadora-*.html --api-key sua_chave_aqui
```

**O que faz:**
- Lê o arquivo HTML
- Extrai o título da calculadora
- Pede ao Gemini para gerar 500 palavras de conteúdo SEO
- Injeta após `<form>` ou antes de `</body>`
- Salva o arquivo modificado

---

## 📊 Resumo dos Problemas e Soluções

| Problema | Causa | Solução | Script |
|----------|-------|--------|--------|
| **404s no Sitemap** (61 URLs) | Arquivos deletados mas ainda no sitemap | Remover URLs inválidas do sitemap.xml | `fix_sitemap_404s.py` |
| **Detectada, mas não indexada** (114 URLs) | Páginas sem links internos apontando para elas | Adicionar links no footer do index.html | `generate_internal_links.py` |
| **Rastreada, mas não indexada** (137 URLs) | Pouco conteúdo (thin content) | Gerar conteúdo SEO com Gemini | `generate_seo_content.py` |

---

## ⚙️ Dependências

Python 3.7+

Para Missão 3:
```bash
pip install google-generativeai
```

---

## 💡 Tips de Uso

### Teste antes de fazer mudanças reais
```bash
# Dry run (não salva mudanças)
python scripts/fix_sitemap_404s.py --html-dir . --verbose
```

### Sempre faça backup
```bash
# Com backup automático
python scripts/fix_sitemap_404s.py --backup
```

### Verifique antes de dar deploy
1. Rode o script local
2. Abra o arquivo gerado e verifique
3. Commit no GitHub
4. Deploy para produção
5. Teste a URL da calculadora no browser
6. Submeta para rastrear no GSC

---

## 🐛 Troubleshooting

**Erro: "Arquivo sitemap.xml não encontrado"**
```bash
# Verifique se o arquivo existe
ls sitemap.xml

# Se estiver em outro lugar, especifique o caminho
python scripts/fix_sitemap_404s.py --sitemap /caminho/para/sitemap.xml
```

**Erro: "Diretório não encontrado"**
```bash
# Verifique o caminho
ls -la

# Execute no diretório raiz do projeto
python scripts/generate_internal_links.py --html-dir . --output links.html
```

**Script rodando muito lento**
- Pode ser normal se há muitos arquivos
- Use `--verbose` para ver o progresso
- Se ficar muito lento, pode ter um arquivo muito grande causando problema

---

## 📞 Suporte

Para dúvidas:
1. Verifique se Python 3.7+ está instalado: `python --version`
2. Teste com `--verbose` para mais detalhes
3. Verifique os logs de erro

---

**Criado em:** 2026-06-16
**Versão:** 1.0
**Manutentor:** @thiagoevanio
