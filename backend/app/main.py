"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, history, sessions, websocket
from app.config import settings
from app.database import close_db, init_db
from app.services.scheduler_service import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for startup and shutdown."""
    # Startup
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")

    # Start scheduler for background tasks
    logger.info("Starting scheduler...")
    start_scheduler()

    yield

    # Shutdown
    logger.info("Stopping scheduler...")
    stop_scheduler()

    logger.info("Closing database connections...")
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title="Stupid Chat Bot API",
    description="A simple, straightforward AI-powered chat application",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(websocket.router)
app.include_router(history.router)
app.include_router(sessions.router)
app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Stupid Chat Bot API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "stupid-chat-bot"}
