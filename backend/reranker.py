from typing import List, Dict

class Reranker:
    def __init__(self):
        pass
    
    def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        if not documents:
            return []
        
        query_words = set(query.lower().split())
        
        for doc in documents:
            doc_words = set(doc['text'].lower().split())
            overlap = len(query_words & doc_words)
            doc['rerank_score'] = overlap / len(query_words) if query_words else 0
        
        reranked = sorted(documents, key=lambda x: x.get('rerank_score', 0), reverse=True)
        
        return reranked[:top_k]
