import re
from typing import List, Dict
import PyPDF2
import docx
from pathlib import Path
from PIL import Image
import os

try:
    import pytesseract
    tesseract_path = os.getenv("TESSERACT_PATH", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

class DocumentProcessor:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load_document(self, file_path: str) -> str:
        path = Path(file_path)
        
        if path.suffix == '.pdf':
            return self._load_pdf(file_path)
        elif path.suffix in ['.docx', '.doc']:
            return self._load_docx(file_path)
        elif path.suffix == '.txt':
            return self._load_txt(file_path)
        elif path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return self._load_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    def _load_pdf(self, file_path: str) -> str:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _load_docx(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    
    def _load_txt(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def _load_image(self, file_path: str) -> str:
        if not TESSERACT_AVAILABLE:
            return "OCR functionality is not available on this server. Image text extraction is disabled. Please upload PDF, DOCX, or TXT files for text-based content."
        
        try:
            import pytesseract
            tesseract_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', None)
            if tesseract_cmd and not os.path.exists(tesseract_cmd):
                return "OCR functionality is not available on this server. Image text extraction is disabled. Please upload PDF, DOCX, or TXT files for text-based content."
            
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            
            if not text or len(text.strip()) < 10:
                return "No text could be extracted from this image. The image may be blank, contain only graphics, or have low quality text."
            
            return text
        except Exception as e:
            return f"OCR functionality is not available on this server. Image text extraction failed. Please upload PDF, DOCX, or TXT files for text-based content."
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        text = re.sub(r'\s+', ' ', text).strip()
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'metadata': metadata or {},
                    'length': current_length
                })
                
                overlap_words = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    overlap_length += len(s.split())
                    if overlap_length >= self.chunk_overlap:
                        break
                    overlap_words.insert(0, s)
                
                current_chunk = overlap_words + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append({
                'text': ' '.join(current_chunk),
                'metadata': metadata or {},
                'length': current_length
            })
        
        return chunks
    
    def process_document(self, file_path: str) -> List[Dict]:
        text = self.load_document(file_path)
        
        text_cleaned = text.strip()
        if len(text_cleaned) < 50:
            raise ValueError(
                f"Document appears to be empty or contains too little text. "
                f"Extracted only {len(text_cleaned)} characters. "
                f"This might be a blank document, image with no text, or corrupted file."
            )
        
        path = Path(file_path)
        metadata = {
            'source': path.name,
            'file_type': path.suffix,
            'file_path': str(path)
        }
        
        chunks = self.chunk_text(text, metadata)
        
        for idx, chunk in enumerate(chunks):
            chunk['chunk_id'] = f"{path.stem}_chunk_{idx}"
        
        return chunks
