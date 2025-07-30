import spacy
import re
import logging
from typing import Dict, List, Any

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Carregar modelo spaCy para português
try:
    nlp = spacy.load("pt_core_news_sm")
    logging.info("Modelo spaCy 'pt_core_news_sm' carregado com sucesso.")
except Exception as e:
    logging.error(f"Erro ao carregar modelo spaCy: {e}. Certifique-se de que o modelo está instalado (python -m spacy download pt_core_news_sm).")
    nlp = None

def analyze_text(text: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    logging.info("Iniciando análise estruturada do texto.")
    analysis_results = {
        "entities": {},
        "sections": [],
        "urgency": "BAIXA"
    }

    if not nlp:
        logging.warning("SpaCy não carregado. Análise de entidades e classificação de seções limitada.")
        return analysis_results

    doc = nlp(text)

    # 1. NER (Named Entity Recognition)
    # Adaptação para identificar entidades relevantes para páginas de vendas
    # Usaremos uma abordagem híbrida: NER do spaCy + regras baseadas em palavras-chave
    entities = {}
    for ent in doc.ents:
        entities[ent.label_] = entities.get(ent.label_, []) + [ent.text]
    
    # Adicionar entidades baseadas em palavras-chave e dados extraídos
    if extracted_data.get("preco"): entities["PRECO"] = [extracted_data["preco"]]
    if extracted_data.get("titulo"): entities["PRODUTO"] = [extracted_data["titulo"]]

    # Palavras-chave para identificar promoções, garantias, etc.
    promo_keywords = ["desconto", "oferta", "promoção", "bônus", "grátis"]
    garantia_keywords = ["garantia", "reembolso", "satisfação", "risco zero"]
    publico_alvo_keywords = ["para quem", "ideal para", "você é", "empreendedores", "afiliados", "iniciantes"]
    diferenciais_keywords = ["diferencial", "exclusivo", "único", "mentoria", "comunidade", "suporte"]

    for sentence in doc.sents:
        s = sentence.text.lower()
        if any(kw in s for kw in promo_keywords):
            entities["PROMOCAO"] = entities.get("PROMOCAO", []) + [sentence.text.strip()]
        if any(kw in s for kw in garantia_keywords):
            entities["GARANTIA"] = entities.get("GARANTIA", []) + [sentence.text.strip()]
        if any(kw in s for kw in publico_alvo_keywords):
            entities["PUBLICO_ALVO"] = entities.get("PUBLICO_ALVO", []) + [sentence.text.strip()]
        if any(kw in s for kw in diferenciais_keywords):
            entities["DIFERENCIAL"] = entities.get("DIFERENCIAL", []) + [sentence.text.strip()]
            
    analysis_results["entities"] = {k: list(set(v)) for k, v in entities.items()} # Remover duplicatas

    # 2. Classificador de Seções
    # Usa regex + heurísticas para categorizar trechos
    section_patterns = {
        "OFERTA": [r"oferta", r"compre agora", r"adquira já", r"inscriç(ão|ões)", r"vagas?", r"desconto"],
        "BENEFICIOS": [r"benefícios?", r"vantagens?", r"o que você vai aprender", r"você terá", r"inclui"],
        "PUBLICO_ALVO": [r"para quem é", r"ideal para", r"você é"],
        "DEPOIMENTOS": [r"depoimentos?", r"o que dizem", r"casos de sucesso"],
        "GARANTIA": [r"garantia", r"reembolso", r"satisfação garantida", r"risco zero"],
        "PRECO": [r"preço", r"investimento", r"valor", r"por apenas", r"r\$"]
    }

    lines = text.split("\n")
    for i, line in enumerate(lines):
        for section_type, patterns in section_patterns.items():
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
                # Capturar a linha e talvez as próximas para o contexto da seção
                section_content = line.strip()
                # Adicionar um pouco mais de contexto se a linha for curta
                if len(section_content) < 50 and i + 1 < len(lines):
                    section_content += " " + lines[i+1].strip()
                analysis_results["sections"].append({"type": section_type, "content": section_content})
                break # Uma linha pode pertencer a apenas uma seção principal

    # 3. Analisador de Urgência
    urgency_keywords = [
        r"últimas\s+\d+\s+vagas?", r"somente\s+\d+\s+dias?", r"por\s+tempo\s+limitado",
        r"não\s+perca\s+essa\s+oportunidade", r"agora\s+ou\s+nunca", r"escassez", r"corra"
    ]
    for sentence in doc.sents:
        if any(re.search(pattern, sentence.text.lower()) for pattern in urgency_keywords):
            analysis_results["urgency"] = "ALTA"
            break

    logging.info("Análise estruturada concluída.")
    return analysis_results

if __name__ == "__main__":
    # Exemplo de uso
    sample_text = """
    Descubra o Arsenal Secreto que está Transformando Afiliados em CEOs de Sucesso!

    “Saia do básico! Com o Arsenal Secreto dos CEOs, você terá acesso às ferramentas e estratégias que os grandes players usam para vender todos os dias. Ideal para afiliados e empreendedores iniciantes ou avançados que querem alavancar seus resultados no marketing digital!”

    💰 Investimento: R$ 697,00

    ✅ Principais benefícios:
    • Transforme leads em clientes fiéis com técnicas avançadas.
    • Alcance resultados visíveis em dias, não meses.
    • Domine ferramentas que otimizam sua produtividade e simplificam suas vendas
    • Aprenda a negociar com confiança, encurtar ciclos de vendas e superar concorrentes com estratégia
    • Fechar mais negócios com confiança.

    💬 Depoimentos: “Saia do básico! Com o Arsenal Secreto dos CEOs, você terá acesso às ferramentas e estratégias que os grandes players usam para vender todos os dias. Ideal para afiliados e empreendedores iniciantes ou avançados que querem alavancar seus resultados no marketing digital!” | Transforme leads em clientes fiéis com técnicas avançadas.Alcance resultados visíveis em dias, não meses.Domine ferramentas que otimizam sua produtividade e simplificam suas vendasAprenda a negociar com confiança, encurtar ciclos de vendas e superar concorrentes com estratégia

    🚀 QUERO O MEU ARSENAL SECRETO AGORA

    Últimas 3 vagas com 50% de desconto! Não perca essa chance!
    """
    
    sample_extracted_data = {
        "titulo": "Arsenal Secreto dos CEOs",
        "preco": "R$ 697,00",
        "beneficios": [
            "Transforme leads em clientes fiéis com técnicas avançadas.",
            "Alcance resultados visíveis em dias, não meses.",
            "Domine ferramentas que otimizam sua produtividade e simplificam suas vendas"
        ]
    }

    analysis_output = analyze_text(sample_text, sample_extracted_data)
    print(json.dumps(analysis_output, indent=2, ensure_ascii=False))

