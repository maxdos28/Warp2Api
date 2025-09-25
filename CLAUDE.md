# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Warp2Api project that provides OpenAI and Claude API compatible interfaces for the Warp terminal AI service. The project consists of two main services:

1. **Warp Protobuf Codec Server** (`server.py`) - Port 28888
2. **OpenAI Compatible Server** (`openai_compat.py`) - Port 28889

## Architecture

### Core Components

- **`warp2protobuf/`** - Core Warp API integration
  - `core/` - Authentication, protobuf handling, session management
  - `api/` - API routes for protobuf encoding/decoding
  - `warp/` - Warp API client and response handling

- **`protobuf2openai/`** - OpenAI/Claude API compatibility layer
  - `router.py` - OpenAI Chat Completions API (`/v1/chat/completions`)
  - `claude_router.py` - Claude Messages API (`/v1/messages`)
  - `claude_converter.py` - Format conversion between Claude and OpenAI
  - `sse_transform.py` - Server-Sent Events streaming

### Key Features

- **Dual API Support**: Both OpenAI and Claude API formats
- **Token Management**: Personal and anonymous token fallback
- **Streaming Support**: Real-time response streaming
- **Error Handling**: Comprehensive error recovery and fallback mechanisms

## Development Commands

### Starting Services

```bash
# Start Warp Protobuf server (port 28888)
uv run python server.py

# Start OpenAI compatible server (port 28889)
uv run python openai_compat.py

# Or use the provided scripts
./start.sh  # Linux/Mac
start.bat   # Windows
```

### Testing

```bash
# Test OpenAI Chat Completions API
curl -X POST http://127.0.0.1:28889/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 123456" \
  -d '{"model":"claude-4-sonnet","messages":[{"role":"user","content":"Hello"}],"max_tokens":100}'

# Test Claude Messages API
curl -X POST http://127.0.0.1:28889/v1/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 123456" \
  -d '{"model":"claude-4-sonnet","messages":[{"role":"user","content":"Hello"}],"max_tokens":100}'

# Test specific functionality
uv run python test_cline_compatibility.py
uv run python test_anonymous_priority.py
uv run python test_anonymous_fallback.py
```

### Configuration

Environment variables in `.env`:
- `WARP_JWT` - Personal JWT token
- `WARP_REFRESH_TOKEN` - Refresh token for JWT renewal
- `DISABLE_ANONYMOUS_FALLBACK` - Disable anonymous token fallback (default: false)
- `PRIORITIZE_ANONYMOUS_TOKEN` - Use anonymous tokens first (default: false)

## Known Issues and Solutions

### 1. Token Usage Shows 0

**Problem**: `/v1/messages` API returns `input_tokens: 0, output_tokens: 0`

**Root Cause**: Warp API internal error affecting response parsing
```
"internal_error": {"message": "json: cannot unmarshal string into Go struct field FileGlobToolCall.patterns of type []string"}
```

**Solution**: 
- Token usage extraction has been improved in `claude_converter.py`
- Fallback estimation based on content length when official counts unavailable
- Monitor logs for `context_window_usage` data

### 2. Cline Compatibility Issues

**Problem**: Cline occasionally reports "This may indicate a failure in his thought process"

**Solution**:
- Added error message filtering in `router.py` and `claude_router.py`
- Improved response validation and fallback mechanisms
- Enhanced logging for debugging

### 3. Anonymous Token Management

**Problem**: Anonymous token acquisition may be rate-limited

**Solution**:
- Cooldown mechanism with `.anonymous_cooldown` file
- Configurable priority between personal and anonymous tokens
- Automatic fallback when personal quotas exhausted

## Debugging

### Log Files
- `logs/openai_compat.log` - OpenAI compatible server logs
- `logs/server.log` - Warp protobuf server logs

### Common Debug Commands
```bash
# Check service status
netstat -an | findstr :28888
netstat -an | findstr :28889

# Monitor logs
tail -f logs/openai_compat.log
tail -f logs/server.log

# Test token acquisition
uv run python debug_token_quota.py
```

### Key Log Patterns
- `[Claude Compat]` - Claude API related logs
- `[OpenAI Compat]` - OpenAI API related logs
- `context_window_usage` - Token usage information
- `Bridge response` - Warp API responses

## File Structure

```
├── server.py                 # Main Warp protobuf server
├── openai_compat.py         # OpenAI compatible server
├── warp2protobuf/           # Core Warp integration
│   ├── core/               # Core functionality
│   ├── api/                # API routes
│   └── warp/               # Warp client
├── protobuf2openai/        # OpenAI/Claude compatibility
│   ├── router.py           # OpenAI Chat Completions
│   ├── claude_router.py    # Claude Messages
│   └── claude_converter.py # Format conversion
├── proto/                  # Protobuf definitions
├── logs/                   # Log files
└── test_*.py              # Test scripts
```

## Development Notes

- Always use `uv run` for Python commands to ensure proper dependency management
- Test both streaming and non-streaming responses
- Monitor token usage and quota management
- Check for Warp API internal errors in logs
- Verify response format compliance with OpenAI/Claude standards
