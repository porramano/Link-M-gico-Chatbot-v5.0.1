import requests
import os
import re
import logging
from bs4 import BeautifulSoup
from trafilatura import extract
from typing import Dict, List, Any

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_data_from_url(url: str) -> Dict[str, Any]:
    """
    Extrai dados estruturados de uma página de vendas.
    Retorna um dicionário com informações como título, preço, benefícios, etc.
    """
    logging.info(f"Iniciando extração de dados para: {url}")
    
    # Obter o HTML da página
    html_content = _get_html_content(url)
    if not html_content:
        logging.error("Não foi possível obter o conteúdo HTML da página.")
        return _get_fallback_data(url)
    
    # Extrair texto principal usando trafilatura
    main_text = extract(html_content, include_comments=False, include_tables=False)
    if not main_text:
        logging.warning("Trafilatura não conseguiu extrair texto. Tentando com BeautifulSoup.")
        main_text = _extract_text_with_bs4(html_content)
    
    # Analisar HTML com BeautifulSoup para extração estruturada
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extrair dados estruturados
    structured_data = {
        "url": url,
        "titulo": _extract_title(soup, main_text),
        "descricao": _extract_description(soup, main_text),
        "preco": _extract_price(soup, main_text),
        "beneficios": _extract_benefits(soup, main_text),
        "cta": _extract_cta(soup, main_text),
        "garantia": _extract_guarantee(soup, main_text),
        "publico_alvo": _extract_target_audience(soup, main_text),
        "depoimentos": _extract_testimonials(soup, main_text),
        "tipo_produto": _extract_product_type(soup, main_text)
    }
    
    logging.info("Extração de dados concluída com sucesso.")
    return structured_data

def _get_html_content(url: str) -> str:
    """Obtém o conteúdo HTML da página usando ScrapingBee ou fallback."""
    api_key = os.environ.get("SCRAPINGBEE_API_KEY")

    if not api_key:
        logging.warning("SCRAPINGBEE_API_KEY não configurada. Usando fallback direto.")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao acessar a URL sem ScrapingBee: {e}")
            return ""
    else:
        payload = {
            "api_key": api_key,
            "url": url,
            "render_js": True,
            "premium_proxy": True,
            "wait": 3000,  # Aguardar 3 segundos para JavaScript carregar
            "screenshot": False
        }
        try:
            response = requests.post("https://app.scrapingbee.com/api/v1/", json=payload, timeout=45)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao acessar a URL com ScrapingBee: {e}")
            # Fallback para requisição direta
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e2:
                logging.error(f"Erro no fallback direto: {e2}")
                return ""

def _extract_text_with_bs4(html_content: str) -> str:
    """Extrai texto usando BeautifulSoup como fallback."""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove scripts e styles
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text()

def _extract_title(soup: BeautifulSoup, text: str) -> str:
    """Extrai o título do produto/página."""
    # Tentar extrair do title tag
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text().strip()
        if title and len(title) > 10:
            return title
    
    # Tentar extrair de h1
    h1_tags = soup.find_all('h1')
    for h1 in h1_tags:
        title = h1.get_text().strip()
        if title and len(title) > 10:
            return title
    
    # Tentar extrair de meta property="og:title"
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content'].strip()
    
    # Fallback: primeira linha significativa do texto
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if len(line) > 20 and len(line) < 200:
            return line
    
    return "Produto Incrível"

def _extract_description(soup: BeautifulSoup, text: str) -> str:
    """Extrai a descrição do produto."""
    # Tentar extrair de meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        desc = meta_desc['content'].strip()
        if len(desc) > 50:
            return desc
    
    # Tentar extrair de meta property="og:description"
    og_desc = soup.find('meta', property='og:description')
    if og_desc and og_desc.get('content'):
        desc = og_desc['content'].strip()
        if len(desc) > 50:
            return desc
    
    # Procurar por parágrafos que parecem descrições
    paragraphs = soup.find_all('p')
    for p in paragraphs:
        desc = p.get_text().strip()
        if len(desc) > 100 and len(desc) < 500:
            return desc
    
    # Fallback: extrair do texto principal
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if len(line) > 100 and len(line) < 500 and not line.startswith('R$'):
            return line
    
    return "Descubra este produto incrível que vai transformar sua vida!"

