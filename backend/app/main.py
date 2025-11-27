"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import websocket

app = FastAPI(
    title="Stupid Chat Bot API",
    description="A simple, straightforward AI-powered chat application",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(websocket.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Stupid Chat Bot API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "stupid-chat-bot"}
