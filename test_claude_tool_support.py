#!/usr/bin/env python3
"""
Test script for Claude API tool support
Tests both tool calls and tool results
"""

import asyncio
import json
import aiohttp


async def test_tool_call():
    """Test that the API can handle tool calls from Claude"""
    
    url = "http://localhost:28889/v1/messages"
    
    # Test request with tool call response
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": "What's the weather like in San Francisco? Use the get_weather tool."
            }
        ],
        "system": "You are an assistant with access to weather tools. When asked about weather, use the get_weather tool with the city name as a parameter."
    }
    
    print("Testing tool call request...")
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=request_data) as response:
                response_data = await response.json()
                print(f"Response status: {response.status}")
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                # Check if response contains tool_use content block
                if response.status == 200:
                    content = response_data.get("content", [])
                    has_tool_use = any(block.get("type") == "tool_use" for block in content if isinstance(block, dict))
                    
                    if has_tool_use:
                        print("✅ Tool use block found in response!")
                        
                        # Extract tool information
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_use":
                                print(f"  Tool: {block.get('name')}")
                                print(f"  ID: {block.get('id')}")
                                print(f"  Input: {block.get('input')}")
                    else:
                        print("⚠️ No tool use block found in response")
                else:
                    print(f"❌ Error: {response_data}")
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")


async def test_tool_result():
    """Test that the API can handle tool results"""
    
    url = "http://localhost:28889/v1/messages"
    
    # Test request with tool result
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": "What's the weather like in San Francisco?"
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "I'll check the weather in San Francisco for you."
                    },
                    {
                        "type": "tool_use",
                        "id": "tool_call_123",
                        "name": "get_weather",
                        "input": {"city": "San Francisco"}
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool_call_123",
                        "content": "Temperature: 68°F, Conditions: Partly cloudy"
                    }
                ]
            }
        ]
    }
    
    print("\n\nTesting tool result handling...")
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=request_data) as response:
                response_data = await response.json()
                print(f"Response status: {response.status}")
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                if response.status == 200:
                    print("✅ Tool result handled successfully!")
                else:
                    print(f"❌ Error: {response_data}")
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")


async def test_streaming_tool_call():
    """Test streaming response with tool calls"""
    
    url = "http://localhost:28889/v1/messages"
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": "Calculate the sum of 25 and 17 using a calculator tool."
            }
        ],
        "system": "You have access to a calculator tool. Use it when asked to perform calculations."
    }
    
    print("\n\nTesting streaming with tool calls...")
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=request_data) as response:
                print(f"Response status: {response.status}")
                
                if response.status == 200:
                    print("Streaming events:")
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data:"):
                            data_str = line[5:].strip()
                            try:
                                event_data = json.loads(data_str)
                                print(f"  Event: {event_data.get('type', 'unknown')}")
                                
                                # Check for tool use content blocks
                                if event_data.get('type') == 'content_block_start':
                                    block = event_data.get('content_block', {})
                                    if block.get('type') == 'tool_use':
                                        print(f"  ✅ Tool use block: {block.get('name')} (id: {block.get('id')})")
                                        
                            except json.JSONDecodeError:
                                # Skip non-JSON lines
                                pass
                else:
                    error_text = await response.text()
                    print(f"❌ Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Claude API Tool Support Tests")
    print("=" * 60)
    
    # Ensure the server is running
    print("\nNote: Make sure the API server is running on port 28889")
    print("You can start it with: python server.py")
    
    await test_tool_call()
    await test_tool_result()
    await test_streaming_tool_call()
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
