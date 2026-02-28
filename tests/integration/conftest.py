"""Integration test configuration and fixtures."""

import os
from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from app.domain.entities.user import User
from app.domain.entities.vault import Vault
from app.infrastructure.database.connection import Base


# Use test database URL from environment or default
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://obsidian:obsidian@localhost:5433/obsidian_test",
)


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine per test."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test."""
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


@pytest_asyncio.fixture
async def clean_db(session: AsyncSession):
    """Clean database tables before each test."""
    # Delete in correct order to respect foreign keys
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
            await session.execute(text(f"DELETE FROM {table}"))
        except Exception:
            pass  # Table might not exist

    await session.commit()


@pytest_asyncio.fixture
async def test_user(session: AsyncSession, clean_db) -> User:
    """Create a test user."""
    from app.infrastructure.database.repositories.user_repository import (
        PostgresUserRepository,
    )

    repo = PostgresUserRepository(session)

    user = User(
        email="integration@test.com",
        password_hash="hashed_password",
        display_name="Integration Test User",
        is_active=True,
    )

    created_user = await repo.create(user)
    await session.commit()

    return created_user


@pytest_asyncio.fixture
async def test_vault(session: AsyncSession, test_user: User) -> Vault:
    """Create a test vault."""
    from app.infrastructure.database.repositories.vault_repository import (
        PostgresVaultRepository,
    )

    repo = PostgresVaultRepository(session)

    vault = Vault(
        user_id=test_user.id,
        name="Integration Test Vault",
        slug="integration-test-vault",
        description="Vault for integration tests",
    )

    created_vault = await repo.create(vault)
    await session.commit()

    return created_vault