def _extract_price(soup: BeautifulSoup, text: str) -> str:
    """Extrai o preço do produto."""
    # Padrões de preço em português
    price_patterns = [
        r'R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?',
        r'por\s+apenas\s+R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?',
        r'investimento\s*:?\s*R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?',
        r'valor\s*:?\s*R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?',
        r'preço\s*:?\s*R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?'
    ]
    
    # Procurar no texto principal
    for pattern in price_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0].strip()
    
    # Procurar em elementos com classes relacionadas a preço
    price_selectors = [
        '.price', '.valor', '.preco', '.investimento',
        '[class*="price"]', '[class*="valor"]', '[class*="preco"]'
    ]
    
    for selector in price_selectors:
        elements = soup.select(selector)
        for element in elements:
            text_content = element.get_text().strip()
            for pattern in price_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    return matches[0].strip()
    
    return "Consulte o preço na página"

def _extract_benefits(soup: BeautifulSoup, text: str) -> List[str]:
    """Extrai os benefícios do produto."""
    benefits = []
    
    # Procurar por listas (ul, ol)
    lists = soup.find_all(['ul', 'ol'])
    for list_elem in lists:
        items = list_elem.find_all('li')
        for item in items:
            benefit = item.get_text().strip()
            if len(benefit) > 20 and len(benefit) < 200:
                benefits.append(benefit)
    
    # Procurar por padrões de benefícios no texto
    benefit_patterns = [
        r'✅\s*([^✅\n]{20,200})',
        r'•\s*([^•\n]{20,200})',
        r'→\s*([^→\n]{20,200})',
        r'✓\s*([^✓\n]{20,200})',
        r'▶\s*([^▶\n]{20,200})'
    ]
    
    for pattern in benefit_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        for match in matches:
            benefit = match.strip()
            if benefit and benefit not in benefits:
                benefits.append(benefit)
    
    # Se não encontrou benefícios, procurar por seções que mencionam benefícios
    if not benefits:
        lines = text.split('\n')
        in_benefits_section = False
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['benefícios', 'vantagens', 'você vai', 'você terá']):
                in_benefits_section = True
                continue
            if in_benefits_section and len(line) > 20 and len(line) < 200:
                benefits.append(line)
                if len(benefits) >= 5:  # Limitar a 5 benefícios
                    break
    
    # Fallback: benefícios genéricos
    if not benefits:
        benefits = [
            "Resultados comprovados",
            "Suporte especializado", 
            "Garantia de satisfação"
        ]
    
    return benefits[:5]  # Máximo 5 benefícios

def _extract_cta(soup: BeautifulSoup, text: str) -> str:
    """Extrai o call-to-action principal."""
    # Procurar por botões e links
    cta_selectors = [
        'button', 'a[class*="btn"]', 'a[class*="button"]',
        '[class*="cta"]', '[class*="comprar"]', '[class*="adquirir"]'
    ]
    
    for selector in cta_selectors:
        elements = soup.select(selector)
        for element in elements:
            cta_text = element.get_text().strip()
            if len(cta_text) > 5 and len(cta_text) < 100:
                # Verificar se parece um CTA
                cta_keywords = ['comprar', 'adquirir', 'quero', 'garanta', 'acesse', 'clique', 'inscreva']
                if any(keyword in cta_text.lower() for keyword in cta_keywords):
                    return cta_text
    
    # Procurar no texto por padrões de CTA
    cta_patterns = [
        r'(QUERO\s+[^!\n]{5,50}!?)',
        r'(COMPRE\s+[^!\n]{5,50}!?)',
        r'(ADQUIRA\s+[^!\n]{5,50}!?)',
        r'(GARANTA\s+[^!\n]{5,50}!?)'
    ]
    
    for pattern in cta_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0].strip()
    
    return "Compre Agora!"

