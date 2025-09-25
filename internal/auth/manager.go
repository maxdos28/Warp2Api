package auth

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"warp2api-go/internal/config"
	"warp2api-go/internal/logger"
	"warp2api-go/internal/models"

	"github.com/go-resty/resty/v2"
	"github.com/golang-jwt/jwt/v5"
	"github.com/patrickmn/go-cache"
)

// Manager handles JWT token management
type Manager struct {
	config     *config.Config
	httpClient *resty.Client
	cache      *cache.Cache
}

// New creates a new auth manager
func New(cfg *config.Config) *Manager {
	client := resty.New()
	client.SetTimeout(30 * time.Second)

	return &Manager{
		config:     cfg,
		httpClient: client,
		cache:      cache.New(5*time.Minute, 10*time.Minute),
	}
}

// GetValidToken returns a valid JWT token, refreshing if necessary
func (m *Manager) GetValidToken() (string, error) {
	// Check if we have a cached token
	if token, found := m.cache.Get("jwt_token"); found {
		if jwtToken, ok := token.(string); ok {
			// Check if token is still valid
			if !m.isTokenExpired(jwtToken) {
				return jwtToken, nil
			}
		}
	}

	// Try to refresh token
	if m.config.Warp.RefreshToken != "" {
		newToken, err := m.refreshToken()
		if err == nil && newToken != "" {
			m.cache.Set("jwt_token", newToken, cache.DefaultExpiration)
			return newToken, nil
		}
		logger.Warnf("Failed to refresh token: %v", err)
	}

	// Try to get anonymous token
	anonymousToken, err := m.getAnonymousToken()
	if err != nil {
		return "", fmt.Errorf("failed to get any valid token: %w", err)
	}

	m.cache.Set("jwt_token", anonymousToken, cache.DefaultExpiration)
	return anonymousToken, nil
}

// refreshToken refreshes the JWT token using refresh token
func (m *Manager) refreshToken() (string, error) {
	reqBody := map[string]interface{}{
		"refresh_token": m.config.Warp.RefreshToken,
		"client_version": m.config.Warp.ClientVersion,
		"os_category":    m.config.Warp.OSCategory,
		"os_name":        m.config.Warp.OSName,
		"os_version":     m.config.Warp.OSVersion,
	}

	resp, err := m.httpClient.R().
		SetHeader("Content-Type", "application/json").
		SetBody(reqBody).
		Post(m.config.Warp.BaseURL + "/auth/refresh")

	if err != nil {
		return "", fmt.Errorf("failed to make refresh request: %w", err)
	}

	if resp.StatusCode() != http.StatusOK {
		return "", fmt.Errorf("refresh request failed with status %d: %s", resp.StatusCode(), resp.String())
	}

	var refreshResp struct {
		AccessToken  string `json:"access_token"`
		RefreshToken string `json:"refresh_token"`
		ExpiresIn    int    `json:"expires_in"`
	}

	if err := json.Unmarshal(resp.Body(), &refreshResp); err != nil {
		return "", fmt.Errorf("failed to parse refresh response: %w", err)
	}

	// Update refresh token if provided
	if refreshResp.RefreshToken != "" {
		m.config.Warp.RefreshToken = refreshResp.RefreshToken
	}

	return refreshResp.AccessToken, nil
}

// getAnonymousToken gets an anonymous access token
func (m *Manager) getAnonymousToken() (string, error) {
	reqBody := map[string]interface{}{
		"client_version": m.config.Warp.ClientVersion,
		"os_category":    m.config.Warp.OSCategory,
		"os_name":        m.config.Warp.OSName,
		"os_version":     m.config.Warp.OSVersion,
	}

	resp, err := m.httpClient.R().
		SetHeader("Content-Type", "application/json").
		SetBody(reqBody).
		Post(m.config.Warp.BaseURL + "/auth/anonymous")

	if err != nil {
		return "", fmt.Errorf("failed to make anonymous request: %w", err)
	}

	if resp.StatusCode() != http.StatusOK {
		return "", fmt.Errorf("anonymous request failed with status %d: %s", resp.StatusCode(), resp.String())
	}

	var anonymousResp struct {
		AccessToken string `json:"access_token"`
		ExpiresIn   int    `json:"expires_in"`
	}

	if err := json.Unmarshal(resp.Body(), &anonymousResp); err != nil {
		return "", fmt.Errorf("failed to parse anonymous response: %w", err)
	}

	return anonymousResp.AccessToken, nil
}

// isTokenExpired checks if a JWT token is expired
func (m *Manager) isTokenExpired(token string) bool {
	// Parse JWT token
	parsedToken, err := jwt.Parse(token, func(token *jwt.Token) (interface{}, error) {
		return []byte(""), nil // We don't need to verify signature for expiration check
	})

	if err != nil {
		return true
	}

	// Check if token is valid and not expired
	if claims, ok := parsedToken.Claims.(jwt.MapClaims); ok {
		if exp, ok := claims["exp"].(float64); ok {
			expTime := time.Unix(int64(exp), 0)
			// Add 5 minute buffer
			return time.Now().Add(5 * time.Minute).After(expTime)
		}
	}

	return true
}

// GetTokenInfo returns token information
func (m *Manager) GetTokenInfo() (*models.TokenInfo, error) {
	token, err := m.GetValidToken()
	if err != nil {
		return nil, err
	}

	// Parse token to get expiration
	parsedToken, err := jwt.Parse(token, func(token *jwt.Token) (interface{}, error) {
		return []byte(""), nil
	})

	if err != nil {
		return &models.TokenInfo{
			Token:     token,
			IsExpired: true,
		}, nil
	}

	var expiresAt time.Time
	if claims, ok := parsedToken.Claims.(jwt.MapClaims); ok {
		if exp, ok := claims["exp"].(float64); ok {
			expiresAt = time.Unix(int64(exp), 0)
		}
	}

	return &models.TokenInfo{
		Token:       token,
		ExpiresAt:   expiresAt,
		IsExpired:   time.Now().After(expiresAt),
		RefreshToken: m.config.Warp.RefreshToken,
	}, nil
}