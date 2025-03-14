package repository

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/onlytwins/user-service/models"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

// Common errors
var (
	ErrUserNotFound       = errors.New("user not found")
	ErrEmailExists        = errors.New("email already exists")
	ErrUsernameExists     = errors.New("username already exists")
	ErrInvalidCredentials = errors.New("invalid credentials")
	ErrRoleNotFound       = errors.New("role not found")
	ErrRoleExists         = errors.New("role already exists")
)

// UserRepository handles all database interactions for users
type UserRepository struct {
	db *gorm.DB
}

// NewUserRepository creates a new UserRepository
func NewUserRepository(db *gorm.DB) *UserRepository {
	return &UserRepository{
		db: db,
	}
}

// Create creates a new user in the database
func (r *UserRepository) Create(ctx context.Context, user models.NewUser) (*models.User, error) {
	// Check if username already exists
	var count int64
	if err := r.db.WithContext(ctx).Model(&models.User{}).Where("username = ?", user.Username).Count(&count).Error; err != nil {
		return nil, fmt.Errorf("error checking username: %w", err)
	}
	if count > 0 {
		return nil, ErrUsernameExists
	}

	// Check if email already exists
	if err := r.db.WithContext(ctx).Model(&models.User{}).Where("email = ?", user.Email).Count(&count).Error; err != nil {
		return nil, fmt.Errorf("error checking email: %w", err)
	}
	if count > 0 {
		return nil, ErrEmailExists
	}

	// Hash the password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(user.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("error hashing password: %w", err)
	}

	// Create the user
	newUser := models.User{
		Username:     user.Username,
		Email:        user.Email,
		PasswordHash: string(hashedPassword),
		FirstName:    user.FirstName,
		LastName:     user.LastName,
		IsActive:     true,
	}

	if err := r.db.WithContext(ctx).Create(&newUser).Error; err != nil {
		return nil, fmt.Errorf("error creating user: %w", err)
	}

	return &newUser, nil
}

// GetByID retrieves a user by ID
func (r *UserRepository) GetByID(ctx context.Context, id int) (*models.User, error) {
	var user models.User
	if err := r.db.WithContext(ctx).First(&user, id).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrUserNotFound
		}
		return nil, fmt.Errorf("error getting user: %w", err)
	}
	return &user, nil
}

// GetByUsername retrieves a user by username
func (r *UserRepository) GetByUsername(ctx context.Context, username string) (*models.User, error) {
	var user models.User
	if err := r.db.WithContext(ctx).Where("username = ?", username).First(&user).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrUserNotFound
		}
		return nil, fmt.Errorf("error getting user by username: %w", err)
	}
	return &user, nil
}

// GetByEmail retrieves a user by email
func (r *UserRepository) GetByEmail(ctx context.Context, email string) (*models.User, error) {
	var user models.User
	if err := r.db.WithContext(ctx).Where("email = ?", email).First(&user).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrUserNotFound
		}
		return nil, fmt.Errorf("error getting user by email: %w", err)
	}
	return &user, nil
}

// List retrieves a list of users with pagination
func (r *UserRepository) List(ctx context.Context, page, limit int) ([]models.User, int, error) {
	var users []models.User
	var total int64

	// Get total count
	if err := r.db.WithContext(ctx).Model(&models.User{}).Count(&total).Error; err != nil {
		return nil, 0, fmt.Errorf("error counting users: %w", err)
	}

	// Calculate offset
	offset := (page - 1) * limit

	// Get users with pagination
	if err := r.db.WithContext(ctx).Offset(offset).Limit(limit).Find(&users).Error; err != nil {
		return nil, 0, fmt.Errorf("error listing users: %w", err)
	}

	return users, int(total), nil
}

