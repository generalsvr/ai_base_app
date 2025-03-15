# OnlyTwins Base Application

A scalable microservices architecture built with Go, providing a foundation for future projects. The application consists of three main services:

1. User Service - Handles user management and authentication
2. AI Service - Provides AI capabilities using OpenAI's API
3. API Gateway - Routes requests to appropriate services

## Features

### User Service
- User CRUD operations
- Role-based access control
- Authentication and authorization
- Session management
- User preferences

### AI Service
- Text completion using OpenAI's GPT models
- Text embedding generation
- Semantic similarity search
- Vector database integration
- Support for multiple AI providers (OpenAI, Groq, Zyphra)

## Prerequisites

- Go 1.21 or later
- Docker and Docker Compose
- OpenAI API key

## Getting Started

1. Start the services:
```bash
docker-compose up -d
```

The services will be available at:
- API Gateway: http://localhost:8080
- User Service: http://localhost:8081
- AI Service: http://localhost:8082

## API Documentation

### User Service API

#### Authentication
- `POST /api/v1/login` - Login user
- `POST /api/v1/logout` - Logout user
- `POST /api/v1/verify-token` - Verify authentication token

#### Users
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

#### Roles
- `GET /api/v1/roles` - List roles
- `POST /api/v1/roles` - Create role
- `GET /api/v1/roles/{id}` - Get role
- `PUT /api/v1/roles/{id}` - Update role
- `DELETE /api/v1/roles/{id}` - Delete role
- `GET /api/v1/users/{id}/roles` - Get user roles
- `PUT /api/v1/users/{id}/roles` - Assign roles to user

### AI Service API

#### Completions
- `POST /api/v1/completions` - Generate text completion
- `POST /api/v1/completions/stream` - Generate streaming text completion

#### Embeddings
- `POST /api/v1/embeddings` - Create embedding
- `GET /api/v1/embeddings/{id}` - Get embedding
- `DELETE /api/v1/embeddings/{id}` - Delete embedding
- `POST /api/v1/similarity` - Find similar embeddings

#### Image Processing
- `POST /api/v1/images` - Process images from URL, base64, or file upload (supports both JSON and multipart form data)

#### Audio Transcription
- `POST /api/v1/audio/transcribe` - Transcribe audio file

#### Text-to-Speech (TTS)
- `POST /api/v1/tts/synthesize` - Convert text to speech
- `POST /api/v1/tts/clone-voice` - Convert text to speech with voice cloning
- `POST /api/v1/tts/emotion` - Convert text to speech with emotion control

## API Gateway Authentication

The API Gateway now requires authentication for all endpoints (except `/health`) using a Bearer token. This ensures that only authorized clients can access your microservices.

### How to authenticate

1. Include an `Authorization` header with a Bearer token in all your requests:

```
Authorization: Bearer your-api-secret-key
```

2. The token value should match the `API_SECRET_KEY` environment variable set in the API Gateway service.

3. By default, the `API_SECRET_KEY` is set to `your-api-secret-key-change-me-in-production` in docker-compose.yml.

4. For production, set a strong, unique value for `API_SECRET_KEY` as an environment variable:

```bash
export API_SECRET_KEY="your-strong-unique-secret-key"
docker-compose up -d
```

### Example authenticated request

```bash
curl -X POST \
  http://localhost:8080/api/v1/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer your-api-secret-key' \
  -d '{
    "prompt": "Hello, world!",
    "provider": "openai"
  }'
```

## New AI Service Providers

The API Gateway now supports the following AI service providers:

### Groq Provider

Access Groq's LLM capabilities through these endpoints:

- **Text Completions**: `/api/v1/completions` with `"provider": "groq"`
- **Audio Transcription**: `/api/v1/audio/transcribe` with `"provider": "groq"`

### Zyphra Provider (TTS)

Access Zyphra's Text-to-Speech capabilities through these endpoints:

- **Basic TTS**: `/api/v1/tts/synthesize`
- **Voice Cloning**: `/api/v1/tts/clone-voice`
- **TTS with Emotion Control**: `/api/v1/tts/emotion`

#### Example Zyphra TTS request

```bash
curl -X POST \
  http://localhost:8080/api/v1/tts/synthesize \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer your-api-secret-key' \
  -d '{
    "text": "Hello, this is a test of the text to speech synthesis API.",
    "speaking_rate": 15.0,
    "language_iso_code": "en-us",
    "mime_type": "audio/mp3"
  }' \
  --output output.mp3
```

## Development

### Project Structure

```
.
├── api-gateway/        # API Gateway service
├── user-service/       # User management service
├── ai-service/         # AI capabilities service
└── docker-compose.yml  # Docker Compose configuration
```

### Adding New Services

1. Create a new service directory
2. Implement the service using the same patterns as existing services
3. Add the service to docker-compose.yml
4. Update the API Gateway to route requests to the new service

### Database Migrations

The services use GORM for database management. Migrations are automatically run when the services start.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
