package middlewares

import (
	"context"
	"net/http"

	"github.com/onlytwins/user-service/repository"
)

// AuthMiddleware is a middleware that extracts and validates JWT tokens
// and sets the user ID in the request context.
func AuthMiddleware(userRepo *repository.UserRepository) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
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

			// Verify token and get user
			session, user, err := userRepo.GetSessionByToken(r.Context(), token)
			if err != nil {
				http.Error(w, "Invalid or expired token", http.StatusUnauthorized)
				return
			}

			// Check if session is valid
			if session == nil || !user.IsActive {
				http.Error(w, "Session expired or user inactive", http.StatusUnauthorized)
				return
			}

			// Set user ID in context
			ctx := context.WithValue(r.Context(), "userID", user.ID)

			// Call next handler with modified context
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
