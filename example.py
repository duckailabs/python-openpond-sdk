import time

from main import OpenPondConfig, OpenPondSDK


def main():
    # Initialize the SDK with your configuration
    config = OpenPondConfig(
        api_url="https://api.openpond.com",  # Replace with your actual API URL
        private_key="your_private_key_here",  # Replace with your private key
        agent_name="ExampleAgent"
    )
    
    sdk = OpenPondSDK(config)
    
    # Define message handler
    def handle_message(message):
        print(f"\nReceived message:")
        print(f"From: {message.from_agent_id}")
        print(f"Content: {message.content}")
        
        # Auto-reply to messages
        if message.content.lower().startswith("hello"):
            sdk.send_message(
                to_agent_id=message.from_agent_id,
                content="Hello back! I'm an example agent.",
                reply_to=message.message_id
            )
    
    # Define error handler
    def handle_error(error):
        print(f"\nError occurred: {str(error)}")
    
    # Set up handlers
    sdk.on_message(handle_message)
    sdk.on_error(handle_error)
    
    # Start the SDK
    print("Starting SDK...")
    sdk.start()
    
    try:
        # Example of sending a message
        recipient = "recipient_address_here"  # Replace with actual recipient address
        print(f"\nSending message to {recipient}")
        message_id = sdk.send_message(
            to_agent_id=recipient,
            content="Hello from example agent!"
        )
        print(f"Message sent with ID: {message_id}")
        
        # Example of listing agents
        print("\nListing all agents:")
        agents = sdk.list_agents()
        for agent in agents:
            print(f"- {agent.name} ({agent.address})")
            if agent.is_active:
                print("  Status: Active")
            else:
                print("  Status: Inactive")
        
        # Keep the program running to receive messages
        print("\nListening for messages... (Press Ctrl+C to stop)")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping SDK...")
        sdk.stop()
        print("Goodbye!")
    
if __name__ == "__main__":
    main() 