import json
import logging
import re
from collections import Counter

class KnowledgeBase:
    def __init__(self, dimension=768):
        """
        Inicializa o banco de conhecimento.
        
        Args:
            dimension (int): Dimensão dos embeddings (mantido para compatibilidade)
        """
        self.dimension = dimension
        self.documents = []
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def add_document(self, metadata, text_content):
        """
        Adiciona um documento ao banco de conhecimento.
        
        Args:
            metadata (dict): Metadados do documento (título, preço, benefícios, etc.)
            text_content (str): Conteúdo textual completo do documento
        """
        try:
            document = {
                'id': len(self.documents),
                'metadata': metadata,
                'text_content': text_content,
                'timestamp': json.dumps(metadata, ensure_ascii=False)
            }
            
            self.documents.append(document)
            self.logger.info(f"Documento adicionado ao KB: {metadata.get('title', 'Sem título')}")
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar documento ao KB: {e}")
    
    def _simple_similarity(self, query, text):
        """
        Calcula similaridade simples baseada em palavras-chave.
        
        Args:
            query (str): Consulta do usuário
            text (str): Texto para comparar
            
        Returns:
            float: Score de similaridade (0-1)
        """
        try:
            # Normalizar textos
            query_words = set(re.findall(r'\b\w+\b', query.lower()))
            text_words = set(re.findall(r'\b\w+\b', text.lower()))
            
            # Calcular interseção
            intersection = query_words.intersection(text_words)
            union = query_words.union(text_words)
            
            if not union:
                return 0.0
            
            return len(intersection) / len(union)
            
        except Exception as e:
            self.logger.error(f"Erro no cálculo de similaridade: {e}")
            return 0.0
    
    def search_similar(self, query, top_k=3):
        """
        Busca documentos similares à consulta.
        
        Args:
            query (str): Consulta do usuário
            top_k (int): Número de documentos mais similares a retornar
            
        Returns:
            list: Lista de documentos similares com scores
        """
        try:
            if not self.documents:
                self.logger.warning("KB vazio")
                return []
            
            results = []
            
            for doc in self.documents:
                # Calcular similaridade com diferentes campos
                text_content = doc['text_content']
                metadata = doc['metadata']
                
                # Combinar texto de diferentes campos
                combined_text = f"{metadata.get('title', '')} {metadata.get('description', '')} "
                combined_text += " ".join(metadata.get('benefits', []))
                combined_text += f" {text_content}"
                
                score = self._simple_similarity(query, combined_text)
                
                if score > 0.1:  # Threshold mínimo
                    results.append({
                        'document': doc,
                        'score': score
                    })
            
            # Ordenar por score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            self.logger.info(f"Encontrados {len(results[:top_k])} documentos similares para: {query}")
            return results[:top_k]
            
        except Exception as e:
            self.logger.error(f"Erro na busca por similaridade: {e}")
            return []
    
    def get_context_for_query(self, query, max_context_length=1000):
        """
        Obtém contexto relevante para uma consulta.
        
        Args:
            query (str): Consulta do usuário
            max_context_length (int): Tamanho máximo do contexto
            
        Returns:
            str: Contexto relevante concatenado
        """
        try:
            similar_docs = self.search_similar(query, top_k=2)
            
            if not similar_docs:
                return ""
            
            context_parts = []
            current_length = 0
            
            for doc_info in similar_docs:
                doc = doc_info['document']
                metadata = doc['metadata']
                
                # Criar contexto estruturado
                context_part = f"Produto: {metadata.get('title', 'N/A')}\n"
                context_part += f"Preço: {metadata.get('price', 'N/A')}\n"
                
                if metadata.get('benefits'):
                    context_part += f"Benefícios: {', '.join(metadata['benefits'][:3])}\n"
                
                if metadata.get('description'):
                    context_part += f"Descrição: {metadata['description'][:200]}...\n"
                
                context_part += "\n"
                
                if current_length + len(context_part) <= max_context_length:
                    context_parts.append(context_part)
                    current_length += len(context_part)
                else:
                    break
            
            return "\n".join(context_parts)
            
        except Exception as e:
            self.logger.error(f"Erro ao obter contexto: {e}")
            return ""

