import json
import time
from threading import Event, Thread
from typing import Callable, List, Optional
from urllib.parse import urljoin

import requests
from requests.exceptions import RequestException
from sseclient import SSEClient

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
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        if config.api_key:
            self.headers["X-API-Key"] = config.api_key
            
        self._sse_client: Optional[SSEClient] = None
        self._sse_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._message_callback: Optional[Callable[[Message], None]] = None
        self._error_callback: Optional[Callable[[Exception], None]] = None

    def on_message(self, callback: Callable[[Message], None]) -> None:
        """Set callback for receiving messages"""
        self._message_callback = callback

    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """Set callback for handling errors"""
        self._error_callback = callback

    def start(self) -> None:
        """Start the SDK and begin listening for messages using SSE"""
        try:
            self._register_agent()
            self._start_sse()
        except Exception as e:
            if self._error_callback:
                self._error_callback(e)
            raise

    def stop(self) -> None:
        """Stop the SDK and clean up resources"""
        self._stop_event.set()
        if self._sse_thread:
            self._sse_thread.join()
            self._sse_thread = None
        if self._sse_client:
            self._sse_client.close()
            self._sse_client = None

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

    def _start_sse(self) -> None:
        """Start SSE connection for real-time messages"""
        def listen_for_messages():
            # Setup SSE headers
            sse_headers = self.headers.copy()
            if self.config.private_key:
                timestamp = str(int(time.time() * 1000))
                message = f"Authenticate to OpenPond API at timestamp {timestamp}"
                sse_headers.update({
                    "X-Agent-Id": self.config.private_key,
                    "X-Timestamp": timestamp,
                    # TODO: Add signature once we implement signing
                    # "X-Signature": signature
                })

            url = urljoin(self.config.api_url, "/messages/stream")
            self._sse_client = SSEClient(url, headers=sse_headers)

            try:
                for event in self._sse_client:
                    if self._stop_event.is_set():
                        break

                    try:
                        message = Message(**json.loads(event.data))
                        # Only process messages intended for us
                        if (self.config.private_key and 
                            message.to_agent_id == self.config.private_key):
                            if self._message_callback:
                                self._message_callback(message)
                    except Exception as e:
                        if self._error_callback:
                            self._error_callback(e)
            except Exception as e:
                if self._error_callback:
                    self._error_callback(e)
                # Wait before reconnecting
                if not self._stop_event.is_set():
                    time.sleep(1)
                    self._start_sse()

        self._sse_thread = Thread(target=listen_for_messages, daemon=True)
        self._sse_thread.start() 