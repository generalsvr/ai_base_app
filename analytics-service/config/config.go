package config

import (
	"log"

	"github.com/spf13/viper"
)

// Config holds all configuration for our application
type Config struct {
	ServerPort         string `mapstructure:"SERVER_PORT"`
	DBHost             string `mapstructure:"DB_HOST"`
	DBPort             string `mapstructure:"DB_PORT"`
	DBUser             string `mapstructure:"DB_USER"`
	DBPassword         string `mapstructure:"DB_PASSWORD"`
	DBName             string `mapstructure:"DB_NAME"`
	LogLevel           string `mapstructure:"LOG_LEVEL"`
	EnableDetailedLogs bool   `mapstructure:"ENABLE_DETAILED_LOGS"`
}

// LoadConfig reads the configuration from environment variables
func LoadConfig() (config Config, err error) {
	viper.AutomaticEnv()

	// Set default values
	viper.SetDefault("SERVER_PORT", "8083")
	viper.SetDefault("DB_HOST", "analytics-db")
	viper.SetDefault("DB_PORT", "5432")
	viper.SetDefault("DB_USER", "postgres")
	viper.SetDefault("DB_PASSWORD", "postgres")
	viper.SetDefault("DB_NAME", "analytics_db")
	viper.SetDefault("LOG_LEVEL", "info")
	viper.SetDefault("ENABLE_DETAILED_LOGS", true)

	err = viper.Unmarshal(&config)
	if err != nil {
		log.Printf("Unable to decode config into struct: %v", err)
		return
	}

	return
}
