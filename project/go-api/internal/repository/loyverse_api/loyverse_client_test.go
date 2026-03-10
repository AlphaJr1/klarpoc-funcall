package loyverse_api

import (
	"klar-api/pkg/logger"
	"testing"
)

func TestLoyverseClient(t *testing.T) {
	l := logger.NewLogger()
	client := NewLoyverseClient(l, "http://mock-loyverse", "dummy-key")

	t.Run("GetDailySummary", func(t *testing.T) {
		summary, err := client.GetDailySummary("store-1", "2023-10-27")
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
		if summary.Revenue == 0 {
			t.Error("Expected non-zero revenue")
		}
	})

	t.Run("GetTopProducts", func(t *testing.T) {
		products, err := client.GetTopProducts("store-1", "2023-10-27", 2)
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
		if len(products) != 2 {
			t.Errorf("Expected 2 products, got %d", len(products))
		}
	})
}
