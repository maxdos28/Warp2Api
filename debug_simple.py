#!/usr/bin/env python3
import requests
import json

url = "http://localhost:28889/v1/messages"
payload = {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1000,
    "stream": True,
    "messages": [{"role": "user", "content": "analyze codebase"}],
    "system": "You have tools available"
}
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 123456",
    "Accept": "text/event-stream"
}

print("Testing forced tool call...")
try:
    response = requests.post(url, headers=headers, json=payload, stream=True, timeout=15)
    print(f"Status: {response.status_code}")
    
    event_count = 0
    for line in response.iter_lines(decode_unicode=True):
        if line.strip():
            print(f"[{event_count:02d}] {line}")
            
            if line.startswith("data:") and "tool_use" in line:
                print("    *** TOOL USE DETECTED ***")
            
            event_count += 1
            if event_count > 20:  # Limit
                break
                
except Exception as e:
    print(f"Error: {e}")
