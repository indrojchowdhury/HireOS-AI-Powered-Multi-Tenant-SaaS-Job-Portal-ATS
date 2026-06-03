# Docker Setup Guide for HireOS

## Overview
This Docker setup orchestrates the entire HireOS application with frontend, backend, database, Redis, and Celery services.

## Prerequisites
- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)

## Quick Start

### 1. Setup Environment Variables
Create a `.env` file in the `backend/` directory:
```bash
# backend/.env
DEBUG=False
SECRET_KEY=your-secret-key-here
DB_ENGINE=django.db.backends.postgresql
DB_NAME=hireos_db
DB_USER=postgres
DB_PASSWORD=admin
DB_HOST=db
DB_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 2. Build and Start Services
```bash
# From the root directory
docker-compose up --build
```

This will:
- Build the backend Docker image (Python 3.12)
- Build the frontend Docker image (Node 18-alpine)
- Start PostgreSQL database (port 5432)
- Start Redis broker (port 6379)
- Start Django backend (port 9000)
- Start React frontend (port 5173)
- Start Celery worker
- Start Celery Beat scheduler

### 3. Access the Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:9000
- Django Admin: http://localhost:9000/admin

## Service Details

### Frontend Service
- **Image**: Node 18-Alpine
- **Port**: 5173
- **Command**: Serves the production build using `serve`
- **Build**: Multi-stage build (builder + production)
- **Volumes**: Frontend source code mounted for development

### Backend Service
- **Image**: Python 3.12-slim
- **Port**: 9000
- **Command**: Runs Django development server + migrations
- **Volumes**: Backend source code and media files
- **Dependencies**: Requires db and redis services

### Database Service
- **Image**: PostgreSQL 15
- **Port**: 5432
- **Volume**: `postgres_data` (persistent storage)
- **Credentials**: postgres/admin (configure in .env)

### Redis Service
- **Image**: Redis latest
- **Port**: 6379
- **Used for**: Celery broker and result backend

### Celery Worker
- **Command**: `celery -A core worker --loglevel=info`
- **Purpose**: Processes background tasks

### Celery Beat
- **Command**: `celery -A core beat --loglevel=info`
- **Purpose**: Schedules periodic tasks

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop Services
```bash
docker-compose down
```

### Stop and Remove Volumes (Reset Database)
```bash
docker-compose down -v
```

### Rebuild Containers
```bash
docker-compose up --build
```

### Run Django Commands
```bash
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py shell
```

### Build Frontend Only
```bash
docker-compose build frontend
```

## Network
All services are connected via the `hireos_network` bridge network, allowing internal communication by service name (e.g., `backend:9000`, `redis:6379`).

## Development Notes
- Frontend volumes allow hot reloading during development
- Backend volumes allow code changes without rebuild (Python)
- Use `docker-compose logs -f` to monitor all services
- Database persists in `postgres_data` volume
- Media files persist in `media_data` volume

## Troubleshooting

### Port Already in Use
Change port mappings in `docker-compose.yml`:
```yaml
ports:
  - "5174:5173"  # Frontend on 5174 instead of 5173
```

### Database Connection Errors
Ensure backend .env file has correct DB_HOST:
```
DB_HOST=db  # Use service name, not localhost
```

### Frontend Can't Connect to Backend
Check API URL in frontend configuration. Should use:
```
http://backend:9000  # From within Docker network
```

### Clean Rebuild
```bash
docker-compose down -v
docker system prune -a
docker-compose up --build
```

## Production Considerations
- Replace `serve` with production web server (nginx, gunicorn)
- Use environment variables for sensitive data
- Enable HTTPS with reverse proxy
- Set DEBUG=False
- Configure allowed hosts in Django settings
- Use stronger database passwords
