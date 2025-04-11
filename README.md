# Django Docker Project

A modern Django web application with Docker support, complete development environment, and production-ready configuration.

## Features

- **Docker-based**: Full containerization for consistent development and deployment
- **PostgreSQL Database**: Robust data storage with PostgreSQL
- **Nginx**: Production-ready web server and reverse proxy
- **Gunicorn**: High-performance WSGI server
- **Redis & Celery**: Background task processing and caching
- **Code Quality Tools**: Black and Flake8 for consistent code style
- **Makefile Support**: Simple commands for common operations

## Prerequisites

- Docker Engine (20.10.x or higher)
- Docker Compose (v2.x or higher)
- Make (for Makefile support)

## Quick Start

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/django-docker-project.git
   cd django-docker-project
   ```

2. Start the development environment:
   ```bash
   make up
   ```

3. Create a new Django project (if not already created):
   ```bash
   make create-project
   ```

4. Run migrations and create superuser:
   ```bash
   make migrate
   make createsuperuser
   ```

5. Visit the application:
   - Web application: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

## Project Structure

```
django-docker-project/
├── .github/                # GitHub Actions workflows
├── core/                   # Django project root
├── apps/                   # Django applications
├── nginx/                  # Nginx configuration
│   ├── Dockerfile
│   └── nginx.conf
├── static/                 # Static files
├── media/                  # User uploaded content
├── .flake8                 # Flake8 configuration
├── .gitignore
├── docker-compose.yml      # Development configuration
├── docker-compose.prod.yml # Production configuration
├── Dockerfile
├── Makefile                # Development commands
├── pyproject.toml          # Black configuration
├── README.md
└── requirements.txt        # Python dependencies
```

## Development

### Common Commands

```bash
# Start the development environment
make up

# Stop all containers
make down

# View logs
make logs

# Apply database migrations
make migrate

# Create a new Django app
make startapp  # You'll be prompted for the app name

# Run the Django shell
make django-shell

# Run tests
make test

# Format code with Black
make format

# Lint code with Flake8
make lint
```

For a complete list of available commands:
```bash
make help
```

### Adding Dependencies

1. Add the dependency to `requirements.txt`
2. Rebuild the containers:
   ```bash
   make down
   make build
   make up
   ```

## Code Quality

This project uses Black and Flake8 to enforce code quality standards:

- **Black**: Automatic code formatting
- **Flake8**: Code linting

To check your code:
```bash
make lint-all  # Runs both formatting and linting
```

## Production Deployment

1. Configure environment variables in a `.env.prod` file
2. Build and start the production environment:
   ```bash
   make prod-build
   make prod-up
   ```

### Production Configuration

The production setup includes:
- Nginx for serving static files and as a reverse proxy
- Gunicorn as the WSGI application server
- PostgreSQL database with volume persistence
- Redis for caching and Celery broker

## Database Management

```bash
# Create a database backup
make backup

# Restore from a backup
make restore  # You'll be prompted for the backup file
```

## Celery Tasks

If you're using Celery for background tasks:

```bash
# Start a Celery worker
make celery-worker

# Start Celery beat scheduler
make celery-beat
```

## Docker Volume Management

Data persistence is handled through Docker volumes:

- `postgres_data`: Database files
- `static_volume`: Collected static files (production)
- `media_volume`: User-uploaded media (production)
- `redis_data`: Redis data (if using Redis)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.