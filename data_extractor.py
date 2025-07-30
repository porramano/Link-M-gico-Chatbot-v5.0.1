import requests
import os
from trafilatura import extract

def extract_data_from_url(url: str):
    # Chave da API ScrapingBee - substitua pela sua chave real
    # É altamente recomendado usar variáveis de ambiente para chaves de API em produção
    api_key = os.environ.get("SCRAPINGBEE_API_KEY", "SUA_CHAVE_SCRAPINGBEE_AQUI")

    if not api_key or api_key == "SUA_CHAVE_SCRAPINGBEE_AQUI":
        print("AVISO: Chave da API ScrapingBee não configurada. A extração pode falhar.")
        # Fallback para requests simples se a chave não estiver configurada
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar a URL sem ScrapingBee: {e}")
            return None
    else:
        # Usar ScrapingBee para extração de dados com renderização de JS
        payload = {
            "api_key": api_key,
            "url": url,
            "render_js": True,  # Renderizar JavaScript para páginas dinâmicas
            "premium_proxy": True, # Usar proxies premium para evitar bloqueios
        }
        try:
            response = requests.post("https://app.scrapingbee.com/api/v1/", json=payload, timeout=30)
            response.raise_for_status()
            html_content = response.text
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar a URL com ScrapingBee: {e}")
            return None

    if html_content:
        # Extrair texto limpo e metadados usando Trafilatura
        extracted_text = extract(html_content, include_comments=False, include_tables=False)
        return extracted_text
    return None

if __name__ == '__main__':
    # Exemplo de uso
    test_url = "https://www.arsenalsecretodosceos.com.br/SUCESSO"
    print(f"Extraindo dados de: {test_url}")
    data = extract_data_from_url(test_url)
    if data:
        print("Dados extraídos com sucesso:")
        print(data[:500])  # Imprime os primeiros 500 caracteres
    else:
        print("Falha na extração de dados.")


