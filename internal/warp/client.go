package warp

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"warp2api-go/internal/config"
	"warp2api-go/internal/models"
	"warp2api-go/internal/streaming"
	"warp2api-go/internal/auth"

	"github.com/gin-gonic/gin"
	"github.com/go-resty/resty/v2"
)

// Client handles communication with Warp API
type Client struct {
	config     *config.Config
	httpClient *resty.Client
	auth       *auth.Manager
}

// New creates a new Warp client
func New(cfg *config.Config) *Client {
	client := resty.New()
	client.SetTimeout(30 * time.Second)
	client.SetRetryCount(3)
	client.SetRetryWaitTime(1 * time.Second)
	client.SetRetryMaxWaitTime(5 * time.Second)

	return &Client{
		config:     cfg,
		httpClient: client,
		auth:       auth.New(cfg),
	}
}

// ProcessRequest processes a request with streaming
func (c *Client) ProcessRequest(stream *streaming.Stream, req *models.WarpRequest) error {
	// Get valid token
	token, err := c.auth.GetValidToken()
	if err != nil {
		return fmt.Errorf("failed to get valid token: %w", err)
	}

	// Prepare request
	reqBody, err := json.Marshal(req)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	// Make request to Warp API
	resp, err := c.httpClient.R().
		SetHeader("Authorization", "Bearer "+token).
		SetHeader("Content-Type", "application/json").
		SetBody(reqBody).
		Post(c.config.Warp.BaseURL + "/v1/chat/completions")

	if err != nil {
		return fmt.Errorf("failed to make request to Warp API: %w", err)
	}

	if resp.StatusCode() != http.StatusOK {
		return fmt.Errorf("Warp API returned error: %s", resp.String())
	}

	// Handle streaming response
	if req.Stream {
		return c.handleStreamingResponse(stream, resp.Body())
	} else {
		return c.handleNonStreamingResponse(stream, resp.Body())
	}
}

// ProcessRequestSync processes a request synchronously
func (c *Client) ProcessRequestSync(req *models.WarpRequest) (*models.WarpResponse, error) {
	// Get valid token
	token, err := c.auth.GetValidToken()
	if err != nil {
		return nil, fmt.Errorf("failed to get valid token: %w", err)
	}

	// Prepare request
	reqBody, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Make request to Warp API
	resp, err := c.httpClient.R().
		SetHeader("Authorization", "Bearer "+token).
		SetHeader("Content-Type", "application/json").
		SetBody(reqBody).
		Post(c.config.Warp.BaseURL + "/v1/chat/completions")

	if err != nil {
		return nil, fmt.Errorf("failed to make request to Warp API: %w", err)
	}

	if resp.StatusCode() != http.StatusOK {
		return nil, fmt.Errorf("Warp API returned error: %s", resp.String())
	}

	// Parse response
	var warpResp models.WarpResponse
	if err := json.Unmarshal(resp.Body(), &warpResp); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &warpResp, nil
}

// handleStreamingResponse handles streaming response
func (c *Client) handleStreamingResponse(stream *streaming.Stream, body []byte) error {
	// For now, simulate streaming by sending the response as a single event
	// In a real implementation, this would parse actual streaming data
	
	event := models.StreamingEvent{
		ID:   "stream_" + fmt.Sprintf("%d", time.Now().Unix()),
		Data: map[string]interface{}{
			"content": "This is a simulated streaming response",
			"timestamp": time.Now().Unix(),
		},
	}

	return stream.SendEvent(event)
}

// handleNonStreamingResponse handles non-streaming response
func (c *Client) handleNonStreamingResponse(stream *streaming.Stream, body []byte) error {
	// Parse as WarpResponse
	var warpResp models.WarpResponse
	if err := json.Unmarshal(body, &warpResp); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}

	// Convert to streaming event and send
	event := models.StreamingEvent{
		ID:   warpResp.ID,
		Data: warpResp,
	}
	
	return stream.SendEvent(event)
}

// NewStream creates a new stream for Warp API
func (c *Client) NewStream(ctx *gin.Context) *streaming.Stream {
	return streaming.New(ctx, nil)
}

// SendStreamRequest sends a streaming request to Warp API
func (c *Client) SendStreamRequest(stream *streaming.Stream, data map[string]interface{}) error {
	// Simulate streaming request processing
	event := models.StreamingEvent{
		ID:   "stream_" + fmt.Sprintf("%d", time.Now().Unix()),
		Data: map[string]interface{}{
			"content": "Streaming request processed",
			"data":    data,
		},
	}

	return stream.SendEvent(event)
}

// SendSSERequest sends an SSE request to Warp API
func (c *Client) SendSSERequest(ctx *gin.Context, data map[string]interface{}) error {
	// Set SSE headers
	ctx.Header("Content-Type", "text/event-stream")
	ctx.Header("Cache-Control", "no-cache")
	ctx.Header("Connection", "keep-alive")

	// Simulate SSE response
	event := models.StreamingEvent{
		ID:   "sse_" + fmt.Sprintf("%d", time.Now().Unix()),
		Data: map[string]interface{}{
			"content": "SSE request processed",
			"data":    data,
		},
	}

	jsonData, err := json.Marshal(event.Data)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %w", err)
	}

	ctx.Writer.WriteString(fmt.Sprintf("data: %s\n\n", string(jsonData)))
	ctx.Writer.Flush()

	return nil
}

// SendRequest sends a request to Warp API
func (c *Client) SendRequest(data map[string]interface{}) (map[string]interface{}, error) {
	// Get valid token
	token, err := c.auth.GetValidToken()
	if err != nil {
		return nil, fmt.Errorf("failed to get valid token: %w", err)
	}

	// Prepare request
	reqBody, err := json.Marshal(data)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Make request to Warp API
	resp, err := c.httpClient.R().
		SetHeader("Authorization", "Bearer "+token).
		SetHeader("Content-Type", "application/json").
		SetBody(reqBody).
		Post(c.config.Warp.BaseURL + "/v1/chat/completions")

	if err != nil {
		return nil, fmt.Errorf("failed to make request to Warp API: %w", err)
	}

	if resp.StatusCode() != http.StatusOK {
		return nil, fmt.Errorf("Warp API returned error: %s", resp.String())
	}

	// Parse response
	var result map[string]interface{}
	if err := json.Unmarshal(resp.Body(), &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return result, nil
}

// GetTokenInfo returns token information
func (c *Client) GetTokenInfo() (*models.TokenInfo, error) {
	return c.auth.GetTokenInfo()
}

// RefreshToken refreshes the JWT token
func (c *Client) RefreshToken() (string, error) {
	return c.auth.GetValidToken()
}

// GetUserID returns the current user ID
func (c *Client) GetUserID() (string, error) {
	// For now, return a placeholder user ID
	// In a real implementation, this would extract user ID from the JWT token
	return "user_" + fmt.Sprintf("%d", time.Now().Unix()), nil
}