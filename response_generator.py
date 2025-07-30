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

    def _generate_llm_response(self, context: str, user_question: str, rules: str, conversation_history: List[Dict[str, str]]) -> str:
        if not self.llm_api_key:
            logging.warning("OPENROUTER_API_KEY não configurada. Usando fallback para respostas baseadas em template.")
            return ""

        messages = [
            {"role": "system", "content": f"CONTEXTO: {context}\nREGRAS: {rules}"}
        ]
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_question})

        try:
            headers = {
                "Authorization": f"Bearer {self.llm_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000", # Pode ser o domínio real do seu app
                "X-Title": "LinkMágico Chatbot"
            }
            payload = {
                "model": self.llm_model,
                "messages": messages,
                "max_tokens": 200,
                "temperature": 0.7,
                "top_p": 0.9
            }
            logging.info(f"Enviando requisição para OpenRouter com modelo {self.llm_model}...")
            response = requests.post(self.openrouter_api_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status() # Levanta HTTPError para bad responses (4xx ou 5xx)
            
            json_response = response.json()
            llm_text = json_response["choices"][0]["message"]["content"].strip()
            logging.info("Resposta do LLM recebida com sucesso.")
            return llm_text
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao chamar a API do LLM: {e}")
            return ""
        except (KeyError, IndexError) as e:
            logging.error(f"Formato de resposta inesperado do LLM: {e}")
            return ""

    def generate_response(self, user_question: str, structured_data: Dict[str, Any], conversation_history: List[Dict[str, str]] = None) -> str:
        if conversation_history is None:
            conversation_history = []

        logging.info(f"Gerando resposta para a pergunta: ")
        
        # Contexto para o LLM
        context = f"Informações da página de vendas: {json.dumps(structured_data, ensure_ascii=False)}"
        rules = (
            "- Seja específico (ex: cite números, valores, prazos) com base no CONTEXTO.\n"
            "- Se não souber a resposta com base no CONTEXTO, diga 'Isso não consta na página'.\n"
            "- Nunca invente detalhes ou informações.\n"
            "- Seja persuasivo e direcione para a compra ou para mais informações sobre o produto.\n"
            "- Mantenha um tom de voz amigável e profissional.\n"
            "- Use emojis moderadamente para engajamento.\n"
            "- Se a pergunta for uma saudação, responda amigavelmente e pergunte como pode ajudar.\n"
            "- Se a pergunta for sobre um tópico já respondido recentemente, tente variar a resposta ou aprofundar.\n"
            f"- O link para compra/mais informações é: {structured_data.get('url', 'Não disponível')}"
        )

        # Tentar gerar resposta com LLM
        llm_response = self._generate_llm_response(context, user_question, rules, conversation_history)
        if llm_response:
            return llm_response

        logging.warning("LLM não gerou resposta ou API Key ausente. Usando fallback baseado em template.")
        # Fallback: Regras de template mais simples se o LLM não responder
        template_str = ""
        if "preço" in user_question.lower() or "investimento" in user_question.lower():
            template_str = "Conforme a página, o investimento é de {{ preco }}."
        elif "benefícios" in user_question.lower() or "vantagens" in user_question.lower():
            template_str = "Os principais benefícios são: {{ beneficios | join(', ') }}."
        elif "garantia" in user_question.lower():
            template_str = "A página menciona uma garantia de {{ garantia }}."
        elif "comprar" in user_question.lower() or "adquirir" in user_question.lower():
            template_str = "Para adquirir, clique aqui: {{ url }}."
        else:
            template_str = "Olá! Como posso te ajudar com o produto {{ titulo }}?"

        template = Template(template_str)
        try:
            return template.render(structured_data)
        except Exception as e:
            logging.error(f"Erro ao renderizar template: {e}")
            return "Desculpe, não consegui gerar uma resposta precisa no momento. Por favor, reformule sua pergunta."

if __name__ == "__main__":
    # Exemplo de uso
    # Certifique-se de ter OPENROUTER_API_KEY configurada no seu ambiente ou passe-a diretamente
    # os.environ["OPENROUTER_API_KEY"] = "sua_chave_aqui"

    generator = ResponseGenerator()

    sample_data = {
        "titulo": "Curso de Marketing Digital",
        "preco": "R$ 997,00 à vista ou 12x R$ 97,00",
        "beneficios": ["Acesso vitalício", "Certificado", "Mentoria individual"],
        "publico_alvo": "Empreendedores iniciantes",
        "diferenciais": ["Mentoria individual", "Acesso a comunidade"],
        "garantia": "Reembolso em 30 dias",
        "url": "https://exemplo.com/curso"
    }

    print("\n--- Teste com LLM (se API Key configurada) ---")
    print("Pergunta: Qual o preço do curso?")
    response = generator.generate_response("Qual o preço do curso?", sample_data)
    print(f"Resposta: {response}")

    print("\nPergunta: Quais os benefícios?")
    response = generator.generate_response("Quais os benefícios?", sample_data)
    print(f"Resposta: {response}")

    print("\nPergunta: Tem garantia?")
    response = generator.generate_response("Tem garantia?", sample_data)
    print(f"Resposta: {response}")

    print("\nPergunta: Olá!")
    response = generator.generate_response("Olá!", sample_data)
    print(f"Resposta: {response}")

    print("\n--- Teste com histórico de conversa ---")
    history = [
        {"role": "user", "content": "Olá"},
        {"role": "assistant", "content": "Olá! Como posso te ajudar hoje?"}
    ]
    print("Pergunta: Quero saber mais sobre o preço.")
    response = generator.generate_response("Quero saber mais sobre o preço.", sample_data, history)
    print(f"Resposta: {response}")

