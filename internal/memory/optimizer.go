package memory

import (
	"runtime"
	"sync"
	"time"
)

// Optimizer handles memory optimization
type Optimizer struct {
	mu           sync.RWMutex
	lastGC       time.Time
	gcCount      int64
	forceGC      bool
}

var (
	globalOptimizer *Optimizer
	once            sync.Once
)

// GetGlobalOptimizer returns the global memory optimizer
func GetGlobalOptimizer() *Optimizer {
	once.Do(func() {
		globalOptimizer = &Optimizer{
			lastGC: time.Now(),
		}
	})
	return globalOptimizer
}

// GetMemoryStats returns current memory statistics
func (o *Optimizer) GetMemoryStats() map[string]interface{} {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	
	o.mu.RLock()
	defer o.mu.RUnlock()
	
	return map[string]interface{}{
		"alloc_mb":        float64(m.Alloc) / 1024 / 1024,
		"total_alloc_mb":  float64(m.TotalAlloc) / 1024 / 1024,
		"sys_mb":          float64(m.Sys) / 1024 / 1024,
		"num_gc":          m.NumGC,
		"gc_count":        o.gcCount,
		"last_gc":         o.lastGC,
		"gc_pause_ns":     m.PauseTotalNs,
		"heap_objects":    m.HeapObjects,
		"stack_inuse_mb":  float64(m.StackInuse) / 1024 / 1024,
	}
}

// Optimize performs memory optimization
func (o *Optimizer) Optimize() {
	o.mu.Lock()
	defer o.mu.Unlock()
	
	// Force garbage collection
	runtime.GC()
	o.gcCount++
	o.lastGC = time.Now()
}

// StartOptimizationTask starts the memory optimization task
func StartOptimizationTask(interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		
		for range ticker.C {
			optimizer := GetGlobalOptimizer()
			
			// Check if we need to optimize
			stats := optimizer.GetMemoryStats()
			allocMB := stats["alloc_mb"].(float64)
			
			// If memory usage is high, force GC
			if allocMB > 100 { // 100MB threshold
				optimizer.Optimize()
			}
		}
	}()
}