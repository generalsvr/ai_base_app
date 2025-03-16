package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/onlytwins/user-service/config"
	"github.com/onlytwins/user-service/handlers"
	"github.com/onlytwins/user-service/models"
	"github.com/onlytwins/user-service/repository"
	"go.uber.org/zap"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

func main() {
	// Initialize logger
	zapLogger, _ := zap.NewProduction()
	defer zapLogger.Sync()

	// Load configuration
	cfg, err := config.LoadConfig()
	if err != nil {
		zapLogger.Fatal("Failed to load configuration", zap.Error(err))
	}

	// Configure GORM logger
	gormLogger := logger.New(
		&zapAdapter{zapLogger},
		logger.Config{
			SlowThreshold:             time.Second,
			LogLevel:                  logger.Info,
			IgnoreRecordNotFoundError: true,
			Colorful:                  false,
		},
	)

	// Connect to database using GORM
	db, err := gorm.Open(postgres.Open(cfg.Database.GetConnectionString()), &gorm.Config{
		Logger: gormLogger,
	})
	if err != nil {
		zapLogger.Fatal("Failed to connect to database", zap.Error(err))
	}

	// Get the underlying SQL DB to set connection pool settings
	sqlDB, err := db.DB()
	if err != nil {
		zapLogger.Fatal("Failed to get SQL DB", zap.Error(err))
	}

	// Set connection pool settings
	sqlDB.SetMaxIdleConns(10)
	sqlDB.SetMaxOpenConns(100)
	sqlDB.SetConnMaxLifetime(time.Hour)

	// Clean database approach - drop tables if exist and recreate
	// This is safer for development. For production, you'd want a proper migration strategy
	if err := db.Exec("DROP TABLE IF EXISTS user_preferences, sessions, users CASCADE").Error; err != nil {
		zapLogger.Error("Failed to drop tables", zap.Error(err))
		// Continue even if drop fails
	}

	// Auto migrate the schema
	if err := db.AutoMigrate(&models.User{}, &models.Session{}, &models.UserPreference{}, &models.APIKey{}); err != nil {
		zapLogger.Fatal("Failed to migrate database", zap.Error(err))
	}
	zapLogger.Info("Database migrated successfully")

	// Initialize repositories
	userRepo := repository.NewUserRepository(db)
	apiKeyRepo := repository.NewAPIKeyRepository(db)

	// Initialize handlers
	userHandler := handlers.NewUserHandler(userRepo, zapLogger)
	apiKeyHandler := handlers.NewAPIKeyHandler(apiKeyRepo, zapLogger)
	authHandler := handlers.NewAuthHandler(apiKeyRepo, userRepo)

	// Create router
	router := mux.NewRouter()

	// Register routes
	userHandler.RegisterRoutes(router)
	apiKeyHandler.RegisterRoutes(router, userRepo)
	authHandler.RegisterRoutes(router)

	// Add health check endpoint
	router.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	}).Methods("GET")

	// Start HTTP server
	srv := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Server.Port),
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Run server in a goroutine so that it doesn't block
	go func() {
		zapLogger.Info("Starting User Service server", zap.Int("port", cfg.Server.Port))
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			zapLogger.Fatal("Failed to start server", zap.Error(err))
		}
	}()

	// Wait for interrupt signal to gracefully shut down the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	zapLogger.Info("Shutting down server...")

	// Create a deadline to wait for
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Doesn't block if no connections, but will otherwise wait
	// until the timeout deadline.
	if err := srv.Shutdown(ctx); err != nil {
		zapLogger.Fatal("Server shutdown failed", zap.Error(err))
	}

	zapLogger.Info("Server gracefully stopped")
}

// zapAdapter adapts zap logger to gorm logger interface
type zapAdapter struct {
	*zap.Logger
}

func (z *zapAdapter) Printf(format string, args ...interface{}) {
	z.Info(fmt.Sprintf(format, args...))
}
