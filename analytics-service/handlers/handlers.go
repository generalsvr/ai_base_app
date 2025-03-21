package handlers

import (
	"analytics-service/models"
	"analytics-service/repository"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// Handler struct holds repository for database operations
type Handler struct {
	repo *repository.Repository
}

// NewHandler creates a new handler with repository
func NewHandler(repo *repository.Repository) *Handler {
	return &Handler{repo: repo}
}

// RegisterRoutes registers all API routes
func (h *Handler) RegisterRoutes(router *gin.Engine) {
	// Add root level health check for Docker healthcheck
	router.GET("/health", h.HealthCheck)

	v1 := router.Group("/api/v1")
	{
		// User statistics endpoints
		v1.POST("/user-activity", h.LogUserActivity)
		v1.GET("/user-stats", h.GetUserStats)
		v1.GET("/user-stats/active", h.GetActiveUsers)
		v1.GET("/user-stats/total", h.GetTotalUsers)

		// AI statistics endpoints
		v1.POST("/ai-call", h.LogAICall)
		v1.GET("/ai-stats", h.GetAIStats)
		v1.GET("/ai-stats/models", h.GetModelUsage)

		// Aggregated statistics
		v1.GET("/stats/daily", h.GetDailyStats)
		v1.GET("/stats/summary", h.GetStatsSummary)

		// Dashboard data
		v1.GET("/dashboard", h.GetDashboardData)

		// Health check
		v1.GET("/health", h.HealthCheck)

		// Metrics (Prometheus endpoint)
		v1.GET("/metrics", h.Metrics)
	}
}

// LogUserActivity logs a user activity
func (h *Handler) LogUserActivity(c *gin.Context) {
	var log models.UserActivityLog
	if err := c.ShouldBindJSON(&log); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	log.Timestamp = time.Now()
	err := h.repo.LogUserActivity(log)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "User activity logged successfully"})
}

// LogAICall logs an AI API call
func (h *Handler) LogAICall(c *gin.Context) {
	var log models.AICallLog
	if err := c.ShouldBindJSON(&log); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	log.Timestamp = time.Now()
	err := h.repo.LogAICall(log)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "AI call logged successfully"})
}

// GetUserStats gets user statistics for a time period
func (h *Handler) GetUserStats(c *gin.Context) {
	// Default to last 7 days if not specified
	startStr := c.DefaultQuery("start", time.Now().AddDate(0, 0, -7).Format("2006-01-02"))
	endStr := c.DefaultQuery("end", time.Now().Format("2006-01-02"))

	start, err := time.Parse("2006-01-02", startStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid start date format"})
		return
	}

	end, err := time.Parse("2006-01-02", endStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid end date format"})
		return
	}

	stats, err := h.repo.GetUserStats(start, end)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, stats)
}

// GetAIStats gets AI statistics for a time period
func (h *Handler) GetAIStats(c *gin.Context) {
	// Default to last 7 days if not specified
	startStr := c.DefaultQuery("start", time.Now().AddDate(0, 0, -7).Format("2006-01-02"))
	endStr := c.DefaultQuery("end", time.Now().Format("2006-01-02"))

	start, err := time.Parse("2006-01-02", startStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid start date format"})
		return
	}

	end, err := time.Parse("2006-01-02", endStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid end date format"})
		return
	}

	// Add a day to end date to include the end day itself in the query
	// This is because timestamps will have time components, so "2023-01-01" needs to include all times on that day
	queryEnd := end.AddDate(0, 0, 1)

	// Try to get statistics from the raw logs directly
	data, err := h.repo.GetAIStatsFromLogs(start, queryEnd)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Check if there are no API calls in the logs
	// Handle both int and int64 types safely
	totalCalls := 0
	switch v := data["totalAPICalls"].(type) {
	case int:
		totalCalls = v
	case int64:
		totalCalls = int(v)
	case float64:
		totalCalls = int(v)
	}

	if totalCalls == 0 {
		// Run aggregation on each day in the range to ensure the stats are up to date
		currentDate := start
		for currentDate.Before(queryEnd) {
			// Trigger aggregation for this day
			h.repo.AggregateAICallsToStats(currentDate)
			currentDate = currentDate.AddDate(0, 0, 1)
		}

		// Try to get statistics from the aggregated table
		stats, err := h.repo.GetAIStats(start, end)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		// Convert to the expected format
		if len(stats) > 0 {
			// Combine stats from multiple days
			totalCalls := 0
			completionCalls := 0
			totalTokens := 0
			totalResponseTime := 0.0
			nDays := 0

			for _, stat := range stats {
				totalCalls += stat.TotalAPICalls
				completionCalls += stat.CompletionCalls
				totalTokens += stat.TokensUsed
				totalResponseTime += stat.AverageResponseTime
				nDays++
			}

			// Calculate averages
			avgResponseTime := 0.0
			if nDays > 0 {
				avgResponseTime = totalResponseTime / float64(nDays)
			}

			// Create response
			data = map[string]interface{}{
				"totalAPICalls":       totalCalls,
				"completionCalls":     completionCalls,
				"averageResponseTime": avgResponseTime,
				"tokensUsed":          totalTokens,
				"callTypeDistribution": map[string]int{
					"completion": completionCalls,
					"embedding":  0, // We could add this but it needs to be calculated
				},
			}
		}
	}

	c.JSON(http.StatusOK, data)
}

// GetActiveUsers gets the count of active users per day
func (h *Handler) GetActiveUsers(c *gin.Context) {
	days := 7 // Default to 7 days

	activeUsers, err := h.repo.GetActiveUsersByDay(days)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, activeUsers)
}

// GetTotalUsers gets the total number of unique users
func (h *Handler) GetTotalUsers(c *gin.Context) {
	count, err := h.repo.GetTotalUsers()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"total_users": count})
}

// GetModelUsage gets AI model usage statistics
func (h *Handler) GetModelUsage(c *gin.Context) {
	// Placeholder - would need to be implemented in the repository
	c.JSON(http.StatusOK, gin.H{"message": "Model usage statistics"})
}

// GetDailyStats gets daily aggregated statistics
func (h *Handler) GetDailyStats(c *gin.Context) {
	// Default to last 30 days if not specified
	startStr := c.DefaultQuery("start", time.Now().AddDate(0, 0, -30).Format("2006-01-02"))
	endStr := c.DefaultQuery("end", time.Now().Format("2006-01-02"))

	start, err := time.Parse("2006-01-02", startStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid start date format"})
		return
	}

	end, err := time.Parse("2006-01-02", endStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid end date format"})
		return
	}

	stats, err := h.repo.GetDailyStats(start, end)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, stats)
}

// GetStatsSummary gets a summary of all statistics
func (h *Handler) GetStatsSummary(c *gin.Context) {
	// Placeholder - would combine various stats into a summary
	c.JSON(http.StatusOK, gin.H{"message": "Statistics summary"})
}

// GetDashboardData gets all data needed for dashboard
func (h *Handler) GetDashboardData(c *gin.Context) {
	// Placeholder - would combine various stats needed for dashboard
	c.JSON(http.StatusOK, gin.H{"message": "Dashboard data"})
}

// HealthCheck provides a simple health check endpoint
func (h *Handler) HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok", "service": "analytics-service"})
}

// Metrics provides Prometheus metrics
func (h *Handler) Metrics(c *gin.Context) {
	c.String(http.StatusOK, "# Placeholder for Prometheus metrics")
}
