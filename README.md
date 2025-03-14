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

#### Embeddings
- `POST /api/v1/embeddings` - Create embedding
- `GET /api/v1/embeddings/{id}` - Get embedding
- `DELETE /api/v1/embeddings/{id}` - Delete embedding
- `POST /api/v1/similarity` - Find similar embeddings

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
