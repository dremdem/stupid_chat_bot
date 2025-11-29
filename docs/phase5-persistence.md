# Phase 5: Persistence & History Implementation Plan

## Overview

This document outlines the implementation strategy for adding persistent storage to the Stupid Chat Bot. The goal is to save chat messages to a database and provide history retrieval functionality while maintaining the application's simplicity philosophy.

## 🎯 Simplified Approach (Based on Review Feedback)

**Key Decision: ONE GLOBAL SESSION FOR ALL USERS**

After review, we're taking a "supersimple" approach for Phase 5:

### What We're Building:
- ✅ **Single shared chat session** for all users
- ✅ **Message persistence** to database
- ✅ **Message history loading** on app start
- ✅ **No session management complexity**

### What We're NOT Building:
- ❌ Multiple sessions per user
- ❌ Session creation/deletion REST APIs
- ❌ Session list UI
- ❌ Session switching

### Why This Approach?
1. **Simplicity**: Maintains "stupid chat bot" philosophy
2. **No UX changes**: Users don't see any difference
3. **Gets persistence**: Messages survive server restarts
4. **Easy upgrade path**: Can add multi-session in Phase 6

### Implementation Impact:
- **Database**: Still need both tables (sessions + messages)
- **REST API**: ❌ Skip session management endpoints
- **WebSocket**: Stays at `/ws/chat` (no session_id in URL)
- **Frontend**: ❌ No changes needed
- **Backend**: Auto-create/load default session on startup

This means ~40% less code to write and maintain!

## Technology Stack

### Database: SQLite
**Why SQLite?**
- **Zero configuration**: No separate database server required
- **File-based**: Perfect for development and simple deployments
- **ACID compliant**: Reliable transaction support
- **Lightweight**: Minimal resource overhead
- **Python native support**: Excellent integration with Python ecosystem
- **Easy migration path**: Can migrate to PostgreSQL later if needed

**Trade-offs:**
- ✅ Perfect for single-server deployments
- ✅ Great for development and testing
- ✅ No authentication/connection management complexity
- ⚠️ Not ideal for high-concurrency write scenarios
- ⚠️ Limited horizontal scalability (but acceptable for our use case)

### ORM: SQLAlchemy 2.0
**Why SQLAlchemy?**
- **Industry standard**: Mature, well-documented Python ORM
- **Type safety**: Excellent support for Python type hints
- **Async support**: Native async/await with SQLAlchemy 2.0+
- **Migration tools**: Alembic integration for schema migrations
- **Flexibility**: Can switch to PostgreSQL without code changes
- **Query builder**: Powerful and intuitive query API

## Database Schema Design

### Entity-Relationship Model

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   ChatSession   │────────<│     Message      │>────────│   MessageType   │
└─────────────────┘         └──────────────────┘         └─────────────────┘
         │                           │                            │
         │                           │                    ┌───────┴────────┐
         │                           │                    │ - user         │
         │                           │                    │ - assistant    │
         │                           │                    │ - system       │
         │                           │                    └────────────────┘
         │                           │
    ┌────┴─────┐              ┌─────┴──────┐
    │ id       │              │ id         │
    │ title    │              │ session_id │
    │ created  │              │ content    │
    │ updated  │              │ sender     │
    │ metadata │              │ msg_type   │
    └──────────┘              │ timestamp  │
                              │ metadata   │
                              └────────────┘
