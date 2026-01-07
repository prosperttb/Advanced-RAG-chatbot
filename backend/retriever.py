from rank_bm25 import BM25Okapi
from typing import List, Dict
import numpy as np

class HybridRetriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.bm25_index = None
        self.bm25_corpus = []
        self.bm25_metadata = []
    
    def build_bm25_index(self, chunks: List[Dict]):
        self.bm25_corpus = [chunk['text'] for chunk in chunks]
        self.bm25_metadata = chunks
        
        tokenized_corpus = [doc.lower().split() for doc in self.bm25_corpus]
        self.bm25_index = BM25Okapi(tokenized_corpus)
    
    def bm25_search(self, query: str, top_k: int = 20) -> List[Dict]:
        if not self.bm25_index:
            return []
        
        tokenized_query = query.lower().split()
        scores = self.bm25_index.get_scores(tokenized_query)
        
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    'text': self.bm25_corpus[idx],
                    'metadata': self.bm25_metadata[idx]['metadata'],
                    'chunk_id': self.bm25_metadata[idx]['chunk_id'],
                    'bm25_score': float(scores[idx])
                })
        
        return results
    
    def retrieve(self, query: str, top_k: int = 20) -> List[Dict]:
        return self.bm25_search(query, top_k)
