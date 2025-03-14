# Analytics Service

A microservice for tracking and analyzing user activities and AI operations in the OnlyTwins application.

## Features

- Track user activities (logins, registrations, etc.)
- Monitor AI service usage and performance
- Provide statistical data for dashboards
- Generate daily/weekly/monthly reports

## API Endpoints

### User Statistics

- `POST /api/v1/user-activity` - Log user activity
- `GET /api/v1/user-stats` - Get user statistics
- `GET /api/v1/user-stats/active` - Get active users
- `GET /api/v1/user-stats/total` - Get total users count

### AI Statistics

- `POST /api/v1/ai-call` - Log AI API call
- `GET /api/v1/ai-stats` - Get AI usage statistics
- `GET /api/v1/ai-stats/models` - Get model usage breakdown

### Aggregated Statistics

- `GET /api/v1/stats/daily` - Get daily statistics
- `GET /api/v1/stats/summary` - Get statistics summary

### Dashboard

- `GET /api/v1/dashboard` - Get all dashboard data

### Utility Endpoints

- `GET /api/v1/health` - Health check endpoint
- `GET /api/v1/metrics` - Prometheus metrics endpoint

## Data Models

### User Statistics

```json
{
  "date": "2024-03-14",
  "logins": 120,
  "registrations": 15,
  "active_users": 85,
  "average_session_time": 320.5
}
```

### AI Statistics

```json
{
  "date": "2024-03-14",
  "total_api_calls": 450,
  "completion_calls": 320,
  "embedding_calls": 130,
  "error_count": 5,
  "average_response_time": 0.85,
  "tokens_used": 24500
}
```

## Usage Examples

### Log User Activity

```bash
curl -X POST http://localhost:8083/api/v1/user-activity \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "action": "login",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
  }'
```

### Log AI Call

```bash
curl -X POST http://localhost:8083/api/v1/ai-call \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "model_used": "gpt-4",
    "call_type": "completion",
    "response_time": 0.75,
    "tokens": 320,
    "success": true
  }'
```

### Get User Statistics

```bash
curl -X GET "http://localhost:8083/api/v1/user-stats?start=2024-03-01&end=2024-03-14"
```

### Get AI Statistics

```bash
curl -X GET "http://localhost:8083/api/v1/ai-stats?start=2024-03-01&end=2024-03-14"
```

## Development

### Requirements

- Go 1.21 or higher
- PostgreSQL 17

### Setup

1. Install dependencies:
   ```
   go mod download
   ```

2. Build the service:
   ```
   go build -o analytics-service
   ```

3. Run the service:
   ```
   ./analytics-service
   ```

### Configuration

Environment variables:

- `SERVER_PORT` - Server port (default: 8083)
- `DB_HOST` - Database host (default: analytics-db)
- `DB_PORT` - Database port (default: 5432)
- `DB_USER` - Database user (default: postgres)
- `DB_PASSWORD` - Database password (default: postgres)
- `DB_NAME` - Database name (default: analytics_db)
- `LOG_LEVEL` - Logging level (default: info)
- `ENABLE_DETAILED_LOGS` - Enable detailed logs (default: true)

## Integration

To integrate with this service, other services need to:

1. Send user activity events to `/api/v1/user-activity`
2. Send AI call events to `/api/v1/ai-call`
3. Retrieve statistics as needed through the GET endpoints 