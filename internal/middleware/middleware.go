package middleware

import (
	"fmt"
	"time"

	"warp2api-go/internal/config"
	"warp2api-go/internal/logger"

	"github.com/gin-gonic/gin"
	"golang.org/x/time/rate"
)

// Logger middleware for request logging
func Logger() gin.HandlerFunc {
	return gin.LoggerWithFormatter(func(param gin.LogFormatterParams) string {
		return fmt.Sprintf("%s - [%s] \"%s %s %s %d %s \"%s\" %s\"\n",
			param.ClientIP,
			param.TimeStamp.Format(time.RFC1123),
			param.Method,
			param.Path,
			param.Request.Proto,
			param.StatusCode,
			param.Latency,
			param.Request.UserAgent(),
			param.ErrorMessage,
		)
	})
}

// RateLimit middleware for rate limiting
func RateLimit(cfg config.RateLimitConfig) gin.HandlerFunc {
	if !cfg.Enabled {
		return gin.HandlerFunc(func(c *gin.Context) {
			c.Next()
		})
	}

	// Create rate limiter
	limiter := rate.NewLimiter(rate.Limit(cfg.RequestsPerMinute/60.0), cfg.BurstSize)

	return gin.HandlerFunc(func(c *gin.Context) {
		if !limiter.Allow() {
			logger.Warnf("Rate limit exceeded for client %s", c.ClientIP())
			c.JSON(429, gin.H{
				"error": "Rate limit exceeded",
				"type":  "rate_limit_error",
			})
			c.Abort()
			return
		}
		c.Next()
	})
}