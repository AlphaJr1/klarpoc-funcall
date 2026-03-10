package clickup_api

import (
	"klar-api/internal/domain"
	"klar-api/pkg/logger"
	"testing"
)

func TestClickUpClient(t *testing.T) {
	l := logger.NewLogger()
	client := NewClickUpClient(l, "http://mock-clickup", "dummy-key")

	t.Run("CreateTask", func(t *testing.T) {
		task := domain.CreateClickUpTaskRequest{Name: "Test Task"}
		result, err := client.CreateTask("list-1", task)
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
		if result.ID == "" {
			t.Error("Expected task ID to be populated")
		}
	})

	t.Run("AddComment", func(t *testing.T) {
		err := client.AddComment("task-1", "Hello")
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
	})
}
