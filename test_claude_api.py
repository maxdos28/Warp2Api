#!/usr/bin/env python3
"""
Test script for Claude Messages API compatibility
"""

import json
import httpx
import asyncio
from typing import Optional


async def test_claude_messages(
    base_url: str = "http://localhost:28889",
    api_key: str = "test-key",
    stream: bool = True
):
    """Test Claude Messages API endpoint"""
    
    print("\n" + "="*60)
    print("Testing Claude Messages API")
    print("="*60)
    
    # Test 1: Basic message
    print("\n1. Testing basic message...")
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "Say hello in one sentence."}
        ],
        "max_tokens": 100,
        "stream": stream
    }
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "x-api-key": api_key
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if stream:
                print("Streaming response:")
                async with client.stream(
                    "POST",
                    f"{base_url}/v1/messages",
                    json=request_data,
                    headers=headers
                ) as response:
                    if response.status_code != 200:
                        print(f"Error: HTTP {response.status_code}")
                        print(await response.aread())
                        return
                    
                    async for line in response.aiter_lines():
                        if line.startswith("event:"):
                            print(f"  {line}")
                        elif line.startswith("data:"):
                            try:
                                data = json.loads(line[5:])
                                print(f"  data: {json.dumps(data, ensure_ascii=False)[:100]}...")
                            except:
                                print(f"  {line[:100]}...")
            else:
                print("Non-streaming response:")
                response = await client.post(
                    f"{base_url}/v1/messages",
                    json=request_data,
                    headers=headers
                )
                if response.status_code != 200:
                    print(f"Error: HTTP {response.status_code}")
                    print(response.text)
                    return
                
                result = response.json()
                print(json.dumps(result, indent=2, ensure_ascii=False))
        
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 2: Message with system prompt
    print("\n2. Testing message with system prompt...")
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "system": "You are a helpful assistant that speaks like a pirate.",
        "messages": [
            {"role": "user", "content": "How's the weather?"}
        ],
        "max_tokens": 100,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/v1/messages",
                json=request_data,
                headers=headers
            )
            if response.status_code == 200:
                print("✓ System prompt test passed")
            else:
                print(f"✗ System prompt test failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ System prompt test failed: {e}")
    
    # Test 3: Tool use
    print("\n3. Testing tool use...")
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "What's the weather in San Francisco?"}
        ],
        "tools": [
            {
                "name": "get_weather",
                "description": "Get the current weather in a location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        }
                    },
                    "required": ["location"]
                }
            }
        ],
        "max_tokens": 200,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/v1/messages",
                json=request_data,
                headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                # Check if tool use is in response
                has_tool_use = any(
                    block.get("type") == "tool_use" 
                    for block in result.get("content", [])
                    if isinstance(block, dict)
                )
                if has_tool_use:
                    print("✓ Tool use test passed")
                else:
                    print("⚠ Tool use test: No tool call in response")
            else:
                print(f"✗ Tool use test failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ Tool use test failed: {e}")
    
    # Test 4: Computer use (with beta header)
    print("\n4. Testing computer use with beta header...")
    headers["anthropic-beta"] = "computer-use-2024-10-22"
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "Take a screenshot of the current screen"}
        ],
        "max_tokens": 200,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/v1/messages",
                json=request_data,
                headers=headers
            )
            if response.status_code == 200:
                print("✓ Computer use test passed")
            else:
                print(f"⚠ Computer use test: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ Computer use test failed: {e}")
    
    # Test 5: Code execution (with beta header)
    print("\n5. Testing code execution with beta header...")
    headers["anthropic-beta"] = "code-execution-2025-08-25"
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "Create a simple hello.py file"}
        ],
        "max_tokens": 200,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/v1/messages",
                json=request_data,
                headers=headers
            )
            if response.status_code == 200:
                print("✓ Code execution test passed")
            else:
                print(f"⚠ Code execution test: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ Code execution test failed: {e}")
    
    print("\n" + "="*60)
    print("Claude API testing complete!")
    print("="*60)


async def test_list_models(base_url: str = "http://localhost:28889"):
    """Test listing Claude models"""
    print("\n" + "="*60)
    print("Testing Claude Models Listing")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{base_url}/v1/messages/models")
            if response.status_code == 200:
                models = response.json()
                print("Available Claude models:")
                for model in models.get("data", []):
                    print(f"  - {model['id']}")
            else:
                print(f"Error: HTTP {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Claude Messages API")
    parser.add_argument("--url", default="http://localhost:28889", help="Base URL")
    parser.add_argument("--api-key", default="test-key", help="API key")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming")
    parser.add_argument("--models-only", action="store_true", help="Only list models")
    
    args = parser.parse_args()
    
    if args.models_only:
        asyncio.run(test_list_models(args.url))
    else:
        asyncio.run(test_claude_messages(
            base_url=args.url,
            api_key=args.api_key,
            stream=not args.no_stream
        ))