package services

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"warp2api-go/internal/config"
	"warp2api-go/internal/logger"
	"warp2api-go/internal/protobuf"
	"warp2api-go/internal/warp"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"github.com/go-resty/resty/v2"
)

// Service handles bridge business logic
type Service struct {
	config     *config.Config
	protobuf   *protobuf.Manager
	warp       *warp.Client
	httpClient *resty.Client
}

// New creates a new service instance
func New(cfg *config.Config) *Service {
	client := resty.New()
	client.SetTimeout(30 * time.Second)

	return &Service{
		config:     cfg,
		protobuf:   protobuf.New(cfg),
		warp:       warp.New(cfg),
		httpClient: client,
	}
}

// EncodeProtobuf encodes JSON to protobuf
func (s *Service) EncodeProtobuf(data map[string]interface{}) (map[string]interface{}, error) {
	return s.protobuf.Encode(data)
}

// DecodeProtobuf decodes protobuf to JSON
func (s *Service) DecodeProtobuf(data map[string]interface{}) (map[string]interface{}, error) {
	return s.protobuf.Decode(data)
}

// StreamDecodeProtobuf handles streaming protobuf decoding
func (s *Service) StreamDecodeProtobuf(c *gin.Context, data map[string]interface{}) error {
	// Set SSE headers
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")

	// Process streaming decode
	decoder := s.protobuf.NewStreamDecoder()
	
	for {
		chunk, err := decoder.DecodeChunk(data)
		if err != nil {
			if err.Error() == "EOF" {
				break
			}
			return fmt.Errorf("failed to decode chunk: %w", err)
		}

		// Send SSE event
		event := fmt.Sprintf("data: %s\n\n", chunk)
		c.Writer.WriteString(event)
		c.Writer.Flush()

		// Simulate streaming delay
		time.Sleep(100 * time.Millisecond)
	}

	return nil
}

// SendToWarp forwards requests to Warp API
func (s *Service) SendToWarp(data map[string]interface{}) (map[string]interface{}, error) {
	// Convert to protobuf
	protobufData, err := s.protobuf.Encode(data)
	if err != nil {
		return nil, fmt.Errorf("failed to encode to protobuf: %w", err)
	}

	// Send to Warp API
	return s.warp.SendRequest(protobufData)
}

// SendToWarpStream forwards streaming requests to Warp API
func (s *Service) SendToWarpStream(c *gin.Context, data map[string]interface{}) error {
	// Set SSE headers
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")

	// Process streaming request
	stream := s.warp.NewStream(c)
	return s.warp.SendStreamRequest(stream, data)
}

// SendToWarpSSE forwards SSE requests to Warp API
func (s *Service) SendToWarpSSE(c *gin.Context, data map[string]interface{}) error {
	// Set SSE headers
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")

	// Process SSE request
	return s.warp.SendSSERequest(c, data)
}

// ProxyGraphQL proxies GraphQL requests to Warp API
func (s *Service) ProxyGraphQL(c *gin.Context) error {
	// Get request body
	body, err := c.GetRawData()
	if err != nil {
		return fmt.Errorf("failed to get request body: %w", err)
	}

	// Forward to Warp GraphQL endpoint
	resp, err := s.httpClient.R().
		SetHeader("Authorization", "Bearer "+s.getAuthToken()).
		SetHeader("Content-Type", "application/json").
		SetBody(body).
		Post(s.config.Warp.BaseURL + "/graphql")

	if err != nil {
		return fmt.Errorf("failed to forward GraphQL request: %w", err)
	}

	// Copy response
	c.Data(resp.StatusCode(), resp.Header().Get("Content-Type"), resp.Body())
	return nil
}

// GetSchemas returns protobuf schema information
func (s *Service) GetSchemas() (map[string]interface{}, error) {
	return s.protobuf.GetSchemas(), nil
}

// GetAuthStatus returns authentication status
func (s *Service) GetAuthStatus() (map[string]interface{}, error) {
	tokenInfo, err := s.warp.GetTokenInfo()
	if err != nil {
		return nil, fmt.Errorf("failed to get token info: %w", err)
	}

	return map[string]interface{}{
		"authenticated": !tokenInfo.IsExpired,
		"token_info":    tokenInfo,
	}, nil
}

// RefreshToken refreshes the JWT token
func (s *Service) RefreshToken() (map[string]interface{}, error) {
	token, err := s.warp.RefreshToken()
	if err != nil {
		return nil, fmt.Errorf("failed to refresh token: %w", err)
	}

	return map[string]interface{}{
		"success": true,
		"token":   token,
	}, nil
}

// GetUserID returns the current user ID
func (s *Service) GetUserID() (string, error) {
	return s.warp.GetUserID()
}

// GetPacketHistory returns packet history
func (s *Service) GetPacketHistory() ([]map[string]interface{}, error) {
	return s.protobuf.GetPacketHistory(), nil
}

// HandleWebSocket handles WebSocket connections
func (s *Service) HandleWebSocket(conn *websocket.Conn) error {
	defer conn.Close()

	// Send welcome message
	welcome := map[string]interface{}{
		"type":    "welcome",
		"message": "Connected to Warp2API Bridge",
		"time":    time.Now().Unix(),
	}

	if err := conn.WriteJSON(welcome); err != nil {
		return fmt.Errorf("failed to send welcome message: %w", err)
	}

	// Handle messages
	for {
		var msg map[string]interface{}
		if err := conn.ReadJSON(&msg); err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				logger.Errorf("WebSocket error: %v", err)
			}
			break
		}

		// Process message
		response := s.processWebSocketMessage(msg)
		
		// Send response
		if err := conn.WriteJSON(response); err != nil {
			return fmt.Errorf("failed to send response: %w", err)
		}
	}

	return nil
}

// processWebSocketMessage processes WebSocket messages
func (s *Service) processWebSocketMessage(msg map[string]interface{}) map[string]interface{} {
	msgType, ok := msg["type"].(string)
	if !ok {
		return map[string]interface{}{
			"type": "error",
			"error": "Invalid message type",
		}
	}

	switch msgType {
	case "ping":
		return map[string]interface{}{
			"type": "pong",
			"time": time.Now().Unix(),
		}
	case "status":
		status, _ := s.GetAuthStatus()
		return map[string]interface{}{
			"type":   "status",
			"status": status,
		}
	default:
		return map[string]interface{}{
			"type": "error",
			"error": "Unknown message type",
		}
	}
}

// getAuthToken returns the current auth token
func (s *Service) getAuthToken() string {
	token, err := s.warp.GetValidToken()
	if err != nil {
		logger.Errorf("Failed to get auth token: %v", err)
		return ""
	}
	return token
}