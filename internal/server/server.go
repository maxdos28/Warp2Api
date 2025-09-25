package server

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"warp2api-go/internal/config"
	"warp2api-go/internal/handlers"
	"warp2api-go/internal/middleware"
	"warp2api-go/internal/logger"

	"github.com/gin-contrib/cors"
	"github.com/gin-contrib/compress"
	"github.com/gin-gonic/gin"
)

// Server represents the HTTP server
type Server struct {
	config *config.Config
	router *gin.Engine
	server *http.Server
}

// New creates a new server instance
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
	router.Use(middleware.RateLimit(cfg.RateLimit))
	router.Use(compress.Gzip())
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

// Start starts the server
func (s *Server) Start() error {
	addr := fmt.Sprintf("%s:%d", s.config.Server.Host, s.config.Server.Port)
	
	s.server = &http.Server{
		Addr:         addr,
		Handler:      s.router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	logger.Infof("Starting server on %s", addr)
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

// registerRoutes registers all API routes
func registerRoutes(router *gin.Engine, h *handlers.Handlers) {
	// Health check
	router.GET("/healthz", h.HealthCheck)
	router.GET("/", h.HealthCheck)

	// API v1 routes
	v1 := router.Group("/v1")
	{
		// Models
		v1.GET("/models", h.ListModels)
		
		// OpenAI Chat Completions API
		v1.POST("/chat/completions", h.ChatCompletions)
		
		// Claude Messages API
		v1.POST("/messages", h.Messages)
	}
}