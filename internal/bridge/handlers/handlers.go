package handlers

import (
	"net/http"

	"warp2api-go/internal/config"
	"warp2api-go/internal/logger"
	"warp2api-go/internal/bridge/services"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

// Handlers contains all bridge HTTP handlers
type Handlers struct {
	config  *config.Config
	service *services.Service
	upgrader websocket.Upgrader
}

// New creates a new handlers instance
func New(cfg *config.Config) *Handlers {
	return &Handlers{
		config:  cfg,
		service: services.New(cfg),
		upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				return true // Allow all origins for development
			},
		},
	}
}

// HealthCheck handles health check requests
func (h *Handlers) HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
		"service": "warp2api-bridge",
		"version": "1.0.0",
	})
}

// Encode handles protobuf encoding requests
func (h *Handlers) Encode(c *gin.Context) {
	var req map[string]interface{}
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Errorf("Invalid encode request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request format"})
		return
	}

	result, err := h.service.EncodeProtobuf(req)
	if err != nil {
		logger.Errorf("Failed to encode protobuf: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Encoding failed"})
		return
	}

	c.JSON(http.StatusOK, result)
}

// Decode handles protobuf decoding requests
func (h *Handlers) Decode(c *gin.Context) {
	var req map[string]interface{}
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Errorf("Invalid decode request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request format"})
		return
	}

	result, err := h.service.DecodeProtobuf(req)
	if err != nil {
		logger.Errorf("Failed to decode protobuf: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Decoding failed"})
		return
	}

	c.JSON(http.StatusOK, result)
}

// StreamDecode handles streaming protobuf decoding
func (h *Handlers) StreamDecode(c *gin.Context) {
	var req map[string]interface{}
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Errorf("Invalid stream decode request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request format"})
		return
	}

	// Set SSE headers
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")

	// Process streaming decode
	if err := h.service.StreamDecodeProtobuf(c, req); err != nil {
		logger.Errorf("Failed to stream decode protobuf: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Stream decoding failed"})
		return
	}
}

// SendToWarp forwards requests to Warp API
func (h *Handlers) SendToWarp(c *gin.Context) {
	var req map[string]interface{}
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Errorf("Invalid Warp request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request format"})
		return
	}

	result, err := h.service.SendToWarp(req)
	if err != nil {
		logger.Errorf("Failed to send to Warp: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Warp request failed"})
		return
	}

	c.JSON(http.StatusOK, result)
}

// SendToWarpStream forwards streaming requests to Warp API
func (h *Handlers) SendToWarpStream(c *gin.Context) {
	var req map[string]interface{}
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Errorf("Invalid Warp stream request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request format"})
		return
	}

	// Set SSE headers
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")

	// Process streaming request
	if err := h.service.SendToWarpStream(c, req); err != nil {
		logger.Errorf("Failed to send stream to Warp: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Warp stream request failed"})
		return
	}
}

// SendToWarpSSE forwards SSE requests to Warp API
func (h *Handlers) SendToWarpSSE(c *gin.Context) {
	var req map[string]interface{}
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Errorf("Invalid Warp SSE request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request format"})
		return
	}

	// Set SSE headers
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")

	// Process SSE request
	if err := h.service.SendToWarpSSE(c, req); err != nil {
		logger.Errorf("Failed to send SSE to Warp: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Warp SSE request failed"})
		return
	}
}

// GraphQLProxy proxies GraphQL requests to Warp API
func (h *Handlers) GraphQLProxy(c *gin.Context) {
	if err := h.service.ProxyGraphQL(c); err != nil {
		logger.Errorf("Failed to proxy GraphQL: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "GraphQL proxy failed"})
		return
	}
}

// GetSchemas returns protobuf schema information
func (h *Handlers) GetSchemas(c *gin.Context) {
	schemas, err := h.service.GetSchemas()
	if err != nil {
		logger.Errorf("Failed to get schemas: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get schemas"})
		return
	}

	c.JSON(http.StatusOK, schemas)
}

// AuthStatus returns authentication status
func (h *Handlers) AuthStatus(c *gin.Context) {
	status, err := h.service.GetAuthStatus()
	if err != nil {
		logger.Errorf("Failed to get auth status: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get auth status"})
		return
	}

	c.JSON(http.StatusOK, status)
}

// RefreshToken refreshes the JWT token
func (h *Handlers) RefreshToken(c *gin.Context) {
	result, err := h.service.RefreshToken()
	if err != nil {
		logger.Errorf("Failed to refresh token: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to refresh token"})
		return
	}

	c.JSON(http.StatusOK, result)
}

// GetUserID returns the current user ID
func (h *Handlers) GetUserID(c *gin.Context) {
	userID, err := h.service.GetUserID()
	if err != nil {
		logger.Errorf("Failed to get user ID: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get user ID"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"user_id": userID})
}

// GetPacketHistory returns packet history
func (h *Handlers) GetPacketHistory(c *gin.Context) {
	history, err := h.service.GetPacketHistory()
	if err != nil {
		logger.Errorf("Failed to get packet history: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get packet history"})
		return
	}

	c.JSON(http.StatusOK, history)
}

// WebSocket handles WebSocket connections for real-time monitoring
func (h *Handlers) WebSocket(c *gin.Context) {
	conn, err := h.upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		logger.Errorf("Failed to upgrade WebSocket connection: %v", err)
		return
	}
	defer conn.Close()

	// Handle WebSocket connection
	if err := h.service.HandleWebSocket(conn); err != nil {
		logger.Errorf("WebSocket error: %v", err)
	}
}