// Update updates a user in the database
func (r *UserRepository) Update(ctx context.Context, id int, update models.UpdateUser) (*models.User, error) {
	// Get the user first
	var user models.User
	if err := r.db.WithContext(ctx).First(&user, id).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrUserNotFound
		}
		return nil, fmt.Errorf("error getting user: %w", err)
	}

	// Check if username is being updated and if it already exists
	if update.Username != nil && *update.Username != user.Username {
		var count int64
		if err := r.db.WithContext(ctx).Model(&models.User{}).Where("username = ? AND id != ?", *update.Username, id).Count(&count).Error; err != nil {
			return nil, fmt.Errorf("error checking username: %w", err)
		}
		if count > 0 {
			return nil, ErrUsernameExists
		}
		user.Username = *update.Username
	}

	// Check if email is being updated and if it already exists
	if update.Email != nil && *update.Email != user.Email {
		var count int64
		if err := r.db.WithContext(ctx).Model(&models.User{}).Where("email = ? AND id != ?", *update.Email, id).Count(&count).Error; err != nil {
			return nil, fmt.Errorf("error checking email: %w", err)
		}
		if count > 0 {
			return nil, ErrEmailExists
		}
		user.Email = *update.Email
	}

	// Update password if provided
	if update.Password != nil {
		hashedPassword, err := bcrypt.GenerateFromPassword([]byte(*update.Password), bcrypt.DefaultCost)
		if err != nil {
			return nil, fmt.Errorf("error hashing password: %w", err)
		}
		user.PasswordHash = string(hashedPassword)
	}

	// Update other fields if provided
	if update.FirstName != nil {
		user.FirstName = *update.FirstName
	}
	if update.LastName != nil {
		user.LastName = *update.LastName
	}
	if update.IsActive != nil {
		user.IsActive = *update.IsActive
	}

	// Save the updated user
	if err := r.db.WithContext(ctx).Save(&user).Error; err != nil {
		return nil, fmt.Errorf("error updating user: %w", err)
	}

	return &user, nil
}

// Delete deletes a user from the database
func (r *UserRepository) Delete(ctx context.Context, id int) error {
	result := r.db.WithContext(ctx).Delete(&models.User{}, id)
	if result.Error != nil {
		return fmt.Errorf("error deleting user: %w", result.Error)
	}
	if result.RowsAffected == 0 {
		return ErrUserNotFound
	}
	return nil
}

// Authenticate authenticates a user with username and password
func (r *UserRepository) Authenticate(ctx context.Context, username, password string) (*models.User, error) {
	// Get the user by username
	user, err := r.GetByUsername(ctx, username)
	if err != nil {
		if errors.Is(err, ErrUserNotFound) {
			return nil, ErrInvalidCredentials
		}
		return nil, err
	}

	// Check if the user is active
	if !user.IsActive {
		return nil, ErrInvalidCredentials
	}

	// Compare the password
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password)); err != nil {
		return nil, ErrInvalidCredentials
	}

	return user, nil
}

// CreateSession creates a new session for a user
func (r *UserRepository) CreateSession(ctx context.Context, userID int, token string, expiresAt time.Time) (*models.Session, error) {
	session := models.Session{
		UserID:    userID,
		Token:     token,
		ExpiresAt: expiresAt,
	}

	if err := r.db.WithContext(ctx).Create(&session).Error; err != nil {
		return nil, fmt.Errorf("error creating session: %w", err)
	}

	return &session, nil
}

// GetSessionByToken retrieves a session by token
func (r *UserRepository) GetSessionByToken(ctx context.Context, token string) (*models.Session, *models.User, error) {
	var session models.Session
	if err := r.db.WithContext(ctx).Where("token = ?", token).First(&session).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil, ErrUserNotFound
		}
		return nil, nil, fmt.Errorf("error getting session: %w", err)
	}

	// Check if session is expired
	if session.ExpiresAt.Before(time.Now()) {
		// Delete the expired session
		r.db.WithContext(ctx).Delete(&session)
		return nil, nil, ErrUserNotFound
	}

	// Get the user
	var user models.User
	if err := r.db.WithContext(ctx).First(&user, session.UserID).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil, ErrUserNotFound
		}
		return nil, nil, fmt.Errorf("error getting user: %w", err)
	}

	return &session, &user, nil
}

