import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))
    
    TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", 20))
    TOP_K_RERANK = int(os.getenv("TOP_K_RERANK", 5))
    
    CONFIDENCE_THRESHOLD = int(os.getenv("CONFIDENCE_THRESHOLD", 7))
    GROQ_MODEL = "llama-3.3-70b-versatile"
    
    DOCUMENTS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "documents")
    UPLOADS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "uploads")

config = Config()
