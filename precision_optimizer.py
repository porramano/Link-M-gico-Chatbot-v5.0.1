import logging
from typing import Dict, Any, List
import re

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class PrecisionOptimizer:
    def __init__(self, html_content: str, structured_data: Dict[str, Any], text_content: str):
        self.html_content = html_content
        self.structured_data = structured_data
        self.text_content = text_content
        logging.info("Otimizador de Precisão inicializado.")

    def fallback_search(self, query: str) -> str:
        logging.info(f"Executando busca de fallback para: ")
        # Simula um "Ctrl+F" no HTML original
        # Busca a query exata, ignorando maiúsculas/minúsculas
        if re.search(re.escape(query), self.html_content, re.IGNORECASE):
            # Tenta encontrar a frase/sentença que contém a query
            sentences = self.text_content.split(".")
            for sentence in sentences:
                if query.lower() in sentence.lower():
                    logging.info("Encontrado no fallback: ")
                    return sentence.strip() + "."
        logging.warning("Não encontrado no fallback.")
        return ""

    def cross_validate(self, response: str, sources: List[str]) -> bool:
        logging.info(f"Validando cruzadamente a resposta: ")
        # Verifica se a resposta tem correspondência em pelo menos N fontes
        # Fontes podem ser: "structured", "text", "html"
        match_count = 0
        response_words = set(response.lower().split())

        if "structured" in sources:
            # Verifica se as palavras da resposta estão nos dados estruturados
            structured_text = json.dumps(self.structured_data, ensure_ascii=False).lower()
            if any(word in structured_text for word in response_words):
                match_count += 1
        
        if "text" in sources:
            if any(word in self.text_content.lower() for word in response_words):
                match_count += 1

        if "html" in sources:
            if any(word in self.html_content.lower() for word in response_words):
                match_count += 1
        
        is_valid = match_count >= 2 # Exige correspondência em pelo menos 2 fontes
        logging.info(f"Validação cruzada: {is_valid} (correspondências: {match_count})")
        return is_valid

    def anti_hallucination_check(self, response: str) -> bool:
        logging.info(f"Verificando alucinação para a resposta: ")
        # Bloqueia respostas sem correspondência em pelo menos 2 fontes (structured e text)
        # Uma regra simples: se a resposta contém números, eles devem estar presentes no texto original
        numbers_in_response = re.findall(r"\d+", response)
        if numbers_in_response:
            for num in numbers_in_response:
                if num not in self.text_content:
                    logging.warning(f"Anti-alucinação: Número ")
                    return False # Resposta contém número que não está no texto original

        # Outra regra: se a resposta contém palavras-chave de benefícios/garantia, elas devem estar nos dados estruturados
        if "benefício" in response.lower() and not self.structured_data.get("beneficios"):
            logging.warning("Anti-alucinação: Resposta menciona benefícios, mas não há benefícios nos dados estruturados.")
            return False
        if "garantia" in response.lower() and not self.structured_data.get("garantia"):
            logging.warning("Anti-alucinação: Resposta menciona garantia, mas não há garantia nos dados estruturados.")
            return False

        logging.info("Anti-alucinação: OK.")
        return True

if __name__ == "__main__":
    # Exemplo de uso
    sample_html = "<html><head><title>Curso de Teste</title></head><body><h1>Preço: R$ 100</h1><p>Garantia de 7 dias.</p><p>Benefício: Acesso vitalício.</p></body></html>"
    sample_structured = {"titulo": "Curso de Teste", "preco": "R$ 100", "garantia": "7 dias", "beneficios": ["Acesso vitalício"]}
    sample_text = "Curso de Teste\nPreço: R$ 100\nGarantia de 7 dias.\nBenefício: Acesso vitalício."

    optimizer = PrecisionOptimizer(sample_html, sample_structured, sample_text)

    print("\n--- Teste de Fallback ---")
    fallback_result = optimizer.fallback_search("preço")
    print(f"Resultado do fallback para 'preço': {fallback_result}")

    print("\n--- Teste de Validação Cruzada ---")
    is_valid = optimizer.cross_validate("O preço é R$ 100", ["structured", "text", "html"])
    print(f"A resposta 'O preço é R$ 100' é válida? {is_valid}")

    print("\n--- Teste de Anti-Alucinação ---")
    is_hallucination = not optimizer.anti_hallucination_check("O preço é R$ 200")
    print(f"A resposta 'O preço é R$ 200' é uma alucinação? {is_hallucination}")

    is_hallucination = not optimizer.anti_hallucination_check("O curso tem garantia de 30 dias")
    print(f"A resposta 'O curso tem garantia de 30 dias' é uma alucinação? {is_hallucination}")

    is_hallucination = not optimizer.anti_hallucination_check("O preço é R$ 100")
    print(f"A resposta 'O preço é R$ 100' é uma alucinação? {is_hallucination}")

