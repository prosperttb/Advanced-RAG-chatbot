import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import shutil
import uuid

from config import config
from document_processor import DocumentProcessor
from vector_store import VectorStore
from retriever import HybridRetriever
from reranker import Reranker
from generator import Generator
from chat_manager import ChatManager

app = FastAPI(title="RAG Chatbot API")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processor = DocumentProcessor(config.CHUNK_SIZE, config.CHUNK_OVERLAP)
vector_store = VectorStore()
retriever = HybridRetriever(vector_store)
reranker = Reranker()
generator = Generator()
chat_manager = ChatManager()

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    confidence: int
    sources: List[dict]
    conversation_id: str

class DocumentResponse(BaseModel):
    message: str
    chunks_created: int
    filename: str

os.makedirs(config.DOCUMENTS_PATH, exist_ok=True)
os.makedirs(config.UPLOADS_PATH, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    documents_path = Path(config.DOCUMENTS_PATH)
    
    if documents_path.exists():
        all_chunks = []
        
        for file_path in documents_path.glob("*.*"):
            if file_path.suffix.lower() in ['.pdf', '.txt', '.docx', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                try:
                    chunks = processor.process_document(str(file_path))
                    all_chunks.extend(chunks)
                    print(f"Loaded: {file_path.name} ({len(chunks)} chunks)")
                except Exception as e:
                    print(f"Error loading {file_path.name}: {e}")
        
        if all_chunks:
            vector_store.add_documents(all_chunks)
            retriever.build_bm25_index(all_chunks)
            print(f"✓ Indexed {len(all_chunks)} chunks")

@app.get("/")
async def root():
    return {"message": "RAG Chatbot API is running", "status": "healthy"}

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    try:
        file_path = Path(config.UPLOADS_PATH) / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        chunks = processor.process_document(str(file_path))
        
        vector_store.add_documents(chunks)
        
        retriever.bm25_corpus.extend([chunk['text'] for chunk in chunks])
        retriever.bm25_metadata.extend(chunks)
        
        return DocumentResponse(
            message="Document uploaded and processed successfully",
            chunks_created=len(chunks),
            filename=file.filename
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        chat_manager.add_message(conversation_id, "user", request.query)
        
        retrieved_docs = retriever.retrieve(request.query, config.TOP_K_RETRIEVAL)
        
        if not retrieved_docs:
            return QueryResponse(
                answer="I don't have any documents to answer from. Please upload documents first.",
                confidence=0,
                sources=[],
                conversation_id=conversation_id
            )
        
        reranked_docs = reranker.rerank(request.query, retrieved_docs, config.TOP_K_RERANK)
        
        result = generator.generate_with_verification(request.query, reranked_docs)
        
        chat_manager.add_message(
            conversation_id, 
            "assistant", 
            result['answer'],
            metadata={'confidence': result['confidence']}
        )
        
        return QueryResponse(
            answer=result['answer'],
            confidence=result['confidence'],
            sources=result['sources'],
            conversation_id=conversation_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{conversation_id}")
async def get_history(conversation_id: str):
    history = chat_manager.get_conversation(conversation_id)
    return {"conversation_id": conversation_id, "messages": history}

@app.delete("/clear")
async def clear_documents():
    try:
        vector_store.clear()
        retriever.bm25_index = None
        retriever.bm25_corpus = []
        retriever.bm25_metadata = []
        return {"message": "All documents cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": config.GROQ_MODEL}
```

PORT=8000
