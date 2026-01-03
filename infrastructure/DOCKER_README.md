# PearlFlow Docker Deployment

This document describes how to deploy PearlFlow using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

### 1. Build and Start All Services

```bash
# From the project root directory
docker-compose up -d --build
```

This will build and start:
- **PostgreSQL** (port 5432) - Database
- **Redis** (port 6379) - Cache & Session Management
- **API** (port 8000) - FastAPI backend
- **Demo Web** (port 3000) - Next.js frontend

### 2. Verify Services Are Running

```bash
# Check all containers
docker-compose ps

# View logs
docker-compose logs -f

# Health check API
curl http://localhost:8000/health
```

### 3. Access the Application

- **Demo Web**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

## Environment Configuration

### API Environment Variables

The API uses the following environment variables (set in docker-compose.yml):

```yaml
environment:
  DATABASE_URL: postgresql+asyncpg://pearlflow:pearlflow_password@postgres:5432/pearlflow_db
  REDIS_URL: redis://redis:6379
  SECRET_KEY: dev-secret-key-change-in-production
  ENVIRONMENT: production
```

### Production Deployment

For production, create a `.env.prod` file and update docker-compose.yml:

```yaml
# docker-compose.yml
api:
  environment:
    - DATABASE_URL=${PROD_DATABASE_URL}
    - REDIS_URL=${PROD_REDIS_URL}
    - SECRET_KEY=${PROD_SECRET_KEY}
    - ENVIRONMENT=production
```

## Service Architecture

```
┌─────────────────┐
│  Demo Web       │  (Port 3000)
│  Next.js App    │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  API            │  (Port 8000)
│  FastAPI        │
└────────┬────────┘
         │ SQL/Redis
         ▼
┌─────────────────┐     ┌─────────────────┐
│  PostgreSQL     │     │  Redis          │
│  Database       │     │  Cache          │
└─────────────────┘     └─────────────────┘
```

## Docker Images

### API Image
- **Base**: python:3.11-slim
- **Size**: ~200MB
- **User**: non-root (pearlflow)
- **Health Check**: /health endpoint

### Demo Web Image
- **Base**: node:20-alpine
- **Size**: ~150MB
- **User**: non-root (nextjs)
- **Health Check**: HTTP GET /

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Connect to PostgreSQL
docker-compose exec postgres psql -U pearlflow -d pearlflow_db
```

### API Not Starting
```bash
# Check API logs
docker-compose logs api

# Check if database is ready
docker-compose exec api python -c "from src.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### Frontend Not Connecting
```bash
# Check demo-web logs
docker-compose logs demo-web

# Verify API is accessible from demo-web
docker-compose exec demo-web wget -qO- http://api:8000/health
```

## Development vs Production

### Development
- Uses SQLite by default (in .env)
- Hot reload enabled
- Debug mode on

### Production
- Uses PostgreSQL (required)
- Redis for caching
- Debug mode off
- Proper secret keys required

## Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker image rm pearlflow-api pearlflow-demo-web
```

## Security Notes

1. **Change default passwords** in production
2. **Use strong SECRET_KEY** (generate with `openssl rand -hex 32`)
3. **Restrict CORS origins** in production
4. **Use HTTPS** for external access
5. **Enable firewall** on host machine

## Performance Tuning

### API
- Adjust `DATABASE_POOL_SIZE` based on concurrent users
- Increase `DATABASE_MAX_OVERFLOW` for burst traffic

### Database
- Add connection pooling with PgBouncer
- Set up read replicas for high availability

### Frontend
- Enable Next.js CDN caching
- Use reverse proxy (nginx/traefik) for SSL termination
