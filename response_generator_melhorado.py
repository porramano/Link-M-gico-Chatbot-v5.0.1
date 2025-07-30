import json
import logging
from typing import Dict, Any, List
from jinja2 import Template
import requests
import os

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ResponseGenerator:
    def __init__(self, llm_api_key: str = None, llm_model: str = "meta-llama/llama-3.1-8b-instruct:free"):
        self.llm_api_key = llm_api_key or os.getenv("OPENROUTER_API_KEY")
        self.llm_model = llm_model
        self.openrouter_api_url = "https://openrouter.ai/api/v1/chat/completions"
        logging.info(f"Gerador de Respostas inicializado com modelo LLM: {self.llm_model}")

    def _generate_llm_response(self, context: str, user_question: str, rules: str, conversation_history: List[Dict[str, str]], instructions: str = "") -> str:
        if not self.llm_api_key:
            logging.warning("OPENROUTER_API_KEY não configurada. Usando fallback para respostas baseadas em template.")
            return ""

        # Sistema de prompt aprimorado para um chatbot especialista em vendas
        system_prompt = f"""Você é um assistente de vendas ESPECIALISTA, altamente persuasivo e inteligente. Sua missão é converter visitantes em clientes através de conversas naturais e estratégicas.

PERSONALIDADE E TOM:
- Seja caloroso, empático e genuinamente interessado em ajudar
- Use um tom conversacional, como se fosse um consultor experiente
- Demonstre entusiasmo pelo produto, mas sem ser exagerado
- Seja direto e objetivo, evitando enrolação

ESTRATÉGIAS DE VENDAS:
- Identifique as necessidades e dores do cliente através das perguntas
- Conecte os benefícios do produto às necessidades específicas do cliente
- Use técnicas de escassez e urgência quando apropriado
- Conduza o cliente através do funil de vendas naturalmente
- Supere objeções com argumentos sólidos baseados no contexto

REGRAS FUNDAMENTAIS:
- Use APENAS informações do CONTEXTO fornecido - nunca invente dados
- Se não souber algo, seja honesto: "Essa informação não está disponível na página"
- Sempre redirecione para os benefícios e valor do produto
- Termine respostas com perguntas ou CTAs que mantenham o engajamento
- Mantenha respostas entre 50-150 palavras para facilitar a leitura

CONTEXTO DO PRODUTO:
{context}

INSTRUÇÕES PERSONALIZADAS:
{instructions}

REGRAS ADICIONAIS:
{rules}

Lembre-se: Seu objetivo é VENDER. Seja um consultor que realmente se importa com o sucesso do cliente."""

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Adiciona o histórico de conversa para manter contexto
        for msg in conversation_history[-10:]:  # Últimas 10 mensagens para não sobrecarregar
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": user_question})

        try:
            headers = {
                "Authorization": f"Bearer {self.llm_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://linkmagico.com.br",
                "X-Title": "LinkMágico Chatbot - Especialista em Vendas"
            }
            
            payload = {
                "model": self.llm_model,
                "messages": messages,
                "max_tokens": 300,  # Respostas mais concisas
                "temperature": 0.7,  # Equilibrio entre criatividade e consistência
                "top_p": 0.9,
                "frequency_penalty": 0.1,  # Evita repetições
                "presence_penalty": 0.1    # Encoraja novos tópicos
            }
            
            logging.info(f"Enviando requisição para OpenRouter com modelo {self.llm_model}...")
            response = requests.post(self.openrouter_api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            json_response = response.json()
            llm_text = json_response["choices"][0]["message"]["content"].strip()
            
            # Pós-processamento para garantir qualidade
            llm_text = self._post_process_response(llm_text)
            
            logging.info("Resposta do LLM recebida e processada com sucesso.")
            return llm_text
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao chamar a API do LLM: {e}")
            return ""
        except (KeyError, IndexError) as e:
            logging.error(f"Formato de resposta inesperado do LLM: {e}")
            return ""

    def _post_process_response(self, response: str) -> str:
        """Pós-processa a resposta para garantir qualidade."""
        # Remove quebras de linha excessivas
        response = ' '.join(response.split())
        
        # Garante que termine com pontuação
        if response and response[-1] not in '.!?':
            response += '.'
        
        # Limita o tamanho se muito longo
        if len(response) > 500:
            sentences = response.split('.')
            response = '. '.join(sentences[:3]) + '.'
        
        return response

    def _get_intelligent_fallback(self, user_question: str, structured_data: Dict[str, Any]) -> str:
        """Fallback inteligente baseado na análise da pergunta."""
        question_lower = user_question.lower()
        
        # Análise de intenção da pergunta
        if any(word in question_lower for word in ['preço', 'valor', 'custa', 'investimento', 'quanto']):
            price = structured_data.get('preco', 'Consulte o preço na página')
            return f"O investimento é de {price}. É um excelente custo-benefício considerando todos os benefícios que você vai receber! Quer saber mais sobre o que está incluso?"
        
        elif any(word in question_lower for word in ['benefício', 'vantagem', 'o que', 'inclui', 'recebo']):
            benefits = structured_data.get('beneficios', [])
            if benefits:
                benefits_text = '\n• '.join(benefits[:3])
                return f"Os principais benefícios são:\n• {benefits_text}\n\nQual desses benefícios mais te interessa?"
            return "Este produto oferece benefícios incríveis que vão transformar seus resultados! Quer saber mais detalhes?"
        
        elif any(word in question_lower for word in ['garantia', 'reembolso', 'risco', 'seguro']):
            guarantee = structured_data.get('garantia', 'Garantia de satisfação')
            return f"Sim! Oferecemos {guarantee}. Você pode experimentar sem riscos! Isso te deixa mais confiante para começar?"
        
        elif any(word in question_lower for word in ['comprar', 'adquirir', 'como', 'onde', 'link']):
            cta = structured_data.get('cta', 'Compre Agora')
            url = structured_data.get('url', '#')
            return f"É muito simples! Clique em '{cta}' na página para garantir o seu. Tem alguma dúvida antes de finalizar?"
        
        elif any(word in question_lower for word in ['olá', 'oi', 'bom dia', 'boa tarde', 'boa noite']):
            title = structured_data.get('titulo', 'nosso produto')
            return f"Olá! 😊 Que bom te ver aqui! Sou especialista em '{title}' e estou aqui para te ajudar. O que gostaria de saber?"
        
        elif any(word in question_lower for word in ['sim', 'ok', 'certo', 'entendi']):
            return "Perfeito! Fico feliz que esteja interessado. Que tal conhecer os benefícios exclusivos que preparamos para você?"
        
        elif any(word in question_lower for word in ['não', 'nao']):
            return "Entendo! Sem problemas. Talvez eu possa esclarecer alguma dúvida que você tenha? Estou aqui para ajudar no que precisar."
        
        else:
            # Resposta genérica inteligente
            title = structured_data.get('titulo', 'nosso produto')
            return f"Interessante pergunta! Sobre '{title}', posso te ajudar com informações sobre preços, benefícios, garantias e processo de compra. O que mais te interessa saber?"

    def generate_response(self, user_question: str, structured_data: Dict[str, Any], conversation_history: List[Dict[str, str]] = None, instructions: str = "") -> str:
        if conversation_history is None:
            conversation_history = []

        logging.info(f"Gerando resposta para: {user_question}")
        
        # Formata o contexto de forma mais estruturada e rica
        context_parts = []
        
        if structured_data.get("titulo"):
            context_parts.append(f"PRODUTO: {structured_data['titulo']}")
        
        if structured_data.get("descricao"):
            context_parts.append(f"DESCRIÇÃO: {structured_data['descricao']}")
        
        if structured_data.get("preco"):
            context_parts.append(f"INVESTIMENTO: {structured_data['preco']}")
        
        if structured_data.get("beneficios"):
            benefits_text = '\n- '.join(structured_data['beneficios'])
            context_parts.append(f"BENEFÍCIOS:\n- {benefits_text}")
        
        if structured_data.get("garantia"):
            context_parts.append(f"GARANTIA: {structured_data['garantia']}")
        
        if structured_data.get("publico_alvo"):
            context_parts.append(f"PÚBLICO-ALVO: {structured_data['publico_alvo']}")
        
        if structured_data.get("tipo_produto"):
            context_parts.append(f"TIPO: {structured_data['tipo_produto']}")
        
        if structured_data.get("cta"):
            context_parts.append(f"CALL TO ACTION: {structured_data['cta']}")
        
        if structured_data.get("url"):
            context_parts.append(f"LINK: {structured_data['url']}")
        
        context = "\n\n".join(context_parts)

        # Regras específicas para vendas
        rules = f"""
- Seja específico usando os dados do CONTEXTO (preços, benefícios, garantias)
- Se não souber algo, diga "Essa informação não está na página" e ofereça ajuda com outros tópicos
- NUNCA invente informações que não estão no CONTEXTO
- Seja persuasivo mas honesto - foque no valor real do produto
- Use técnicas de vendas: escassez, prova social, benefícios vs características
- Termine sempre com uma pergunta ou CTA para manter o engajamento
- Se o cliente demonstrar interesse, conduza para a compra
- Se houver objeções, use os dados do CONTEXTO para superá-las
- Mantenha um tom consultivo e empático
- Link para compra: {structured_data.get('url', 'Consulte a página')}
"""

        # Tentar gerar resposta com LLM
        llm_response = self._generate_llm_response(context, user_question, rules, conversation_history, instructions)
        
        if llm_response:
            return llm_response

        # Fallback inteligente se LLM falhar
        logging.warning("LLM não disponível. Usando fallback inteligente.")
        return self._get_intelligent_fallback(user_question, structured_data)

if __name__ == "__main__":
    # Teste do sistema
    generator = ResponseGenerator()

    sample_data = {
        "titulo": "Arsenal Secreto dos CEOs",
        "descricao": "Ferramentas e estratégias que os grandes players usam para vender todos os dias",
        "preco": "R$ 697,00",
        "beneficios": [
            "Transforme leads em clientes fiéis com técnicas avançadas",
            "Alcance resultados visíveis em dias, não meses",
            "Domine ferramentas que otimizam sua produtividade"
        ],
        "garantia": "30 dias de garantia",
        "publico_alvo": "Empreendedores e afiliados",
        "tipo_produto": "curso online",
        "cta": "QUERO O MEU ARSENAL SECRETO AGORA",
        "url": "https://exemplo.com/arsenal"
    }

    # Testes
    perguntas = [
        "Olá!",
        "Qual o preço?",
        "Quais os benefícios?",
        "Tem garantia?",
        "Como faço para comprar?",
        "Isso é um curso ou livro?",
        "Vale a pena?",
        "sim"
    ]

    print("=== TESTE DO CHATBOT ESPECIALISTA ===\n")
    
    history = []
    for pergunta in perguntas:
        print(f"👤 Cliente: {pergunta}")
        resposta = generator.generate_response(pergunta, sample_data, history)
        print(f"🤖 Assistente: {resposta}\n")
        
        # Adiciona ao histórico
        history.append({"role": "user", "content": pergunta})
        history.append({"role": "assistant", "content": resposta})

