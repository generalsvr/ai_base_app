package handlers

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
	"time"

	"github.com/gorilla/mux"
	"github.com/onlytwins/user-service/models"
	"github.com/onlytwins/user-service/repository"
	"go.uber.org/zap"
)

// UserHandler handles all user-related HTTP requests
type UserHandler struct {
	userRepo *repository.UserRepository
	logger   *zap.Logger
}

// NewUserHandler creates a new UserHandler
func NewUserHandler(userRepo *repository.UserRepository, logger *zap.Logger) *UserHandler {
	return &UserHandler{
		userRepo: userRepo,
		logger:   logger,
	}
}

// RegisterRoutes registers all routes for the UserHandler
func (h *UserHandler) RegisterRoutes(router *mux.Router) {
	router.HandleFunc("/api/v1/users", h.GetUsers).Methods("GET")
	router.HandleFunc("/api/v1/users", h.CreateUser).Methods("POST")
	router.HandleFunc("/api/v1/users/{id}", h.GetUser).Methods("GET")
	router.HandleFunc("/api/v1/users/{id}", h.UpdateUser).Methods("PUT")
	router.HandleFunc("/api/v1/users/{id}", h.DeleteUser).Methods("DELETE")
	router.HandleFunc("/api/v1/login", h.Login).Methods("POST")
	router.HandleFunc("/api/v1/logout", h.Logout).Methods("POST")
	router.HandleFunc("/api/v1/verify-token", h.VerifyToken).Methods("POST")
}

