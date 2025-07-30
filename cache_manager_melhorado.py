import redis
import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class CacheManager:
    def __init__(self, redis_url: str = None, default_ttl: int = 3600):
        """
        Inicializa o gerenciador de cache com Redis.
        
        Args:
            redis_url: URL de conexão do Redis
            default_ttl: Tempo de vida padrão do cache em segundos (1 hora)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.default_ttl = default_ttl
        self.redis_client = None
        self._connect()

    def _connect(self):
        """Conecta ao Redis com tratamento de erro."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Testa a conexão
            self.redis_client.ping()
            logging.info("Conectado ao Redis com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao conectar ao Redis: {e}")
            logging.warning("Cache será desabilitado. Funcionando sem persistência.")
            self.redis_client = None

    def _is_connected(self) -> bool:
        """Verifica se a conexão com Redis está ativa."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            logging.warning("Conexão com Redis perdida. Tentando reconectar...")
            self._connect()
            return self.redis_client is not None

class PageCache(CacheManager):
    """Gerencia cache de dados extraídos de páginas."""
    
    def __init__(self, redis_url: str = None):
        super().__init__(redis_url, default_ttl=7200)  # 2 horas para dados de página
        self.prefix = "page_data:"

    def get_cached_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Recupera dados em cache para uma URL.
        
        Args:
            url: URL da página
            
        Returns:
            Dados em cache ou None se não encontrado
        """
        if not self._is_connected():
            return None
            
        try:
            cache_key = f"{self.prefix}{url}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logging.info(f"Dados encontrados no cache para: {url}")
                return data
            
            logging.info(f"Nenhum dado em cache para: {url}")
            return None
            
        except Exception as e:
            logging.error(f"Erro ao recuperar dados do cache: {e}")
            return None

    def set_cached_data(self, url: str, data: Dict[str, Any], ttl: int = None) -> bool:
        """
        Armazena dados no cache para uma URL.
        
        Args:
            url: URL da página
            data: Dados a serem armazenados
            ttl: Tempo de vida em segundos (opcional)
            
        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        if not self._is_connected():
            return False
            
        try:
            cache_key = f"{self.prefix}{url}"
            
            # Adiciona metadados
            cache_data = {
                "data": data,
                "cached_at": datetime.now().isoformat(),
                "url": url
            }
            
            ttl = ttl or self.default_ttl
            success = self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data, ensure_ascii=False)
            )
            
            if success:
                logging.info(f"Dados armazenados no cache para: {url} (TTL: {ttl}s)")
                return True
            else:
                logging.warning(f"Falha ao armazenar dados no cache para: {url}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao armazenar dados no cache: {e}")
            return False

    def invalidate_cache(self, url: str) -> bool:
        """
        Remove dados do cache para uma URL específica.
        
        Args:
            url: URL da página
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        if not self._is_connected():
            return False
            
        try:
            cache_key = f"{self.prefix}{url}"
            result = self.redis_client.delete(cache_key)
            
            if result:
                logging.info(f"Cache invalidado para: {url}")
                return True
            else:
                logging.info(f"Nenhum cache encontrado para invalidar: {url}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao invalidar cache: {e}")
            return False

