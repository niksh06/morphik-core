#!/bin/bash

# Morphik Quick Start with Qdrant and UI
# This script sets up Morphik with Qdrant vector store and WebUI

set -e

echo "🚀 Starting Morphik with Qdrant and WebUI..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Copy Qdrant configuration if morphik.toml doesn't exist or user wants to use Qdrant
if [ ! -f "morphik.toml" ]; then
    echo "📋 No morphik.toml found. Copying Qdrant configuration..."
    cp morphik.qdrant.toml morphik.toml
    echo "✅ Qdrant configuration copied to morphik.toml"
elif grep -q 'provider = "pgvector"' morphik.toml; then
    echo "🔄 Current config uses pgvector. Would you like to switch to Qdrant? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "📋 Copying Qdrant configuration..."
        cp morphik.qdrant.toml morphik.toml
        echo "✅ Switched to Qdrant configuration"
    fi
fi

# Set up environment variables
echo "⚙️ Setting up environment variables..."
if [ ! -f ".env" ]; then
    echo "JWT_SECRET_KEY=your-secret-key-here" > .env
    echo "SESSION_SECRET_KEY=super-secret-session-key" >> .env
    echo "POSTGRES_URI=postgresql+asyncpg://morphik:morphik@postgres:5432/morphik" >> .env
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" >> .env
    echo "✅ Created .env file with default values"
fi

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker-compose pull

# Build and start services
echo "🐳 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."

# Wait for Postgres
echo "🔄 Waiting for PostgreSQL..."
timeout 60 bash -c "until docker-compose exec postgres pg_isready -U morphik; do sleep 2; done"

# Wait for Qdrant
echo "🔄 Waiting for Qdrant..."
timeout 60 bash -c "until curl -s http://localhost:6333/health > /dev/null; do sleep 2; done"

# Wait for Morphik API
echo "🔄 Waiting for Morphik API..."
timeout 120 bash -c "until curl -s http://localhost:8000/health > /dev/null; do sleep 2; done"

# Wait for UI
echo "🔄 Waiting for WebUI..."
timeout 60 bash -c "until curl -s http://localhost:3000 > /dev/null; do sleep 2; done"

echo ""
echo "🎉 Morphik is ready!"
echo ""
echo "📊 Available services:"
echo "  • Morphik API:      http://localhost:8000"
echo "  • WebUI:            http://localhost:3000"
echo "  • Qdrant API:       http://localhost:6333"
echo "  • Qdrant Dashboard: http://localhost:6333/dashboard"
echo "  • PostgreSQL:       localhost:5432"
echo "  • Redis:            localhost:6379"
echo ""
echo "🔍 Check service status:"
echo "  docker-compose ps"
echo ""
echo "📝 View logs:"
echo "  docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "  docker-compose down"
echo ""
echo "Happy exploring! 🚀"