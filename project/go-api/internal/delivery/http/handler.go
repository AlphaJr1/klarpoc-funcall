package http

import (
	"klar-api/internal/domain"
	"klar-api/internal/usecase"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

type Handler struct {
	loyUseCase usecase.LoyverseUseCase
	cupUseCase usecase.ClickUpUseCase
}

func NewHandler(loyUseCase usecase.LoyverseUseCase, cupUseCase usecase.ClickUpUseCase) *Handler {
	return &Handler{
		loyUseCase: loyUseCase,
		cupUseCase: cupUseCase,
	}
}

// LOYVERSE Handlers

// GetDailySummary godoc
// @Summary      Get daily summary
// @Description  Fetch revenue, transactions, and new customers for a specific store and date
// @Tags         Loyverse
// @Accept       json
// @Produce      json
// @Param        store_id  query     string  true  "Store ID"
// @Param        date      query     string  true  "Date (YYYY-MM-DD)"
// @Success      200       {object}  domain.DailySummary
// @Failure      400       {object}  map[string]string
// @Failure      500       {object}  map[string]string
// @Router       /api/v1/loyverse/summary [get]
func (h *Handler) GetDailySummary(c *gin.Context) {
	storeID := c.Query("store_id")
	date := c.Query("date")

	if storeID == "" || date == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "store_id and date are required"})
		return
	}

	summary, err := h.loyUseCase.GetDailySummary(storeID, date)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, summary)
}

// GetTopProducts godoc
// @Summary      Get top selling products
// @Description  Fetch top selling products for a specific store and date
// @Tags         Loyverse
// @Accept       json
// @Produce      json
// @Param        store_id  query     string  true   "Store ID"
// @Param        date      query     string  true   "Date (YYYY-MM-DD)"
// @Param        limit     query     int     false  "Limit (default 5)"
// @Success      200       {array}   domain.ProductMetric
// @Router       /api/v1/loyverse/top-products [get]
func (h *Handler) GetTopProducts(c *gin.Context) {
	storeID := c.Query("store_id")
	date := c.Query("date")
	limitStr := c.DefaultQuery("limit", "5")
	limit, _ := strconv.Atoi(limitStr)

	products, err := h.loyUseCase.GetTopProducts(storeID, date, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, products)
}

// GetEmployeePerformance godoc
// @Summary (HIDDEN)
// Router /api/v1/loyverse/employee-performance [get]
func (h *Handler) GetEmployeePerformance(c *gin.Context) {
	storeID := c.Query("store_id")
	date := c.Query("date")

	performance, err := h.loyUseCase.GetEmployeePerformance(storeID, date)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, performance)
}

// GetStoreInfo godoc
// @Summary      Get store metadata
// @Description  Fetch detailed information about a store by its ID
// @Tags         Loyverse
// @Accept       json
// @Produce      json
// @Param        store_id  path      string  true  "Store ID"
// @Success      200       {object}  domain.StoreInfo
// @Router       /api/v1/loyverse/store/{store_id} [get]
func (h *Handler) GetStoreInfo(c *gin.Context) {
	storeID := c.Param("store_id")

	info, err := h.loyUseCase.GetStoreInfo(storeID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, info)
}

// GetDateRangeMetrics godoc
// @Summary      Get aggregated metrics for a date range
// @Description  Fetch revenue and other metrics between two dates
// @Tags         Loyverse
// @Accept       json
// @Produce      json
// @Param        store_id    query     string  true  "Store ID"
// @Param        start_date  query     string  true  "Start Date (YYYY-MM-DD)"
// @Param        end_date    query     string  true  "End Date (YYYY-MM-DD)"
// @Success      200         {object}  domain.DateRangeMetrics
// @Router       /api/v1/loyverse/metrics [get]
func (h *Handler) GetDateRangeMetrics(c *gin.Context) {
	storeID := c.Query("store_id")
	start := c.Query("start_date")
	end := c.Query("end_date")

	metrics, err := h.loyUseCase.GetDateRangeMetrics(storeID, start, end)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, metrics)
}

// GetLoyverseItem godoc
// @Summary      Get item info
// @Description  Fetch details of a single item by its ID
// @Tags         Loyverse
// @Accept       json
// @Produce      json
// @Param        item_id  path      string  true  "Item ID"
// @Success      200      {object}  domain.LoyverseItem
// @Router       /api/v1/loyverse/items/{item_id} [get]
func (h *Handler) GetLoyverseItem(c *gin.Context) {
	itemID := c.Param("item_id")
	item, err := h.loyUseCase.GetItem(itemID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, item)
}

