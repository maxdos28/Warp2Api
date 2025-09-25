package services

import (
	"warp2api-go/internal/config"
	"warp2api-go/internal/models"
	"warp2api-go/internal/warp"
	"warp2api-go/internal/streaming"

	"github.com/gin-gonic/gin"
)

// Service handles business logic
type Service struct {
	config *config.Config
	warp   *warp.Client
}

// New creates a new service instance
func New(cfg *config.Config) *Service {
	return &Service{
		config: cfg,
		warp:   warp.New(cfg),
	}
}

// CreateStreamingResponse creates a streaming response handler
func (s *Service) CreateStreamingResponse(c *gin.Context, req interface{}) *streaming.Stream {
	return streaming.New(c, req)
}

// ProcessChatRequest processes a chat request with streaming
func (s *Service) ProcessChatRequest(stream *streaming.Stream, req *models.ChatCompletionsRequest) error {
	// Convert to Warp request
	warpReq := s.convertToWarpRequest(req)
	
	// Process with Warp API
	return s.warp.ProcessRequest(stream, warpReq)
}

// ProcessChatRequestSync processes a chat request synchronously
func (s *Service) ProcessChatRequestSync(req *models.ChatCompletionsRequest) (*models.ChatCompletionsResponse, error) {
	// Convert to Warp request
	warpReq := s.convertToWarpRequest(req)
	
	// Process with Warp API
	return s.warp.ProcessRequestSync(warpReq)
}

// ProcessMessagesRequest processes a Claude messages request with streaming
func (s *Service) ProcessMessagesRequest(stream *streaming.Stream, req *models.MessagesRequest) error {
	// Convert to Warp request
	warpReq := s.convertMessagesToWarpRequest(req)
	
	// Process with Warp API
	return s.warp.ProcessRequest(stream, warpReq)
}

// ProcessMessagesRequestSync processes a Claude messages request synchronously
func (s *Service) ProcessMessagesRequestSync(req *models.MessagesRequest) (*models.MessagesResponse, error) {
	// Convert to Warp request
	warpReq := s.convertMessagesToWarpRequest(req)
	
	// Process with Warp API and convert response
	warpResp, err := s.warp.ProcessRequestSync(warpReq)
	if err != nil {
		return nil, err
	}
	
	return s.convertWarpToMessagesResponse(warpResp), nil
}

// convertToWarpRequest converts OpenAI request to Warp request
func (s *Service) convertToWarpRequest(req *models.ChatCompletionsRequest) *models.WarpRequest {
	return &models.WarpRequest{
		Model:       req.Model,
		Messages:    req.Messages,
		MaxTokens:   req.MaxTokens,
		Temperature: req.Temperature,
		Stream:      req.Stream,
		Tools:       req.Tools,
		ToolChoice:  req.ToolChoice,
	}
}

// convertMessagesToWarpRequest converts Claude messages request to Warp request
func (s *Service) convertMessagesToWarpRequest(req *models.MessagesRequest) *models.WarpRequest {
	// Convert Claude messages to OpenAI format
	messages := make([]models.ChatMessage, len(req.Messages))
	for i, msg := range req.Messages {
		messages[i] = models.ChatMessage{
			Role:    msg.Role,
			Content: msg.Content,
		}
	}
	
	// Convert tools if present
	var tools []models.Tool
	for _, tool := range req.Tools {
		tools = append(tools, models.Tool{
			Type: "function",
			Function: models.ToolFunction{
				Name:        tool.Name,
				Description: tool.Description,
				Parameters:  tool.InputSchema,
			},
		})
	}
	
	return &models.WarpRequest{
		Model:       req.Model,
		Messages:    messages,
		MaxTokens:   req.MaxTokens,
		Temperature: req.Temperature,
		Stream:      req.Stream,
		Tools:       tools,
		ToolChoice:  req.ToolChoice,
	}
}

// convertWarpToMessagesResponse converts Warp response to Claude messages response
func (s *Service) convertWarpToMessagesResponse(warpResp *models.WarpResponse) *models.MessagesResponse {
	// Extract content from the first choice
	var content []models.ClaudeContent
	if len(warpResp.Choices) > 0 {
		msg := warpResp.Choices[0].Message
		if text, ok := msg.Content.(string); ok {
			content = []models.ClaudeContent{
				{Type: "text", Text: text},
			}
		}
	}
	
	return &models.MessagesResponse{
		ID:         warpResp.ID,
		Type:       "message",
		Role:       "assistant",
		Content:    content,
		Model:      warpResp.Model,
		StopReason: warpResp.Choices[0].FinishReason,
		Usage: models.ClaudeUsage{
			InputTokens:  warpResp.Usage.PromptTokens,
			OutputTokens: warpResp.Usage.CompletionTokens,
		},
	}
}