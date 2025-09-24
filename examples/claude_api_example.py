#!/usr/bin/env python3
"""
Example of using Claude API format with the Anthropic Python SDK
"""

import os
from anthropic import Anthropic


def main():
    # Configure the client to use our local server
    client = Anthropic(
        base_url="http://localhost:28889/v1",
        api_key="dummy",  # Our server doesn't validate API keys
    )
    
    # Example 1: Basic message
    print("Example 1: Basic message")
    print("-" * 40)
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Hello! How are you today?"}
        ]
    )
    
    print(f"Response: {response.content[0].text}")
    print()
    
    # Example 2: Message with system prompt
    print("Example 2: Message with system prompt")
    print("-" * 40)
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        system="You are a helpful assistant that speaks like Shakespeare.",
        messages=[
            {"role": "user", "content": "Tell me about the weather."}
        ]
    )
    
    print(f"Response: {response.content[0].text}")
    print()
    
    # Example 3: Streaming response
    print("Example 3: Streaming response")
    print("-" * 40)
    
    stream = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        messages=[
            {"role": "user", "content": "Write a haiku about programming."}
        ],
        stream=True
    )
    
    print("Response: ", end="")
    for event in stream:
        if event.type == "content_block_delta":
            print(event.delta.text, end="", flush=True)
    print("\n")
    
    # Example 4: Using tools
    print("Example 4: Using tools")
    print("-" * 40)
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[
            {"role": "user", "content": "What's the weather like in Tokyo and Paris?"}
        ],
        tools=[
            {
                "name": "get_weather",
                "description": "Get the current weather in a location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and country, e.g. San Francisco, USA"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "The unit of temperature"
                        }
                    },
                    "required": ["location"]
                }
            }
        ]
    )
    
    print("Response content:")
    for block in response.content:
        if block.type == "text":
            print(f"  Text: {block.text}")
        elif block.type == "tool_use":
            print(f"  Tool call: {block.name}")
            print(f"    Input: {block.input}")
    print()
    
    # Example 5: Computer use (requires beta header)
    print("Example 5: Computer use (beta feature)")
    print("-" * 40)
    
    # Note: This requires the anthropic-beta header which the SDK handles
    client_beta = Anthropic(
        base_url="http://localhost:28889/v1",
        api_key="dummy",
        default_headers={
            "anthropic-beta": "computer-use-2024-10-22"
        }
    )
    
    response = client_beta.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        messages=[
            {"role": "user", "content": "Take a screenshot and describe what you see."}
        ]
    )
    
    print("Response content:")
    for block in response.content:
        if block.type == "text":
            print(f"  Text: {block.text}")
        elif block.type == "tool_use":
            print(f"  Tool: {block.name} - {block.input}")
    

if __name__ == "__main__":
    main()