```

### Tables

#### 1. `chat_sessions` - Chat conversation sessions

| Column       | Type         | Constraints           | Description                              |
|--------------|--------------|----------------------|------------------------------------------|
| id           | UUID         | PRIMARY KEY          | Unique session identifier                |
| title        | VARCHAR(255) | NOT NULL             | Session title (auto-generated or custom) |
| created_at   | TIMESTAMP    | NOT NULL, DEFAULT NOW| When the session was created             |
| updated_at   | TIMESTAMP    | NOT NULL, DEFAULT NOW| Last activity in the session             |
| metadata     | JSON         | NULLABLE             | Flexible metadata storage                |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `created_at` (for sorting/pagination)
- INDEX on `updated_at` (for recent sessions)

**Design Notes:**
- UUID for globally unique identifiers
- `title` can be auto-generated from first message or set explicitly
- `metadata` allows storing additional session info without schema changes
  - Examples: theme preferences, user preferences, tags, etc.

#### 2. `messages` - Individual chat messages

| Column       | Type         | Constraints              | Description                           |
|--------------|--------------|--------------------------|---------------------------------------|
| id           | UUID         | PRIMARY KEY              | Unique message identifier             |
| session_id   | UUID         | FOREIGN KEY, NOT NULL    | Reference to chat_sessions.id         |
| content      | TEXT         | NOT NULL                 | Message content                       |
| sender       | VARCHAR(50)  | NOT NULL                 | Sender identifier (user/assistant)    |
| message_type | VARCHAR(20)  | NOT NULL, DEFAULT 'message' | Type: message, system, typing, etc. |
| timestamp    | TIMESTAMP    | NOT NULL, DEFAULT NOW    | When the message was created          |
| metadata     | JSON         | NULLABLE                 | Flexible metadata (reactions, edits)  |

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `session_id` REFERENCES `chat_sessions(id)` ON DELETE CASCADE
- INDEX on `(session_id, timestamp)` (for efficient message retrieval)
- INDEX on `timestamp` (for global timeline queries)

**Design Notes:**
- `sender` values: 'user', 'assistant', 'system'
- `message_type` values: 'message', 'system', 'typing', 'ai_stream', etc.
- CASCADE delete ensures messages are removed when session is deleted
- `metadata` can store:
  - Reactions/emoji
  - Edit history
  - Message versions
  - Streaming state
  - Model/provider information

### Schema Rationale

**Why this design?**

1. **Simplicity**: Two tables cover all current and near-future needs
2. **Flexibility**: JSON metadata fields allow evolution without migrations
3. **Performance**: Proper indexing for common query patterns
4. **Scalability**: Session-based partitioning enables future optimizations
5. **Clean relationships**: One-to-many relationship is straightforward

**Alternative designs considered:**

❌ **Single table (messages only)**
- Pro: Even simpler
- Con: No way to group conversations or manage multiple chats
- Con: Difficult to implement session list UI

❌ **Separate users table**
- Pro: Better for authenticated multi-user scenarios
- Con: Over-engineering for current "stupid chat bot" philosophy
- Con: No authentication in current design
- Decision: Can be added later if authentication is implemented

❌ **Separate message_types table**
- Pro: Enforces type constraints
- Con: Over-engineering for limited set of types
- Con: CHECK constraint on ENUM is sufficient

## SQLAlchemy Models

### File Structure

```
backend/app/
├── models/
│   ├── __init__.py           # Export all models
│   ├── base.py               # Base class and common mixins
│   ├── session.py            # ChatSession model
│   └── message.py            # Message model
├── database.py               # Database connection and session management
└── ...
```

### Model Design

#### Base Model (`models/base.py`)

```python
"""Base models and mixins for SQLAlchemy."""
from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class UUIDMixin:
    """Mixin for UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
```

#### ChatSession Model (`models/session.py`)

```python
"""ChatSession model for managing conversation sessions."""
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .message import Message


class ChatSession(Base, UUIDMixin, TimestampMixin):
    """Represents a chat conversation session."""

    __tablename__ = "chat_sessions"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.timestamp"
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, title='{self.title}')>"
```

#### Message Model (`models/message.py`)

```python
"""Message model for individual chat messages."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin

if TYPE_CHECKING:
    from .session import ChatSession


class Message(Base, UUIDMixin):
    """Represents a single message in a chat session."""

    __tablename__ = "messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sender: Mapped[str] = mapped_column(String(50), nullable=False)
    message_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="message"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, sender='{self.sender}', type='{self.message_type}')>"
```

### Database Connection (`database.py`)

```python
"""Database connection and session management."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.models.base import Base

# Create async engine
# SQLite async driver: aiosqlite
DATABASE_URL = f"sqlite+aiosqlite:///{settings.database_path}"

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,  # Log SQL in debug mode
    future=True,
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions.

    Usage in FastAPI endpoints:
        @app.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose of the database engine."""
    await engine.dispose()
