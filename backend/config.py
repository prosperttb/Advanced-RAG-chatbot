import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Chunking Settings
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))
    
    # Retrieval Settings
    TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", 20))
    TOP_K_RERANK = int(os.getenv("TOP_K_RERANK", 5))
    
    # Generation Settings
    CONFIDENCE_THRESHOLD = int(os.getenv("CONFIDENCE_THRESHOLD", 7))
    GROQ_MODEL = "llama-3.1-8b-instant"
    
    # Paths
    DOCUMENTS_PATH = "data/documents"
    UPLOADS_PATH = "data/uploads"
    CHROMA_PATH = "data/chroma_db"
    
    # Embedding Model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

config = Config()