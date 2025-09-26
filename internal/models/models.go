package models

import "time"

// Model represents an AI model
type Model struct {
	ID     string `json:"id"`
	Object string `json:"object"`
}

// ChatMessage represents a chat message
type ChatMessage struct {
	Role      string                 `json:"role"`
	Content   interface{}            `json:"content"`
	Name      string                 `json:"name,omitempty"`
	ToolCalls []ToolCall             `json:"tool_calls,omitempty"`
	ToolCallID string                `json:"tool_call_id,omitempty"`
}

// ToolCall represents a tool call
type ToolCall struct {
	ID       string                 `json:"id"`
	Type     string                 `json:"type"`
	Function ToolCallFunction       `json:"function"`
}

// ToolCallFunction represents a tool call function
type ToolCallFunction struct {
	Name      string                 `json:"name"`
	Arguments map[string]interface{} `json:"arguments"`
}

// Tool represents a tool definition
type Tool struct {
	Type     string                 `json:"type"`
	Function ToolFunction           `json:"function"`
}

// ToolFunction represents a tool function definition
type ToolFunction struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description,omitempty"`
	Parameters  map[string]interface{} `json:"parameters,omitempty"`
}

// ChatCompletionsRequest represents OpenAI Chat Completions API request
type ChatCompletionsRequest struct {
	Model       string                 `json:"model"`
	Messages    []ChatMessage          `json:"messages"`
	MaxTokens   int                    `json:"max_tokens,omitempty"`
	Temperature float64                `json:"temperature,omitempty"`
	TopP        float64                `json:"top_p,omitempty"`
	Stream      bool                   `json:"stream,omitempty"`
	Tools       []Tool                 `json:"tools,omitempty"`
	ToolChoice  interface{}            `json:"tool_choice,omitempty"`
	User        string                 `json:"user,omitempty"`
}

// ChatCompletionsResponse represents OpenAI Chat Completions API response
type ChatCompletionsResponse struct {
	ID      string                 `json:"id"`
	Object  string                 `json:"object"`
	Created int64                  `json:"created"`
	Model   string                 `json:"model"`
	Choices []ChatChoice           `json:"choices"`
	Usage   Usage                  `json:"usage"`
}

// ChatChoice represents a chat choice
type ChatChoice struct {
	Index        int                    `json:"index"`
	Message      ChatMessage            `json:"message"`
	FinishReason string                 `json:"finish_reason"`
	Delta        *ChatMessage           `json:"delta,omitempty"`
}

// Usage represents token usage
type Usage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

// MessagesRequest represents Claude Messages API request
type MessagesRequest struct {
	Model       string                 `json:"model"`
	MaxTokens   int                    `json:"max_tokens"`
	Messages    []ClaudeMessage        `json:"messages"`
	System      string                 `json:"system,omitempty"`
	Temperature float64                `json:"temperature,omitempty"`
	TopP        float64                `json:"top_p,omitempty"`
	TopK        int                    `json:"top_k,omitempty"`
	Stream      bool                   `json:"stream,omitempty"`
	Stop        []string               `json:"stop,omitempty"`
	Tools       []ClaudeTool           `json:"tools,omitempty"`
	ToolChoice  interface{}            `json:"tool_choice,omitempty"`
}

// ClaudeMessage represents a Claude message
type ClaudeMessage struct {
	Role    string                 `json:"role"`
	Content interface{}            `json:"content"`
}

// ClaudeTool represents a Claude tool
type ClaudeTool struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description,omitempty"`
	InputSchema map[string]interface{} `json:"input_schema"`
}

// MessagesResponse represents Claude Messages API response
type MessagesResponse struct {
	ID           string                 `json:"id"`
	Type         string                 `json:"type"`
	Role         string                 `json:"role"`
	Content      []ClaudeContent        `json:"content"`
	Model        string                 `json:"model"`
	StopReason   string                 `json:"stop_reason"`
	StopSequence string                 `json:"stop_sequence,omitempty"`
	Usage        ClaudeUsage            `json:"usage"`
}

// ClaudeContent represents Claude content
type ClaudeContent struct {
	Type string                 `json:"type"`
	Text string                 `json:"text,omitempty"`
}

// ClaudeUsage represents Claude usage
type ClaudeUsage struct {
	InputTokens  int `json:"input_tokens"`
	OutputTokens int `json:"output_tokens"`
}

// StreamingEvent represents a streaming event
type StreamingEvent struct {
	ID    string                 `json:"id,omitempty"`
	Event string                 `json:"event,omitempty"`
	Data  interface{}            `json:"data,omitempty"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error ErrorDetail `json:"error"`
}

// ErrorDetail represents error details
type ErrorDetail struct {
	Message string `json:"message"`
	Type    string `json:"type"`
	Code    string `json:"code,omitempty"`
}

// WarpRequest represents a request to Warp API
type WarpRequest struct {
	Model       string                 `json:"model"`
	Messages    []ChatMessage          `json:"messages"`
	MaxTokens   int                    `json:"max_tokens,omitempty"`
	Temperature float64                `json:"temperature,omitempty"`
	Stream      bool                   `json:"stream,omitempty"`
	Tools       []Tool                 `json:"tools,omitempty"`
	ToolChoice  interface{}            `json:"tool_choice,omitempty"`
}

// WarpResponse represents a response from Warp API
type WarpResponse struct {
	ID      string                 `json:"id"`
	Object  string                 `json:"object"`
	Created int64                  `json:"created"`
	Model   string                 `json:"model"`
	Choices []ChatChoice           `json:"choices"`
	Usage   Usage                  `json:"usage"`
}

// TokenInfo represents JWT token information
type TokenInfo struct {
	Token       string    `json:"token"`
	ExpiresAt   time.Time `json:"expires_at"`
	IsExpired   bool      `json:"is_expired"`
	RefreshToken string   `json:"refresh_token,omitempty"`
}