```

## Repository Pattern (Data Access Layer)

To keep business logic separate from database operations, we'll use the Repository pattern.

### Repository Structure

```
backend/app/
├── repositories/
│   ├── __init__.py
│   ├── base.py              # Base repository with common CRUD operations
│   ├── session_repository.py
│   └── message_repository.py
```

### Base Repository (`repositories/base.py`)

```python
"""Base repository with common CRUD operations."""
from typing import Generic, TypeVar, Type, Optional, List
import uuid

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository providing common database operations."""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        """Get a single record by ID."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[ModelType]:
        """Get all records with pagination."""
        result = await self.db.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(
        self,
        id: uuid.UUID,
        **kwargs
    ) -> Optional[ModelType]:
        """Update a record by ID."""
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            setattr(instance, key, value)

        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: uuid.UUID) -> bool:
        """Delete a record by ID."""
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0
```

### Session Repository (`repositories/session_repository.py`)

```python
"""Repository for ChatSession operations."""
from typing import Optional, List
from datetime import datetime
import uuid

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import ChatSession
from app.models.message import Message
from .base import BaseRepository


class SessionRepository(BaseRepository[ChatSession]):
    """Repository for ChatSession-specific operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(ChatSession, db)

    async def get_with_messages(
        self,
        session_id: uuid.UUID
    ) -> Optional[ChatSession]:
        """Get session with all messages loaded."""
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .options(selectinload(ChatSession.messages))
        )
        return result.scalar_one_or_none()

    async def get_recent_sessions(
        self,
        limit: int = 20
    ) -> List[ChatSession]:
        """Get most recently updated sessions."""
        result = await self.db.execute(
            select(ChatSession)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_sessions(
        self,
        query: str,
        limit: int = 20
    ) -> List[ChatSession]:
        """Search sessions by title."""
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.title.ilike(f"%{query}%"))
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_with_title(
        self,
        first_message: str = "",
        title: Optional[str] = None
    ) -> ChatSession:
        """Create a new session with auto-generated or custom title."""
        if not title:
            # Auto-generate title from first message
            title = self._generate_title(first_message)

        return await self.create(title=title)

    def _generate_title(self, message: str) -> str:
        """Generate a session title from the first message."""
        # Take first 50 chars or until first newline
        title = message.split('\n')[0][:50]
        if not title.strip():
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        return title.strip()
```

### Message Repository (`repositories/message_repository.py`)

```python
"""Repository for Message operations."""
from typing import List, Optional
from datetime import datetime
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from .base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for Message-specific operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Message, db)

    async def get_session_messages(
        self,
        session_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        before: Optional[datetime] = None
    ) -> List[Message]:
        """Get messages for a session with pagination."""
        query = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.timestamp.asc())
        )

        if before:
            query = query.where(Message.timestamp < before)

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent_context(
        self,
        session_id: uuid.UUID,
        message_count: int = 10
    ) -> List[Message]:
        """Get the most recent N messages for context."""
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .where(Message.message_type == "message")  # Exclude system messages
            .order_by(Message.timestamp.desc())
            .limit(message_count)
        )
        messages = list(result.scalars().all())
        return list(reversed(messages))  # Return in chronological order

    async def create_message(
        self,
        session_id: uuid.UUID,
        content: str,
        sender: str,
        message_type: str = "message",
        metadata: Optional[dict] = None
    ) -> Message:
        """Create a new message in a session."""
        return await self.create(
            session_id=session_id,
            content=content,
            sender=sender,
            message_type=message_type,
            metadata=metadata
        )

    async def count_session_messages(
        self,
        session_id: uuid.UUID
    ) -> int:
        """Count total messages in a session."""
        result = await self.db.execute(
            select(func.count(Message.id))
            .where(Message.session_id == session_id)
        )
        return result.scalar_one()
```

## API Endpoints

### Simplified API Design (No Session Management)

**Decision: Skip REST API for session management**

In the simplified Phase 5 approach, we're NOT creating session management endpoints. The single global session is managed internally by the backend.

### What We're NOT Building:
```
❌ GET    /api/sessions                    # Skip - only one session
❌ POST   /api/sessions                    # Skip - auto-created
❌ GET    /api/sessions/{session_id}       # Skip - not needed
❌ DELETE /api/sessions/{session_id}       # Skip - can't delete default
❌ GET    /api/sessions/{session_id}/messages  # Skip - use WebSocket
❌ POST   /api/sessions/{session_id}/messages  # Skip - use WebSocket
```

### What We ARE Building:
- WebSocket endpoint remains the same: `/ws/chat`
- Messages are persisted automatically
- History is loaded on connection
- No API endpoints needed!

### API Router Structure

```
backend/app/
├── api/
│   ├── __init__.py
│   ├── websocket.py          # Updated: Add database persistence
│   └── dependencies.py       # Shared dependencies (database session)
```

### Why Skip REST API?
1. **Simplicity**: No extra code to write/maintain
2. **No frontend changes**: Current UI works as-is
3. **Single session**: No need for CRUD operations
4. **WebSocket handles everything**: Real-time messaging + persistence

### Future Phase 6 Consideration:
When we add multi-session support, we can add REST endpoints then. For now, keep it simple!

### ~~Example Endpoints (`api/sessions.py`)~~ (SKIPPED IN PHASE 5)

```python
"""API endpoints for session and message management."""
from typing import List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# Pydantic schemas
class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    content: str
    sender: str
    message_type: str
    timestamp: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str
    sender: str
    message_type: str = "message"


# Endpoints
@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List recent chat sessions."""
    repo = SessionRepository(db)
    sessions = await repo.get_recent_sessions(limit=limit)
    return sessions


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session."""
    repo = SessionRepository(db)
    session = await repo.create_with_title(title=session_data.title)
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific session."""
    repo = SessionRepository(db)
    session = await repo.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a session and all its messages."""
    repo = SessionRepository(db)
    deleted = await repo.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated messages for a session."""
    repo = MessageRepository(db)
    messages = await repo.get_session_messages(
        session_id=session_id,
        limit=limit,
        offset=offset
    )
    return messages