// DeleteSession deletes a session by token
func (r *UserRepository) DeleteSession(ctx context.Context, token string) error {
	result := r.db.WithContext(ctx).Where("token = ?", token).Delete(&models.Session{})
	if result.Error != nil {
		return fmt.Errorf("error deleting session: %w", result.Error)
	}
	return nil
}

// CreateUserPreference creates a new user preference
func (r *UserRepository) CreateUserPreference(ctx context.Context, userID int, key, value string) (*models.UserPreference, error) {
	// Check if the user exists
	if _, err := r.GetByID(ctx, userID); err != nil {
		return nil, err
	}

	// Check if the preference already exists
	var existingPref models.UserPreference
	err := r.db.WithContext(ctx).Where("user_id = ? AND preference_key = ?", userID, key).First(&existingPref).Error
	if err == nil {
		// Update the existing preference
		existingPref.PreferenceValue = value
		if err := r.db.WithContext(ctx).Save(&existingPref).Error; err != nil {
			return nil, fmt.Errorf("error updating preference: %w", err)
		}
		return &existingPref, nil
	} else if !errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, fmt.Errorf("error checking preference: %w", err)
	}

	// Create a new preference
	pref := models.UserPreference{
		UserID:          userID,
		PreferenceKey:   key,
		PreferenceValue: value,
	}

	if err := r.db.WithContext(ctx).Create(&pref).Error; err != nil {
		return nil, fmt.Errorf("error creating preference: %w", err)
	}

	return &pref, nil
}

// GetUserPreferences retrieves all preferences for a user
func (r *UserRepository) GetUserPreferences(ctx context.Context, userID int) ([]models.UserPreference, error) {
	// Check if the user exists
	if _, err := r.GetByID(ctx, userID); err != nil {
		return nil, err
	}

	var prefs []models.UserPreference
	if err := r.db.WithContext(ctx).Where("user_id = ?", userID).Find(&prefs).Error; err != nil {
		return nil, fmt.Errorf("error getting preferences: %w", err)
	}

	return prefs, nil
}

// GetUserPreferenceByKey retrieves a specific preference for a user
func (r *UserRepository) GetUserPreferenceByKey(ctx context.Context, userID int, key string) (*models.UserPreference, error) {
	// Check if the user exists
	if _, err := r.GetByID(ctx, userID); err != nil {
		return nil, err
	}

	var pref models.UserPreference
	if err := r.db.WithContext(ctx).Where("user_id = ? AND preference_key = ?", userID, key).First(&pref).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrUserNotFound
		}
		return nil, fmt.Errorf("error getting preference: %w", err)
	}

	return &pref, nil
}

// DeleteUserPreference deletes a user preference
func (r *UserRepository) DeleteUserPreference(ctx context.Context, userID int, key string) error {
	// Check if the user exists
	if _, err := r.GetByID(ctx, userID); err != nil {
		return err
	}

	result := r.db.WithContext(ctx).Where("user_id = ? AND preference_key = ?", userID, key).Delete(&models.UserPreference{})
	if result.Error != nil {
		return fmt.Errorf("error deleting preference: %w", result.Error)
	}
	if result.RowsAffected == 0 {
		return ErrUserNotFound
	}

	return nil
}

// ListRoles retrieves all roles
func (r *UserRepository) ListRoles(ctx context.Context) ([]models.Role, error) {
	var roles []models.Role
	if err := r.db.WithContext(ctx).Find(&roles).Error; err != nil {
		return nil, fmt.Errorf("error listing roles: %w", err)
	}
	return roles, nil
}

// CreateRole creates a new role
func (r *UserRepository) CreateRole(ctx context.Context, role models.NewRole) (*models.Role, error) {
	// Check if role already exists
	var count int64
	if err := r.db.WithContext(ctx).Model(&models.Role{}).Where("name = ?", role.Name).Count(&count).Error; err != nil {
		return nil, fmt.Errorf("error checking role name: %w", err)
	}
	if count > 0 {
		return nil, ErrRoleExists
	}

	newRole := models.Role{
		Name:        role.Name,
		Description: role.Description,
	}

	if err := r.db.WithContext(ctx).Create(&newRole).Error; err != nil {
		return nil, fmt.Errorf("error creating role: %w", err)
	}

	return &newRole, nil
}

