package handlers

import (
	"net/http"

	"warp2api-go/internal/config"
	"warp2api-go/internal/logger"
	"warp2api-go/internal/models"
	"warp2api-go/internal/services"

	"github.com/gin-gonic/gin"
)

// Handlers contains all HTTP handlers
type Handlers struct {
	config  *config.Config
	service *services.Service
}

// New creates a new handlers instance
func New(cfg *config.Config) *Handlers {
	return &Handlers{
		config:  cfg,
		service: services.New(cfg),
	}
}

// HealthCheck handles health check requests
func (h *Handlers) HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
		"service": "warp2api-go",
		"version": "1.0.0",
	})
}

// ListModels handles model listing requests
func (h *Handlers) ListModels(c *gin.Context) {
	models := []models.Model{
		{ID: "claude-4-sonnet", Object: "model"},
		{ID: "claude-4-opus", Object: "model"},
		{ID: "claude-4.1-opus", Object: "model"},
		{ID: "gemini-2.5-pro", Object: "model"},
		{ID: "gpt-4.1", Object: "model"},
		{ID: "gpt-4o", Object: "model"},
		{ID: "gpt-5", Object: "model"},
		{ID: "gpt-5 (high reasoning)", Object: "model"},
		{ID: "o3", Object: "model"},
		{ID: "o4-mini", Object: "model"},
	}

	c.JSON(http.StatusOK, gin.H{
		"object": "list",
		"data":   models,
	})
}

// ChatCompletions handles OpenAI Chat Completions API requests
func (h *Handlers) ChatCompletions(c *gin.Context) {
	var req models.ChatCompletionsRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Errorf("Invalid request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request format"})
		return
	}

	// Validate required fields
	if len(req.Messages) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Messages cannot be empty"})
		return
	}

	// Process request
	if req.Stream {
		h.handleStreamingChat(c, &req)
	} else {
		h.handleNonStreamingChat(c, &req)
	}
}

// Messages handles Claude Messages API requests
func (h *Handlers) Messages(c *gin.Context) {
	var req models.MessagesRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Errorf("Invalid request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request format"})
		return
	}

	// Validate required fields
	if len(req.Messages) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Messages cannot be empty"})
		return
	}

	// Process request
	if req.Stream {
		h.handleStreamingMessages(c, &req)
	} else {
		h.handleNonStreamingMessages(c, &req)
	}
}

// handleStreamingChat handles streaming chat completions
func (h *Handlers) handleStreamingChat(c *gin.Context, req *models.ChatCompletionsRequest) {
	// Set SSE headers
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")

	// Create streaming response
	stream := h.service.CreateStreamingResponse(c, req)
	defer stream.Close()

	// Process the request
	if err := h.service.ProcessChatRequest(stream, req); err != nil {
		logger.Errorf("Error processing chat request: %v", err)
		stream.SendError(err)
		return
	}
}

// handleNonStreamingChat handles non-streaming chat completions
func (h *Handlers) handleNonStreamingChat(c *gin.Context, req *models.ChatCompletionsRequest) {
	response, err := h.service.ProcessChatRequestSync(req)
	if err != nil {
		logger.Errorf("Error processing chat request: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, response)
}

// handleStreamingMessages handles streaming Claude messages
func (h *Handlers) handleStreamingMessages(c *gin.Context, req *models.MessagesRequest) {
	// Set SSE headers
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")

	// Create streaming response
	stream := h.service.CreateStreamingResponse(c, req)
	defer stream.Close()

	// Process the request
	if err := h.service.ProcessMessagesRequest(stream, req); err != nil {
		logger.Errorf("Error processing messages request: %v", err)
		stream.SendError(err)
		return
	}
}

// handleNonStreamingMessages handles non-streaming Claude messages
func (h *Handlers) handleNonStreamingMessages(c *gin.Context, req *models.MessagesRequest) {
	response, err := h.service.ProcessMessagesRequestSync(req)
	if err != nil {
		logger.Errorf("Error processing messages request: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, response)
}