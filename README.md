# RAG Chatbot

A smart document Q&A chatbot that actually knows what it's talking about. Upload your PDFs, Word docs, or even images, and ask questions - it'll search through everything and give you accurate answers with sources.

## What Makes It Different?

Most chatbots just do basic keyword search or pure AI generation. This one does both:
- **Hybrid Search**: Combines old-school keyword matching with modern semantic understanding
- **Smart Reranking**: Double-checks which documents are actually relevant
- **Answer Verification**: The AI reviews its own answers and gives you a confidence score
- **Works Without Documents**: If you ask something not in your files, it uses its general knowledge

## Quick Setup

**You'll need:**
- Python 3.11
- A free Groq API key (sign up at console.groq.com)
- Tesseract OCR for reading images (download for Windows)

**Install:**
```bash
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Configure:**
Create a `.env` file:
```
GROQ_API_KEY=your_key_here
```

**Run:**
```bash
python backend/main.py
```
Then open `frontend/index.html` in your browser.

## Features

- Upload PDFs, Word docs, text files, and images (JPG, PNG, etc.)
- Ask questions in plain English
- Get answers with confidence scores and source citations
- Dark/light mode interface
- Conversation history
- Drag & drop file uploads

## How It Works

1. **Upload**: Your document gets chunked into smart pieces with overlap so context isn't lost
2. **Ask**: Your question triggers both keyword search (BM25) and AI semantic search
3. **Rank**: A reranker model picks the best 5 chunks from the top 20 results
4. **Answer**: The AI reads those chunks and generates an answer
5. **Verify**: The AI checks its own work and gives you a confidence score (1-10)

If confidence is below 7, it tells you it's not sure. If your documents don't have the answer, it'll use its general knowledge and let you know.

## Tech Stack

**Backend:**
- FastAPI (Python web framework)
- Groq (fast LLM inference with Llama 3.1 70B)
- ChromaDB (vector database)
- Sentence Transformers (embeddings)
- BM25 (keyword search)
- Cross-encoder (reranking)
- Tesseract (OCR)

**Frontend:**
- Vanilla HTML/CSS/JavaScript
- No frameworks, just clean code

## File Support

| Format | What Works |
|--------|-----------|
| PDF | Text extraction |
| Word (.docx) | Full support |
| Text (.txt) | UTF-8 |
| Images (.png, .jpg, etc.) | OCR text extraction |

Max file size: 10MB

## Common Issues

**"Backend offline" error?**
Make sure you ran `python backend/main.py` first.

**Images not working?**
Install Tesseract OCR and check the path in `document_processor.py`.

**Empty document error?**
The file might actually be blank, or OCR couldn't read the text. Try a different file.

**Dependency conflicts?**
Delete your venv folder and reinstall with Python 3.11.

## What's Next?

Things I might add:
- Streaming responses (see the answer as it types)
- Excel and PowerPoint support
- Multi-language documents
- Export conversations
- Admin dashboard

## Credits

Built with Groq, ChromaDB, Sentence Transformers, Tesseract OCR, and FastAPI. Thanks to the open-source community for making this possible.

## License

MIT - do whatever you want with it.

---

Made by someone who got tired of searching through PDFs manually
# @legacyttb on x
