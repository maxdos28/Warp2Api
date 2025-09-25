package pool

import (
	"net/http"
	"sync"
	"time"

	"github.com/go-resty/resty/v2"
)

// ConnectionPool manages HTTP connections
type ConnectionPool struct {
	mu       sync.RWMutex
	clients  []*resty.Client
	available []*resty.Client
	inUse    map[*resty.Client]bool
	maxSize  int
	timeout  time.Duration
}

var (
	globalPool *ConnectionPool
	once       sync.Once
)

// GetGlobalPool returns the global connection pool
func GetGlobalPool() *ConnectionPool {
	once.Do(func() {
		globalPool = &ConnectionPool{
			maxSize: 10,
			timeout: 30 * time.Second,
		}
		globalPool.initialize()
	})
	return globalPool
}

// initialize initializes the connection pool
func (p *ConnectionPool) initialize() {
	p.mu.Lock()
	defer p.mu.Unlock()
	
	p.clients = make([]*resty.Client, 0, p.maxSize)
	p.available = make([]*resty.Client, 0, p.maxSize)
	p.inUse = make(map[*resty.Client]bool)
	
	// Create initial clients
	for i := 0; i < 3; i++ {
		client := p.createClient()
		p.clients = append(p.clients, client)
		p.available = append(p.available, client)
	}
}

// createClient creates a new HTTP client
func (p *ConnectionPool) createClient() *resty.Client {
	client := resty.New()
	client.SetTimeout(p.timeout)
	client.SetRetryCount(3)
	client.SetRetryWaitTime(1 * time.Second)
	client.SetRetryMaxWaitTime(5 * time.Second)
	
	// Configure connection pooling
	client.SetTransport(&http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 10,
		IdleConnTimeout:     90 * time.Second,
		DisableKeepAlives:   false,
	})
	
	return client
}

// GetClient gets a client from the pool
func (p *ConnectionPool) GetClient() *resty.Client {
	p.mu.Lock()
	defer p.mu.Unlock()
	
	// Try to get an available client
	if len(p.available) > 0 {
		client := p.available[len(p.available)-1]
		p.available = p.available[:len(p.available)-1]
		p.inUse[client] = true
		return client
	}
	
	// Create new client if under limit
	if len(p.clients) < p.maxSize {
		client := p.createClient()
		p.clients = append(p.clients, client)
		p.inUse[client] = true
		return client
	}
	
	// Return the first available client (round-robin)
	if len(p.clients) > 0 {
		client := p.clients[0]
		p.inUse[client] = true
		return client
	}
	
	// Fallback: create a new client
	return p.createClient()
}

// ReturnClient returns a client to the pool
func (p *ConnectionPool) ReturnClient(client *resty.Client) {
	p.mu.Lock()
	defer p.mu.Unlock()
	
	if p.inUse[client] {
		delete(p.inUse, client)
		p.available = append(p.available, client)
	}
}

// GetStats returns pool statistics
func (p *ConnectionPool) GetStats() map[string]interface{} {
	p.mu.RLock()
	defer p.mu.RUnlock()
	
	return map[string]interface{}{
		"total_clients":    len(p.clients),
		"available_clients": len(p.available),
		"in_use_clients":   len(p.inUse),
		"max_size":         p.maxSize,
		"timeout":          p.timeout.String(),
	}
}

// Warmup warms up the connection pool
func (p *ConnectionPool) Warmup() {
	p.mu.Lock()
	defer p.mu.Unlock()
	
	// Ensure we have at least 3 clients
	for len(p.clients) < 3 {
		client := p.createClient()
		p.clients = append(p.clients, client)
		p.available = append(p.available, client)
	}
}