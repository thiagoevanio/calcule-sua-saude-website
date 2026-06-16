#!/usr/bin/env python3
"""
Missão 1: Limpar Erros 404 do Sitemap
===========================================

Script que:
1. Lê o arquivo sitemap.xml
2. Verifica se cada URL tem arquivo .html correspondente na pasta local
3. Remove do sitemap URLs que apontam para arquivos deletados
4. Salva o sitemap limpo

Uso:
    python scripts/fix_sitemap_404s.py --sitemap sitemap.xml --html-dir .
"""

import xml.etree.ElementTree as ET
import os
import argparse
from pathlib import Path
from urllib.parse import urlparse
import sys


def parse_arguments():
    """Parseia argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Remove URLs do sitemap que não têm arquivo HTML correspondente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Usar valores padrão
  python scripts/fix_sitemap_404s.py
  
  # Especificar sitemap e diretório HTML
  python scripts/fix_sitemap_404s.py --sitemap dist/sitemap.xml --html-dir dist/
  
  # Criar backup antes de processar
  python scripts/fix_sitemap_404s.py --backup
        """
    )
    parser.add_argument(
        "--sitemap",
        type=str,
        default="sitemap.xml",
        help="Caminho para o arquivo sitemap.xml (padrão: sitemap.xml)"
    )
    parser.add_argument(
        "--html-dir",
        type=str,
        default=".",
        help="Diretório raiz onde estão os arquivos HTML (padrão: . = diretório atual)"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Criar arquivo sitemap.xml.backup antes de processar"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar detalhes de cada verificação"
    )
    
    return parser.parse_args()


def load_sitemap(filepath):
    """Carrega e parseia o arquivo XML do sitemap."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        return tree, root
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo '{filepath}' não encontrado!")
        sys.exit(1)
    except ET.ParseError as e:
        print(f"❌ Erro ao parsear XML: {e}")
        sys.exit(1)


def get_namespace(root):
    """Extrai o namespace do XML."""
    # O namespace padrão do sitemap é http://www.sitemaps.org/schemas/sitemap/0.9
    namespaces = {}
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'
        namespaces['ns'] = ns.strip('{}')
    return namespaces


def url_to_filepath(url, html_dir, base_domain=None):
    """
    Converte uma URL do sitemap para o caminho local do arquivo.
    
    Exemplos:
        https://calculesuasaude.com.br/calculadora-imc.html 
        -> calculesuasaude/calculadora-imc.html
        
        https://calculesuasaude.com.br/ 
        -> calculesuasaude/index.html
    """
    parsed = urlparse(url)
    path = parsed.path.lstrip('/')
    
    # Se a URL é raiz (/), procura por index.html
    if not path or path == '':
        path = 'index.html'
    
    # Monta o caminho completo
    full_path = os.path.join(html_dir, path)
    
    return full_path


def check_file_exists(url, html_dir):
    """Verifica se o arquivo .html correspondente à URL existe."""
    filepath = url_to_filepath(url, html_dir)
    
    # Tenta encontrar o arquivo em variações comuns
    candidates = [
        filepath,
        filepath.replace('.html', '/index.html') if filepath.endswith('.html') else filepath + '/index.html',
    ]
    
    for candidate in candidates:
        if os.path.isfile(candidate):
            return True, candidate
    
    return False, filepath


def remove_url_from_sitemap(root, url, namespaces):
    """Remove um elemento <url> do sitemap."""
    ns = namespaces.get('ns', '')
    
    # Monta o tag com namespace se necessário
    url_tag = f"{{{ns}}}url" if ns else "url"
    loc_tag = f"{{{ns}}}loc" if ns else "loc"
    
    for url_elem in root.findall(url_tag):
        loc_elem = url_elem.find(loc_tag)
        if loc_elem is not None and loc_elem.text == url:
            root.remove(url_elem)
            return True
    
    return False


def process_sitemap(sitemap_path, html_dir, backup=False, verbose=False):
    """
    Processa o sitemap e remove URLs com arquivos 404.
    """
    print(f"📂 Lendo sitemap de: {sitemap_path}")
    print(f"📂 Diretório HTML: {html_dir}")
    
    # Criar backup se solicitado
    if backup:
        backup_path = f"{sitemap_path}.backup"
        os.system(f"cp {sitemap_path} {backup_path}")
        print(f"✅ Backup criado: {backup_path}")
    
    # Carregar sitemap
    tree, root = load_sitemap(sitemap_path)
    namespaces = get_namespace(root)
    
    # Extrair namespace se houver
    ns = namespaces.get('ns', '')
    url_tag = f"{{{ns}}}url" if ns else "url"
    loc_tag = f"{{{ns}}}loc" if ns else "loc"
    
    # Coletar todas as URLs
    urls = []
    for url_elem in root.findall(url_tag):
        loc_elem = url_elem.find(loc_tag)
        if loc_elem is not None:
            urls.append(loc_elem.text)
    
    print(f"\n🔍 Encontradas {len(urls)} URLs no sitemap")
    
    # Verificar cada URL
    urls_removidas = []
    urls_validas = []
    
    for i, url in enumerate(urls, 1):
        exists, filepath = check_file_exists(url, html_dir)
        
        if not exists:
            urls_removidas.append(url)
            status = "❌ 404"
        else:
            urls_validas.append(url)
            status = "✅ OK"
        
        if verbose:
            print(f"  [{i:3d}/{len(urls)}] {status} {url}")
        elif i % 10 == 0:
            print(f"  Verificadas {i}/{len(urls)} URLs...", end='\r')
    
    if not verbose:
        print(f"  Verificadas {len(urls)}/{len(urls)} URLs... ✓")
    
    # Remover URLs com 404
    print(f"\n🗑️  Removendo {len(urls_removidas)} URLs com 404...")
    for url in urls_removidas:
        remove_url_from_sitemap(root, url, namespaces)
        print(f"   - {url}")
    
    # Salvar sitemap limpo
    tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)
    print(f"\n✅ Sitemap salvo com sucesso!")
    
    # Resumo
    print(f"\n📊 Resumo:")
    print(f"   Total de URLs originais: {len(urls)}")
    print(f"   URLs removidas (404):    {len(urls_removidas)}")
    print(f"   URLs válidas:            {len(urls_validas)}")
    print(f"   Redução:                 {len(urls_removidas)}/{len(urls)} URLs ({100*len(urls_removidas)/len(urls):.1f}%)")
    
    return len(urls_removidas), len(urls_validas)


if __name__ == "__main__":
    args = parse_arguments()
    
    try:
        removed, valid = process_sitemap(
            args.sitemap,
            args.html_dir,
            backup=args.backup,
            verbose=args.verbose
        )
    except Exception as e:
        print(f"\n❌ Erro durante processamento: {e}")
        sys.exit(1)
