package models

import (
	"time"
)

// Role represents a role in the system
type Role struct {
	ID          int       `json:"id" gorm:"primaryKey"`
	Name        string    `json:"name" gorm:"uniqueIndex;size:50;not null"`
	Description string    `json:"description,omitempty" gorm:"size:255"`
	CreatedAt   time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time `json:"updated_at" gorm:"autoUpdateTime"`
}

// TableName specifies the table name for Role
func (Role) TableName() string {
	return "roles"
}

// UserRole represents the many-to-many relationship between users and roles
type UserRole struct {
	UserID    int       `json:"user_id" gorm:"primaryKey"`
	RoleID    int       `json:"role_id" gorm:"primaryKey"`
	CreatedAt time.Time `json:"created_at" gorm:"autoCreateTime"`
	User      User      `json:"-" gorm:"foreignKey:UserID"`
	Role      Role      `json:"role" gorm:"foreignKey:RoleID"`
}

// TableName specifies the table name for UserRole
func (UserRole) TableName() string {
	return "user_roles"
}

// NewRole represents a role creation request
type NewRole struct {
	Name        string `json:"name" validate:"required,min=3,max=50"`
	Description string `json:"description,omitempty" validate:"omitempty,max=255"`
}

// UpdateRole represents a role update request
type UpdateRole struct {
	Name        *string `json:"name,omitempty" validate:"omitempty,min=3,max=50"`
	Description *string `json:"description,omitempty" validate:"omitempty,max=255"`
}

// RoleResponse represents the response with role information
type RoleResponse struct {
	ID          int       `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description,omitempty"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// UserRolesResponse represents the response for the list user roles endpoint
type UserRolesResponse struct {
	Roles []RoleResponse `json:"roles"`
	Total int            `json:"total"`
}
