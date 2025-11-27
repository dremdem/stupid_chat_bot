# Backend - Stupid Chat Bot

FastAPI backend for the Stupid Chat Bot application.

## Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── api/              # API route handlers
│   ├── services/         # Business logic and services
│   └── models/           # Data models and schemas
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variable template
├── Dockerfile           # Docker configuration
└── pyproject.toml       # Python project configuration
```

## Setup

1. Install dependencies:
```bash
uv pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

When the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

More endpoints will be added in Phase 2 (WebSocket) and Phase 3 (AI integration).

## Development

### Code Formatting
```bash
black .
```

### Linting
```bash
ruff check .
```
