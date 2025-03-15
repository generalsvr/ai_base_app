package repository

import (
	"analytics-service/models"
	"fmt"
	"time"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// Repository provides access to the database
type Repository struct {
	db *gorm.DB
}

// NewRepository creates a new repository with the given database connection
func NewRepository(db *gorm.DB) *Repository {
	return &Repository{db: db}
}

// InitDB initializes the database connection
func InitDB(host, port, user, password, dbname string) (*gorm.DB, error) {
	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname)

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		return nil, err
	}

	// Auto-migrate the schema
	err = db.AutoMigrate(
		&models.UserStatistic{},
		&models.AIStatistic{},
		&models.UserActivityLog{},
		&models.AICallLog{},
		&models.DailyStatsAggregate{},
	)
	if err != nil {
		return nil, err
	}

	return db, nil
}

// LogUserActivity logs a user activity
func (r *Repository) LogUserActivity(log models.UserActivityLog) error {
	return r.db.Create(&log).Error
}

// LogAICall logs an AI API call
func (r *Repository) LogAICall(log models.AICallLog) error {
	err := r.db.Create(&log).Error
	if err == nil {
		// After successfully logging the call, update aggregate stats
		go r.AggregateAICallsToStats(log.Timestamp)
	}
	return err
}

// AggregateAICallsToStats aggregates AI call logs into daily statistics
func (r *Repository) AggregateAICallsToStats(timestamp time.Time) error {
	// Get the date part only (without time)
	date := time.Date(timestamp.Year(), timestamp.Month(), timestamp.Day(), 0, 0, 0, 0, timestamp.Location())

	// Get all logs for the day
	var logs []models.AICallLog
	err := r.db.Where("DATE(timestamp) = DATE(?)", timestamp).Find(&logs).Error
	if err != nil {
		return err
	}

	// Calculate aggregate statistics
	totalCalls := len(logs)
	var completionCalls int
	var embeddingCalls int
	var totalTokens int
	var totalResponseTime float64
	var errorCount int

	for _, log := range logs {
		// Count by call type
		if log.CallType == "completion" {
			completionCalls++
		} else if log.CallType == "embedding" {
			embeddingCalls++
		}

		// Total tokens
		totalTokens += log.Tokens

		// Response time
		totalResponseTime += log.ResponseTime

		// Count errors
		if !log.Success {
			errorCount++
		}
	}

	// Calculate average response time
	averageResponseTime := 0.0
	if totalCalls > 0 {
		averageResponseTime = totalResponseTime / float64(totalCalls)
	}

	// Create or update statistics
	stats := models.AIStatistic{
		Date:                date,
		TotalAPICalls:       totalCalls,
		CompletionCalls:     completionCalls,
		EmbeddingCalls:      embeddingCalls,
		ErrorCount:          errorCount,
		AverageResponseTime: averageResponseTime,
		TokensUsed:          totalTokens,
	}

	// Save to database
	var existingStat models.AIStatistic
	result := r.db.Where("date = ?", date.Format("2006-01-02")).First(&existingStat)

	if result.Error == nil {
		// Update existing record
		return r.db.Model(&existingStat).Updates(stats).Error
	} else if result.Error == gorm.ErrRecordNotFound {
		// Create new record
		return r.db.Create(&stats).Error
	}

	return result.Error
}

// GetUserStats retrieves user statistics for a given period
func (r *Repository) GetUserStats(start, end time.Time) ([]models.UserStatistic, error) {
	var stats []models.UserStatistic
	err := r.db.Where("date BETWEEN ? AND ?", start, end).Find(&stats).Error
	return stats, err
}

// GetAIStats retrieves AI statistics for a given period
func (r *Repository) GetAIStats(start, end time.Time) ([]models.AIStatistic, error) {
	var stats []models.AIStatistic
	err := r.db.Where("date BETWEEN ? AND ?", start, end).Find(&stats).Error
	return stats, err
}

