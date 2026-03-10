package main

import (
	_ "klar-api/docs" // This is important for swag
	"klar-api/internal/delivery/http"
	"klar-api/internal/repository/clickup_api"
	"klar-api/internal/repository/loyverse_api"
	"klar-api/internal/usecase"
	"klar-api/pkg/logger"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
)

// @title           Klar API Integrator
// @version         1.0
// @description     API Integrator for Loyverse and ClickUp data and task management.
// @termsOfService  http://swagger.io/terms/

// @contact.name   API Support
// @contact.url    http://www.swagger.io/support
// @contact.email  support@swagger.io

// @license.name  Apache 2.0
// @license.url   http://www.apache.org/licenses/LICENSE-2.0.html

// @schemes     http https
// @BasePath    /klar-api
func main() {
	_ = godotenv.Load()
	l := logger.NewLogger()

	// 1. Load Config (Base URLs & API Keys)
	loyURL := os.Getenv("LOYVERSE_BASE_URL")
	if loyURL == "" {
		loyURL = "https://api.loyverse.com/v1.0"
	}
	cupURL := os.Getenv("CLICKUP_BASE_URL")
	if cupURL == "" {
		cupURL = "https://api.clickup.com/api/v2"
	}

	loyKey := os.Getenv("LOYVERSE_API_KEY")
	cupKey := os.Getenv("CLICKUP_API_KEY")

	// 2. Initialize Repositories with BaseURLs and API Keys
	loyRepo := loyverse_api.NewLoyverseClient(l, loyURL, loyKey)
	cupRepo := clickup_api.NewClickUpClient(l, cupURL, cupKey)

	// 3. Initialize UseCases
	loyUseCase := usecase.NewLoyverseUseCase(loyRepo)
	cupUseCase := usecase.NewClickUpUseCase(cupRepo)

	// 4. Initialize Handler (HTTP Layer)
	h := http.NewHandler(loyUseCase, cupUseCase)

	// 5. Setup Routes (Gin)
	r := gin.Default()

	// CORS Middleware
	r.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With, ngrok-skip-browser-warning")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT, DELETE")
		c.Writer.Header().Set("ngrok-skip-browser-warning", "true")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	})

	// Base Group
	base := r.Group("/klar-api")

	// Swagger documentation route
	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	// API V1 Group
	api := base.Group("/api/v1")
	{
		// Loyverse Routes
		loy := api.Group("/loyverse")
		{
			loy.GET("/summary", h.GetDailySummary)
			loy.GET("/top-products", h.GetTopProducts)
			loy.GET("/employee-performance", h.GetEmployeePerformance)
			loy.GET("/store/:store_id", h.GetStoreInfo)
			loy.GET("/metrics", h.GetDateRangeMetrics)
			loy.GET("/items", h.ListLoyverseItems)
			loy.GET("/items/:item_id", h.GetLoyverseItem)
			loy.GET("/receipts", h.ListLoyverseReceipts)
			loy.GET("/receipts/:receipt_number", h.GetLoyverseReceipt)
			loy.GET("/employees", h.ListLoyverseEmployees)
			loy.GET("/employees/:employee_id", h.GetLoyverseEmployee)
		}

		// ClickUp Routes
		cup := api.Group("/clickup")
		{
			cup.POST("/list/:list_id/task", h.CreateClickUpTask)
			cup.GET("/tasks/:task_id", h.GetClickUpTaskDetails)
			cup.PUT("/tasks/:task_id", h.UpdateClickUpTask)
			cup.POST("/tasks/:task_id/comment", h.AddClickUpComment)
			cup.POST("/tasks/:task_id/assign", h.AssignClickUpTask)
		}
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	l.Info("Starting server on port %s", port)
	l.Info("Swagger UI available at http://localhost:%s/swagger/index.html", port)
	r.Run(":" + port)
}
