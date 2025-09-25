package streaming

import (
	"encoding/json"
	"fmt"

	"warp2api-go/internal/models"

	"github.com/gin-gonic/gin"
)

// Stream handles streaming responses
type Stream struct {
	ctx    *gin.Context
	req    interface{}
	writer gin.ResponseWriter
}

// New creates a new stream
func New(c *gin.Context, req interface{}) *Stream {
	return &Stream{
		ctx:    c,
		req:    req,
		writer: c.Writer,
	}
}

// SendEvent sends a streaming event
func (s *Stream) SendEvent(event models.StreamingEvent) error {
	// Format as SSE
	data, err := json.Marshal(event.Data)
	if err != nil {
		return fmt.Errorf("failed to marshal event data: %w", err)
	}

	// Write SSE format
	s.writer.WriteString(fmt.Sprintf("data: %s\n\n", string(data)))
	s.writer.Flush()

	return nil
}

// SendError sends an error event
func (s *Stream) SendError(err error) {
	errorEvent := models.StreamingEvent{
		Event: "error",
		Data: models.ErrorResponse{
			Error: models.ErrorDetail{
				Message: err.Error(),
				Type:    "server_error",
			},
		},
	}

	s.SendEvent(errorEvent)
}

// SendDone sends a done event
func (s *Stream) SendDone() {
	doneEvent := models.StreamingEvent{
		Event: "done",
		Data:  map[string]interface{}{},
	}

	s.SendEvent(doneEvent)
}

// Close closes the stream
func (s *Stream) Close() {
	// Send final newline to ensure proper SSE termination
	s.writer.WriteString("\n")
	s.writer.Flush()
}

// SendChatCompletionChunk sends a chat completion chunk
func (s *Stream) SendChatCompletionChunk(chunk models.ChatCompletionsResponse) error {
	event := models.StreamingEvent{
		ID:   chunk.ID,
		Data: chunk,
	}
	return s.SendEvent(event)
}

// SendMessagesChunk sends a messages chunk
func (s *Stream) SendMessagesChunk(chunk models.MessagesResponse) error {
	event := models.StreamingEvent{
		ID:   chunk.ID,
		Data: chunk,
	}
	return s.SendEvent(event)
}