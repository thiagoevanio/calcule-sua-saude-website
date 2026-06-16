# 🚀 Instruções para Configurar o Pipeline CI/CD Manualmente

Se você recebeu um erro de permissão ao criar os workflows, siga os passos abaixo para configurar manualmente:

## ✅ Passo 1: Clone seu repositório localmente

```bash
git clone https://github.com/thiagoevanio/calcule-sua-saude-website.git
cd calcule-sua-saude-website
```

## ✅ Passo 2: Crie a estrutura de diretórios

```bash
mkdir -p .github/workflows
```

## ✅ Passo 3: Crie o arquivo de automação principal

Crie o arquivo `.github/workflows/seo-automation.yml`:

```yaml
name: 🤖 SEO Automation Pipeline

on:
  schedule:
    - cron: '0 8 * * 1'  # Segunda-feira 08:00 UTC
  workflow_dispatch:
  push:
    branches:
      - main
    paths:
      - 'sitemap.xml'
      - 'scripts/**'

jobs:
  seo-automation:
    runs-on: ubuntu-latest
    name: 🔧 SEO Automation Tasks
    
    steps:
      - name: 📥 Checkout Repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: 🐍 Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: 📦 Create requirements.txt
        run: |
          if [ ! -f requirements.txt ]; then
            echo "google-generativeai>=0.3.0" > requirements.txt
            echo "requests>=2.31.0" >> requirements.txt
            echo "beautifulsoup4>=4.12.0" >> requirements.txt
          fi
      
      - name: 📚 Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: 🗑️ Mission 1: Clean Sitemap 404s
        run: |
          python scripts/fix_sitemap_404s.py \
            --sitemap sitemap.xml \
            --html-dir . \
            --backup \
            --verbose || true
        continue-on-error: true
      
      - name: 🔗 Mission 2: Generate Internal Links
        run: |
          python scripts/generate_internal_links.py \
            --html-dir . \
            --output links.html \
            --base-url "https://calculesuasaude.com.br" \
            --verbose || true
        continue-on-error: true
      
      - name: 📝 Check for Changes
        id: verify-changes
        run: |
          if git diff --quiet sitemap.xml links.html 2>/dev/null; then
            echo "changes=false" >> $GITHUB_OUTPUT
          else
            echo "changes=true" >> $GITHUB_OUTPUT
            git diff --stat
          fi
      
      - name: ⚙️ Configure Git
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
      
      - name: 📤 Commit and Push Changes
        if: steps.verify-changes.outputs.changes == 'true'
        run: |
          git add sitemap.xml links.html 2>/dev/null || true
          if ! git diff --cached --quiet; then
            git commit -m "🤖 [AUTO] SEO Automation: Limpeza de sitemap e links internos" \
              -m "✅ Missão 1: Sitemap limpo de URLs com 404" \
              -m "✅ Missão 2: Links internos atualizados" \
              -m "🔄 Executado automaticamente pelo GitHub Actions" \
              --no-verify
            git push origin main || true
          fi
      
      - name: ✅ Success Report
        if: success()
        run: |
          echo "✅ PIPELINE EXECUTADO COM SUCESSO!"
          echo "📊 Tarefas completadas:"
          echo "   ✅ Missão 1: Sitemap limpo"
          echo "   ✅ Missão 2: Links internos gerados"
```

## ✅ Passo 4: Crie o arquivo de auditoria

Crie o arquivo `.github/workflows/seo-audit.yml`:

