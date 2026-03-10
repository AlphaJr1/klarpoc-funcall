package usecase

import (
	"klar-api/internal/domain"
)

type LoyverseUseCase interface {
	GetDailySummary(storeID, date string) (*domain.DailySummary, error)
	GetTopProducts(storeID, date string, limit int) ([]domain.ProductMetric, error)
	GetEmployeePerformance(storeID, date string) ([]domain.EmployeePerformance, error)
	GetStoreInfo(storeID string) (*domain.StoreInfo, error)
	GetDateRangeMetrics(storeID, start, end string) (*domain.DateRangeMetrics, error)
	GetItem(itemID string) (*domain.LoyverseItem, error)
	ListItems() ([]domain.LoyverseItem, error)
	GetReceipt(receiptNumber string) (*domain.LoyverseReceipt, error)
	ListReceipts() ([]domain.LoyverseReceipt, error)
	GetEmployee(employeeID string) (*domain.LoyverseEmployee, error)
	ListEmployees() ([]domain.LoyverseEmployee, string, error)
}

type loyverseUseCase struct {
	repo domain.LoyverseRepository
}

func NewLoyverseUseCase(repo domain.LoyverseRepository) LoyverseUseCase {
	return &loyverseUseCase{repo: repo}
}

func (u *loyverseUseCase) GetDailySummary(storeID, date string) (*domain.DailySummary, error) {
	return u.repo.GetDailySummary(storeID, date)
}

func (u *loyverseUseCase) GetTopProducts(storeID, date string, limit int) ([]domain.ProductMetric, error) {
	return u.repo.GetTopProducts(storeID, date, limit)
}

func (u *loyverseUseCase) GetEmployeePerformance(storeID, date string) ([]domain.EmployeePerformance, error) {
	return u.repo.GetEmployeePerformance(storeID, date)
}

func (u *loyverseUseCase) GetStoreInfo(storeID string) (*domain.StoreInfo, error) {
	return u.repo.GetStoreInfo(storeID)
}

func (u *loyverseUseCase) GetDateRangeMetrics(storeID, start, end string) (*domain.DateRangeMetrics, error) {
	return u.repo.GetDateRangeMetrics(storeID, start, end)
}

func (u *loyverseUseCase) GetItem(itemID string) (*domain.LoyverseItem, error) {
	return u.repo.GetItem(itemID)
}

func (u *loyverseUseCase) ListItems() ([]domain.LoyverseItem, error) {
	return u.repo.ListItems()
}

func (u *loyverseUseCase) GetReceipt(receiptNumber string) (*domain.LoyverseReceipt, error) {
	return u.repo.GetReceipt(receiptNumber)
}

func (u *loyverseUseCase) ListReceipts() ([]domain.LoyverseReceipt, error) {
	return u.repo.ListReceipts()
}

func (u *loyverseUseCase) GetEmployee(employeeID string) (*domain.LoyverseEmployee, error) {
	return u.repo.GetEmployee(employeeID)
}

func (u *loyverseUseCase) ListEmployees() ([]domain.LoyverseEmployee, string, error) {
	return u.repo.ListEmployees()
}
