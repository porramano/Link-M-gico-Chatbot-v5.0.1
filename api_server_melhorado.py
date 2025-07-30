from flask import Flask, request, jsonify
from flask_cors import CORS
from data_extractor_melhorado import extract_data_from_url
from response_generator_melhorado import ResponseGenerator
from cache_manager_melhorado import page_cache, conversation_cache, get_cache_stats
import logging
import os
from datetime import datetime

# Configuração da aplicação Flask
app = Flask(__name__)
CORS(app)  # Permite requisições de qualquer origem

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api_server.log"),
        logging.StreamHandler()
    ]
)

# Inicializa o ResponseGenerator com as chaves de API
response_generator = ResponseGenerator(
    llm_api_key=os.getenv("OPENROUTER_API_KEY"),
    llm_model=os.getenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
)

@app.route("/", methods=["GET"])
def health_check():
    """Endpoint de verificação de saúde da API."""
    return jsonify({
        "status": "online",
        "service": "LinkMágico Chatbot API",
        "version": "5.0.1",
        "timestamp": datetime.now().isoformat(),
        "cache_stats": get_cache_stats()
    })

@app.route("/extract_data", methods=["POST"])
def extract_data():
    """
    Extrai dados estruturados de uma página de vendas.
    
    Body JSON:
    {
        "url": "https://exemplo.com/produto"
    }
    """
    try:
        data = request.json
        if not data or not data.get("url"):
            return jsonify({"error": "URL é obrigatória"}), 400

        url = data["url"]
        logging.info(f"Solicitação de extração de dados para: {url}")

        # Verifica cache primeiro
        cached_data = page_cache.get_cached_data(url)
        if cached_data:
            logging.info(f"Dados encontrados no cache para: {url}")
            return jsonify({
                "data": cached_data.get("data", cached_data),
                "cached": True,
                "timestamp": cached_data.get("cached_at")
            })

        # Extrai dados da página
        logging.info(f"Extraindo dados de: {url}")
        structured_data = extract_data_from_url(url)

        if structured_data:
            # Armazena no cache
            page_cache.set_cached_data(url, structured_data)
            
            logging.info(f"Dados extraídos com sucesso para: {url}")
            return jsonify({
                "data": structured_data,
                "cached": False,
                "timestamp": datetime.now().isoformat()
            })
        else:
            logging.error(f"Falha na extração de dados para: {url}")
            return jsonify({
                "error": "Não foi possível extrair dados da URL fornecida."
            }), 500

    except Exception as e:
        logging.error(f"Erro no endpoint extract_data: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route("/generate_response", methods=["POST"])
def generate_response():
    """
    Gera resposta do chatbot baseada na pergunta do usuário e dados da página.
    
    Body JSON:
    {
        "user_question": "Qual o preço?",
        "structured_data": {...},
        "session_id": "session_123",
        "instructions": "Seja mais formal" (opcional)
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados JSON são obrigatórios"}), 400

        user_question = data.get("user_question")
        structured_data = data.get("structured_data", {})
        session_id = data.get("session_id")
        instructions = data.get("instructions", "")

        if not user_question or not session_id:
            return jsonify({
                "error": "user_question e session_id são obrigatórios"
            }), 400

        logging.info(f"Gerando resposta para sessão: {session_id}")
        logging.info(f"Pergunta: {user_question}")

        # Recupera histórico da conversa
        conversation_history = conversation_cache.get_conversation_history(session_id)

        # Gera resposta usando o ResponseGenerator
        response_text = response_generator.generate_response(
            user_question=user_question,
            structured_data=structured_data,
            conversation_history=conversation_history,
            instructions=instructions
        )

        if not response_text:
            response_text = "Desculpe, não consegui gerar uma resposta no momento. Pode reformular sua pergunta?"

        # Adiciona mensagens ao histórico
        conversation_cache.add_message(session_id, "user", user_question)
        conversation_cache.add_message(session_id, "assistant", response_text)

        logging.info(f"Resposta gerada com sucesso para sessão: {session_id}")
        
        return jsonify({
            "response": response_text,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "conversation_length": len(conversation_history) + 2
        })

    except Exception as e:
        logging.error(f"Erro no endpoint generate_response: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route("/conversation/<session_id>", methods=["GET"])
def get_conversation(session_id):
    """
    Recupera o histórico de conversa para uma sessão.
    
    Parâmetros:
    - session_id: ID da sessão
    """
    try:
        history = conversation_cache.get_conversation_history(session_id)
        return jsonify({
            "session_id": session_id,
            "history": history,
            "message_count": len(history),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Erro ao recuperar conversa: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route("/conversation/<session_id>", methods=["DELETE"])
def clear_conversation(session_id):
    """
    Limpa o histórico de conversa para uma sessão.
    
    Parâmetros:
    - session_id: ID da sessão
    """
    try:
        success = conversation_cache.clear_conversation(session_id)
        return jsonify({
            "session_id": session_id,
            "cleared": success,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Erro ao limpar conversa: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route("/cache/stats", methods=["GET"])
def cache_stats():
    """Retorna estatísticas do cache."""
    try:
        stats = get_cache_stats()
        return jsonify({
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Erro ao obter estatísticas do cache: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route("/cache/invalidate", methods=["POST"])
def invalidate_cache():
    """
    Invalida cache para uma URL específica.
    
    Body JSON:
    {
        "url": "https://exemplo.com/produto"
    }
    """
    try:
        data = request.json
        if not data or not data.get("url"):
            return jsonify({"error": "URL é obrigatória"}), 400

        url = data["url"]
        success = page_cache.invalidate_cache(url)
        
        return jsonify({
            "url": url,
            "invalidated": success,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Erro ao invalidar cache: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.errorhandler(404)
def not_found(error):
    """Handler para rotas não encontradas."""
    return jsonify({
        "error": "Endpoint não encontrado",
        "available_endpoints": [
            "GET /",
            "POST /extract_data",
            "POST /generate_response",
            "GET /conversation/<session_id>",
            "DELETE /conversation/<session_id>",
            "GET /cache/stats",
            "POST /cache/invalidate"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos."""
    logging.error(f"Erro interno: {error}")
    return jsonify({
        "error": "Erro interno do servidor",
        "message": "Verifique os logs para mais detalhes"
    }), 500

if __name__ == "__main__":
    # Carrega variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv()
    
    # Configurações do servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logging.info(f"Iniciando API Server na porta {port}")
    logging.info(f"Debug mode: {debug}")
    logging.info(f"Redis URL: {os.getenv('REDIS_URL', 'redis://localhost:6379')}")
    logging.info(f"OpenRouter API Key: {'Configurada' if os.getenv('OPENROUTER_API_KEY') else 'Não configurada'}")
    logging.info(f"ScrapingBee API Key: {'Configurada' if os.getenv('SCRAPINGBEE_API_KEY') else 'Não configurada'}")
    
    app.run(host=host, port=port, debug=debug)

