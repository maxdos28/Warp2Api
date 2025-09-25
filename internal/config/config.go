package config

import (
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

// Config represents the application configuration
type Config struct {
	Server   ServerConfig   `json:"server"`
	Warp     WarpConfig     `json:"warp"`
	Logging  LoggingConfig  `json:"logging"`
	Bridge   BridgeConfig   `json:"bridge"`
	RateLimit RateLimitConfig `json:"rate_limit"`
}

// ServerConfig holds server configuration
type ServerConfig struct {
	Host string `json:"host"`
	Port int    `json:"port"`
}

// WarpConfig holds Warp API configuration
type WarpConfig struct {
	JWT           string `json:"jwt"`
	RefreshToken  string `json:"refresh_token"`
	BaseURL       string `json:"base_url"`
	ClientVersion string `json:"client_version"`
	OSCategory    string `json:"os_category"`
	OSName        string `json:"os_name"`
	OSVersion     string `json:"os_version"`
}

// LoggingConfig holds logging configuration
type LoggingConfig struct {
	Level  string `json:"level"`
	Format string `json:"format"`
	File   string `json:"file"`
}

// BridgeConfig holds bridge server configuration
type BridgeConfig struct {
	URL string `json:"url"`
}

// RateLimitConfig holds rate limiting configuration
type RateLimitConfig struct {
	Enabled     bool `json:"enabled"`
	RequestsPerMinute int `json:"requests_per_minute"`
	BurstSize   int  `json:"burst_size"`
}

// Load loads configuration from environment variables and optional config file
func Load(configFile string) (*Config, error) {
	// Load .env file if it exists
	if _, err := os.Stat(".env"); err == nil {
		if err := godotenv.Load(); err != nil {
			return nil, err
		}
	}

	cfg := &Config{
		Server: ServerConfig{
			Host: getEnv("HOST", "127.0.0.1"),
			Port: getEnvInt("PORT", 28889),
		},
		Warp: WarpConfig{
			JWT:           getEnv("WARP_JWT", ""),
			RefreshToken:  getEnv("WARP_REFRESH_TOKEN", ""),
			BaseURL:       getEnv("WARP_BASE_URL", "https://api.warp.dev"),
			ClientVersion: getEnv("CLIENT_VERSION", "1.0.0"),
			OSCategory:    getEnv("OS_CATEGORY", "linux"),
			OSName:        getEnv("OS_NAME", "linux"),
			OSVersion:     getEnv("OS_VERSION", "6.12.8+"),
		},
		Logging: LoggingConfig{
			Level:  getEnv("W2A_VERBOSE", "false"),
			Format: getEnv("LOG_FORMAT", "json"),
			File:   getEnv("LOG_FILE", ""),
		},
		Bridge: BridgeConfig{
			URL: getEnv("WARP_BRIDGE_URL", "http://127.0.0.1:28888"),
		},
		RateLimit: RateLimitConfig{
			Enabled:          getEnvBool("RATE_LIMIT_ENABLED", true),
			RequestsPerMinute: getEnvInt("RATE_LIMIT_RPM", 60),
			BurstSize:        getEnvInt("RATE_LIMIT_BURST", 10),
		},
	}

	// Parse verbose flag
	if cfg.Logging.Level == "true" {
		cfg.Logging.Level = "debug"
	} else if cfg.Logging.Level == "false" {
		cfg.Logging.Level = "info"
	}

	return cfg, nil
}

// Helper functions for environment variables
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
	}
	return defaultValue
}