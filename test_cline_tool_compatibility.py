#!/usr/bin/env python3
"""
Test script for Claude Code (Cline) tool compatibility
Tests the specific tool formats used by Cline
"""

import asyncio
import json
import aiohttp


async def test_cline_tool_format():
    """Test Cline-specific tool format"""
    
    url = "http://localhost:28889/v1/messages"
    
    # Cline-style request with tool use
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 8192,
        "messages": [
            {
                "role": "user",
                "content": "Create a simple Python hello world script"
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "I'll create a simple Python hello world script for you."
                    },
                    {
                        "type": "tool_use",
                        "id": "toolu_01ABC123",
                        "name": "str_replace_editor",
                        "input": {
                            "command": "create",
                            "path": "hello.py",
                            "file_text": "#!/usr/bin/env python3\n\ndef main():\n    print(\"Hello, World!\")\n\nif __name__ == \"__main__\":\n    main()\n"
                        }
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01ABC123",
                        "content": "File created successfully at hello.py"
                    }
                ]
            },
            {
                "role": "assistant",
                "content": "I've created a simple Python hello world script. Now let me run it to show you the output."
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_01DEF456",
                        "name": "execute_command",
                        "input": {
                            "command": "python hello.py"
                        }
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01DEF456",
                        "content": "Hello, World!"
                    }
                ]
            },
            {
                "role": "user",
                "content": "Great! Now modify it to say 'Hello, Claude!'"
            }
        ],
        "system": "You are Claude, an AI assistant created by Anthropic. You are being used through Cline (Claude Code), a VS Code extension. You have access to various tools for file operations and command execution."
    }
    
    print("Testing Cline tool format compatibility...")
    print(f"Request messages count: {len(request_data['messages'])}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=request_data) as response:
                response_data = await response.json()
                print(f"Response status: {response.status}")
                
                if response.status == 200:
                    print("✅ Cline tool format handled successfully!")
                    
                    # Check response content
                    content = response_data.get("content", [])
                    for block in content:
                        if isinstance(block, dict):
                            if block.get("type") == "text":
                                print(f"Text response: {block.get('text')[:100]}...")
                            elif block.get("type") == "tool_use":
                                print(f"Tool use: {block.get('name')} (id: {block.get('id')})")
                                print(f"  Input: {json.dumps(block.get('input'), indent=2)}")
                else:
                    print(f"❌ Error: {response_data}")
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")


async def test_cline_streaming():
    """Test Cline streaming with tools"""
    
    url = "http://localhost:28889/v1/messages"
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4096,
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": "List the files in the current directory using a tool"
            }
        ],
        "system": "You are Claude, an AI assistant with access to file system tools. Use the list_files tool to list directory contents."
    }
    
    print("\n\nTesting Cline streaming format...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=request_data) as response:
                print(f"Response status: {response.status}")
                
                if response.status == 200:
                    events_received = []
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                            events_received.append(event_type)
                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                            try:
                                event_data = json.loads(data_str)
                                
                                # Check for Cline-compatible events
                                if event_data.get("type") == "content_block_start":
                                    block = event_data.get("content_block", {})
                                    if block.get("type") == "tool_use":
                                        print(f"  ✅ Tool use streaming: {block.get('name')}")
                                        
                            except json.JSONDecodeError:
                                pass
                    
                    print(f"Events received: {', '.join(set(events_received))}")
                    
                    if "content_block_start" in events_received:
                        print("✅ Cline-compatible streaming events detected!")
                else:
                    error_text = await response.text()
                    print(f"❌ Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")


async def main():
    """Run all Cline compatibility tests"""
    print("=" * 60)
    print("Claude Code (Cline) Tool Compatibility Tests")
    print("=" * 60)
    
    print("\nNote: Make sure the API server is running on port 28889")
    
    await test_cline_tool_format()
    await test_cline_streaming()
    
    print("\n" + "=" * 60)
    print("Cline compatibility tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
