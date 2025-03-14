package handlers

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
	"github.com/onlytwins/user-service/models"
	"github.com/onlytwins/user-service/repository"
	"go.uber.org/zap"
)

// RoleHandler handles all role-related HTTP requests
type RoleHandler struct {
	userRepo *repository.UserRepository
	logger   *zap.Logger
}

// NewRoleHandler creates a new RoleHandler
func NewRoleHandler(userRepo *repository.UserRepository, logger *zap.Logger) *RoleHandler {
	return &RoleHandler{
		userRepo: userRepo,
		logger:   logger,
	}
}

// RegisterRoutes registers all routes for the RoleHandler
func (h *RoleHandler) RegisterRoutes(router *mux.Router) {
	router.HandleFunc("/api/v1/roles", h.GetRoles).Methods("GET")
	router.HandleFunc("/api/v1/roles", h.CreateRole).Methods("POST")
	router.HandleFunc("/api/v1/roles/{id}", h.GetRole).Methods("GET")
	router.HandleFunc("/api/v1/roles/{id}", h.UpdateRole).Methods("PUT")
	router.HandleFunc("/api/v1/roles/{id}", h.DeleteRole).Methods("DELETE")
	router.HandleFunc("/api/v1/users/{id}/roles", h.GetUserRoles).Methods("GET")
	router.HandleFunc("/api/v1/users/{id}/roles", h.AssignUserRoles).Methods("PUT")
}

// GetRoles handles GET /api/v1/roles
func (h *RoleHandler) GetRoles(w http.ResponseWriter, r *http.Request) {
	roles, err := h.userRepo.ListRoles(r.Context())
	if err != nil {
		h.logger.Error("Error getting roles", zap.Error(err))
		http.Error(w, "Error getting roles", http.StatusInternalServerError)
		return
	}

	response := make([]models.RoleResponse, len(roles))
	for i, role := range roles {
		response[i] = models.RoleResponse{
			ID:          role.ID,
			Name:        role.Name,
			Description: role.Description,
			CreatedAt:   role.CreatedAt,
			UpdatedAt:   role.UpdatedAt,
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// CreateRole handles POST /api/v1/roles
func (h *RoleHandler) CreateRole(w http.ResponseWriter, r *http.Request) {
	var newRole models.NewRole
	if err := json.NewDecoder(r.Body).Decode(&newRole); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	role, err := h.userRepo.CreateRole(r.Context(), newRole)
	if err != nil {
		if errors.Is(err, repository.ErrRoleExists) {
			http.Error(w, "Role already exists", http.StatusConflict)
		} else {
			h.logger.Error("Error creating role", zap.Error(err))
			http.Error(w, "Error creating role", http.StatusInternalServerError)
		}
		return
	}

	response := models.RoleResponse{
		ID:          role.ID,
		Name:        role.Name,
		Description: role.Description,
		CreatedAt:   role.CreatedAt,
		UpdatedAt:   role.UpdatedAt,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(response)
}

// GetRole handles GET /api/v1/roles/{id}
func (h *RoleHandler) GetRole(w http.ResponseWriter, r *http.Request) {
	idStr := mux.Vars(r)["id"]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid role ID", http.StatusBadRequest)
		return
	}

	role, err := h.userRepo.GetRoleByID(r.Context(), id)
	if err != nil {
		if errors.Is(err, repository.ErrRoleNotFound) {
			http.Error(w, "Role not found", http.StatusNotFound)
		} else {
			h.logger.Error("Error getting role", zap.Error(err))
			http.Error(w, "Error getting role", http.StatusInternalServerError)
		}
		return
	}

	response := models.RoleResponse{
		ID:          role.ID,
		Name:        role.Name,
		Description: role.Description,
		CreatedAt:   role.CreatedAt,
		UpdatedAt:   role.UpdatedAt,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// UpdateRole handles PUT /api/v1/roles/{id}
func (h *RoleHandler) UpdateRole(w http.ResponseWriter, r *http.Request) {
	idStr := mux.Vars(r)["id"]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid role ID", http.StatusBadRequest)
		return
	}

	var updateRole models.UpdateRole
	if err := json.NewDecoder(r.Body).Decode(&updateRole); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	role, err := h.userRepo.UpdateRole(r.Context(), id, updateRole)
	if err != nil {
		if errors.Is(err, repository.ErrRoleNotFound) {
			http.Error(w, "Role not found", http.StatusNotFound)
		} else if errors.Is(err, repository.ErrRoleExists) {
			http.Error(w, "Role already exists", http.StatusConflict)
		} else {
			h.logger.Error("Error updating role", zap.Error(err))
			http.Error(w, "Error updating role", http.StatusInternalServerError)
		}
		return
	}

	response := models.RoleResponse{
		ID:          role.ID,
		Name:        role.Name,
		Description: role.Description,
		CreatedAt:   role.CreatedAt,
		UpdatedAt:   role.UpdatedAt,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// DeleteRole handles DELETE /api/v1/roles/{id}
func (h *RoleHandler) DeleteRole(w http.ResponseWriter, r *http.Request) {
	idStr := mux.Vars(r)["id"]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid role ID", http.StatusBadRequest)
		return
	}

	err = h.userRepo.DeleteRole(r.Context(), id)
	if err != nil {
		if errors.Is(err, repository.ErrRoleNotFound) {
			http.Error(w, "Role not found", http.StatusNotFound)
		} else {
			h.logger.Error("Error deleting role", zap.Error(err))
			http.Error(w, "Error deleting role", http.StatusInternalServerError)
		}
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// GetUserRoles handles GET /api/v1/users/{id}/roles
func (h *RoleHandler) GetUserRoles(w http.ResponseWriter, r *http.Request) {
	idStr := mux.Vars(r)["id"]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid user ID", http.StatusBadRequest)
		return
	}

	roles, err := h.userRepo.GetUserRoles(r.Context(), id)
	if err != nil {
		if errors.Is(err, repository.ErrUserNotFound) {
			http.Error(w, "User not found", http.StatusNotFound)
		} else {
			h.logger.Error("Error getting user roles", zap.Error(err))
			http.Error(w, "Error getting user roles", http.StatusInternalServerError)
		}
		return
	}

	response := make([]models.RoleResponse, len(roles))
	for i, role := range roles {
		response[i] = models.RoleResponse{
			ID:          role.ID,
			Name:        role.Name,
			Description: role.Description,
			CreatedAt:   role.CreatedAt,
			UpdatedAt:   role.UpdatedAt,
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// AssignUserRoles handles PUT /api/v1/users/{id}/roles
func (h *RoleHandler) AssignUserRoles(w http.ResponseWriter, r *http.Request) {
	idStr := mux.Vars(r)["id"]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid user ID", http.StatusBadRequest)
		return
	}

	var roleIDs []int
	if err := json.NewDecoder(r.Body).Decode(&roleIDs); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	err = h.userRepo.AssignUserRoles(r.Context(), id, roleIDs)
	if err != nil {
		if errors.Is(err, repository.ErrUserNotFound) {
			http.Error(w, "User not found", http.StatusNotFound)
		} else if errors.Is(err, repository.ErrRoleNotFound) {
			http.Error(w, "One or more roles not found", http.StatusNotFound)
		} else {
			h.logger.Error("Error assigning user roles", zap.Error(err))
			http.Error(w, "Error assigning user roles", http.StatusInternalServerError)
		}
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
