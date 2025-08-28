"""Tests for the conversation module."""

import pytest
import time
from src.conversation import Conversation, Message


def test_conversation_initialization():
    """Test conversation initialization."""
    conv = Conversation()
    
    assert conv.messages == []
    assert conv.is_active is True
    assert conv.get_message_count() == 0


def test_add_user_message():
    """Test adding user messages."""
    conv = Conversation()
    msg = conv.add_user_message("Hello, AI!")
    
    assert isinstance(msg, Message)
    assert msg.role == "user"
    assert msg.content == "Hello, AI!"
    assert conv.get_message_count() == 1


def test_add_assistant_message():
    """Test adding assistant messages."""
    conv = Conversation()
    msg = conv.add_assistant_message("Hello! How can I help you?")
    
    assert isinstance(msg, Message)
    assert msg.role == "assistant"
    assert msg.content == "Hello! How can I help you?"
    assert conv.get_message_count() == 1


def test_conversation_history():
    """Test conversation history retrieval."""
    conv = Conversation()
    conv.add_user_message("Hi")
    conv.add_assistant_message("Hello!")
    conv.add_user_message("How are you?")
    
    history = conv.get_conversation_history()
    assert len(history) == 3
    assert history[0].content == "Hi"
    assert history[1].content == "Hello!"
    assert history[2].content == "How are you?"


def test_formatted_history():
    """Test formatted conversation history."""
    conv = Conversation()
    conv.add_user_message("Hi")
    conv.add_assistant_message("Hello!")
    
    formatted = conv.get_formatted_history()
    expected = "User: Hi\nAssistant: Hello!"
    assert formatted == expected


def test_end_conversation():
    """Test ending a conversation."""
    conv = Conversation()
    conv.add_user_message("Hi")
    conv.add_assistant_message("Hello!")
    
    assert conv.is_active is True
    conv.end_conversation()
    assert conv.is_active is False
    assert conv.get_message_count() == 2


def test_duration_calculation():
    """Test duration calculation."""
    conv = Conversation()
    
    # Small delay to ensure different timestamps
    time.sleep(0.1)
    
    # Duration should be positive while active
    duration = conv.get_duration()
    assert duration > 0
    
    # End conversation and check duration
    conv.end_conversation()
    final_duration = conv.get_duration()
    assert final_duration > 0
    assert final_duration >= duration


def test_clear_history():
    """Test clearing conversation history."""
    conv = Conversation()
    conv.add_user_message("Hi")
    conv.add_assistant_message("Hello!")
    
    assert conv.get_message_count() == 2
    conv.clear_history()
    assert conv.get_message_count() == 0
    assert conv.messages == []


def test_conversation_summary():
    """Test conversation summary generation."""
    conv = Conversation()
    conv.add_user_message("Hi")
    conv.add_assistant_message("Hello!")
    
    summary = conv.get_summary()
    
    assert summary["message_count"] == 2
    assert summary["user_messages"] == 1
    assert summary["assistant_messages"] == 1
    assert summary["is_active"] is True
    assert "start_time" in summary
    assert "duration_seconds" in summary

