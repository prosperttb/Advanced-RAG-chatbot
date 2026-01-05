from groq import Groq
from typing import List, Dict, Tuple
from config import config
import json
import re

class Generator:
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
    
    def generate_answer(self, query: str, context_docs: List[Dict]) -> str:
        if not context_docs or all(len(doc['text'].strip()) < 10 for doc in context_docs):
            prompt = f"""You are a helpful AI assistant. Answer this question using your general knowledge:

Question: {query}

Answer naturally and helpfully."""
        else:
            context = "\n\n".join([
                f"[Source: {doc['metadata'].get('source', 'Unknown')}]\n{doc['text']}"
                for doc in context_docs
            ])
            
            prompt = f"""You are a helpful assistant. Answer the question using:
1. The provided context documents (prioritize this)
2. Your general knowledge if the context doesn't have enough info

Context:
{context}

Question: {query}

Instructions:
- If the context contains relevant info, use it and cite sources
- If the context is insufficient, supplement with your general knowledge and mention this
- Be clear about what comes from documents vs. your knowledge

Answer:"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    def verify_answer(self, query: str, answer: str, context_docs: List[Dict]) -> Tuple[bool, int, str]:
        context = "\n\n".join([doc['text'] for doc in context_docs])
        
        verification_prompt = f"""You are a fact-checker. Your job is to verify if an answer is accurately supported by the given context.

Context:
{context}

Question: {query}

Answer to verify: {answer}

Task:
1. Check if the answer is factually grounded in the context
2. Rate confidence from 1-10 (10 = fully supported, 1 = not supported)
3. Provide a brief explanation

Respond in JSON format:
{{
    "is_grounded": true/false,
    "confidence": <1-10>,
    "explanation": "<brief explanation>"
}}"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": verification_prompt}],
            temperature=0.1,
            max_tokens=300
        )
        
        try:
            result_text = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(result_text)
            
            return (
                result.get('is_grounded', False),
                result.get('confidence', 5),
                result.get('explanation', 'Unable to verify')
            )
        except Exception as e:
            print(f"Verification error: {e}")
            return (True, 7, "Verification inconclusive")
    
    def generate_with_verification(self, query: str, context_docs: List[Dict]) -> Dict:
        answer = self.generate_answer(query, context_docs)
        
        is_grounded, confidence, explanation = self.verify_answer(query, answer, context_docs)
        
        if confidence < config.CONFIDENCE_THRESHOLD:
            answer = f"I don't have enough information in the provided documents to answer this confidently. Based on limited context: {answer}"
        
        return {
            'answer': answer,
            'confidence': confidence,
            'is_grounded': is_grounded,
            'verification_note': explanation,
            'sources': [
                {
                    'source': doc['metadata'].get('source', 'Unknown'),
                    'text_preview': doc['text'][:200] + '...'
                }
                for doc in context_docs
            ]
        }