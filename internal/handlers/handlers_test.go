package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"warp2api-go/internal/config"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func TestHealthCheck(t *testing.T) {
	// 设置测试环境
	gin.SetMode(gin.TestMode)
	
	// 创建配置
	cfg := &config.Config{
		Server: config.ServerConfig{
			Host: "127.0.0.1",
			Port: 28889,
		},
	}
	
	// 创建处理器
	h := New(cfg)
	
	// 创建测试请求
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest("GET", "/healthz", nil)
	
	// 执行处理器
	h.HealthCheck(c)
	
	// 验证响应
	assert.Equal(t, http.StatusOK, w.Code)
	
	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "healthy", response["status"])
	assert.Equal(t, "warp2api-go", response["service"])
}

func TestListModels(t *testing.T) {
	// 设置测试环境
	gin.SetMode(gin.TestMode)
	
	// 创建配置
	cfg := &config.Config{
		Server: config.ServerConfig{
			Host: "127.0.0.1",
			Port: 28889,
		},
	}
	
	// 创建处理器
	h := New(cfg)
	
	// 创建测试请求
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest("GET", "/v1/models", nil)
	
	// 执行处理器
	h.ListModels(c)
	
	// 验证响应
	assert.Equal(t, http.StatusOK, w.Code)
	
	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "list", response["object"])
	
	data, ok := response["data"].([]interface{})
	assert.True(t, ok)
	assert.Greater(t, len(data), 0)
}

func TestChatCompletions(t *testing.T) {
	// 设置测试环境
	gin.SetMode(gin.TestMode)
	
	// 创建配置
	cfg := &config.Config{
		Server: config.ServerConfig{
			Host: "127.0.0.1",
			Port: 28889,
		},
	}
	
	// 创建处理器
	h := New(cfg)
	
	// 准备测试数据
	reqData := map[string]interface{}{
		"model": "claude-4-sonnet",
		"messages": []map[string]interface{}{
			{"role": "user", "content": "Hello"},
		},
		"max_tokens": 100,
	}
	
	reqBody, _ := json.Marshal(reqData)
	
	// 创建测试请求
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest("POST", "/v1/chat/completions", bytes.NewBuffer(reqBody))
	c.Request.Header.Set("Content-Type", "application/json")
	
	// 执行处理器
	h.ChatCompletions(c)
	
	// 验证响应
	assert.Equal(t, http.StatusOK, w.Code)
}

func TestMessages(t *testing.T) {
	// 设置测试环境
	gin.SetMode(gin.TestMode)
	
	// 创建配置
	cfg := &config.Config{
		Server: config.ServerConfig{
			Host: "127.0.0.1",
			Port: 28889,
		},
	}
	
	// 创建处理器
	h := New(cfg)
	
	// 准备测试数据
	reqData := map[string]interface{}{
		"model": "claude-3-5-sonnet-20241022",
		"max_tokens": 100,
		"messages": []map[string]interface{}{
			{"role": "user", "content": "Hello"},
		},
	}
	
	reqBody, _ := json.Marshal(reqData)
	
	// 创建测试请求
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest("POST", "/v1/messages", bytes.NewBuffer(reqBody))
	c.Request.Header.Set("Content-Type", "application/json")
	
	// 执行处理器
	h.Messages(c)
	
	// 验证响应
	assert.Equal(t, http.StatusOK, w.Code)
}