class ConversationCache(CacheManager):
    """Gerencia cache de histórico de conversas."""
    
    def __init__(self, redis_url: str = None):
        super().__init__(redis_url, default_ttl=86400)  # 24 horas para conversas
        self.prefix = "conversation:"
        self.max_messages = 50  # Máximo de mensagens por conversa

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Recupera o histórico de conversa para uma sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Lista de mensagens da conversa
        """
        if not self._is_connected():
            return []
            
        try:
            cache_key = f"{self.prefix}{session_id}"
            cached_history = self.redis_client.get(cache_key)
            
            if cached_history:
                history = json.loads(cached_history)
                logging.info(f"Histórico recuperado para sessão: {session_id} ({len(history)} mensagens)")
                return history
            
            logging.info(f"Nenhum histórico encontrado para sessão: {session_id}")
            return []
            
        except Exception as e:
            logging.error(f"Erro ao recuperar histórico de conversa: {e}")
            return []

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Adiciona uma mensagem ao histórico de conversa.
        
        Args:
            session_id: ID da sessão
            role: Papel (user ou assistant)
            content: Conteúdo da mensagem
            
        Returns:
            True se adicionado com sucesso, False caso contrário
        """
        if not self._is_connected():
            return False
            
        try:
            # Recupera histórico atual
            history = self.get_conversation_history(session_id)
            
            # Adiciona nova mensagem
            new_message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            history.append(new_message)
            
            # Limita o número de mensagens
            if len(history) > self.max_messages:
                history = history[-self.max_messages:]
            
            # Salva histórico atualizado
            cache_key = f"{self.prefix}{session_id}"
            success = self.redis_client.setex(
                cache_key,
                self.default_ttl,
                json.dumps(history, ensure_ascii=False)
            )
            
            if success:
                logging.info(f"Mensagem adicionada à sessão: {session_id}")
                return True
            else:
                logging.warning(f"Falha ao adicionar mensagem à sessão: {session_id}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao adicionar mensagem: {e}")
            return False

    def clear_conversation(self, session_id: str) -> bool:
        """
        Limpa o histórico de uma conversa específica.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            True se limpo com sucesso, False caso contrário
        """
        if not self._is_connected():
            return False
            
        try:
            cache_key = f"{self.prefix}{session_id}"
            result = self.redis_client.delete(cache_key)
            
            if result:
                logging.info(f"Conversa limpa para sessão: {session_id}")
                return True
            else:
                logging.info(f"Nenhuma conversa encontrada para limpar: {session_id}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao limpar conversa: {e}")
            return False

    def get_active_sessions(self) -> List[str]:
        """
        Retorna lista de sessões ativas.
        
        Returns:
            Lista de IDs de sessões ativas
        """
        if not self._is_connected():
            return []
            
        try:
            pattern = f"{self.prefix}*"
            keys = self.redis_client.keys(pattern)
            sessions = [key.replace(self.prefix, "") for key in keys]
            
            logging.info(f"Encontradas {len(sessions)} sessões ativas")
            return sessions
            
        except Exception as e:
            logging.error(f"Erro ao recuperar sessões ativas: {e}")
            return []

# Instâncias globais para uso na aplicação
page_cache = PageCache()
conversation_cache = ConversationCache()

def get_cache_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas do cache.
    
    Returns:
        Dicionário com estatísticas
    """
    stats = {
        "redis_connected": False,
        "active_sessions": 0,
        "cached_pages": 0,
        "redis_info": {}
    }
    
    try:
        if page_cache._is_connected():
            stats["redis_connected"] = True
            
            # Conta sessões ativas
            sessions = conversation_cache.get_active_sessions()
            stats["active_sessions"] = len(sessions)
            
            # Conta páginas em cache
            page_keys = page_cache.redis_client.keys(f"{page_cache.prefix}*")
            stats["cached_pages"] = len(page_keys)
            
            # Informações do Redis
            redis_info = page_cache.redis_client.info()
            stats["redis_info"] = {
                "used_memory_human": redis_info.get("used_memory_human", "N/A"),
                "connected_clients": redis_info.get("connected_clients", 0),
                "total_commands_processed": redis_info.get("total_commands_processed", 0)
            }
            
    except Exception as e:
        logging.error(f"Erro ao obter estatísticas do cache: {e}")
    
    return stats

if __name__ == "__main__":
    # Teste do sistema de cache
    print("=== TESTE DO SISTEMA DE CACHE ===\n")
    
    # Teste do cache de páginas
    print("1. Testando cache de páginas...")
    test_url = "https://exemplo.com/produto"
    test_data = {
        "titulo": "Produto Teste",
        "preco": "R$ 100,00",
        "beneficios": ["Benefício 1", "Benefício 2"]
    }
    
    # Armazenar
    success = page_cache.set_cached_data(test_url, test_data)
    print(f"   Armazenamento: {'✓' if success else '✗'}")
    
    # Recuperar
    cached = page_cache.get_cached_data(test_url)
    print(f"   Recuperação: {'✓' if cached else '✗'}")
    
    # Teste do cache de conversas
    print("\n2. Testando cache de conversas...")
    test_session = "session_123"
    
    # Adicionar mensagens
    conversation_cache.add_message(test_session, "user", "Olá!")
    conversation_cache.add_message(test_session, "assistant", "Oi! Como posso ajudar?")
    conversation_cache.add_message(test_session, "user", "Qual o preço?")
    
    # Recuperar histórico
    history = conversation_cache.get_conversation_history(test_session)
    print(f"   Mensagens no histórico: {len(history)}")
    
    # Estatísticas
    print("\n3. Estatísticas do cache:")
    stats = get_cache_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n=== TESTE CONCLUÍDO ===")

