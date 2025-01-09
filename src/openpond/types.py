from dataclasses import dataclass
from typing import Optional


@dataclass
class OpenPondConfig:
    """Configuration options for the OpenPond SDK"""
    api_url: str
    private_key: str
    agent_name: Optional[str] = None
    api_key: Optional[str] = None

@dataclass
class Message:
    """Message structure for communication between agents"""
    message_id: str
    from_agent_id: str
    to_agent_id: str
    content: str
    timestamp: int
    conversation_id: Optional[str] = None
    reply_to: Optional[str] = None

@dataclass
class Agent:
    """Agent information from the registry"""
    address: str
    name: str
    metadata: str
    reputation: int
    is_active: bool
    is_blocked: bool
    registration_time: int 