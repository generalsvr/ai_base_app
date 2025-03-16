package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/spf13/viper"
	"go.uber.org/zap"
)

// Config holds all configuration for the API Gateway
type Config struct {
	Port                string `mapstructure:"PORT"`
	UserServiceURL      string `mapstructure:"USER_SERVICE_URL"`
	AIServiceURL        string `mapstructure:"AI_SERVICE_URL"`
	AnalyticsServiceURL string `mapstructure:"ANALYTICS_SERVICE_URL"`
	APISecretKey        string `mapstructure:"API_SECRET_KEY"`
}

// loadConfig loads configuration from environment variables
func loadConfig() (*Config, error) {
	viper.AutomaticEnv()

	// Set default values
	viper.SetDefault("PORT", "8080")
	viper.SetDefault("USER_SERVICE_URL", "http://user-service:8081")
	viper.SetDefault("AI_SERVICE_URL", "http://ai-service:8082")
	viper.SetDefault("ANALYTICS_SERVICE_URL", "http://analytics-service:8083")
	viper.SetDefault("API_SECRET_KEY", "your-api-secret-key-change-me-in-production")

	config := &Config{}
	if err := viper.Unmarshal(config); err != nil {
		return nil, err
	}

	return config, nil
}

// authMiddleware authenticates API requests using either Bearer token or API key
func authMiddleware(secretKey string, userServiceURL string, logger *zap.Logger) mux.MiddlewareFunc {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip auth for health check
			if r.URL.Path == "/health" {
				next.ServeHTTP(w, r)
				return
			}

			// Skip auth for login and user creation
			if r.URL.Path == "/api/v1/login" || (r.URL.Path == "/api/v1/users" && r.Method == "POST") {
				next.ServeHTTP(w, r)
				return
			}

			// First, check for API key in X-API-Key header
			apiKey := r.Header.Get("X-API-Key")
			if apiKey != "" {
				// Validate the API key with the user service
				valid, userData := validateAPIKey(apiKey, userServiceURL, logger)
				if valid {
					// Add user info to request context for downstream services
					ctx := context.WithValue(r.Context(), "user", userData)
					next.ServeHTTP(w, r.WithContext(ctx))
					return
				}

				logger.Warn("Invalid API key")
				http.Error(w, "Unauthorized: Invalid API key", http.StatusUnauthorized)
				return
			}

			// If no API key, check Bearer token format
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" || !strings.HasPrefix(authHeader, "Bearer ") {
				logger.Warn("Missing or invalid Authorization header")
				http.Error(w, "Unauthorized: Missing or invalid Authorization header", http.StatusUnauthorized)
				return
			}

			// Extract token
			token := strings.TrimPrefix(authHeader, "Bearer ")
			if token == "" {
				logger.Warn("Empty token")
				http.Error(w, "Unauthorized: Empty token", http.StatusUnauthorized)
				return
			}

			// If token matches API secret key, allow access (for direct API access)
			if token == secretKey {
				next.ServeHTTP(w, r)
				return
			}

			// Otherwise, verify token with user service
			client := &http.Client{Timeout: 5 * time.Second}
			verifyReq, err := http.NewRequest("POST", userServiceURL+"/api/v1/verify-token", nil)
			if err != nil {
				logger.Error("Failed to create token verification request", zap.Error(err))
				http.Error(w, "Internal server error", http.StatusInternalServerError)
				return
			}

			// Forward the token to the user service
			verifyReq.Header.Set("Authorization", authHeader)

			resp, err := client.Do(verifyReq)
			if err != nil {
				logger.Error("Failed to verify token with user service", zap.Error(err))
				http.Error(w, "Internal server error", http.StatusInternalServerError)
				return
			}
			defer resp.Body.Close()

			if resp.StatusCode != http.StatusOK {
				logger.Warn("Invalid token", zap.Int("status", resp.StatusCode))
				http.Error(w, "Unauthorized: Invalid token", http.StatusUnauthorized)
				return
			}

			// Token is valid, proceed with the request
			next.ServeHTTP(w, r)
		})
	}
}

