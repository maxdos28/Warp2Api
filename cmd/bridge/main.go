package main

import (
	"flag"
	"log"
	"os"
	"os/signal"
	"syscall"

	"warp2api-go/internal/config"
	"warp2api-go/internal/logger"
	"warp2api-go/internal/bridge"
)

func main() {
	var (
		port       = flag.Int("port", 28888, "Bridge server port")
		host       = flag.String("host", "127.0.0.1", "Bridge server host")
		verbose    = flag.Bool("verbose", false, "Enable verbose logging")
		configFile = flag.String("config", "", "Configuration file path")
	)
	flag.Parse()

	// Load configuration
	cfg, err := config.Load(*configFile)
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Override config with command line flags
	if *port != 28888 {
		cfg.Server.Port = *port
	}
	if *host != "127.0.0.1" {
		cfg.Server.Host = *host
	}
	if *verbose {
		cfg.Logging.Level = "debug"
	}

	// Initialize logger
	logger.Init(logger.Config{
		Level:  cfg.Logging.Level,
		Format: cfg.Logging.Format,
		File:   cfg.Logging.File,
	})

	// Create and start bridge server
	srv := bridge.New(cfg)
	
	// Handle graceful shutdown
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	
	go func() {
		<-c
		logger.Info("Shutting down bridge server...")
		srv.Shutdown()
	}()

	// Start server
	if err := srv.Start(); err != nil {
		logger.Fatalf("Failed to start bridge server: %v", err)
	}
}