```

## Integration with WebSocket

### Modified WebSocket Handler

The WebSocket endpoint needs to be updated to:
1. Create/use a session ID
2. Save messages to the database
3. Load initial history when connecting

```python
# Pseudo-code for websocket.py modifications

@router.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    await manager.connect(websocket)

    # Load recent message history and send to client
    message_repo = MessageRepository(db)
    history = await message_repo.get_recent_context(session_id, limit=50)

    for msg in history:
        await websocket.send_json({
            "type": "message",
            "content": msg.content,
            "sender": msg.sender,
            "timestamp": msg.timestamp.isoformat()
        })

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Save user message to database
            user_msg = await message_repo.create_message(
                session_id=session_id,
                content=message_data["content"],
                sender=message_data.get("sender", "user"),
                message_type="message"
            )

            # Broadcast to all connected clients
            await manager.broadcast({...})

            # Generate AI response
            ai_response = ""
            async for chunk in ai_service.generate_response_stream(...):
                ai_response += chunk
                await manager.broadcast({...})

            # Save AI response to database
            await message_repo.create_message(
                session_id=session_id,
                content=ai_response,
                sender="assistant",
                message_type="message"
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

## Database Migrations

### Migration Strategy: Alembic

**Why Alembic?**
- Industry standard for SQLAlchemy migrations
- Version-controlled schema changes
- Automatic migration generation from model changes
- Rollback support
- Works with both SQLite and PostgreSQL

### Alembic Setup

```bash
# Install
pip install alembic

# Initialize in backend directory
cd backend
alembic init alembic

# Directory structure
backend/
├── alembic/
│   ├── versions/          # Migration scripts
│   ├── env.py            # Alembic environment config
│   ├── script.py.mako    # Template for migrations
│   └── README
├── alembic.ini           # Alembic configuration
```

### Configuration (`alembic/env.py`)

```python
"""Alembic environment configuration."""
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.models.base import Base
from app.config import settings

# Import all models to ensure they're registered
from app.models.session import ChatSession
from app.models.message import Message

# Alembic Config object
config = context.config

# Set SQLAlchemy URL from app settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata for autogenerate
target_metadata = Base.metadata

# ... rest of env.py
```

### Creating Initial Migration

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema: sessions and messages"

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Migration Workflow

1. **Make model changes** - Update SQLAlchemy models
2. **Generate migration** - `alembic revision --autogenerate -m "description"`
3. **Review migration** - Check generated file in `alembic/versions/`
4. **Test migration** - `alembic upgrade head` on test database
5. **Commit migration** - Add migration file to version control
6. **Deploy** - Run migrations on production: `alembic upgrade head`

## Configuration Updates

### Add to `backend/app/config.py`

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Database Configuration
    database_path: str = "data/chat.db"  # Relative to project root
    database_url: str = ""  # Computed property below
    debug: bool = False  # Enable SQL logging

    @property
    def database_url(self) -> str:
        """Get database URL for SQLAlchemy."""
        if self.database_url:
            return self.database_url
        return f"sqlite+aiosqlite:///{self.database_path}"
```

### Add to `requirements.txt`

```
# Existing dependencies...

# Database (Phase 5)
sqlalchemy[asyncio]==2.0.23
aiosqlite==0.19.0
alembic==1.13.0
```

## Implementation Phases (Simplified)

### Phase 5.1: Database Setup (Days 1-2)
- [ ] Install dependencies: SQLAlchemy, aiosqlite, alembic
- [ ] Create database configuration module (`database.py`)
- [ ] Create base models and mixins
- [ ] Set up async engine and session management
- [ ] Initialize Alembic for migrations
- [ ] Test database connection

### Phase 5.2: Models & Repositories (Days 2-3)
- [ ] Implement ChatSession model
- [ ] Implement Message model
- [ ] Create initial migration
- [ ] Implement base repository pattern
- [ ] Implement session repository (simple: get default session only)
- [ ] Implement message repository (create, get recent, get by session)
- [ ] Write unit tests for repositories

### Phase 5.3: WebSocket Integration (Days 3-4)
- [ ] Create helper: `get_or_create_default_session()`
- [ ] Update WebSocket handler to load default session on startup
- [ ] Integrate message persistence in WebSocket flow:
  - [ ] Save user messages to database
  - [ ] Save AI responses to database
  - [ ] Load recent history (last 50 messages) on connection
- [ ] Update ConnectionManager to load history from database
- [ ] Remove old in-memory-only conversation history code
- [ ] Test end-to-end persistence flow

### ~~Phase 5.4: API Endpoints~~ ❌ SKIPPED
**No REST API needed for single-session approach**

### ~~Phase 5.5: Frontend Integration~~ ❌ MINIMAL CHANGES
- [ ] ~~Add session management UI~~ (Not needed - single session)
- [ ] Test that existing UI works with persistence
- [ ] Verify messages persist across server restart
- [ ] Optional: Add "Clear History" button (future enhancement)

**Total Time Estimate: 4-5 days** (vs 7 days originally)

### Simplified Flow Summary:

```python
# On app startup
@app.on_event("startup")
async def startup():
    async with async_session_maker() as db:
        # Get or create the default session
        default_session = await get_or_create_default_session(db)
        logger.info(f"Using default session: {default_session.id}")

# In WebSocket handler
@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # Load default session
    async with async_session_maker() as db:
        default_session = await get_or_create_default_session(db)

        # Load recent history into memory
        message_repo = MessageRepository(db)
        recent_messages = await message_repo.get_recent(default_session.id, limit=50)
        manager.load_history(recent_messages)

    while True:
        # Receive message
        data = await websocket.receive_text()

        # Save to database
        async with async_session_maker() as db:
            message_repo = MessageRepository(db)
            await message_repo.create_message(
                session_id=default_session.id,
                content=data["content"],
                sender="user"
            )

        # Broadcast and generate AI response...
```

## Testing Strategy

### Unit Tests

```python
# Example: test_message_repository.py

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.repositories.message_repository import MessageRepository


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_message(db_session):
    """Test creating a message."""
    repo = MessageRepository(db_session)

    # Create a session first
    session_id = uuid.uuid4()

    message = await repo.create_message(
        session_id=session_id,
        content="Test message",
        sender="user"
    )

    assert message.id is not None
    assert message.content == "Test message"
    assert message.sender == "user"
```

### Integration Tests

```python
# Example: test_session_api.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_session():
    """Test creating a new session via API."""
    response = client.post("/api/sessions", json={"title": "Test Chat"})

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Chat"
    assert "id" in data


def test_get_session_messages():
    """Test retrieving messages for a session."""
    # Create session
    session_resp = client.post("/api/sessions", json={})
    session_id = session_resp.json()["id"]

    # Get messages (should be empty)
    response = client.get(f"/api/sessions/{session_id}/messages")

    assert response.status_code == 200
    assert response.json() == []
```

## Performance Considerations

### Indexing Strategy

1. **Primary Keys (UUID)**: B-tree index (automatic)
2. **Foreign Keys**: Indexed for JOIN performance
3. **Timestamp columns**: For sorting recent sessions/messages
4. **Composite index**: `(session_id, timestamp)` for message retrieval

### Query Optimization

1. **Pagination**: Always use LIMIT/OFFSET for large result sets
2. **Eager loading**: Use `selectinload()` to avoid N+1 queries
3. **Lazy loading**: Don't load messages unless needed
4. **Connection pooling**: Use SQLAlchemy's connection pool

### Scaling Considerations

**Current (Phase 5):**
- SQLite with single connection
- File-based storage
- Perfect for development and small deployments

**Future improvements:**
- **PostgreSQL migration**: Change connection string, no code changes
- **Connection pooling**: Already configured in SQLAlchemy
- **Read replicas**: Add read-only database for queries
- **Caching**: Redis for session cache
- **Partitioning**: Partition messages table by date

## Security Considerations

### SQL Injection Prevention
- ✅ **SQLAlchemy ORM**: Parameterized queries by default
- ✅ **Pydantic validation**: Input validation before database
- ✅ **Type safety**: Python type hints enforce correct types

### Data Privacy
- ⚠️ **No encryption at rest**: SQLite file is plain text
  - Future: SQLite encryption extension (SQLCipher)
- ⚠️ **No authentication**: Anyone can access any session
  - Future: User authentication + session ownership

### Access Control
- Current: No access control (public chat)
- Future: User-based permissions, session ownership

## Error Handling

### Database Errors

```python
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

async def create_message_safe(repo, session_id, content, sender):
    """Create message with error handling."""
    try:
        return await repo.create_message(
            session_id=session_id,
            content=content,
            sender=sender
        )
    except IntegrityError as e:
        # Foreign key violation, session doesn't exist
        logger.error(f"Invalid session_id: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    except SQLAlchemyError as e:
        # General database error
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
```

### WebSocket Error Handling

- Network failures: Reconnect with session persistence
- Database unavailable: Queue messages in memory, retry
- Invalid session: Create new session automatically

## Monitoring & Observability

### Logging Strategy

```python
import logging

# Configure SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)  # SQL queries
logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)   # Connection pool

# Application logging
logger = logging.getLogger(__name__)

# Log slow queries
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # Log queries taking > 100ms
        logger.warning(f"Slow query ({total:.3f}s): {statement}")
```

### Metrics to Track

- Database connection pool size
- Query execution time
- Messages per session (average/max)
- Session creation rate
- Database file size growth

## Deployment Checklist

### Pre-deployment
- [ ] Run all migrations: `alembic upgrade head`
- [ ] Verify database file location and permissions
- [ ] Set up database backups
- [ ] Configure production database URL
- [ ] Test rollback procedures

### Post-deployment
- [ ] Monitor database file size
- [ ] Check query performance
- [ ] Verify migration status: `alembic current`
- [ ] Test backup restoration

## Future Enhancements

### Phase 6+ (Optional)

1. **PostgreSQL Migration**
   - Production-ready database
   - Better concurrency support
   - Advanced features (full-text search, JSON queries)

2. **Full-Text Search**
   - Search messages across all sessions
   - SQLite FTS5 or PostgreSQL full-text search

3. **Message Reactions & Metadata**
   - Emoji reactions stored in message.metadata
   - Message edit history
   - Message threading/replies

4. **Session Features**
   - Session sharing via public links
   - Session export (JSON, PDF)
   - Session templates
   - Session tags/categories

5. **Performance Optimizations**
   - Message archival (move old messages to archive table)
   - Database partitioning by date
   - Redis caching layer
   - Read replicas

## Conclusion

This implementation plan provides a solid foundation for adding persistence to the Stupid Chat Bot while maintaining its simplicity. The use of SQLite and SQLAlchemy allows for rapid development while keeping the migration path to PostgreSQL open for future scalability needs.

The repository pattern keeps the data access layer clean and testable, while the straightforward schema design ensures the database can evolve without major refactoring.

## References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [FastAPI Database](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [aiosqlite Documentation](https://aiosqlite.omnilib.dev/)
