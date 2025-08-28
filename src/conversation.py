"""Conversation management and state handling."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Represents a single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class Conversation:
    """Manages conversation state and history."""
    
    def __init__(self):
        """Initialize a new conversation."""
        self.messages: List[Message] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.is_active = True
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add a new message to the conversation."""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.messages.append(message)
        logger.debug(f"Added {role} message: {content[:50]}...")
        return message
    
    def add_user_message(self, content: str) -> Message:
        """Add a user message to the conversation."""
        return self.add_message("user", content)
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add an assistant message to the conversation."""
        return self.add_message("assistant", content, metadata)
    
    def get_conversation_history(self, max_messages: Optional[int] = None) -> List[Message]:
        """Get conversation history, optionally limited to recent messages."""
        if max_messages is None:
            return self.messages.copy()
        return self.messages[-max_messages:]
    
    def get_formatted_history(self, max_messages: Optional[int] = None) -> str:
        """Get conversation history formatted as a string for LLM context."""
        messages = self.get_conversation_history(max_messages)
        formatted = []
        
        for msg in messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            formatted.append(f"{role_label}: {msg.content}")
        
        return "\n".join(formatted)
    
    def get_last_message(self) -> Optional[Message]:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None
    
    def get_message_count(self) -> int:
        """Get the total number of messages in the conversation."""
        return len(self.messages)
    
    def clear_history(self):
        """Clear the conversation history."""
        self.messages.clear()
        logger.info("Conversation history cleared")
    
    def end_conversation(self):
        """Mark the conversation as ended."""
        self.is_active = False
        self.end_time = datetime.now()
        logger.info("Conversation ended")
    
    def get_duration(self) -> float:
        """Get the duration of the conversation in seconds."""
        if self.is_active:
            return (datetime.now() - self.start_time).total_seconds()
        elif self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        return {
            "message_count": self.get_message_count(),
            "user_messages": len([m for m in self.messages if m.role == "user"]),
            "assistant_messages": len([m for m in self.messages if m.role == "assistant"]),
            "start_time": self.start_time.isoformat(),
            "duration_seconds": self.get_duration(),
            "is_active": self.is_active
        }