// GetAIStatsFromLogs generates AI statistics directly from call logs
func (r *Repository) GetAIStatsFromLogs(start, end time.Time) (map[string]interface{}, error) {
	// Create response structure to match the expected format
	result := map[string]interface{}{
		"totalAPICalls":        0,
		"completionCalls":      0,
		"averageResponseTime":  0.0,
		"tokensUsed":           0,
		"callTypeDistribution": map[string]int{},
	}

	// Get total API calls
	var totalCalls int64
	if err := r.db.Model(&models.AICallLog{}).
		Where("timestamp BETWEEN ? AND ?", start, end).
		Count(&totalCalls).Error; err != nil {
		return result, err
	}
	result["totalAPICalls"] = totalCalls

	// No need to continue if there are no calls
	if totalCalls == 0 {
		return result, nil
	}

	// Get completion calls
	var completionCalls int64
	if err := r.db.Model(&models.AICallLog{}).
		Where("timestamp BETWEEN ? AND ?", start, end).
		Where("call_type = ?", "completion").
		Count(&completionCalls).Error; err != nil {
		return result, err
	}
	result["completionCalls"] = completionCalls

	// Get average response time
	var avgResponseTime float64
	if err := r.db.Model(&models.AICallLog{}).
		Where("timestamp BETWEEN ? AND ?", start, end).
		Select("COALESCE(AVG(response_time), 0) as avg_time").
		Row().Scan(&avgResponseTime); err != nil {
		return result, err
	}
	result["averageResponseTime"] = avgResponseTime

	// Get total tokens used
	var tokensUsed int64
	if err := r.db.Model(&models.AICallLog{}).
		Where("timestamp BETWEEN ? AND ?", start, end).
		Select("COALESCE(SUM(tokens), 0) as total_tokens").
		Row().Scan(&tokensUsed); err != nil {
		return result, err
	}
	result["tokensUsed"] = tokensUsed

	// Get call type distribution
	type CallTypeCount struct {
		CallType string
		Count    int
	}
	var callTypeCounts []CallTypeCount
	if err := r.db.Model(&models.AICallLog{}).
		Where("timestamp BETWEEN ? AND ?", start, end).
		Select("CASE WHEN call_type = '' OR call_type IS NULL THEN 'unknown' ELSE call_type END as call_type, COUNT(*) as count").
		Group("CASE WHEN call_type = '' OR call_type IS NULL THEN 'unknown' ELSE call_type END").
		Scan(&callTypeCounts).Error; err != nil {
		return result, err
	}

	callTypeDistribution := map[string]int{}
	for _, ctc := range callTypeCounts {
		callTypeDistribution[ctc.CallType] = ctc.Count
	}
	result["callTypeDistribution"] = callTypeDistribution

	return result, nil
}

// GetDailyStats retrieves aggregated daily statistics for a given period
func (r *Repository) GetDailyStats(start, end time.Time) ([]models.DailyStatsAggregate, error) {
	var stats []models.DailyStatsAggregate
	err := r.db.Where("date BETWEEN ? AND ?", start, end).Find(&stats).Error
	return stats, err
}

// UpdateDailyStats updates or creates daily statistics
func (r *Repository) UpdateDailyStats(date time.Time, stats models.DailyStatsAggregate) error {
	var existingStat models.DailyStatsAggregate
	result := r.db.Where("date = ?", date.Format("2006-01-02")).First(&existingStat)

	if result.Error == nil {
		// Record exists, update it
		return r.db.Model(&existingStat).Updates(stats).Error
	} else if result.Error == gorm.ErrRecordNotFound {
		// Record doesn't exist, create it
		stats.Date = date
		return r.db.Create(&stats).Error
	}

	return result.Error
}

// GetTotalUsers gets the total number of unique users
func (r *Repository) GetTotalUsers() (int, error) {
	var count int64
	err := r.db.Model(&models.UserActivityLog{}).Distinct("user_id").Count(&count).Error
	return int(count), err
}

// GetActiveUsersByDay gets the number of active users per day
func (r *Repository) GetActiveUsersByDay(days int) (map[string]int, error) {
	result := make(map[string]int)

	// Calculate the start date (n days ago)
	startDate := time.Now().AddDate(0, 0, -days)

	// Query for active users by day
	type DailyActive struct {
		Day   string
		Count int
	}

	var dailyActives []DailyActive
	err := r.db.Model(&models.UserActivityLog{}).
		Select("DATE(timestamp) as day, COUNT(DISTINCT user_id) as count").
		Where("timestamp >= ?", startDate).
		Group("DATE(timestamp)").
		Scan(&dailyActives).Error

	if err != nil {
		return nil, err
	}

	// Convert to map
	for _, da := range dailyActives {
		result[da.Day] = da.Count
	}

	return result, nil
}
