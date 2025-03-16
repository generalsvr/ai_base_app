package models

import (
	"time"
)

// APIKey represents an API key for accessing AI services
type APIKey struct {
	ID        int       `json:"id" gorm:"primaryKey"`
	UserID    int       `json:"user_id" gorm:"index;not null"`
	Key       string    `json:"key" gorm:"uniqueIndex;size:64;not null"`
	Name      string    `json:"name" gorm:"size:100;not null"` // User-friendly name for the key
	ExpiresAt time.Time `json:"expires_at" gorm:"not null"`
	IsActive  bool      `json:"is_active" gorm:"default:true;not null"`
	CreatedAt time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt time.Time `json:"updated_at" gorm:"autoUpdateTime"`
	LastUsed  time.Time `json:"last_used,omitempty"`
	User      User      `json:"-" gorm:"foreignKey:UserID"`
}

// TableName specifies the table name for APIKey
func (APIKey) TableName() string {
	return "api_keys"
}

// CreateAPIKeyRequest represents a request to create a new API key
type CreateAPIKeyRequest struct {
	Name      string    `json:"name" validate:"required,min=1,max=100"`
	ExpiresAt time.Time `json:"expires_at,omitempty"`
}

// APIKeyResponse represents the response for an API key
type APIKeyResponse struct {
	ID        int       `json:"id"`
	Name      string    `json:"name"`
	Key       string    `json:"key,omitempty"` // Only included when first created
	ExpiresAt time.Time `json:"expires_at"`
	IsActive  bool      `json:"is_active"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	LastUsed  time.Time `json:"last_used,omitempty"`
}

// APIKeysResponse represents the response for the list API keys endpoint
type APIKeysResponse struct {
	APIKeys []APIKeyResponse `json:"api_keys"`
	Total   int              `json:"total"`
}
