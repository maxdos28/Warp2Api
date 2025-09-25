package batching

import (
	"sync"
	"time"
)

// BatchRequest represents a batched request
type BatchRequest struct {
	ID        string
	Data      interface{}
	Timestamp time.Time
	Response  chan interface{}
}

// Processor handles request batching
type Processor struct {
	mu           sync.RWMutex
	batchSize    int
	batchTimeout time.Duration
	requests     []BatchRequest
	processing   bool
}

var (
	globalProcessor *Processor
	once            sync.Once
)

// GetGlobalProcessor returns the global batch processor
func GetGlobalProcessor() *Processor {
	once.Do(func() {
		globalProcessor = &Processor{
			batchSize:    10,
			batchTimeout: 100 * time.Millisecond,
		}
	})
	return globalProcessor
}

// AddRequest adds a request to the batch
func (p *Processor) AddRequest(id string, data interface{}) <-chan interface{} {
	p.mu.Lock()
	defer p.mu.Unlock()
	
	responseChan := make(chan interface{}, 1)
	request := BatchRequest{
		ID:        id,
		Data:      data,
		Timestamp: time.Now(),
		Response:  responseChan,
	}
	
	p.requests = append(p.requests, request)
	
	// Start processing if batch is full or timeout reached
	if len(p.requests) >= p.batchSize {
		go p.processBatch()
	} else if len(p.requests) == 1 {
		// Start timeout timer for first request
		go p.startTimeout()
	}
	
	return responseChan
}

// startTimeout starts the batch timeout timer
func (p *Processor) startTimeout() {
	time.Sleep(p.batchTimeout)
	
	p.mu.Lock()
	defer p.mu.Unlock()
	
	if len(p.requests) > 0 && !p.processing {
		go p.processBatch()
	}
}

// processBatch processes the current batch
func (p *Processor) processBatch() {
	p.mu.Lock()
	if p.processing || len(p.requests) == 0 {
		p.mu.Unlock()
		return
	}
	
	p.processing = true
	requests := make([]BatchRequest, len(p.requests))
	copy(requests, p.requests)
	p.requests = p.requests[:0]
	p.mu.Unlock()
	
	// Process batch
	responses := p.processRequests(requests)
	
	// Send responses
	for i, response := range responses {
		if i < len(requests) {
			select {
			case requests[i].Response <- response:
			default:
			}
		}
	}
	
	p.mu.Lock()
	p.processing = false
	p.mu.Unlock()
}

// processRequests processes a batch of requests
func (p *Processor) processRequests(requests []BatchRequest) []interface{} {
	responses := make([]interface{}, len(requests))
	
	// Simulate batch processing
	for i, req := range requests {
		responses[i] = map[string]interface{}{
			"id":      req.ID,
			"result":  "processed",
			"data":    req.Data,
			"batch_size": len(requests),
		}
	}
	
	return responses
}

// GetStats returns batch processing statistics
func (p *Processor) GetStats() map[string]interface{} {
	p.mu.RLock()
	defer p.mu.RUnlock()
	
	return map[string]interface{}{
		"pending_requests": len(p.requests),
		"processing":       p.processing,
		"batch_size":       p.batchSize,
		"batch_timeout":    p.batchTimeout.String(),
	}
}