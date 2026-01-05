from typing import List, Dict
from datetime import datetime

class ChatManager:
    def __init__(self):
        self.conversations = {}
    
    def create_conversation(self, conversation_id: str):
        """Create a new conversation"""
        self.conversations[conversation_id] = {
            'messages': [],
            'created_at': datetime.now().isoformat()
        }
    
    def add_message(self, conversation_id: str, role: str, content: str, metadata: Dict = None):
        """Add message to conversation"""
        if conversation_id not in self.conversations:
            self.create_conversation(conversation_id)
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.conversations[conversation_id]['messages'].append(message)
    
    def get_conversation(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        if conversation_id not in self.conversations:
            return []
        return self.conversations[conversation_id]['messages']
    
    def get_recent_context(self, conversation_id: str, num_messages: int = 5) -> str:
        """Get recent conversation context for query expansion"""
        messages = self.get_conversation(conversation_id)
        recent = messages[-num_messages:] if len(messages) > num_messages else messages
        
        context = []
        for msg in recent:
            context.append(f"{msg['role']}: {msg['content']}")
        
        return "\n".join(context)