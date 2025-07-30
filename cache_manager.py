import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional

class CacheManager:
    def __init__(self, cache_duration_seconds=3600):  # 1 hora por padrão
        """
        Inicializa o gerenciador de cache.
        
        Args:
            cache_duration_seconds (int): Duração do cache em segundos
        """
        self.cache = {}
        self.cache_duration = cache_duration_seconds
        self.logger = logging.getLogger(__name__)
        
    def _generate_cache_key(self, url: str) -> str:
        """
        Gera uma chave única para o cache baseada na URL.
        
        Args:
            url (str): URL da página
            
        Returns:
            str: Chave do cache
        """
        return hashlib.md5(url.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """
        Verifica se uma entrada do cache ainda é válida.
        
        Args:
            cache_entry (dict): Entrada do cache
            
        Returns:
            bool: True se o cache é válido
        """
        current_time = time.time()
        cache_time = cache_entry.get('timestamp', 0)
        return (current_time - cache_time) < self.cache_duration
    
    def get_cached_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Recupera dados do cache se disponíveis e válidos.
        
        Args:
            url (str): URL da página
            
        Returns:
            dict or None: Dados em cache ou None se não disponível
        """
        try:
            cache_key = self._generate_cache_key(url)
            
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                
                if self._is_cache_valid(cache_entry):
                    self.logger.info(f"Cache HIT para URL: {url}")
                    return cache_entry['data']
                else:
                    # Cache expirado, remover
                    del self.cache[cache_key]
                    self.logger.info(f"Cache EXPIRED para URL: {url}")
            
            self.logger.info(f"Cache MISS para URL: {url}")
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar cache: {e}")
            return None
    
    def set_cached_data(self, url: str, data: Dict[str, Any]) -> bool:
        """
        Armazena dados no cache.
        
        Args:
            url (str): URL da página
            data (dict): Dados para armazenar
            
        Returns:
            bool: True se armazenado com sucesso
        """
        try:
            cache_key = self._generate_cache_key(url)
            
            cache_entry = {
                'data': data,
                'timestamp': time.time(),
                'url': url
            }
            
            self.cache[cache_key] = cache_entry
            self.logger.info(f"Dados armazenados no cache para URL: {url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao armazenar no cache: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """
        Limpa todo o cache.
        
        Returns:
            bool: True se limpo com sucesso
        """
        try:
            self.cache.clear()
            self.logger.info("Cache limpo completamente")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao limpar cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            dict: Estatísticas do cache
        """
        try:
            current_time = time.time()
            valid_entries = 0
            expired_entries = 0
            
            for cache_entry in self.cache.values():
                if self._is_cache_valid(cache_entry):
                    valid_entries += 1
                else:
                    expired_entries += 1
            
            return {
                'total_entries': len(self.cache),
                'valid_entries': valid_entries,
                'expired_entries': expired_entries,
                'cache_duration_seconds': self.cache_duration
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas do cache: {e}")
            return {
                'error': str(e)
            }
    
    def cleanup_expired_entries(self) -> int:
        """
        Remove entradas expiradas do cache.
        
        Returns:
            int: Número de entradas removidas
        """
        try:
            expired_keys = []
            
            for cache_key, cache_entry in self.cache.items():
                if not self._is_cache_valid(cache_entry):
                    expired_keys.append(cache_key)
            
            for key in expired_keys:
                del self.cache[key]
            
            self.logger.info(f"Removidas {len(expired_keys)} entradas expiradas do cache")
            return len(expired_keys)
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar entradas expiradas: {e}")
            return 0


class ConversationCache:
    def __init__(self, max_conversations=100, max_messages_per_conversation=20):
        """
        Cache para conversas do chatbot.
        
        Args:
            max_conversations (int): Máximo de conversas a manter
            max_messages_per_conversation (int): Máximo de mensagens por conversa
        """
        self.conversations = {}
        self.max_conversations = max_conversations
        self.max_messages = max_messages_per_conversation
        self.logger = logging.getLogger(__name__)
    
    def add_message(self, conversation_id: str, role: str, content: str):
        """
        Adiciona uma mensagem à conversa.
        
        Args:
            conversation_id (str): ID da conversa
            role (str): 'user' ou 'assistant'
            content (str): Conteúdo da mensagem
        """
        try:
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = {
                    'messages': [],
                    'created_at': time.time(),
                    'last_activity': time.time()
                }
            
            conversation = self.conversations[conversation_id]
            
            # Adicionar nova mensagem
            message = {
                'role': role,
                'content': content,
                'timestamp': time.time()
            }
            
            conversation['messages'].append(message)
            conversation['last_activity'] = time.time()
            
            # Manter apenas as últimas N mensagens
            if len(conversation['messages']) > self.max_messages:
                conversation['messages'] = conversation['messages'][-self.max_messages:]
            
            # Limitar número total de conversas
            if len(self.conversations) > self.max_conversations:
                self._cleanup_old_conversations()
            
            self.logger.info(f"Mensagem adicionada à conversa {conversation_id}")
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar mensagem: {e}")
    
    def get_conversation_history(self, conversation_id: str) -> list:
        """
        Recupera o histórico de uma conversa.
        
        Args:
            conversation_id (str): ID da conversa
            
        Returns:
            list: Lista de mensagens
        """
        try:
            if conversation_id in self.conversations:
                return self.conversations[conversation_id]['messages']
            return []
        except Exception as e:
            self.logger.error(f"Erro ao recuperar histórico: {e}")
            return []
    
    def _cleanup_old_conversations(self):
        """Remove conversas mais antigas para liberar espaço."""
        try:
            # Ordenar por última atividade
            sorted_conversations = sorted(
                self.conversations.items(),
                key=lambda x: x[1]['last_activity']
            )
            
            # Remover as mais antigas
            conversations_to_remove = len(sorted_conversations) - self.max_conversations + 10
            
            for i in range(conversations_to_remove):
                conversation_id = sorted_conversations[i][0]
                del self.conversations[conversation_id]
            
            self.logger.info(f"Removidas {conversations_to_remove} conversas antigas")
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar conversas antigas: {e}")


# Instâncias globais
page_cache = CacheManager(cache_duration_seconds=1800)  # 30 minutos
conversation_cache = ConversationCache()

