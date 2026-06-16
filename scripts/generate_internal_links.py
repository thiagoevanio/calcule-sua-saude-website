#!/usr/bin/env python3
"""
Missão 2: Resolver "Detectada, mas não indexada" (Páginas Órfãs)
==================================================================

Script que:
1. Lê todos os arquivos .html de uma pasta
2. Extrai a tag <title> de cada um
3. Gera um bloco HTML com lista <ul> de links internos
4. Salva o resultado em um arquivo HTML que você cola no footer

Isso força o Google a rastrear todas as páginas órfãs.

Uso:
    python scripts/generate_internal_links.py --html-dir artigos --output links.html
"""

import os
import re
import argparse
from pathlib import Path
from urllib.parse import quote
import sys


def parse_arguments():
    """Parseia argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Gera lista HTML com links internos para forçar rastreamento",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Gerar links de uma pasta específica
  python scripts/generate_internal_links.py --html-dir artigos --output links.html
  
  # Usar diretório raiz
  python scripts/generate_internal_links.py --html-dir . --output footer-links.html
  
  # Com base URL personalizada
  python scripts/generate_internal_links.py --html-dir artigos --output links.html --base-url https://calculesuasaude.com.br
        """
    )
    parser.add_argument(
        "--html-dir",
        type=str,
        default="artigos",
        help="Diretório contendo os arquivos HTML (padrão: artigos)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="links.html",
        help="Arquivo de saída com os links (padrão: links.html)"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="https://calculesuasaude.com.br",
        help="URL base para os links (padrão: https://calculesuasaude.com.br)"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Buscar recursivamente em subpastas"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar detalhes de cada arquivo processado"
    )
    
    return parser.parse_args()


def extract_title(html_content):
    """Extrai o conteúdo da tag <title> de um arquivo HTML."""
    match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if match:
        title = match.group(1).strip()
        # Remove entities HTML comuns
        title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return title
    return None


def extract_meta_description(html_content):
    """Extrai o conteúdo da meta tag description (alternativa para fallback)."""
    match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']
', html_content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def get_html_files(directory, recursive=False):
    """
    Encontra todos os arquivos .html em um diretório.
    """
    html_files = []
    
    if not os.path.isdir(directory):
        print(f"❌ Erro: Diretório '{directory}' não encontrado!")
        return []
    
    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.html'):
                    full_path = os.path.join(root, file)
                    html_files.append(full_path)
    else:
        for file in os.listdir(directory):
            if file.endswith('.html'):
                full_path = os.path.join(directory, file)
                if os.path.isfile(full_path):
                    html_files.append(full_path)
    
    return sorted(html_files)


def filepath_to_url(filepath, base_url, html_dir):
    """
    Converte um caminho de arquivo para URL.
    
    Exemplos:
        artigos/calculadora-imc.html -> https://calculesuasaude.com.br/artigos/calculadora-imc.html
        ./index.html -> https://calculesuasaude.com.br/index.html
    """
    # Remove o diretório base do caminho
    relative_path = filepath.replace(html_dir, '').lstrip('/')
    relative_path = relative_path.replace('\\', '/')  # Windows compatibility
    
    # Monta a URL
    url = f"{base_url.rstrip('/')}/{relative_path}"
    
    return url


def generate_links_html(links_data, recursive=False):
    """
    Gera o HTML com a lista de links internos.
    """
    
    html = """<!-- ========================================
LINKS INTERNOS PARA RASTREAMENTO (Gerado automaticamente)
Adicione este bloco ao seu footer para forçar o Google a rastrear todas as páginas
======================================== -->
<div class="internal-links-footer" style="margin-top: 40px; padding: 20px; background-color: #f5f5f5; border-radius: 8px;">
    <h3 style="margin-top: 0;">Ferramentas e Calculadoras</h3>
    <ul style="list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
"""
    
    for title, url in links_data:
        # Escapar caracteres especiais no título
        title_escaped = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        
        html += f'        <li><a href="{url}" title="{title_escaped}" style="text-decoration: none; color: #0066cc; font-weight: 500; display: flex; align-items: center; gap: 8px;"><span style="display: inline-block; width: 6px; height: 6px; background-color: #0066cc; border-radius: 50%;"></span>{title_escaped}</a></li>\n'
    
    html += """    </ul>
</div>
<!-- FIM DOS LINKS INTERNOS -->
"""
    
    return html


def process_html_files(html_dir, output_file, base_url, recursive=False, verbose=False):
    """
    Processa os arquivos HTML e gera o arquivo de links.
    """
    print(f"📂 Lendo arquivos HTML de: {html_dir}")
    print(f"🔗 URL base: {base_url}\n")
    
    # Encontrar arquivos HTML
    html_files = get_html_files(html_dir, recursive=recursive)
    
    if not html_files:
        print(f"❌ Nenhum arquivo .html encontrado em '{html_dir}'!")
        return 0
    
    print(f"📄 Encontrados {len(html_files)} arquivos HTML\n")
    
    # Processar cada arquivo
    links_data = []
    
    for i, filepath in enumerate(html_files, 1):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            # Extrair título
            title = extract_title(html_content)
            
            # Se não houver title, tenta description
            if not title:
                title = extract_meta_description(html_content)
            
            # Se ainda não houver título, usa o nome do arquivo
            if not title:
                title = Path(filepath).stem.replace('-', ' ').title()
            
            # Converter para URL
            url = filepath_to_url(filepath, base_url, html_dir)
            
            links_data.append((title, url))
            
            status = "✅"
            if verbose:
                print(f"[{i:3d}] {status} {title}")
                print(f"       📍 {url}\n")
            else:
                if i % 10 == 0:
                    print(f"Processados {i}/{len(html_files)} arquivos...", end='\r')
        
        except Exception as e:
            print(f"❌ Erro ao processar {filepath}: {e}")
            continue
    
    if not verbose:
        print(f"Processados {len(html_files)}/{len(html_files)} arquivos... ✓")
    
    # Gerar HTML
    print(f"\n🎨 Gerando HTML com {len(links_data)} links...")
    html_output = generate_links_html(links_data, recursive=recursive)
    
    # Salvar arquivo
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"✅ Arquivo salvo: {output_file}")
    
    # Resumo
    print(f"\n📊 Resumo:")
    print(f"   Total de links gerados: {len(links_data)}")
    print(f"   Arquivo de saída:       {output_file}")
    print(f"\n📋 Próximos passos:")
    print(f"   1. Abra o arquivo {output_file}")
    print(f"   2. Copie TODO o conteúdo")
    print(f"   3. Abra seu arquivo index.html")
    print(f"   4. Cole o conteúdo logo antes de </body>")
    print(f"   5. Commit, push, deploy e submeta no GSC")
    
    return len(links_data)


if __name__ == "__main__":
    args = parse_arguments()
    
    try:
        count = process_html_files(
            args.html_dir,
            args.output,
            args.base_url,
            recursive=args.recursive,
            verbose=args.verbose
        )
    except Exception as e:
        print(f"\n❌ Erro durante processamento: {e}")
        sys.exit(1)
