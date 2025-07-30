import faiss
import numpy as np
import json
import logging
from typing import Dict, List, Any

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class KnowledgeBase:
    def __init__(self, dimension: int = 768): # Dimensão padrão para embeddings comuns
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension) # Usando L2 para distância euclidiana
        self.data_store = [] # Armazena os dados originais e seus IDs
        self.id_counter = 0
        logging.info(f"Base de Conhecimento inicializada com dimensão {dimension}.")

    def _generate_embedding(self, text: str) -> np.ndarray:
        # Placeholder para geração de embedding. Em um ambiente real, usaria um modelo como Sentence-BERT.
        # Para demonstração, uma abordagem simples (e ineficaz para busca semântica real) é usada.
        # Isso DEVE ser substituído por um modelo de embedding adequado.
        logging.warning("Usando placeholder para geração de embedding. Substitua por um modelo real para busca semântica eficaz.")
        # Simplesmente cria um vetor de floats baseado no hash do texto para garantir unicidade e dimensão.
        # Isso NÃO é um embedding semântico.
        np.random.seed(hash(text) % (2**32 - 1)) # Garante o mesmo 'embedding' para o mesmo texto
        return np.random.rand(self.dimension).astype("float32")

    def add_document(self, document: Dict[str, Any], text_for_embedding: str):
        doc_id = self.id_counter
        self.id_counter += 1
        
        embedding = self._generate_embedding(text_for_embedding)
        self.index.add(np.array([embedding]))
        
        self.data_store.append({"id": doc_id, "document": document, "embedding_text": text_for_embedding})
        logging.info(f"Documento com ID {doc_id} adicionado à Base de Conhecimento.")

    def search(self, query_text: str, k: int = 1) -> List[Dict[str, Any]]:
        query_embedding = self._generate_embedding(query_text)
        D, I = self.index.search(np.array([query_embedding]), k) # D: distâncias, I: índices
        
        results = []
        for i in I[0]:
            if i != -1: # FAISS retorna -1 para resultados vazios
                results.append(self.data_store[i]["document"])
        logging.info(f"Busca por '{query_text}' retornou {len(results)} resultados.")
        return results

    def get_all_documents(self) -> List[Dict[str, Any]]:
        return [item["document"] for item in self.data_store]

if __name__ == "__main__":
    kb = KnowledgeBase(dimension=768) # Exemplo com dimensão 768

    # Exemplo de dados de página de vendas
    page_data_1 = {
        "titulo": "Curso de Marketing Digital Avançado",
        "preco": "R$ 997,00",
        "beneficios": ["Acesso vitalício", "Certificado", "Mentoria"],
        "publico_alvo": "Empreendedores experientes",
        "garantia": "Reembolso em 30 dias"
    }
    text_for_embedding_1 = json.dumps(page_data_1, ensure_ascii=False)
    kb.add_document(page_data_1, text_for_embedding_1)

    page_data_2 = {
        "titulo": "Ebook de Vendas Rápidas",
        "preco": "R$ 49,90",
        "beneficios": ["Técnicas comprovadas", "Download imediato"],
        "publico_alvo": "Iniciantes em vendas",
        "garantia": "Satisfação garantida"
    }
    text_for_embedding_2 = json.dumps(page_data_2, ensure_ascii=False)
    kb.add_document(page_data_2, text_for_embedding_2)

    # Testando a busca
    print("\n--- Teste de Busca ---")
    query = "Qual o preço do curso?"
    results = kb.search(query)
    print(f"Resultados para '{query}':")
    for res in results:
        print(json.dumps(res, indent=2, ensure_ascii=False))

    query = "Quero algo para iniciantes"
    results = kb.search(query)
    print(f"\nResultados para '{query}':")
    for res in results:
        print(json.dumps(res, indent=2, ensure_ascii=False))

    print("\n--- Todos os Documentos ---")
    print(json.dumps(kb.get_all_documents(), indent=2, ensure_ascii=False))

