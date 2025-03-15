package main

import (
	"context"
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

// authMiddleware authenticates API requests using a Bearer token
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

			// Check Bearer token format
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

func main() {
	// Initialize logger
	logger, _ := zap.NewProduction()
	defer logger.Sync()

	// Load configuration
	config, err := loadConfig()
	if err != nil {
		logger.Fatal("Failed to load configuration", zap.Error(err))
	}

	// Create router
	router := mux.NewRouter()

	// Apply middleware
	router.Use(authMiddleware(config.APISecretKey, config.UserServiceURL, logger))

	// Health check endpoint
	router.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	}).Methods("GET")

	// User service routes
	router.PathPrefix("/api/v1/users").Handler(createProxyHandler(config.UserServiceURL, logger))
	router.HandleFunc("/api/v1/login", createProxyHandler(config.UserServiceURL, logger)).Methods("POST")
	router.HandleFunc("/api/v1/logout", createProxyHandler(config.UserServiceURL, logger)).Methods("POST")
	router.HandleFunc("/api/v1/verify-token", createProxyHandler(config.UserServiceURL, logger)).Methods("POST", "GET")

	// Analytics service routes
	router.PathPrefix("/api/v1/analytics").Handler(createProxyHandler(config.AnalyticsServiceURL, logger))

	// AI service routes - standard endpoints
	router.PathPrefix("/api/v1/completions").Handler(createProxyHandler(config.AIServiceURL, logger))
	router.PathPrefix("/api/v1/embeddings").Handler(createProxyHandler(config.AIServiceURL, logger))
	router.PathPrefix("/api/v1/similarity").Handler(createProxyHandler(config.AIServiceURL, logger))
	router.PathPrefix("/api/v1/images").Handler(createProxyHandler(config.AIServiceURL, logger))

	// AI service routes - Groq provider endpoints
	router.PathPrefix("/api/v1/audio/transcribe").Handler(createProxyHandler(config.AIServiceURL, logger))

	// AI service routes - Zyphra TTS provider endpoints
	router.PathPrefix("/api/v1/tts").Handler(createProxyHandler(config.AIServiceURL, logger))

	// Start HTTP server
	srv := &http.Server{
		Addr:         ":" + config.Port,
		Handler:      router,
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
			Timeout: 10 * time.Second,
		}

		// Construct the target URL
		url := fmt.Sprintf("%s%s", targetURL, r.URL.Path)
		if r.URL.RawQuery != "" {
			url = fmt.Sprintf("%s?%s", url, r.URL.RawQuery)
		}

		// Create a new request
		req, err := http.NewRequest(r.Method, url, r.Body)
		if err != nil {
			logger.Error("Failed to create request", zap.Error(err))
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		// Copy all headers
		for name, values := range r.Header {
			for _, value := range values {
				req.Header.Add(name, value)
			}
		}

		// Execute the request
		resp, err := client.Do(req)
		if err != nil {
			logger.Error("Failed to forward request",
				zap.String("target", url),
				zap.Error(err))
			w.WriteHeader(http.StatusBadGateway)
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
		limited := http.MaxBytesReader(w, resp.Body, 1048576)
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
