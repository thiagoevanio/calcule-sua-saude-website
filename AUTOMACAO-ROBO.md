# 🤖 Robô de Artigo Diário — Guia de Configuração

Este repositório já vem com um robô que **publica 1 artigo novo por dia**, sozinho,
usando a **API da Gemini** (Google) e o **GitHub Actions**. Quando o artigo é gerado,
ele é salvo, aparece na página de artigos, entra no `sitemap.xml` e é enviado pro ar
automaticamente (o GitHub Pages republica o site a cada push).

Você só precisa fazer **3 configurações uma única vez**. Leva ~5 minutos.

---

## ✅ Passo 1 — Pegar a chave da Gemini (grátis)

1. Acesse **https://aistudio.google.com/app/apikey**
2. Faça login com sua conta Google.
3. Clique em **"Create API key"** e **copie** a chave (algo como `AIza...`).

> A Gemini tem um nível gratuito generoso. 1 artigo por dia fica tranquilamente dentro dele.

---

## ✅ Passo 2 — Guardar a chave no GitHub (em segredo)

1. No GitHub, abra o seu repositório do site.
2. Vá em **Settings** → **Secrets and variables** → **Actions**.
3. Clique em **"New repository secret"**.
4. Em **Name**, escreva exatamente: `GEMINI_API_KEY`
5. Em **Secret**, cole a chave que você copiou. Salve.

> A chave fica criptografada. Ninguém consegue vê-la, nem você depois de salvar.

---

## ✅ Passo 3 — Deixar o robô escrever no repositório

1. Ainda em **Settings**, vá em **Actions** → **General**.
2. Role até **"Workflow permissions"**.
3. Marque **"Read and write permissions"** e salve.

Pronto. A partir daí o robô roda **todo dia às 09:00 UTC (~06:00 de Brasília)**.

---

## 🚀 Testar agora (sem esperar o dia seguinte)

1. No GitHub, abra a aba **Actions**.
2. Clique no workflow **"📝 Artigo Diário (Gemini)"**.
3. Clique em **"Run workflow"** (botão à direita).
   - Pode deixar o campo de tema **vazio** (ele usa a fila) ou escrever um tema.
4. Aguarde ~1 minuto. Um novo artigo aparece em `artigos/` e na página **Artigos**.

---

## 🗂️ Como escolher os temas — `content/topics.json`

O robô pega o **primeiro tema da fila** (`queue`) que esteja como `"status": "pending"`.
Depois de publicar, ele move o tema para `published` e segue para o próximo no dia seguinte.

Para adicionar temas, edite `content/topics.json` e inclua novos itens na lista `queue`:

```json
{ "theme": "Seu novo tema de saúde aqui", "category_hint": "Nutrição Clínica", "status": "pending" }
```

- `theme` — o assunto do artigo (quanto mais específico, melhor).
- `category_hint` — opcional; ajuda a IA a escolher a editoria.
- **Se a fila acabar**, o robô pede um tema inédito à própria Gemini, evitando repetir
  artigos que já existem. Ou seja: ele nunca fica sem assunto.

---

## 🧪 Rodar/testar no seu computador (opcional)

```bash
pip install -r requirements.txt

# Teste SEM usar a API (gera um artigo de exemplo):
python scripts/generate_daily_article.py --mock --dry-run

# De verdade, com a sua chave:
export GEMINI_API_KEY="sua_chave"
python scripts/generate_daily_article.py                 # usa a fila
python scripts/generate_daily_article.py --theme "Tema X" # tema específico
python scripts/generate_daily_article.py --dry-run        # não grava nada
```

Flags úteis:

| Flag | O que faz |
|------|-----------|
| `--mock` | Gera um artigo de exemplo **sem** chamar a API (ótimo para testar o fluxo). |
| `--dry-run` | Faz tudo, mas **não grava** nada em disco. |
| `--theme "..."` | Usa um tema específico em vez da fila. |
| `--model nome` | Troca o modelo (padrão `gemini-2.5-flash`). |

---

## 🔧 O que o robô faz a cada execução

1. Escolhe o tema (fila → senão, sugestão da IA, sem repetir o que já existe).
2. Gera o artigo em **JSON estruturado** com a Gemini (título, meta, índice, seções,
   FAQ e referências), em português e com tom baseado em evidências.
3. Monta o HTML no **mesmo padrão visual** do site (`scripts/templates/article_template.html`),
   já com `schema.org` (MedicalWebPage + FAQPage), índice, aviso médico e referências.
4. Salva em `artigos/<slug>.html`.
5. Insere o **card** na página `artigos.html` (no topo, como mais recente).
6. Adiciona a URL no `sitemap.xml`.
7. Marca o tema como publicado em `content/topics.json`.
8. Faz **commit e push** — o GitHub Pages republica o site sozinho.

---

## ⏰ Mudar o horário

No arquivo `.github/workflows/daily-article.yml`, ajuste a linha do `cron`
(está em **UTC**). Exemplos:

- `'0 9 * * *'` → 09:00 UTC (~06:00 Brasília) — **padrão**
- `'0 12 * * *'` → 12:00 UTC (~09:00 Brasília)
- `'0 21 * * *'` → 21:00 UTC (~18:00 Brasília)

---

## ❓ Problemas comuns

- **Não gerou nada / erro de permissão no push** → confira o **Passo 3** (Read and write).
- **Erro de autenticação da API** → confira se o secret se chama exatamente `GEMINI_API_KEY`.
- **Quero pausar o robô** → em **Actions**, abra o workflow e clique em **"Disable workflow"**.
- **Quero trocar o modelo** → crie uma *variable* `GEMINI_MODEL` em Settings → Variables,
  ou edite o padrão no workflow.
