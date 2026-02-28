"""API test configuration and fixtures."""

import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.domain.entities.user import User
from app.domain.entities.vault import Vault
from app.infrastructure.database.connection import Base


# Use test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://obsidian:obsidian@localhost:5433/obsidian_test",
)


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine per test."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for API tests."""
    session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def clean_db(db_session: AsyncSession):
    """Clean database tables before each test."""
    tables = [
        "document_table_links",
        "table_relationships",
        "table_rows",
        "data_tables",
        "document_tags",
        "embedding_chunks",
        "document_links",
        "documents",
        "folders",
        "tags",
        "vaults",
        "users",
    ]
    for table in tables:
        try:
            await db_session.execute(text(f"DELETE FROM {table}"))
        except Exception:
            pass  # Table might not exist
    await db_session.commit()


@pytest_asyncio.fixture
async def mock_user(db_session: AsyncSession, clean_db) -> User:
    """Create mock authenticated user in database."""
    from app.infrastructure.database.repositories.user_repository import (
        PostgresUserRepository,
    )

    repo = PostgresUserRepository(db_session)

    user = User(
        email="testuser@example.com",
        password_hash="hashed_password_for_testing",
        display_name="Test User",
        is_active=True,
    )

    created_user = await repo.create(user)
    await db_session.commit()

    return created_user


@pytest_asyncio.fixture
async def mock_vault(db_session: AsyncSession, mock_user: User) -> Vault:
    """Create mock vault in database."""
    from app.infrastructure.database.repositories.vault_repository import (
        PostgresVaultRepository,
    )

    repo = PostgresVaultRepository(db_session)

    vault = Vault(
        user_id=mock_user.id,
        name="Test Vault",
        slug="test-vault",
        document_count=5,
    )

    created_vault = await repo.create(vault)
    await db_session.commit()

    return created_vault


@pytest.fixture
def app(mock_user: User, db_session: AsyncSession) -> FastAPI:
    """Create test FastAPI application with mocked dependencies."""
    from app.api.routes import auth, vaults, documents, search, graph
    from app.api.dependencies import get_current_user, get_db_session

    app = FastAPI()

    # Override auth dependency to return our test user
    async def override_get_current_user():
        return mock_user

    # Override database session to use test session
    async def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db_session] = override_get_db_session

    # Include routers
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(vaults.router, prefix="/vaults", tags=["vaults"])
    app.include_router(documents.router, tags=["documents"])
    app.include_router(search.router, tags=["search"])
    app.include_router(graph.router, tags=["graph"])

    return app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Create authorization headers."""
    return {"Authorization": "Bearer mock_token"}
