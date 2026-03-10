package loyverse_api

import (
	"klar-api/internal/domain"
	"klar-api/pkg/logger"
	"sort"

	"github.com/go-resty/resty/v2"
)

type loyverseClient struct {
	logger *logger.Logger
	client *resty.Client
}

func NewLoyverseClient(logger *logger.Logger, baseURL, apiKey string) domain.LoyverseRepository {
	client := resty.New().
		SetBaseURL(baseURL).
		SetHeader("Authorization", "Bearer "+apiKey).
		SetHeader("Content-Type", "application/json")

	return &loyverseClient{
		logger: logger,
		client: client,
	}
}

func (c *loyverseClient) GetDailySummary(storeID string, date string) (*domain.DailySummary, error) {
	c.logger.Info("Fetching daily summary for store %s on %s", storeID, date)

	var result struct {
		Receipts []domain.LoyverseReceipt `json:"receipts"`
	}

	resp, err := c.client.R().
		SetQueryParams(map[string]string{
			"store_id":       storeID,
			"created_at_min": date + "T00:00:00Z",
			"created_at_max": date + "T23:59:59Z",
		}).
		SetResult(&result).
		Get("/receipts")

	if err != nil {
		c.logger.Error("Failed to fetch Loyverse receipts: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("Loyverse API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	summary := &domain.DailySummary{
		Revenue:        0,
		Transactions:   len(result.Receipts),
		TotalItemsSold: 0,
	}

	for _, r := range result.Receipts {
		summary.Revenue += r.TotalMoney
		for _, item := range r.LineItems {
			summary.TotalItemsSold += item.Quantity
		}
	}

	c.logger.Info("Successfully calculated daily summary for store %s: revenue=%v, items=%v", storeID, summary.Revenue, summary.TotalItemsSold)
	return summary, nil
}

func (c *loyverseClient) GetTopProducts(storeID string, date string, limit int) ([]domain.ProductMetric, error) {
	c.logger.Info("Calculating top %d products for store %s on %s", limit, storeID, date)

	var result struct {
		Receipts []domain.LoyverseReceipt `json:"receipts"`
	}
	resp, err := c.client.R().
		SetQueryParams(map[string]string{
			"store_id":       storeID,
			"created_at_min": date + "T00:00:00Z",
			"created_at_max": date + "T23:59:59Z",
		}).
		SetResult(&result).
		Get("/receipts")

	if err != nil {
		c.logger.Error("Failed to fetch Loyverse receipts for top products: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("Loyverse API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	// Aggregate quantities by product name
	productCounts := make(map[string]float64)
	for _, r := range result.Receipts {
		for _, item := range r.LineItems {
			productCounts[item.ItemName] += item.Quantity
		}
	}

	// Convert map to slice for sorting
	var metrics []domain.ProductMetric
	for name, qty := range productCounts {
		metrics = append(metrics, domain.ProductMetric{
			Name:     name,
			Quantity: int(qty), // domain.ProductMetric uses int for Quantity
		})
	}

	// Sort by Quantity descending
	sort.Slice(metrics, func(i, j int) bool {
		return metrics[i].Quantity > metrics[j].Quantity
	})

	// Apply limit
	if len(metrics) > limit {
		metrics = metrics[:limit]
	}

	return metrics, nil
}

func (c *loyverseClient) GetEmployeePerformance(storeID string, date string) ([]domain.EmployeePerformance, error) {
	c.logger.Info("Fetching employee performance for store %s on %s", storeID, date)

	var result []domain.EmployeePerformance
	resp, err := c.client.R().
		SetQueryParams(map[string]string{
			"store_id": storeID,
			"date":     date,
		}).
		SetResult(&result).
		Get("/analytics/employees") // Illustrative endpoint

	if err != nil {
		c.logger.Error("Failed to fetch Loyverse employee performance: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("Loyverse API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	return result, nil
}

func (c *loyverseClient) GetStoreInfo(storeID string) (*domain.StoreInfo, error) {
	c.logger.Info("Fetching store info for ID %s", storeID)

	var result domain.StoreInfo
	resp, err := c.client.R().
		SetResult(&result).
		Get("/stores/" + storeID)

	if err != nil {
		c.logger.Error("Failed to fetch Loyverse store info: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("Loyverse API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	c.logger.Info("Successfully fetched Loyverse store info for ID %s", storeID)
	return &result, nil
}

func (c *loyverseClient) GetDateRangeMetrics(storeID string, start, end string) (*domain.DateRangeMetrics, error) {
	c.logger.Info("Calculating metrics for store %s from %s to %s", storeID, start, end)

	var result struct {
		Receipts []domain.LoyverseReceipt `json:"receipts"`
	}
	resp, err := c.client.R().
		SetQueryParams(map[string]string{
			"store_id":       storeID,
			"created_at_min": start + "T00:00:00Z",
			"created_at_max": end + "T23:59:59Z",
		}).
		SetResult(&result).
		Get("/receipts")

	if err != nil {
		c.logger.Error("Failed to fetch Loyverse receipts for metrics: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("Loyverse API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	metrics := &domain.DateRangeMetrics{
		StartDate:      start,
		EndDate:        end,
		Revenue:        0,
		Transactions:   len(result.Receipts),
		TotalItemsSold: 0,
	}

	for _, r := range result.Receipts {
		metrics.Revenue += r.TotalMoney
		for _, item := range r.LineItems {
			metrics.TotalItemsSold += item.Quantity
		}
	}

	c.logger.Info("Successfully calculated metrics for store %s: revenue=%v, items=%v", storeID, metrics.Revenue, metrics.TotalItemsSold)
	return metrics, nil
}

func (c *loyverseClient) GetItem(itemID string) (*domain.LoyverseItem, error) {
	c.logger.Info("Fetching Loyverse item %s", itemID)

	var result domain.LoyverseItem
	resp, err := c.client.R().
		SetResult(&result).
		Get("/items/" + itemID)

	if err != nil {
		c.logger.Error("Failed to fetch Loyverse item: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("Loyverse API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	return &result, nil
}

func (c *loyverseClient) ListItems() ([]domain.LoyverseItem, error) {
	c.logger.Info("Listing all Loyverse items")

	var result struct {
		Items []domain.LoyverseItem `json:"items"`
	}
	resp, err := c.client.R().
		SetResult(&result).
		Get("/items")

	if err != nil {
		c.logger.Error("Failed to list Loyverse items: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("Loyverse API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	return result.Items, nil
}

func (c *loyverseClient) GetReceipt(receiptNumber string) (*domain.LoyverseReceipt, error) {
	c.logger.Info("Fetching Loyverse receipt %s", receiptNumber)

	var result domain.LoyverseReceipt
	resp, err := c.client.R().
		SetResult(&result).
		Get("/receipts/" + receiptNumber)

	if err != nil {
		c.logger.Error("Failed to fetch Loyverse receipt: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("Loyverse API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	return &result, nil
}

func (c *loyverseClient) ListReceipts() ([]domain.LoyverseReceipt, error) {
	c.logger.Info("Listing all Loyverse receipts")

	var result struct {
		Receipts []domain.LoyverseReceipt `json:"receipts"`
	}
	resp, err := c.client.R().
		SetResult(&result).
		Get("/receipts")

	if err != nil {
		c.logger.Error("Failed to list Loyverse receipts: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("Loyverse API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	return result.Receipts, nil
}

func (c *loyverseClient) GetEmployee(employeeID string) (*domain.LoyverseEmployee, error) {
	c.logger.Info("Fetching Loyverse employee %s", employeeID)

	var result domain.LoyverseEmployee
	resp, err := c.client.R().
		SetResult(&result).
		Get("/employees/" + employeeID)

	if err != nil {
		c.logger.Error("Failed to fetch Loyverse employee: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("Loyverse API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	return &result, nil
}

func (c *loyverseClient) ListEmployees() ([]domain.LoyverseEmployee, string, error) {
	c.logger.Info("Listing all Loyverse employees")

	var result struct {
		Employees []domain.LoyverseEmployee `json:"employees"`
		Cursor    string                    `json:"cursor"`
	}
	resp, err := c.client.R().
		SetResult(&result).
		Get("/employees")

	if err != nil {
		c.logger.Error("Failed to list Loyverse employees: %v", err)
		return nil, "", err
	}

	if resp.IsError() {
		c.logger.Error("Loyverse API error: %s", resp.String())
		return nil, "", domain.ErrExternalAPI
	}

	return result.Employees, result.Cursor, nil
}
