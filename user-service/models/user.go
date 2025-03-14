package models

import (
	"time"
)

// User represents a user in the system
type User struct {
	ID           int       `json:"id" gorm:"primaryKey"`
	Username     string    `json:"username" gorm:"uniqueIndex;size:50;not null"`
	Email        string    `json:"email" gorm:"uniqueIndex;size:100;not null"`
	PasswordHash string    `json:"-" gorm:"column:password_hash;size:100;not null"` // Never send password hash in response
	FirstName    string    `json:"first_name,omitempty" gorm:"size:50"`
	LastName     string    `json:"last_name,omitempty" gorm:"size:50"`
	IsActive     bool      `json:"is_active" gorm:"default:true;not null"`
	CreatedAt    time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt    time.Time `json:"updated_at" gorm:"autoUpdateTime"`
	Roles        []Role    `json:"roles,omitempty" gorm:"many2many:user_roles;"`
}

// TableName specifies the table name for User
func (User) TableName() string {
	return "users"
}

// NewUser represents a user creation request
type NewUser struct {
	Username  string `json:"username" validate:"required,min=3,max=50"`
	Email     string `json:"email" validate:"required,email"`
	Password  string `json:"password" validate:"required,min=8"`
	FirstName string `json:"first_name,omitempty"`
	LastName  string `json:"last_name,omitempty"`
}

// UpdateUser represents a user update request
type UpdateUser struct {
	Username  *string `json:"username,omitempty" validate:"omitempty,min=3,max=50"`
	Email     *string `json:"email,omitempty" validate:"omitempty,email"`
	Password  *string `json:"password,omitempty" validate:"omitempty,min=8"`
	FirstName *string `json:"first_name,omitempty"`
	LastName  *string `json:"last_name,omitempty"`
	IsActive  *bool   `json:"is_active,omitempty"`
}

// Session represents a user session
type Session struct {
	ID        int       `json:"id" gorm:"primaryKey"`
	UserID    int       `json:"user_id" gorm:"index;not null"`
	Token     string    `json:"token" gorm:"uniqueIndex;size:255;not null"`
	ExpiresAt time.Time `json:"expires_at" gorm:"not null"`
	CreatedAt time.Time `json:"created_at" gorm:"autoCreateTime"`
	User      User      `json:"-" gorm:"foreignKey:UserID"`
}

// TableName specifies the table name for Session
func (Session) TableName() string {
	return "sessions"
}

// LoginRequest represents a user login request
type LoginRequest struct {
	Username string `json:"username" validate:"required"`
	Password string `json:"password" validate:"required"`
}

// LoginResponse represents a successful login response
type LoginResponse struct {
	User  User   `json:"user"`
	Token string `json:"token"`
}

// UserPreference represents a user preference
type UserPreference struct {
	ID              int       `json:"id" gorm:"primaryKey"`
	UserID          int       `json:"user_id" gorm:"index;not null"`
	PreferenceKey   string    `json:"preference_key" gorm:"size:50;not null"`
	PreferenceValue string    `json:"preference_value" gorm:"type:text;not null"`
	CreatedAt       time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt       time.Time `json:"updated_at" gorm:"autoUpdateTime"`
	User            User      `json:"-" gorm:"foreignKey:UserID"`
}

// TableName specifies the table name for UserPreference
func (UserPreference) TableName() string {
	return "user_preferences"
}

// UserResponse represents the response with user information
type UserResponse struct {
	ID        int            `json:"id"`
	Username  string         `json:"username"`
	Email     string         `json:"email"`
	FirstName string         `json:"first_name,omitempty"`
	LastName  string         `json:"last_name,omitempty"`
	IsActive  bool           `json:"is_active"`
	Roles     []RoleResponse `json:"roles,omitempty"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
}

// UsersResponse represents the response for the list users endpoint
type UsersResponse struct {
	Users []UserResponse `json:"users"`
	Total int            `json:"total"`
	Page  int            `json:"page"`
	Limit int            `json:"limit"`
}
