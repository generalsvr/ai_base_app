package repository

import (
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/onlytwins/user-service/models"

	"gorm.io/gorm"
)

// APIKeyRepository provides access to API key data
type APIKeyRepository struct {
	db *gorm.DB
}

// NewAPIKeyRepository creates a new APIKeyRepository
func NewAPIKeyRepository(db *gorm.DB) *APIKeyRepository {
	return &APIKeyRepository{db: db}
}

// generateAPIKey generates a secure random API key
func generateAPIKey() (string, error) {
	// Generate 32 bytes (256 bits) of random data
	bytes := make([]byte, 32)
	_, err := rand.Read(bytes)
	if err != nil {
		return "", err
	}

	// Encode as base64 and clean it up
	key := base64.URLEncoding.EncodeToString(bytes)
	key = strings.TrimRight(key, "=") // Remove padding characters

	// Add a prefix to easily identify this as an API key
	return fmt.Sprintf("sk_%s", key), nil
}

// CreateAPIKey creates a new API key for a user
func (r *APIKeyRepository) CreateAPIKey(userID int, name string, expiresAt time.Time) (*models.APIKey, error) {
	// If no expiration is provided, set default (1 year)
	if expiresAt.IsZero() {
		expiresAt = time.Now().AddDate(1, 0, 0)
	}

	// Generate a secure random API key
	keyString, err := generateAPIKey()
	if err != nil {
		return nil, fmt.Errorf("error generating API key: %w", err)
	}

	apiKey := models.APIKey{
		UserID:    userID,
		Key:       keyString,
		Name:      name,
		ExpiresAt: expiresAt,
		IsActive:  true,
	}

	// Save to database
	if err := r.db.Create(&apiKey).Error; err != nil {
		return nil, fmt.Errorf("error saving API key: %w", err)
	}

	return &apiKey, nil
}

// GetAPIKeysByUserID gets all API keys for a user
func (r *APIKeyRepository) GetAPIKeysByUserID(userID int) ([]models.APIKey, error) {
	var apiKeys []models.APIKey

	if err := r.db.Where("user_id = ?", userID).Find(&apiKeys).Error; err != nil {
		return nil, fmt.Errorf("error fetching API keys: %w", err)
	}

	return apiKeys, nil
}

// GetAPIKeyByID gets an API key by its ID
func (r *APIKeyRepository) GetAPIKeyByID(keyID int, userID int) (*models.APIKey, error) {
	var apiKey models.APIKey

	if err := r.db.Where("id = ? AND user_id = ?", keyID, userID).First(&apiKey).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, fmt.Errorf("API key not found")
		}
		return nil, fmt.Errorf("error fetching API key: %w", err)
	}

	return &apiKey, nil
}

// RevokeAPIKey revokes (deactivates) an API key
func (r *APIKeyRepository) RevokeAPIKey(keyID int, userID int) error {
	result := r.db.Model(&models.APIKey{}).
		Where("id = ? AND user_id = ?", keyID, userID).
		Update("is_active", false)

	if result.Error != nil {
		return fmt.Errorf("error revoking API key: %w", result.Error)
	}

	if result.RowsAffected == 0 {
		return fmt.Errorf("API key not found or already revoked")
	}

	return nil
}

// ValidateAPIKey checks if an API key is valid and returns the associated user ID
func (r *APIKeyRepository) ValidateAPIKey(keyString string) (int, error) {
	var apiKey models.APIKey

	if err := r.db.Where("key = ? AND is_active = ? AND expires_at > ?",
		keyString, true, time.Now()).First(&apiKey).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return 0, fmt.Errorf("invalid or expired API key")
		}
		return 0, fmt.Errorf("error validating API key: %w", err)
	}

	// Update last used timestamp
	r.db.Model(&apiKey).Update("last_used", time.Now())

	return apiKey.UserID, nil
}

// DeleteAPIKey permanently deletes an API key
func (r *APIKeyRepository) DeleteAPIKey(keyID int, userID int) error {
	result := r.db.Where("id = ? AND user_id = ?", keyID, userID).Delete(&models.APIKey{})

	if result.Error != nil {
		return fmt.Errorf("error deleting API key: %w", result.Error)
	}

	if result.RowsAffected == 0 {
		return fmt.Errorf("API key not found")
	}

	return nil
}
