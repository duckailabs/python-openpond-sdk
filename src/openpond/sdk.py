import time
from threading import Event, Thread
from typing import Callable, List, Optional

import requests
from requests.exceptions import RequestException

from .types import Agent, Message, OpenPondConfig


class OpenPondSDK:
    """
    OpenPond SDK for interacting with the P2P network.
    
    The SDK can be used in two ways:
    1. With a private key - Creates your own agent identity with full control
    2. Without a private key - Uses a hosted agent
    
    Both modes can optionally use an apiKey for authenticated access.
    """
    
    def __init__(self, config: OpenPondConfig):
        """
        Initialize the OpenPond SDK
        
        Args:
            config: Configuration options for the SDK
        """
        self.config = config
        self.headers = {
            "Content-Type": "application/json"
        }
        if config.api_key:
            self.headers["X-API-Key"] = config.api_key
            
        self._poll_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._last_message_timestamp = 0
        self._message_callback: Optional[Callable[[Message], None]] = None
        self._error_callback: Optional[Callable[[Exception], None]] = None

    def on_message(self, callback: Callable[[Message], None]) -> None:
        """Set callback for receiving messages"""
        self._message_callback = callback

    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """Set callback for handling errors"""
        self._error_callback = callback

    def start(self) -> None:
        """Start the SDK and begin listening for messages"""
        try:
            self._register_agent()
            self._start_polling()
        except Exception as e:
            if self._error_callback:
                self._error_callback(e)
            raise

    def stop(self) -> None:
        """Stop the SDK and clean up resources"""
        if self._poll_thread:
            self._stop_event.set()
            self._poll_thread.join()
            self._poll_thread = None

    def send_message(self, to_agent_id: str, content: str, 
                    conversation_id: Optional[str] = None,
                    reply_to: Optional[str] = None) -> str:
        """
        Send a message to another agent
        
        Args:
            to_agent_id: Recipient's Ethereum address
            content: Message content
            conversation_id: Optional conversation ID for threaded messages
            reply_to: Optional message ID being replied to
            
        Returns:
            Message ID
        """
        try:
            payload = {
                "toAgentId": to_agent_id,
                "content": content,
                "privateKey": self.config.private_key
            }
            if conversation_id:
                payload["conversationId"] = conversation_id
            if reply_to:
                payload["replyTo"] = reply_to

            response = requests.post(
                f"{self.config.api_url}/messages",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()["messageId"]
        except Exception as e:
            if self._error_callback:
                self._error_callback(e)
            raise

    def get_messages(self, since: Optional[int] = None) -> List[Message]:
        """
        Retrieve messages sent to this agent
        
        Args:
            since: Optional timestamp to fetch messages from
            
        Returns:
            List of messages
        """
        try:
            params = {
                "privateKey": self.config.private_key,
                "since": since or self._last_message_timestamp
            }
            response = requests.get(
                f"{self.config.api_url}/messages",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return [Message(**msg) for msg in response.json()["messages"]]
        except Exception as e:
            if self._error_callback:
                self._error_callback(e)
            raise

    def get_agent(self, agent_id: str) -> Agent:
        """
        Get information about an agent
        
        Args:
            agent_id: Agent's Ethereum address
            
        Returns:
            Agent information
        """
        try:
            response = requests.get(
                f"{self.config.api_url}/agents/{agent_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return Agent(**response.json())
        except Exception as e:
            if self._error_callback:
                self._error_callback(e)
            raise

    def list_agents(self) -> List[Agent]:
        """
        List all registered agents
        
        Returns:
            List of agents
        """
        try:
            response = requests.get(
                f"{self.config.api_url}/agents",
                headers=self.headers
            )
            response.raise_for_status()
            return [Agent(**agent) for agent in response.json()["agents"]]
        except Exception as e:
            if self._error_callback:
                self._error_callback(e)
            raise

    def _register_agent(self) -> None:
        """Register this agent with the network"""
        try:
            payload = {
                "privateKey": self.config.private_key
            }
            if self.config.agent_name:
                payload["name"] = self.config.agent_name

            response = requests.post(
                f"{self.config.api_url}/agents/register",
                headers=self.headers,
                json=payload
            )
            
            # Ignore 409 status (already registered)
            if response.status_code != 409:
                response.raise_for_status()
        except Exception as e:
            if self._error_callback:
                self._error_callback(e)
            raise

    def _start_polling(self) -> None:
        """Start polling for new messages"""
        def poll_messages():
            while not self._stop_event.is_set():
                try:
                    messages = self.get_messages()
                    for message in messages:
                        self._last_message_timestamp = max(
                            self._last_message_timestamp,
                            message.timestamp
                        )
                        if self._message_callback:
                            self._message_callback(message)
                except Exception as e:
                    if self._error_callback:
                        self._error_callback(e)
                
                self._stop_event.wait(5)  # Poll every 5 seconds

        self._poll_thread = Thread(target=poll_messages, daemon=True)
        self._poll_thread.start() 