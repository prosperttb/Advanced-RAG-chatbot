from typing import List, Dict

class VectorStore:
    def __init__(self):
        self.documents = []
    
    def add_documents(self, chunks: List[Dict]):
        self.documents.extend(chunks)
    
    def search(self, query: str, top_k: int = 20) -> List[Dict]:
        return []
    
    def clear(self):
        self.documents = []
