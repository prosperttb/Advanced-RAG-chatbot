import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from config import config

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=config.CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        self.embedder = SentenceTransformer(config.EMBEDDING_MODEL)
    
    def add_documents(self, chunks: List[Dict]):
        """Add document chunks to vector store"""
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedder.encode(texts).tolist()
        
        ids = [chunk['chunk_id'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(self, query: str, top_k: int = 20) -> List[Dict]:
        """Semantic search using embeddings"""
        query_embedding = self.embedder.encode([query])[0].tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        documents = []
        for i in range(len(results['ids'][0])):
            documents.append({
                'chunk_id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return documents
    
    def clear(self):
        """Clear all documents"""
        self.client.delete_collection("documents")
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )