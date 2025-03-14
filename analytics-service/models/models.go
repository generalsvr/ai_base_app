package models

import (
	"time"

	"gorm.io/gorm"
)

// UserStatistic represents statistics for user activities
type UserStatistic struct {
	ID                 uint           `json:"id" gorm:"primaryKey"`
	CreatedAt          time.Time      `json:"created_at"`
	UpdatedAt          time.Time      `json:"updated_at"`
	DeletedAt          gorm.DeletedAt `json:"-" gorm:"index"`
	Date               time.Time      `json:"date" gorm:"index"`
	Logins             int            `json:"logins"`
	Registrations      int            `json:"registrations"`
	ActiveUsers        int            `json:"active_users"`
	UniqueUserIDs      []string       `json:"unique_user_ids" gorm:"-"` // Not stored in DB
	AverageSessionTime float64        `json:"average_session_time"`
}

// AIStatistic represents statistics for AI operations
type AIStatistic struct {
	ID                  uint           `json:"id" gorm:"primaryKey"`
	CreatedAt           time.Time      `json:"created_at"`
	UpdatedAt           time.Time      `json:"updated_at"`
	DeletedAt           gorm.DeletedAt `json:"-" gorm:"index"`
	Date                time.Time      `json:"date" gorm:"index"`
	TotalAPICalls       int            `json:"total_api_calls"`
	CompletionCalls     int            `json:"completion_calls"`
	EmbeddingCalls      int            `json:"embedding_calls"`
	ErrorCount          int            `json:"error_count"`
	AverageResponseTime float64        `json:"average_response_time"`
	TokensUsed          int            `json:"tokens_used"`
}

// UserActivityLog represents individual user activities
type UserActivityLog struct {
	ID        uint           `json:"id" gorm:"primaryKey"`
	CreatedAt time.Time      `json:"created_at"`
	DeletedAt gorm.DeletedAt `json:"-" gorm:"index"`
	UserID    string         `json:"user_id" gorm:"index"`
	Action    string         `json:"action" gorm:"index"` // login, logout, register, etc.
	Timestamp time.Time      `json:"timestamp"`
	IPAddress string         `json:"ip_address"`
	UserAgent string         `json:"user_agent"`
}

// AICallLog represents individual AI API calls
type AICallLog struct {
	ID           uint           `json:"id" gorm:"primaryKey"`
	CreatedAt    time.Time      `json:"created_at"`
	DeletedAt    gorm.DeletedAt `json:"-" gorm:"index"`
	UserID       string         `json:"user_id" gorm:"index"`
	Timestamp    time.Time      `json:"timestamp"`
	ModelUsed    string         `json:"model_used"`
	CallType     string         `json:"call_type" gorm:"index"` // completion, embedding, etc.
	ResponseTime float64        `json:"response_time"`
	Tokens       int            `json:"tokens"`
	Success      bool           `json:"success"`
	ErrorMessage string         `json:"error_message"`
}

// DailyStatsAggregate stores aggregated statistics for a specific day
type DailyStatsAggregate struct {
	ID                  uint           `json:"id" gorm:"primaryKey"`
	CreatedAt           time.Time      `json:"created_at"`
	UpdatedAt           time.Time      `json:"updated_at"`
	DeletedAt           gorm.DeletedAt `json:"-" gorm:"index"`
	Date                time.Time      `json:"date" gorm:"uniqueIndex"`
	TotalUsers          int            `json:"total_users"`
	ActiveUsers         int            `json:"active_users"`
	NewUsers            int            `json:"new_users"`
	TotalAPICalls       int            `json:"total_api_calls"`
	AverageResponseTime float64        `json:"average_response_time"`
	TotalTokensUsed     int            `json:"total_tokens_used"`
	SuccessRate         float64        `json:"success_rate"` // Percentage of successful API calls
}
