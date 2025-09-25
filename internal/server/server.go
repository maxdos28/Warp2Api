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
	"warp2api-go/internal/performance"
	"warp2api-go/internal/cache"
	"warp2api-go/internal/memory"
	"warp2api-go/internal/pool"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"golang.org/x/net/http2"
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

	// Initialize performance monitoring
	monitor := performance.GetGlobalMonitor()
	performance.StartMonitoring(5 * time.Minute)
	
	// Initialize cache
	_ = cache.GetGlobalCache()
	cache.StartCleanupTask(5 * time.Minute)
	
	// Initialize memory optimizer
	_ = memory.GetGlobalOptimizer()
	memory.StartOptimizationTask(5 * time.Minute)
	
	// Initialize connection pool
	connectionPool := pool.GetGlobalPool()
	connectionPool.Warmup()

	router := gin.New()

	// Add performance monitoring middleware
	router.Use(performanceMiddleware(monitor))
	
	// Add middleware
	router.Use(gin.Recovery())
	router.Use(middleware.Logger())
	router.Use(middleware.RateLimit(cfg.RateLimit))
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

// Start starts the server with HTTP/2 support
func (s *Server) Start() error {
	addr := fmt.Sprintf("%s:%d", s.config.Server.Host, s.config.Server.Port)
	
	s.server = &http.Server{
		Addr:         addr,
		Handler:      s.router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Configure HTTP/2
	http2.ConfigureServer(s.server, &http2.Server{
		MaxConcurrentStreams: 1000,
		MaxReadFrameSize:     1048576, // 1MB
		PermitProhibitedCipherSuites: false,
	})

	logger.Infof("Starting server with HTTP/2 support on %s", addr)
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
	
	// Performance monitoring endpoints
	router.GET("/metrics", h.GetMetrics)
	router.GET("/stats", h.GetStats)
}

// performanceMiddleware adds performance monitoring to requests
func performanceMiddleware(monitor *performance.Monitor) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		
		// Record connection
		monitor.RecordConnection(1)
		defer monitor.RecordConnection(-1)
		
		c.Next()
		
		// Record request metrics
		duration := time.Since(start)
		isError := c.Writer.Status() >= 400
		monitor.RecordRequest(duration, isError)
	}
}