// GetUsers handles GET /api/v1/users
func (h *UserHandler) GetUsers(w http.ResponseWriter, r *http.Request) {
	// Parse pagination parameters
	pageStr := r.URL.Query().Get("page")
	limitStr := r.URL.Query().Get("limit")

	page := 1
	limit := 10

	if pageStr != "" {
		pageInt, err := strconv.Atoi(pageStr)
		if err == nil && pageInt > 0 {
			page = pageInt
		}
	}

	if limitStr != "" {
		limitInt, err := strconv.Atoi(limitStr)
		if err == nil && limitInt > 0 && limitInt <= 100 {
			limit = limitInt
		}
	}

	// Get users from repository
	users, total, err := h.userRepo.List(r.Context(), page, limit)
	if err != nil {
		h.logger.Error("Error getting users", zap.Error(err))
		http.Error(w, "Error getting users", http.StatusInternalServerError)
		return
	}

	// Convert to response format
	response := models.UsersResponse{
		Users: make([]models.UserResponse, 0, len(users)),
		Total: total,
		Page:  page,
		Limit: limit,
	}

	for _, user := range users {
		response.Users = append(response.Users, models.UserResponse{
			ID:        user.ID,
			Username:  user.Username,
			Email:     user.Email,
			FirstName: user.FirstName,
			LastName:  user.LastName,
			IsActive:  user.IsActive,
			CreatedAt: user.CreatedAt,
			UpdatedAt: user.UpdatedAt,
		})
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// GetUser handles GET /api/v1/users/{id}
func (h *UserHandler) GetUser(w http.ResponseWriter, r *http.Request) {
	// Parse user ID from URL
	idStr := mux.Vars(r)["id"]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid user ID", http.StatusBadRequest)
		return
	}

	// Get user from repository
	user, err := h.userRepo.GetByID(r.Context(), id)
	if err != nil {
		if errors.Is(err, repository.ErrUserNotFound) {
			http.Error(w, "User not found", http.StatusNotFound)
		} else {
			h.logger.Error("Error getting user", zap.Error(err))
			http.Error(w, "Error getting user", http.StatusInternalServerError)
		}
		return
	}

	// Return response
	response := models.UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Email:     user.Email,
		FirstName: user.FirstName,
		LastName:  user.LastName,
		IsActive:  user.IsActive,
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// CreateUser handles POST /api/v1/users
func (h *UserHandler) CreateUser(w http.ResponseWriter, r *http.Request) {
	// Parse request body
	var newUser models.NewUser
	if err := json.NewDecoder(r.Body).Decode(&newUser); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if newUser.Username == "" || newUser.Email == "" || newUser.Password == "" {
		http.Error(w, "Username, email, and password are required", http.StatusBadRequest)
		return
	}

	// Create user in repository
	user, err := h.userRepo.Create(r.Context(), newUser)
	if err != nil {
		if errors.Is(err, repository.ErrUsernameExists) {
			http.Error(w, "Username already exists", http.StatusConflict)
		} else if errors.Is(err, repository.ErrEmailExists) {
			http.Error(w, "Email already exists", http.StatusConflict)
		} else {
			h.logger.Error("Error creating user", zap.Error(err))
			http.Error(w, "Error creating user", http.StatusInternalServerError)
		}
		return
	}

	// Return response
	response := models.UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Email:     user.Email,
		FirstName: user.FirstName,
		LastName:  user.LastName,
		IsActive:  user.IsActive,
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(response)
}

// UpdateUser handles PUT /api/v1/users/{id}
func (h *UserHandler) UpdateUser(w http.ResponseWriter, r *http.Request) {
	// Parse user ID from URL
	idStr := mux.Vars(r)["id"]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid user ID", http.StatusBadRequest)
		return
	}

	// Parse request body
	var updateUser models.UpdateUser
	if err := json.NewDecoder(r.Body).Decode(&updateUser); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Update user in repository
	user, err := h.userRepo.Update(r.Context(), id, updateUser)
	if err != nil {
		if errors.Is(err, repository.ErrUserNotFound) {
			http.Error(w, "User not found", http.StatusNotFound)
		} else if errors.Is(err, repository.ErrUsernameExists) {
			http.Error(w, "Username already exists", http.StatusConflict)
		} else if errors.Is(err, repository.ErrEmailExists) {
			http.Error(w, "Email already exists", http.StatusConflict)
		} else {
			h.logger.Error("Error updating user", zap.Error(err))
			http.Error(w, "Error updating user", http.StatusInternalServerError)
		}
		return
	}

	// Return response
	response := models.UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Email:     user.Email,
		FirstName: user.FirstName,
		LastName:  user.LastName,
		IsActive:  user.IsActive,
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// DeleteUser handles DELETE /api/v1/users/{id}
func (h *UserHandler) DeleteUser(w http.ResponseWriter, r *http.Request) {
	// Parse user ID from URL
	idStr := mux.Vars(r)["id"]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid user ID", http.StatusBadRequest)
		return
	}

	// Delete user from repository
	err = h.userRepo.Delete(r.Context(), id)
	if err != nil {
		if errors.Is(err, repository.ErrUserNotFound) {
			http.Error(w, "User not found", http.StatusNotFound)
		} else {
			h.logger.Error("Error deleting user", zap.Error(err))
			http.Error(w, "Error deleting user", http.StatusInternalServerError)
		}
		return
	}

	// Return success
	w.WriteHeader(http.StatusNoContent)
}

// Login handles POST /api/v1/login
func (h *UserHandler) Login(w http.ResponseWriter, r *http.Request) {
	// Parse request body
	var loginRequest models.LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&loginRequest); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if loginRequest.Username == "" || loginRequest.Password == "" {
		http.Error(w, "Username and password are required", http.StatusBadRequest)
		return
	}

	// Authenticate user
	user, err := h.userRepo.Authenticate(r.Context(), loginRequest.Username, loginRequest.Password)
	if err != nil {
		if errors.Is(err, repository.ErrInvalidCredentials) {
			http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		} else {
			h.logger.Error("Error authenticating user", zap.Error(err))
			http.Error(w, "Error authenticating user", http.StatusInternalServerError)
		}
		return
	}

	// Generate token
	token, err := generateToken()
	if err != nil {
		h.logger.Error("Error generating token", zap.Error(err))
		http.Error(w, "Error generating token", http.StatusInternalServerError)
		return
	}

	// Create session
	expiresAt := time.Now().Add(24 * time.Hour)
	_, err = h.userRepo.CreateSession(r.Context(), user.ID, token, expiresAt)
	if err != nil {
		h.logger.Error("Error creating session", zap.Error(err))
		http.Error(w, "Error creating session", http.StatusInternalServerError)
		return
	}

	// Return response
	response := models.LoginResponse{
		User:  *user,
		Token: token,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Logout handles POST /api/v1/logout
func (h *UserHandler) Logout(w http.ResponseWriter, r *http.Request) {
	// Get token from Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		http.Error(w, "Authorization header required", http.StatusUnauthorized)
		return
	}

	// Extract token from "Bearer <token>"
	token := ""
	if len(authHeader) > 7 && authHeader[:7] == "Bearer " {
		token = authHeader[7:]
	} else {
		token = authHeader
	}

	// Delete session
	err := h.userRepo.DeleteSession(r.Context(), token)
	if err != nil {
		h.logger.Error("Error deleting session", zap.Error(err))
		http.Error(w, "Error deleting session", http.StatusInternalServerError)
		return
	}

	// Return success
	w.WriteHeader(http.StatusNoContent)
}

// VerifyToken handles POST /api/v1/verify-token
func (h *UserHandler) VerifyToken(w http.ResponseWriter, r *http.Request) {
	// Get token from Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		http.Error(w, "Authorization header required", http.StatusUnauthorized)
		return
	}

	// Extract token from "Bearer <token>"
	token := ""
	if len(authHeader) > 7 && authHeader[:7] == "Bearer " {
		token = authHeader[7:]
	} else {
		token = authHeader
	}

	// Get session by token
	_, user, err := h.userRepo.GetSessionByToken(r.Context(), token)
	if err != nil {
		http.Error(w, "Invalid or expired token", http.StatusUnauthorized)
		return
	}

	// Return response
	response := models.UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Email:     user.Email,
		FirstName: user.FirstName,
		LastName:  user.LastName,
		IsActive:  user.IsActive,
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// GetUserFromContext retrieves a user from the request context
func GetUserFromContext(ctx context.Context) (*models.User, error) {
	user, ok := ctx.Value("user").(*models.User)
	if !ok {
		return nil, errors.New("user not found in context")
	}
	return user, nil
}

// generateToken generates a random token
func generateToken() (string, error) {
	tokenBytes := make([]byte, 16)
	_, err := rand.Read(tokenBytes)
	if err != nil {
		return "", err
	}
	return hex.EncodeToString(tokenBytes), nil
}