// GetRoleByID retrieves a role by ID
func (r *UserRepository) GetRoleByID(ctx context.Context, id int) (*models.Role, error) {
	var role models.Role
	if err := r.db.WithContext(ctx).First(&role, id).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrRoleNotFound
		}
		return nil, fmt.Errorf("error getting role: %w", err)
	}
	return &role, nil
}

// UpdateRole updates a role
func (r *UserRepository) UpdateRole(ctx context.Context, id int, update models.UpdateRole) (*models.Role, error) {
	var role models.Role
	if err := r.db.WithContext(ctx).First(&role, id).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrRoleNotFound
		}
		return nil, fmt.Errorf("error getting role: %w", err)
	}

	// Check if name is being updated and if it already exists
	if update.Name != nil && *update.Name != role.Name {
		var count int64
		if err := r.db.WithContext(ctx).Model(&models.Role{}).Where("name = ? AND id != ?", *update.Name, id).Count(&count).Error; err != nil {
			return nil, fmt.Errorf("error checking role name: %w", err)
		}
		if count > 0 {
			return nil, ErrRoleExists
		}
		role.Name = *update.Name
	}

	if update.Description != nil {
		role.Description = *update.Description
	}

	if err := r.db.WithContext(ctx).Save(&role).Error; err != nil {
		return nil, fmt.Errorf("error updating role: %w", err)
	}

	return &role, nil
}

// DeleteRole deletes a role
func (r *UserRepository) DeleteRole(ctx context.Context, id int) error {
	// First, delete all user-role associations
	if err := r.db.WithContext(ctx).Where("role_id = ?", id).Delete(&models.UserRole{}).Error; err != nil {
		return fmt.Errorf("error deleting user-role associations: %w", err)
	}

	// Then delete the role
	result := r.db.WithContext(ctx).Delete(&models.Role{}, id)
	if result.Error != nil {
		return fmt.Errorf("error deleting role: %w", result.Error)
	}
	if result.RowsAffected == 0 {
		return ErrRoleNotFound
	}
	return nil
}

// GetUserRoles retrieves all roles for a user
func (r *UserRepository) GetUserRoles(ctx context.Context, userID int) ([]models.Role, error) {
	var roles []models.Role
	if err := r.db.WithContext(ctx).Joins("JOIN user_roles ON roles.id = user_roles.role_id").Where("user_roles.user_id = ?", userID).Find(&roles).Error; err != nil {
		return nil, fmt.Errorf("error getting user roles: %w", err)
	}
	return roles, nil
}

// AssignUserRoles assigns roles to a user
func (r *UserRepository) AssignUserRoles(ctx context.Context, userID int, roleIDs []int) error {
	// Start a transaction
	tx := r.db.WithContext(ctx).Begin()
	if tx.Error != nil {
		return fmt.Errorf("error starting transaction: %w", tx.Error)
	}
	defer func() {
		if r := recover(); r != nil {
			tx.Rollback()
		}
	}()

	// Delete existing user-role associations
	if err := tx.Where("user_id = ?", userID).Delete(&models.UserRole{}).Error; err != nil {
		tx.Rollback()
		return fmt.Errorf("error deleting existing user-role associations: %w", err)
	}

	// Create new user-role associations
	for _, roleID := range roleIDs {
		userRole := models.UserRole{
			UserID: userID,
			RoleID: roleID,
		}
		if err := tx.Create(&userRole).Error; err != nil {
			tx.Rollback()
			return fmt.Errorf("error creating user-role association: %w", err)
		}
	}

	// Commit the transaction
	if err := tx.Commit().Error; err != nil {
		return fmt.Errorf("error committing transaction: %w", err)
	}

	return nil
}
