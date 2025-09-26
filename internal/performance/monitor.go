package performance

import (
	"sync"
	"time"
)

// Monitor tracks performance metrics
type Monitor struct {
	mu                sync.RWMutex
	requestCount      int64
	responseTimeSum   time.Duration
	errorCount        int64
	activeConnections int64
	startTime         time.Time
}

var (
	globalMonitor *Monitor
	once          sync.Once
)

// GetGlobalMonitor returns the global performance monitor
func GetGlobalMonitor() *Monitor {
	once.Do(func() {
		globalMonitor = &Monitor{
			startTime: time.Now(),
		}
	})
	return globalMonitor
}

// RecordRequest records a request
func (m *Monitor) RecordRequest(duration time.Duration, isError bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	m.requestCount++
	m.responseTimeSum += duration
	if isError {
		m.errorCount++
	}
}

// RecordConnection records a connection change
func (m *Monitor) RecordConnection(delta int64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	m.activeConnections += delta
	if m.activeConnections < 0 {
		m.activeConnections = 0
	}
}

// GetStats returns current performance statistics
func (m *Monitor) GetStats() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	uptime := time.Since(m.startTime)
	avgResponseTime := time.Duration(0)
	if m.requestCount > 0 {
		avgResponseTime = m.responseTimeSum / time.Duration(m.requestCount)
	}
	
	errorRate := float64(0)
	if m.requestCount > 0 {
		errorRate = float64(m.errorCount) / float64(m.requestCount) * 100
	}
	
	return map[string]interface{}{
		"uptime":            uptime.String(),
		"request_count":     m.requestCount,
		"error_count":       m.errorCount,
		"error_rate":        errorRate,
		"avg_response_time": avgResponseTime.String(),
		"active_connections": m.activeConnections,
		"requests_per_second": float64(m.requestCount) / uptime.Seconds(),
	}
}

// StartMonitoring starts the performance monitoring task
func StartMonitoring(interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		
		for range ticker.C {
			stats := GetGlobalMonitor().GetStats()
			// Log performance stats (in production, you might want to send to metrics system)
			_ = stats // Avoid unused variable warning
		}
	}()
}