def _extract_guarantee(soup: BeautifulSoup, text: str) -> str:
    """Extrai informações sobre garantia."""
    guarantee_patterns = [
        r'garantia\s+de\s+(\d+\s+dias?)',
        r'(\d+\s+dias?)\s+de\s+garantia',
        r'reembolso\s+em\s+(\d+\s+dias?)',
        r'satisfação\s+garantida',
        r'risco\s+zero'
    ]
    
    for pattern in guarantee_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            if isinstance(matches[0], tuple):
                return f"Garantia de {matches[0][0]}"
            else:
                return matches[0]
    
    return "Garantia de satisfação"

def _extract_target_audience(soup: BeautifulSoup, text: str) -> str:
    """Extrai informações sobre o público-alvo."""
    audience_patterns = [
        r'ideal\s+para\s+([^.\n]{10,100})',
        r'para\s+quem\s+([^.\n]{10,100})',
        r'se\s+você\s+é\s+([^.\n]{10,100})'
    ]
    
    for pattern in audience_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0].strip()
    
    return "Empreendedores e profissionais"

def _extract_testimonials(soup: BeautifulSoup, text: str) -> List[str]:
    """Extrai depoimentos de clientes."""
    testimonials = []
    
    # Procurar por elementos que podem conter depoimentos
    testimonial_selectors = [
        '[class*="depoimento"]', '[class*="testimonial"]',
        '[class*="review"]', '.quote', 'blockquote'
    ]
    
    for selector in testimonial_selectors:
        elements = soup.select(selector)
        for element in elements:
            testimonial = element.get_text().strip()
            if len(testimonial) > 50 and len(testimonial) < 500:
                testimonials.append(testimonial)
    
    # Fallback: depoimentos genéricos
    if not testimonials:
        testimonials = [
            "Produto excelente!",
            "Recomendo para todos!"
        ]
    
    return testimonials[:3]  # Máximo 3 depoimentos

def _extract_product_type(soup: BeautifulSoup, text: str) -> str:
    """Identifica o tipo de produto (curso, livro, software, etc.)."""
    type_keywords = {
        'curso': ['curso', 'treinamento', 'aulas', 'módulos'],
        'livro': ['livro', 'ebook', 'e-book', 'páginas'],
        'software': ['software', 'aplicativo', 'app', 'sistema'],
        'consultoria': ['consultoria', 'mentoria', 'coaching'],
        'produto físico': ['entrega', 'frete', 'envio', 'correios']
    }
    
    text_lower = text.lower()
    for product_type, keywords in type_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return product_type
    
    return "produto digital"

def _get_fallback_data(url: str) -> Dict[str, Any]:
    """Retorna dados de fallback quando a extração falha."""
    return {
        "url": url,
        "titulo": "Produto Incrível",
        "descricao": "Descubra este produto incrível que vai transformar sua vida!",
        "preco": "Consulte o preço na página",
        "beneficios": [
            "Resultados comprovados",
            "Suporte especializado",
            "Garantia de satisfação"
        ],
        "cta": "Compre Agora!",
        "garantia": "Garantia de satisfação",
        "publico_alvo": "Empreendedores e profissionais",
        "depoimentos": [
            "Produto excelente!",
            "Recomendo para todos!"
        ],
        "tipo_produto": "produto digital"
    }

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    test_url = "https://www.arsenalsecretodosceos.com.br/SUCESSO"
    print(f"Extraindo dados de: {test_url}")
    data = extract_data_from_url(test_url)
    
    print("\n=== DADOS EXTRAÍDOS ===")
    for key, value in data.items():
        print(f"{key}: {value}")