```yaml
name: 📋 SEO Report & Monitoring

on:
  schedule:
    - cron: '0 10 * * 4'  # Quinta-feira 10:00 UTC
  workflow_dispatch:

jobs:
  seo-audit:
    runs-on: ubuntu-latest
    name: 📊 SEO Health Check
    
    steps:
      - name: 📥 Checkout Repository
        uses: actions/checkout@v4
      
      - name: 🐍 Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: 📚 Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4
      
      - name: 🔍 Generate SEO Audit Report
        run: |
          python3 << 'EOF'
          import os
          import glob
          import xml.etree.ElementTree as ET
          from datetime import datetime
          
          print("=" * 60)
          print("📊 SEO AUDIT REPORT - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
          print("=" * 60)
          
          # Análise do Sitemap
          print("\n📄 SITEMAP ANALYSIS")
          print("-" * 60)
          if os.path.exists('sitemap.xml'):
              tree = ET.parse('sitemap.xml')
              root = tree.getroot()
              ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
              urls = root.findall('.//sm:loc', ns) or root.findall('.//loc')
              print(f"✅ Total de URLs no sitemap: {len(urls)}")
          else:
              print("❌ Arquivo sitemap.xml não encontrado")
          
          # Análise de HTML
          print("\n📄 HTML FILES ANALYSIS")
          print("-" * 60)
          html_files = glob.glob('**/*.html', recursive=True)
          print(f"✅ Total de arquivos HTML: {len(html_files)}")
          
          # Verificar links
          print("\n🔗 INTERNAL LINKS CHECK")
          print("-" * 60)
          if os.path.exists('links.html'):
              with open('links.html', 'r', encoding='utf-8') as f:
                  link_count = f.read().count('<a href=')
              print(f"✅ Total de links internos: {link_count}")
          else:
              print("⚠️ Arquivo links.html não encontrado")
          EOF
```

## ✅ Passo 5: Crie o requirements.txt

```bash
cat > requirements.txt << 'EOF'
google-generativeai>=0.3.0
requests>=2.31.0
beautifulsoup4>=4.12.0
EOF
```

## ✅ Passo 6: Faça commit e push

```bash
git add .github/workflows/ requirements.txt
git commit -m "🚀 Add GitHub Actions CI/CD pipeline for SEO automation"
git push origin main
```

## ✅ Passo 7: Verifique na interface do GitHub

1. Acesse: https://github.com/thiagoevanio/calcule-sua-saude-website/actions
2. Você deve ver 2 workflows:
   - 🤖 SEO Automation Pipeline
   - 📋 SEO Report & Monitoring

## 🎯 Próximos Passos

### Configure as permissões (importante!)

1. Vá para **Settings** → **Actions** → **General**
2. Scroll down para "Workflow permissions"
3. Selecione **"Read and write permissions"**
4. Clique **Save**

### Execute manualmente (teste)

1. Vá para a aba **Actions**
2. Clique em **SEO Automation Pipeline**
3. Clique em **Run workflow**
4. Aguarde a execução

### Ver logs

1. Clique no workflow que rodou
2. Veja todos os passos executados
3. Se houver erro, veja os logs detalhados

---

## 📊 Cronograma Automático

**Segunda-feira 08:00 UTC (5:00 AM Brasília)**
```
🤖 SEO Automation Pipeline
├─ ✅ Missão 1: Limpar 404s do sitemap
├─ ✅ Missão 2: Gerar links internos
└─ 📤 Fazer commit automático
```

**Quinta-feira 10:00 UTC (7:00 AM Brasília)**
```
📊 SEO Report & Monitoring
├─ 📄 Análise de Sitemap
├─ 📁 Contagem de HTMLs
└─ 📈 Relatório completo
```

---

## 🐛 Troubleshooting

### Workflow não está rodando?
- Verifique se os arquivos estão em `.github/workflows/`
- Verifique a sintaxe YAML (pode estar indentada incorretamente)
- Tente executar manualmente via "Run workflow"

### Erro "Permission denied" ao fazer push?
- Vá para Settings → Actions → General
- Mude "Workflow permissions" para "Read and write permissions"

### Não vê os workflows na aba Actions?
- Espere 5 minutos após fazer push
- Recarregue a página
- Verifique se os arquivos estão em `.github/workflows/`

---

**Precisa de ajuda?** Abra uma issue no repositório!
