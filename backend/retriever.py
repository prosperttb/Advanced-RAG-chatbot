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
    
    def reciprocal_rank_fusion(self, bm25_results: List[Dict], vector_results: List[Dict], k: int = 60) -> List[Dict]:
        scores = {}
        docs = {}
        
        for rank, doc in enumerate(bm25_results):
            chunk_id = doc['chunk_id']
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (rank + k)
            docs[chunk_id] = doc
        
        for rank, doc in enumerate(vector_results):
            chunk_id = doc['chunk_id']
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (rank + k)
            if chunk_id not in docs:
                docs[chunk_id] = doc
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        results = []
        for chunk_id in sorted_ids:
            doc = docs[chunk_id]
            doc['rrf_score'] = scores[chunk_id]
            results.append(doc)
        
        return results
    
    def retrieve(self, query: str, top_k: int = 20) -> List[Dict]:
        bm25_results = self.bm25_search(query, top_k)
        vector_results = self.vector_store.search(query, top_k)
        
        fused_results = self.reciprocal_rank_fusion(bm25_results, vector_results)
        
        return fused_results[:top_k]
