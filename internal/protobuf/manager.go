package protobuf

import (
	"encoding/json"
	"fmt"
	"time"

	"warp2api-go/internal/config"
)

// Manager handles protobuf encoding/decoding
type Manager struct {
	config       *config.Config
	packetHistory []map[string]interface{}
}

// New creates a new protobuf manager
func New(cfg *config.Config) *Manager {
	return &Manager{
		config:       cfg,
		packetHistory: make([]map[string]interface{}, 0),
	}
}

// Encode encodes JSON to protobuf
func (m *Manager) Encode(data map[string]interface{}) (map[string]interface{}, error) {
	// For now, we'll simulate protobuf encoding
	// In a real implementation, this would use actual protobuf libraries
	
	encoded := map[string]interface{}{
		"protobuf_data": data,
		"encoded_at":    time.Now().Unix(),
		"size":          len(fmt.Sprintf("%v", data)),
	}

	// Add to history
	m.addToHistory("encode", data, encoded)

	return encoded, nil
}

// Decode decodes protobuf to JSON
func (m *Manager) Decode(data map[string]interface{}) (map[string]interface{}, error) {
	// For now, we'll simulate protobuf decoding
	// In a real implementation, this would use actual protobuf libraries
	
	decoded := map[string]interface{}{
		"json_data":   data,
		"decoded_at":  time.Now().Unix(),
		"original":    true,
	}

	// Add to history
	m.addToHistory("decode", data, decoded)

	return decoded, nil
}

// NewStreamDecoder creates a new stream decoder
func (m *Manager) NewStreamDecoder() *StreamDecoder {
	return &StreamDecoder{
		manager: m,
	}
}

// GetSchemas returns protobuf schema information
func (m *Manager) GetSchemas() map[string]interface{} {
	return map[string]interface{}{
		"schemas": []map[string]interface{}{
			{
				"name":        "ChatMessage",
				"description": "Chat message schema",
				"fields": []map[string]interface{}{
					{"name": "role", "type": "string"},
					{"name": "content", "type": "string"},
				},
			},
			{
				"name":        "ChatRequest",
				"description": "Chat request schema",
				"fields": []map[string]interface{}{
					{"name": "model", "type": "string"},
					{"name": "messages", "type": "repeated ChatMessage"},
				},
			},
		},
		"version": "1.0.0",
	}
}

// GetPacketHistory returns packet history
func (m *Manager) GetPacketHistory() []map[string]interface{} {
	return m.packetHistory
}

// addToHistory adds an operation to the packet history
func (m *Manager) addToHistory(operation string, input, output map[string]interface{}) {
	entry := map[string]interface{}{
		"operation": operation,
		"input":     input,
		"output":    output,
		"timestamp": time.Now().Unix(),
	}

	m.packetHistory = append(m.packetHistory, entry)

	// Keep only last 100 entries
	if len(m.packetHistory) > 100 {
		m.packetHistory = m.packetHistory[len(m.packetHistory)-100:]
	}
}

// StreamDecoder handles streaming protobuf decoding
type StreamDecoder struct {
	manager *Manager
}

// DecodeChunk decodes a chunk of streaming data
func (d *StreamDecoder) DecodeChunk(data map[string]interface{}) (string, error) {
	// Simulate streaming decode
	chunk := map[string]interface{}{
		"chunk":     data,
		"timestamp": time.Now().Unix(),
	}

	jsonData, err := json.Marshal(chunk)
	if err != nil {
		return "", fmt.Errorf("failed to marshal chunk: %w", err)
	}

	return string(jsonData), nil
}