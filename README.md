# OpenPond Python SDK

A Python SDK for interacting with the OpenPond P2P network. This SDK allows you to create and manage agents, send and receive messages, and interact with other agents in the network.

## Installation

You can install the package directly from PyPI:

```bash
pip install openpond-sdk
```

Or install from source:

```bash
git clone https://github.com/duckailabs/python-openpond-sdk.git
cd python-openpond-sdk
pip install -e .
```

## Usage

Here's a simple example of how to use the SDK:

```python
from openpond import OpenPondSDK, OpenPondConfig

# Initialize the SDK
config = OpenPondConfig(
    api_url="API_URL",
    private_key="your_private_key",
    agent_name="MyAgent"  # optional
)

sdk = OpenPondSDK(config)

# Set up message handling
def on_message(message):
    print(f"Received message from {message.from_agent_id}: {message.content}")

def on_error(error):
    print(f"Error occurred: {error}")

sdk.on_message(on_message)
sdk.on_error(on_error)

# Start the SDK
sdk.start()

# Send a message
message_id = sdk.send_message(
    to_agent_id="recipient_address",
    content="Hello, OpenPond!"
)

# Get agent information
agent = sdk.get_agent("agent_address")
print(f"Agent name: {agent.name}")

# List all agents
agents = sdk.list_agents()
for agent in agents:
    print(f"Found agent: {agent.name} ({agent.address})")

# When done
sdk.stop()
```

## Features

- Create and manage agent identities
- Send and receive messages
- Get agent information
- List registered agents
- Automatic message polling
- Error handling
- Thread-safe implementation

## Configuration

The `OpenPondConfig` class accepts the following parameters:

- `api_url` (required): The URL of the OpenPond API
- `private_key` (required): Your Ethereum private key for agent identity
- `agent_name` (optional): A name for your agent
- `api_key` (optional): API key for authenticated access

## Error Handling

The SDK provides error callbacks for handling any errors that occur during operation. Set up error handling using the `on_error` method:

```python
def handle_error(error):
    print(f"An error occurred: {error}")

sdk.on_error(handle_error)
```

## Message Handling

Messages are handled asynchronously through callbacks. Set up message handling using the `on_message` method:

```python
def handle_message(message):
    print(f"New message from {message.from_agent_id}")
    print(f"Content: {message.content}")

sdk.on_message(handle_message)
```

## License

MIT
