from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import logging
import json

# Importar os módulos Python desenvolvidos
from data_extractor import extract_data_from_url
from analyzer import analyze_text
from knowledge_base_simple import KnowledgeBase
from response_generator import ResponseGenerator
from precision_optimizer import PrecisionOptimizer
from cache_manager import page_cache, conversation_cache

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas as rotas

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Inicializar componentes globais
kb = KnowledgeBase(dimension=768)
response_gen = ResponseGenerator(llm_api_key=os.getenv("OPENROUTER_API_KEY"))

@app.route("/extract_and_process", methods=["POST"])
def extract_and_process():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL é obrigatória"}), 400

    try:
        # Verificar cache primeiro
        cached_data = page_cache.get_cached_data(url)
        if cached_data:
            logging.info(f"Dados recuperados do cache para {url}")
            return jsonify({
                "extracted_data": cached_data,
                "analysis_results": {"cached": True},
                "from_cache": True
            })

        # Módulo 1: Extração de Dados
        extracted_data = asyncio.run(extract_data_from_url(url))
        logging.info(f"Dados extraídos para {url}: {extracted_data}")

        # Armazenar no cache
        page_cache.set_cached_data(url, extracted_data)

        # Módulo 2: Análise Estruturada
        analysis_input_text = extracted_data.get("titulo", "") + "\n" + "\n".join(extracted_data.get("beneficios", []))
        analysis_results = analyze_text(analysis_input_text, extracted_data)
        logging.info(f"Resultados da análise: {analysis_results}")

        # Módulo 3: Banco de Conhecimento
        kb.add_document(extracted_data, json.dumps(extracted_data, ensure_ascii=False))
        logging.info("Dados adicionados ao Banco de Conhecimento.")

        return jsonify({
            "extracted_data": extracted_data,
            "analysis_results": analysis_results,
            "from_cache": False
        })
    except Exception as e:
        logging.error(f"Erro no endpoint /extract_and_process: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/generate_response", methods=["POST"])
def generate_ai_response():
    data = request.json
    user_message = data.get("user_message")
    page_data = data.get("page_data")
    conversation_history = data.get("conversation_history", [])
    conversation_id = data.get("conversation_id", "default")

    if not user_message or not page_data:
        return jsonify({"error": "Mensagem do usuário e dados da página são obrigatórios"}), 400

    try:
        # Adicionar mensagem do usuário ao cache de conversa
        conversation_cache.add_message(conversation_id, "user", user_message)
        
        # Recuperar histórico da conversa do cache
        cached_history = conversation_cache.get_conversation_history(conversation_id)
        
        # Usar histórico do cache se disponível, senão usar o fornecido
        if cached_history:
            conversation_history = cached_history[-10:]  # Últimas 10 mensagens

        # Módulo 4: Gerador de Respostas
        response = response_gen.generate_response(user_message, page_data, conversation_history)
        logging.info(f"Resposta gerada: {response}")

        # Adicionar resposta da IA ao cache de conversa
        conversation_cache.add_message(conversation_id, "assistant", response)

        return jsonify({
            "response": response,
            "conversation_id": conversation_id
        })
    except Exception as e:
        logging.error(f"Erro no endpoint /generate_response: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/cache/stats", methods=["GET"])
def cache_stats():
    """Endpoint para verificar estatísticas do cache."""
    try:
        stats = page_cache.get_cache_stats()
        return jsonify({
            "page_cache": stats,
            "conversation_cache": {
                "active_conversations": len(conversation_cache.conversations),
                "max_conversations": conversation_cache.max_conversations,
                "max_messages_per_conversation": conversation_cache.max_messages
            }
        })
    except Exception as e:
        logging.error(f"Erro ao obter estatísticas do cache: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/cache/clear", methods=["POST"])
def clear_cache():
    """Endpoint para limpar o cache."""
    try:
        page_cache.clear_cache()
        conversation_cache.conversations.clear()
        return jsonify({"message": "Cache limpo com sucesso"})
    except Exception as e:
        logging.error(f"Erro ao limpar cache: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "OK",
        "message": "API Python funcionando com cache otimizado",
        "version": "1.1.0",
        "cache_stats": page_cache.get_cache_stats()
    })



