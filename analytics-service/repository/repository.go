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
	return r.db.Create(&log).Error
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
