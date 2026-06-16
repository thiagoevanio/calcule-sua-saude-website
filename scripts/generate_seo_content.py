#!/usr/bin/env python3
"""
Missão 3: Resolver "Rastreada, mas não indexada" (Thin Content)
==================================================================

Script que:
1. Lê um arquivo HTML de calculadora
2. Extrai o título
3. Usa Gemini API para gerar 500 palavras de conteúdo SEO
4. Injeta o conteúdo após <form> ou antes de </body>
5. Salva o arquivo com conteúdo enriquecido

IMPORTANTE: Configure sua API Key do Gemini primeiro!

Uso:
    export GOOGLE_API_KEY="sua_chave_aqui"
    python scripts/generate_seo_content.py --input calculadora-imc.html

Obter API Key:
    https://makersuite.google.com/app/apikey
"""

import os
import re
import argparse
import sys
from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    print("❌ Erro: biblioteca google-generativeai não instalada")
    print("   Execute: pip install google-generativeai")
    sys.exit(1)


def parse_arguments():
    """Parseia argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Gera conteúdo SEO com Gemini para enriquecer calculadoras",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Usar API Key da variável de ambiente
  export GOOGLE_API_KEY="sua_chave_aqui"
  python scripts/generate_seo_content.py --input calculadora-imc.html
  
  # Especificar API Key diretamente
  python scripts/generate_seo_content.py --input calculadora-imc.html --api-key "sua_chave"
  
  # Múltiplos arquivos (wildcard)
  python scripts/generate_seo_content.py --input "calculadora-*.html" --api-key "sua_chave"
  
  # Sem salvar (test)
  python scripts/generate_seo_content.py --input calculadora-imc.html --dry-run
        """
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Arquivo HTML a processar (suporta wildcards: *.html)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Google Gemini API Key (se não especificado, usa GOOGLE_API_KEY env)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Gerar conteúdo mas não salvar no arquivo"
    )
    parser.add_argument(
        "--words",
        type=int,
        default=500,
        help="Número de palavras para gerar (padrão: 500)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-pro",
        help="Modelo Gemini a usar (padrão: gemini-pro)"
    )
    
    return parser.parse_args()