// ListLoyverseItems godoc
// @Summary      List all items
// @Description  Fetch a list of all items from Loyverse
// @Tags         Loyverse
// @Accept       json
// @Produce      json
// @Success      200      {array}   domain.LoyverseItem
// @Router       /api/v1/loyverse/items [get]
func (h *Handler) ListLoyverseItems(c *gin.Context) {
	items, err := h.loyUseCase.ListItems()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

// GetLoyverseReceipt godoc
// @Summary      Get receipt info
// @Description  Fetch details of a single receipt by its number
// @Tags         Loyverse
// @Accept       json
// @Produce      json
// @Param        receipt_number  path      string  true  "Receipt Number"
// @Success      200             {object}  domain.LoyverseReceipt
// @Router       /api/v1/loyverse/receipts/{receipt_number} [get]
func (h *Handler) GetLoyverseReceipt(c *gin.Context) {
	receiptNumber := c.Param("receipt_number")
	receipt, err := h.loyUseCase.GetReceipt(receiptNumber)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, receipt)
}

// ListLoyverseReceipts godoc
// @Summary      List all receipts
// @Description  Fetch a list of all receipts from Loyverse
// @Tags         Loyverse
// @Accept       json
// @Produce      json
// @Success      200      {array}   domain.LoyverseReceipt
// @Router       /api/v1/loyverse/receipts [get]
func (h *Handler) ListLoyverseReceipts(c *gin.Context) {
	receipts, err := h.loyUseCase.ListReceipts()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, receipts)
}

// GetLoyverseEmployee godoc
// @Summary      Get employee info
// @Description  Fetch details of a single employee by its ID
// @Tags         Loyverse
// @Accept       json
// @Produce      json
// @Param        employee_id  path      string  true  "Employee ID"
// @Success      200          {object}  domain.LoyverseEmployee
// @Router       /api/v1/loyverse/employees/{employee_id} [get]
func (h *Handler) GetLoyverseEmployee(c *gin.Context) {
	employeeID := c.Param("employee_id")
	employee, err := h.loyUseCase.GetEmployee(employeeID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, employee)
}

// ListLoyverseEmployees godoc
// @Summary      List all employees
// @Description  Fetch a list of all employees from Loyverse
// @Tags         Loyverse
// @Accept       json
// @Produce      json
// @Success      200      {object}  map[string]interface{}
// @Router       /api/v1/loyverse/employees [get]
func (h *Handler) ListLoyverseEmployees(c *gin.Context) {
	employees, cursor, err := h.loyUseCase.ListEmployees()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"employees": employees,
		"cursor":    cursor,
	})
}

// CLICKUP Handlers

// CreateClickUpTask godoc
// @Summary      Create a new ClickUp task
// @Description  Insert a new task into a specific ClickUp list
// @Tags         ClickUp
// @Accept       json
// @Produce      json
// @Param        list_id  path      string                          true  "List ID"
// @Param        task     body      domain.CreateClickUpTaskRequest true  "Task content"
// @Success      201      {object}  domain.ClickUpTask
// @Router       /api/v1/clickup/list/{list_id}/task [post]
func (h *Handler) CreateClickUpTask(c *gin.Context) {
	listID := c.Param("list_id")
	var task domain.CreateClickUpTaskRequest
	if err := c.ShouldBindJSON(&task); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	result, err := h.cupUseCase.CreateTask(listID, task)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, result)
}

// UpdateClickUpTask godoc
// @Summary      Update an existing ClickUp task
// @Description  Modify task details in ClickUp (name, description, status, due_date)
// @Tags         ClickUp
// @Accept       json
// @Produce      json
// @Param        task_id  path      string                          true  "Task ID"
// @Param        task     body      domain.UpdateClickUpTaskRequest true  "Updated content"
// @Success      200      {object}  map[string]string
// @Router       /api/v1/clickup/tasks/{task_id} [put]
func (h *Handler) UpdateClickUpTask(c *gin.Context) {
	taskID := c.Param("task_id")
	var task domain.UpdateClickUpTaskRequest
	if err := c.ShouldBindJSON(&task); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	err := h.cupUseCase.UpdateTask(taskID, task)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":  "external API returned an error",
			"detail": err.Error(),
		})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "updated"})
}

// GetClickUpTaskDetails godoc
// @Summary      Get ClickUp task details
// @Description  Fetch all info for a single ClickUp task
// @Tags         ClickUp
// @Accept       json
// @Produce      json
// @Param        task_id  path      string  true  "Task ID"
// @Success      200      {object}  domain.ClickUpTask
// @Router       /api/v1/clickup/tasks/{task_id} [get]
func (h *Handler) GetClickUpTaskDetails(c *gin.Context) {
	taskID := c.Param("task_id")

	task, err := h.cupUseCase.GetTaskDetails(taskID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, task)
}

// AddClickUpComment godoc
// @Summary (HIDDEN)
// Router /api/v1/clickup/tasks/{task_id}/comment [post]
func (h *Handler) AddClickUpComment(c *gin.Context) {
	taskID := c.Param("task_id")
	var req domain.ClickUpCommentRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	err := h.cupUseCase.AddComment(taskID, req.Comment)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "comment added"})
}

// AssignClickUpTask godoc
// @Summary (HIDDEN)
// Router /api/v1/clickup/tasks/{task_id}/assign [post]
func (h *Handler) AssignClickUpTask(c *gin.Context) {
	taskID := c.Param("task_id")
	var req domain.ClickUpAssignRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	err := h.cupUseCase.AssignTask(taskID, req.UserID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "task assigned"})
}
