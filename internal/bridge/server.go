package bridge

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"warp2api-go/internal/config"
	"warp2api-go/internal/logger"
	"warp2api-go/internal/bridge/handlers"
	"warp2api-go/internal/bridge/middleware"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

// Server represents the bridge server
type Server struct {
	config *config.Config
	router *gin.Engine
	server *http.Server
}

// New creates a new bridge server instance
func New(cfg *config.Config) *Server {
	// Set Gin mode
	if cfg.Logging.Level == "debug" {
		gin.SetMode(gin.DebugMode)
	} else {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()

	// Add middleware
	router.Use(gin.Recovery())
	router.Use(middleware.Logger())
	router.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"*"},
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"*"},
		ExposeHeaders:    []string{"*"},
		AllowCredentials: true,
	}))

	// Create handlers
	h := handlers.New(cfg)

	// Register routes
	registerRoutes(router, h)

	return &Server{
		config: cfg,
		router: router,
	}
}

// Start starts the bridge server
func (s *Server) Start() error {
	addr := fmt.Sprintf("%s:%d", s.config.Server.Host, s.config.Server.Port)
	
	s.server = &http.Server{
		Addr:         addr,
		Handler:      s.router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	logger.Infof("Starting bridge server on %s", addr)
	return s.server.ListenAndServe()
}

// Shutdown gracefully shuts down the server
func (s *Server) Shutdown() {
	if s.server != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		s.server.Shutdown(ctx)
	}
}

// registerRoutes registers all bridge routes
func registerRoutes(router *gin.Engine, h *handlers.Handlers) {
	// Health check
	router.GET("/healthz", h.HealthCheck)
	router.GET("/", h.HealthCheck)

	// API routes
	api := router.Group("/api")
	{
		// Protobuf encoding/decoding
		api.POST("/encode", h.Encode)
		api.POST("/decode", h.Decode)
		api.POST("/stream-decode", h.StreamDecode)
		
		// Warp API forwarding
		api.POST("/warp/send", h.SendToWarp)
		api.POST("/warp/send_stream", h.SendToWarpStream)
		api.POST("/warp/send_stream_sse", h.SendToWarpSSE)
		
		// GraphQL forwarding
		api.Any("/warp/graphql/*path", h.GraphQLProxy)
		
		// Schema information
		api.GET("/schemas", h.GetSchemas)
		
		// Auth endpoints
		auth := api.Group("/auth")
		{
			auth.GET("/status", h.AuthStatus)
			auth.POST("/refresh", h.RefreshToken)
			auth.GET("/user_id", h.GetUserID)
		}
		
		// Packet history
		api.GET("/packets/history", h.GetPacketHistory)
	}

	// WebSocket endpoint
	router.GET("/ws", h.WebSocket)
}