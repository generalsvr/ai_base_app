package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"github.com/onlytwins/user-service/middlewares"
	"github.com/onlytwins/user-service/repository"

	"github.com/gorilla/mux"
	"go.uber.org/zap"
)

// APIKeyHandler handles API key related requests
type APIKeyHandler struct {
	apiKeyRepo *repository.APIKeyRepository
	logger     *zap.Logger
}

// NewAPIKeyHandler creates a new APIKeyHandler
func NewAPIKeyHandler(apiKeyRepo *repository.APIKeyRepository, logger *zap.Logger) *APIKeyHandler {
	return &APIKeyHandler{
		apiKeyRepo: apiKeyRepo,
		logger:     logger,
	}
}

// APIKeyRequest represents a request to create an API key
type APIKeyRequest struct {
	Name      string    `json:"name"`
	ExpiresAt time.Time `json:"expires_at"`
}

// CreateAPIKey handles creating a new API key
func (h *APIKeyHandler) CreateAPIKey(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context (set by auth middleware)
	userID, ok := r.Context().Value("userID").(int)
	if !ok {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Parse request body
	var req APIKeyRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.logger.Error("Failed to decode request", zap.Error(err))
		http.Error(w, "Invalid request format", http.StatusBadRequest)
		return
	}

	// Validate request
	if req.Name == "" {
		http.Error(w, "Name is required", http.StatusBadRequest)
		return
	}

	// Create API key
	apiKey, err := h.apiKeyRepo.CreateAPIKey(userID, req.Name, req.ExpiresAt)
	if err != nil {
		h.logger.Error("Failed to create API key", zap.Error(err))
		http.Error(w, "Failed to create API key", http.StatusInternalServerError)
		return
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(apiKey)
}

// GetAPIKeys handles retrieving all API keys for a user
func (h *APIKeyHandler) GetAPIKeys(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context (set by auth middleware)
	userID, ok := r.Context().Value("userID").(int)
	if !ok {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Get API keys
	apiKeys, err := h.apiKeyRepo.GetAPIKeysByUserID(userID)
	if err != nil {
		h.logger.Error("Failed to get API keys", zap.Error(err))
		http.Error(w, "Failed to get API keys", http.StatusInternalServerError)
		return
	}

	// Return response
	response := map[string]interface{}{
		"api_keys": apiKeys,
		"total":    len(apiKeys),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// RevokeAPIKey handles revoking an API key
func (h *APIKeyHandler) RevokeAPIKey(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context (set by auth middleware)
	userID, ok := r.Context().Value("userID").(int)
	if !ok {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Get key ID from URL
	vars := mux.Vars(r)
	keyIDStr := vars["id"]
	keyID, err := strconv.Atoi(keyIDStr)
	if err != nil {
		http.Error(w, "Invalid key ID", http.StatusBadRequest)
		return
	}

	// Revoke API key
	err = h.apiKeyRepo.RevokeAPIKey(keyID, userID)
	if err != nil {
		h.logger.Error("Failed to revoke API key", zap.Error(err))
		http.Error(w, "Failed to revoke API key", http.StatusInternalServerError)
		return
	}

	// Return success
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]bool{"success": true})
}

// DeleteAPIKey handles deleting an API key
func (h *APIKeyHandler) DeleteAPIKey(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context (set by auth middleware)
	userID, ok := r.Context().Value("userID").(int)
	if !ok {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Get key ID from URL
	vars := mux.Vars(r)
	keyIDStr := vars["id"]
	keyID, err := strconv.Atoi(keyIDStr)
	if err != nil {
		http.Error(w, "Invalid key ID", http.StatusBadRequest)
		return
	}

	// Delete API key
	err = h.apiKeyRepo.DeleteAPIKey(keyID, userID)
	if err != nil {
		h.logger.Error("Failed to delete API key", zap.Error(err))
		http.Error(w, "Failed to delete API key", http.StatusInternalServerError)
		return
	}

	// Return success
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]bool{"success": true})
}

// RegisterRoutes registers API key routes
func (h *APIKeyHandler) RegisterRoutes(router *mux.Router, userRepo *repository.UserRepository) {
	// Create a subrouter for api key endpoints with authentication
	apiKeyRouter := router.PathPrefix("/api/v1/keys").Subrouter()

	// Add auth middleware
	apiKeyRouter.Use(middlewares.AuthMiddleware(userRepo))

	// Register API key routes
	apiKeyRouter.HandleFunc("", h.CreateAPIKey).Methods("POST")
	apiKeyRouter.HandleFunc("", h.GetAPIKeys).Methods("GET")
	apiKeyRouter.HandleFunc("/{id}", h.RevokeAPIKey).Methods("PUT")
	apiKeyRouter.HandleFunc("/{id}", h.DeleteAPIKey).Methods("DELETE")
}
