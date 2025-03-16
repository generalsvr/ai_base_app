package handlers

import (
	"net/http"

	"github.com/onlytwins/user-service/repository"

	"encoding/json"

	"github.com/gorilla/mux"
)

// AuthHandler handles authentication-related requests
type AuthHandler struct {
	apiKeyRepo *repository.APIKeyRepository
	userRepo   *repository.UserRepository
}

// NewAuthHandler creates a new auth handler
func NewAuthHandler(apiKeyRepo *repository.APIKeyRepository, userRepo *repository.UserRepository) *AuthHandler {
	return &AuthHandler{
		apiKeyRepo: apiKeyRepo,
		userRepo:   userRepo,
	}
}

// RegisterRoutes registers auth routes
func (h *AuthHandler) RegisterRoutes(router *mux.Router) {
	// Create a subrouter for auth endpoints
	authRouter := router.PathPrefix("/api/auth").Subrouter()

	// Register auth routes
	authRouter.HandleFunc("/validate-key", h.ValidateAPIKey).Methods("POST")
}

// ValidateAPIKeyRequest represents a request to validate an API key
type ValidateAPIKeyRequest struct {
	APIKey string `json:"api_key"`
}

// ValidateAPIKey handles validating an API key
func (h *AuthHandler) ValidateAPIKey(w http.ResponseWriter, r *http.Request) {
	// Parse request
	var req ValidateAPIKeyRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request format", http.StatusBadRequest)
		return
	}

	// Validate API key
	userID, err := h.apiKeyRepo.ValidateAPIKey(req.APIKey)
	if err != nil {
		http.Error(w, "Invalid or expired API key", http.StatusUnauthorized)
		return
	}

	// Get user information
	user, err := h.userRepo.GetByID(r.Context(), userID)
	if err != nil {
		http.Error(w, "User not found", http.StatusInternalServerError)
		return
	}

	// Return user information with the response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	response := map[string]interface{}{
		"valid": true,
		"user": map[string]interface{}{
			"id":        user.ID,
			"username":  user.Username,
			"email":     user.Email,
			"is_active": user.IsActive,
		},
	}

	// Encode response
	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, "Error encoding response", http.StatusInternalServerError)
		return
	}
}
