FROM golang:1.22-alpine AS builder

WORKDIR /app

# Install git and required build dependencies
RUN apk add --no-cache git gcc musl-dev

# Copy the entire project
COPY . .

# Get all dependencies and create a proper go.sum
RUN go mod download
RUN go mod tidy

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o api-gateway .

FROM alpine:latest

WORKDIR /app

# Copy the binary from builder
COPY --from=builder /app/api-gateway .

# Expose port
EXPOSE 8080

# Command to run the executable
CMD ["./api-gateway"] 