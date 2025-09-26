package cache

import (
	"sync"
	"time"
)

// CacheItem represents a cached item
type CacheItem struct {
	Value     interface{}
	ExpiresAt time.Time
}

// Manager handles caching operations
type Manager struct {
	mu    sync.RWMutex
	items map[string]*CacheItem
}

var (
	globalCache *Manager
	once        sync.Once
)

// GetGlobalCache returns the global cache manager
func GetGlobalCache() *Manager {
	once.Do(func() {
		globalCache = &Manager{
			items: make(map[string]*CacheItem),
		}
	})
	return globalCache
}

// Set stores a value in cache
func (m *Manager) Set(key string, value interface{}, ttl time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	m.items[key] = &CacheItem{
		Value:     value,
		ExpiresAt: time.Now().Add(ttl),
	}
}

// Get retrieves a value from cache
func (m *Manager) Get(key string) (interface{}, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	item, exists := m.items[key]
	if !exists {
		return nil, false
	}
	
	if time.Now().After(item.ExpiresAt) {
		// Item expired, remove it
		go m.Delete(key)
		return nil, false
	}
	
	return item.Value, true
}

// Delete removes an item from cache
func (m *Manager) Delete(key string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	delete(m.items, key)
}

// Cleanup removes expired items
func (m *Manager) Cleanup() {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	now := time.Now()
	for key, item := range m.items {
		if now.After(item.ExpiresAt) {
			delete(m.items, key)
		}
	}
}

// GetStats returns cache statistics
func (m *Manager) GetStats() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	expiredCount := 0
	now := time.Now()
	for _, item := range m.items {
		if now.After(item.ExpiresAt) {
			expiredCount++
		}
	}
	
	return map[string]interface{}{
		"total_items":   len(m.items),
		"expired_items": expiredCount,
		"active_items":  len(m.items) - expiredCount,
	}
}

// StartCleanupTask starts the cache cleanup task
func StartCleanupTask(interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		
		for range ticker.C {
			GetGlobalCache().Cleanup()
		}
	}()
}