def get_api_key(api_key_arg=None):
    """Obtém a API Key do Gemini."""
    if api_key_arg:
        return api_key_arg
    
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ Erro: API Key não configurada!")
        print("\nConfigure de uma destas formas:")
        print("  1. Variável de ambiente:")
        print("     export GOOGLE_API_KEY='sua_chave'")
        print("  2. Argumento da linha de comando:")
        print("     python script.py --api-key 'sua_chave'")
        print("\nObter API Key em: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    return api_key


def extract_title(html_content):
    """Extrai o título do arquivo HTML."""
    # Tenta primeira pela tag <title>
    match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Tenta pelo primeiro <h1>
    match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Tenta por meta description
    match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']
', html_content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    return "Calculadora"


def find_injection_point(html_content):
    """
    Encontra o melhor lugar para injetar o conteúdo.
    Ordem de prioridade:
    1. Depois de </form>
    2. Depois de <form...> ... </form>
    3. Antes de </body>
    """
    
    # Procura por </form>
    form_close_match = re.search(r'</form\s*>', html_content, re.IGNORECASE)
    if form_close_match:
        return form_close_match.end(), "após </form>"
    
    # Procura por <form> até </form>
    form_match = re.search(r'<form[^>]*>.*?</form\s*>', html_content, 
                          re.IGNORECASE | re.DOTALL)
    if form_match:
        return form_match.end(), "após o formulário"
    
    # Procura por </body>
    body_close_match = re.search(r'</body\s*>', html_content, re.IGNORECASE)
    if body_close_match:
        return body_close_match.start(), "antes de </body>"
    
    # Se nada disso, injeta no final (antes de últimas tags de fechamento)
    return len(html_content), "no final do arquivo"


def generate_seo_content(title, api_key, words=500, model="gemini-pro"):
    """
    Usa Gemini para gerar conteúdo SEO sobre o título.
    """
    
    print(f"\n🤖 Gerando conteúdo com Gemini...")
    print(f"   Título: {title}")
    print(f"   Palavras: {words}")
    print(f"   Modelo: {model}")
    
    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(model)
    
    prompt = f"""Você é um especialista em SEO e criação de conteúdo para calculadoras online.

Gere um texto SEO completo e informativo sobre "{title}". 

Requisitos:
- Exatamente {words} palavras
- Use tags HTML: <h2> para subtítulos e <p> para parágrafos
- Explique o propósito da calculadora
- Descreva como usar
- Mencione benefícios
- Inclua informações educativas relevantes
- Use linguagem clara e acessível
- Otimizado para SEO (keywords naturais)

IMPORTANTE: 
- Responda APENAS com o HTML (sem explanações)
- Comece direto com <h2> ou <p>
- Não inclua </body>, </html> ou outras tags de fechamento do documento

Texto:"""
    
    try:
        response = model_obj.generate_content(prompt)
        
        if not response or not response.text:
            print("❌ Erro: API retornou resposta vazia")
            return None
        
        content = response.text.strip()
        
        # Limpar conteúdo gerado
        # Remove tags de HTML/body se acidentalmente incluídas
        content = re.sub(r'</?(html|body|head)[^>]*>', '', content, flags=re.IGNORECASE)
        
        # Conta palavras
        word_count = len(content.split())
        print(f"✅ Conteúdo gerado: {word_count} palavras")
        
        return content
        
    except Exception as e:
        print(f"❌ Erro ao chamar Gemini: {e}")
        return None


def inject_content(html_content, seo_content):
    """
    Injeta o conteúdo SEO no HTML.
    """
    
    injection_point, location = find_injection_point(html_content)
    
    # Cria wrapper HTML para o conteúdo gerado
    wrapper = f"""\n<!-- =======================================
CONTEÚDO SEO GERADO AUTOMATICAMENTE (IA/Gemini)
======================================= -->
<section class="seo-content" style="padding: 20px; background-color: #fafafa; border-radius: 8px; margin: 20px 0;">
{seo_content}
</section>
<!-- FIM DO CONTEÚDO SEO -->
\n"""
    
    # Injeta o conteúdo
    modified_html = html_content[:injection_point] + wrapper + html_content[injection_point:]
    
    print(f"✅ Conteúdo injetado {location}")
    
    return modified_html


def process_html_file(filepath, api_key, words=500, model="gemini-pro", dry_run=False):
    """
    Processa um arquivo HTML.
    """
    
    if not os.path.exists(filepath):
        print(f"❌ Arquivo não encontrado: {filepath}")
        return False
    
    print(f"\n📄 Processando: {filepath}")
    
    # Ler arquivo
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return False
    
    # Extrair título
    title = extract_title(html_content)
    print(f"   Título: {title}")
    
    # Gerar conteúdo
    seo_content = generate_seo_content(title, api_key, words=words, model=model)
    
    if not seo_content:
        print(f"❌ Falha ao gerar conteúdo para {filepath}")
        return False
    
    # Injetar conteúdo
    modified_html = inject_content(html_content, seo_content)
    
    # Salvar arquivo
    if dry_run:
        print(f"🔄 DRY RUN - Nenhum arquivo modificado")
        print(f"\n📋 Preview do conteúdo gerado:")
        print("=" * 60)
        print(seo_content[:500] + "..." if len(seo_content) > 500 else seo_content)
        print("=" * 60)
    else:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified_html)
            print(f"✅ Arquivo salvo: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar arquivo: {e}")
            return False
    
    return True


def get_matching_files(pattern):
    """
    Encontra arquivos que correspondem ao padrão (suporta wildcards).
    """
    from glob import glob
    
    files = glob(pattern)
    return sorted(files)


if __name__ == "__main__":
    args = parse_arguments()
    
    # Obter API Key
    api_key = get_api_key(args.api_key)
    
    # Encontrar arquivos
    files = get_matching_files(args.input)
    
    if not files:
        print(f"❌ Nenhum arquivo encontrado para: {args.input}")
        sys.exit(1)
    
    print(f"🔍 Encontrados {len(files)} arquivo(s)")
    
    # Processar cada arquivo
    success_count = 0
    fail_count = 0
    
    for filepath in files:
        success = process_html_file(
            filepath,
            api_key,
            words=args.words,
            model=args.model,
            dry_run=args.dry_run
        )
        
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    # Resumo
    print(f"\n📊 Resumo:")
    print(f"   Arquivos processados: {success_count}/{len(files)}")
    if fail_count > 0:
        print(f"   Erros: {fail_count}")
    
    if success_count > 0:
        print(f"\n✅ Conteúdo SEO adicionado com sucesso!")
        print(f"   Próximos passos:")
        print(f"   1. Revise os arquivos modificados")
        print(f"   2. Teste no navegador")
        print(f"   3. Commit no GitHub")
        print(f"   4. Deploy para produção")
        print(f"   5. Submeta para rastrear no Google Search Console")