// validateAPIKey validates an API key with the user service
func validateAPIKey(apiKey string, userServiceURL string, logger *zap.Logger) (bool, map[string]interface{}) {
	client := &http.Client{Timeout: 5 * time.Second}

	// Create the request body
	reqBody, err := json.Marshal(map[string]string{
		"api_key": apiKey,
	})
	if err != nil {
		logger.Error("Failed to marshal API key validation request", zap.Error(err))
		return false, nil
	}

	// Create the request
	req, err := http.NewRequest("POST", userServiceURL+"/api/auth/validate-key", bytes.NewBuffer(reqBody))
	if err != nil {
		logger.Error("Failed to create API key validation request", zap.Error(err))
		return false, nil
	}

	req.Header.Set("Content-Type", "application/json")

	// Send the request
	resp, err := client.Do(req)
	if err != nil {
		logger.Error("Failed to validate API key with user service", zap.Error(err))
		return false, nil
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode != http.StatusOK {
		logger.Warn("API key validation failed", zap.Int("status", resp.StatusCode))
		return false, nil
	}

	// Parse response
	var validationResponse struct {
		Valid bool                   `json:"valid"`
		User  map[string]interface{} `json:"user"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&validationResponse); err != nil {
		logger.Error("Failed to decode API key validation response", zap.Error(err))
		return false, nil
	}

	return validationResponse.Valid, validationResponse.User
}

func main() {
	// Configure logger
	logger, err := zap.NewProduction()
	if err != nil {
		fmt.Printf("Failed to create logger: %v\n", err)
		os.Exit(1)
	}
	defer logger.Sync()

	// Load configuration
	config, err := loadConfig()
	if err != nil {
		logger.Fatal("Failed to load configuration", zap.Error(err))
	}

	// Set up router
	r := mux.NewRouter()

	// Health check endpoint
	r.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("OK"))
	}).Methods("GET")

	// API routes with authentication
	api := r.PathPrefix("/api/v1").Subrouter()
	api.Use(authMiddleware(config.APISecretKey, config.UserServiceURL, logger))

	// User service routes
	api.PathPrefix("/users").Handler(createProxyHandler(config.UserServiceURL, logger))
	api.PathPrefix("/login").Handler(createProxyHandler(config.UserServiceURL, logger))
	api.PathPrefix("/logout").Handler(createProxyHandler(config.UserServiceURL, logger))
	api.PathPrefix("/verify-token").Handler(createProxyHandler(config.UserServiceURL, logger))
	api.PathPrefix("/keys").Handler(createProxyHandler(config.UserServiceURL, logger))

	// AI service routes
	api.PathPrefix("/completions").Handler(createProxyHandler(config.AIServiceURL, logger))
	api.PathPrefix("/embeddings").Handler(createProxyHandler(config.AIServiceURL, logger))
	api.PathPrefix("/similarity").Handler(createProxyHandler(config.AIServiceURL, logger))
	api.PathPrefix("/images").Handler(createProxyHandler(config.AIServiceURL, logger))
	api.PathPrefix("/audio").Handler(createProxyHandler(config.AIServiceURL, logger))
	api.PathPrefix("/tts").Handler(createProxyHandler(config.AIServiceURL, logger))

	// Analytics service routes
	api.PathPrefix("/analytics").Handler(createProxyHandler(config.AnalyticsServiceURL, logger))
	api.PathPrefix("/stats").Handler(createProxyHandler(config.AnalyticsServiceURL, logger))

	// Start HTTP server
	srv := &http.Server{
		Addr:         ":" + config.Port,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Run server in a goroutine so that it doesn't block
	go func() {
		logger.Info("Starting API Gateway server", zap.String("port", config.Port))
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal("Failed to start server", zap.Error(err))
		}
	}()

	// Wait for interrupt signal to gracefully shut down the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down server...")

	// Create a deadline to wait for
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Doesn't block if no connections, but will otherwise wait
	// until the timeout deadline.
	if err := srv.Shutdown(ctx); err != nil {
		logger.Fatal("Server shutdown failed", zap.Error(err))
	}

	logger.Info("Server gracefully stopped")
}

// createProxyHandler creates a reverse proxy handler for a target service
func createProxyHandler(targetURL string, logger *zap.Logger) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Create a new HTTP client
		client := &http.Client{
			Timeout: 30 * time.Second, // Increased timeout for image processing
		}

		// Construct the target URL
		url := fmt.Sprintf("%s%s", targetURL, r.URL.Path)
		if r.URL.RawQuery != "" {
			url = fmt.Sprintf("%s?%s", url, r.URL.RawQuery)
		}

		// Create a new request with the same body
		req, err := http.NewRequest(r.Method, url, r.Body)
		if err != nil {
			logger.Error("Failed to create request", zap.Error(err))
			http.Error(w, "Failed to create request to target service", http.StatusInternalServerError)
			return
		}

		// Copy all headers to preserve Content-Type, Content-Length, etc.
		for name, values := range r.Header {
			for _, value := range values {
				req.Header.Add(name, value)
			}
		}

		// If we have a user in the context (from API key auth), add user info to the request headers
		if userData, ok := r.Context().Value("user").(map[string]interface{}); ok {
			// Add user ID header for backend services
			if userID, ok := userData["id"]; ok {
				req.Header.Set("X-User-ID", fmt.Sprintf("%v", userID))
			}

			// Add username header for backend services
			if username, ok := userData["username"]; ok {
				req.Header.Set("X-Username", fmt.Sprintf("%v", username))
			}
		}

		// Special handling for paths related to image processing
		if strings.Contains(r.URL.Path, "/api/v1/images") {
			// Log additional information for debugging
			contentType := r.Header.Get("Content-Type")
			logger.Info("Processing image request",
				zap.String("path", r.URL.Path),
				zap.String("content-type", contentType),
				zap.String("method", r.Method))
		}

		// Execute the request
		resp, err := client.Do(req)
		if err != nil {
			logger.Error("Failed to forward request",
				zap.String("target", url),
				zap.String("method", r.Method),
				zap.Error(err))
			http.Error(w, fmt.Sprintf("Failed to forward request to %s: %v", targetURL, err), http.StatusBadGateway)
			return
		}
		defer resp.Body.Close()

		// Copy the response headers
		for name, values := range resp.Header {
			for _, value := range values {
				w.Header().Add(name, value)
			}
		}

		// Set the status code
		w.WriteHeader(resp.StatusCode)

		// Copy the response body
		limited := http.MaxBytesReader(w, resp.Body, 10*1024*1024) // Increased limit for larger responses
		_, err = io.Copy(w, limited)
		if err != nil {
			logger.Error("Failed to write response", zap.Error(err))
		}

		logger.Info("Proxied request",
			zap.String("method", r.Method),
			zap.String("path", r.URL.Path),
			zap.String("target", url),
			zap.Int("status", resp.StatusCode))
	}
}
