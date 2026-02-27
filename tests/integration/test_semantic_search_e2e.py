"""End-to-end test for semantic search functionality."""

import io
import zipfile
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.vault import IngestVaultUseCase
from app.application.use_cases.search import SemanticSearchUseCase
from app.application.dto.search_dto import SearchQueryDTO
from app.domain.entities.user import User
from app.infrastructure.database.repositories.user_repository import PostgresUserRepository
from app.infrastructure.database.repositories.vault_repository import PostgresVaultRepository
from app.infrastructure.database.repositories.document_repository import PostgresDocumentRepository
from app.infrastructure.database.repositories.folder_repository import PostgresFolderRepository
from app.infrastructure.database.repositories.link_repository import PostgresDocumentLinkRepository
from app.infrastructure.database.repositories.tag_repository import PostgresTagRepository
from app.infrastructure.database.repositories.embedding_repository import PostgresEmbeddingChunkRepository


def create_test_vault_zip() -> bytes:
    """Create a test vault ZIP with sample documents."""
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Document about machine learning
        zf.writestr(
            "Notes/machine-learning.md",
            """---
title: Machine Learning Basics
tags: [ai, ml]
---

# Machine Learning Basics

Machine learning is a subset of artificial intelligence that focuses on
building systems that can learn from data. Deep learning is a type of
machine learning that uses neural networks with many layers.

Key concepts:
- Supervised learning
- Unsupervised learning
- Reinforcement learning
"""
        )

        # Document about Python
        zf.writestr(
            "Notes/python-programming.md",
            """---
title: Python Programming
tags: [programming, python]
---

# Python Programming

Python is a versatile programming language known for its simplicity and
readability. It is widely used in web development, data science, and
automation.

Popular frameworks:
- Django
- Flask
- FastAPI
"""
        )

        # Document about cooking
        zf.writestr(
            "Notes/cooking-tips.md",
            """---
title: Cooking Tips
tags: [cooking, food]
---

# Cooking Tips

Essential cooking techniques for beginners:
- Always preheat your oven
- Use sharp knives for better cuts
- Season food throughout the cooking process
- Let meat rest after cooking
"""
        )

    return buffer.getvalue()


@pytest.mark.integration
class TestSemanticSearchE2E:
    """End-to-end tests for semantic search."""

    @pytest_asyncio.fixture
    async def test_user(self, session: AsyncSession, clean_db) -> User:
        """Create test user."""
        repo = PostgresUserRepository(session)
        user = User(
            email="semantic-test@example.com",
            password_hash="hashed",
            display_name="Semantic Test User",
        )
        created = await repo.create(user)
        await session.commit()
        return created

    @pytest.mark.asyncio
    async def test_semantic_search_finds_relevant_documents(
        self, session: AsyncSession, test_user: User
    ):
        """Test that semantic search finds relevant documents based on meaning."""
        # Create mock embedding provider
        mock_embedding_provider = MagicMock()

        # Generate fake embeddings that will create meaningful similarity
        # ML document embedding (index 0)
        ml_embedding = [0.9] + [0.0] * 1535  # Strong on dimension 0
        # Python document embedding (index 1)
        python_embedding = [0.0] + [0.9] + [0.0] * 1534  # Strong on dimension 1
        # Cooking document embedding (index 2)
        cooking_embedding = [0.0] * 2 + [0.9] + [0.0] * 1533  # Strong on dimension 2

        # Query about AI/ML should match ML document
        ml_query_embedding = [0.85] + [0.1] + [0.0] * 1534

        mock_embedding_provider.chunk_text = MagicMock(side_effect=lambda text, **kwargs: [
            (text[:500], 100)  # Return single chunk for simplicity
        ])

        # Track which texts are being embedded
        embed_call_count = [0]
        def mock_embed_texts(texts):
            result = []
            for text in texts:
                if "machine learning" in text.lower() or "artificial intelligence" in text.lower():
                    result.append(ml_embedding)
                elif "python" in text.lower():
                    result.append(python_embedding)
                else:
                    result.append(cooking_embedding)
            return result

        mock_embedding_provider.embed_texts = AsyncMock(side_effect=mock_embed_texts)
        mock_embedding_provider.embed_text = AsyncMock(return_value=ml_query_embedding)

        # Set up repositories
        vault_repo = PostgresVaultRepository(session)
        document_repo = PostgresDocumentRepository(session)
        folder_repo = PostgresFolderRepository(session)
        link_repo = PostgresDocumentLinkRepository(session)
        tag_repo = PostgresTagRepository(session)
        embedding_repo = PostgresEmbeddingChunkRepository(session)

        # Ingest vault with embeddings
        ingest_use_case = IngestVaultUseCase(
            vault_repo=vault_repo,
            document_repo=document_repo,
            folder_repo=folder_repo,
            link_repo=link_repo,
            tag_repo=tag_repo,
            embedding_repo=embedding_repo,
            embedding_provider=mock_embedding_provider,
            graph_provider=None,
        )

        zip_content = create_test_vault_zip()
        vault_dto = await ingest_use_case.execute(
            user_id=test_user.id,
            vault_name="Semantic Test Vault",
            zip_content=zip_content,
            generate_embeddings=True,
        )
        await session.commit()

        # Verify embeddings were generated
        assert mock_embedding_provider.embed_texts.called

        # Verify documents were created
        assert vault_dto.document_count == 3

        # Now perform semantic search
        search_use_case = SemanticSearchUseCase(
            vault_repo=vault_repo,
            document_repo=document_repo,
            embedding_repo=embedding_repo,
            embedding_provider=mock_embedding_provider,
        )

        results = await search_use_case.execute(
            user_id=test_user.id,
            vault_slug=vault_dto.slug,
            query=SearchQueryDTO(
                query="artificial intelligence and neural networks",
                limit=10,
                threshold=0.5,
            ),
        )

        # Verify search returns results
        assert len(results) > 0

        # The ML document should be found with highest score
        # (because its embedding is closest to query embedding)
        top_result = results[0]
        assert "machine" in top_result.document.title.lower() or "learning" in top_result.document.title.lower()

    @pytest.mark.asyncio
    async def test_semantic_search_with_filter(
        self, session: AsyncSession, test_user: User
    ):
        """Test semantic search with folder filter."""
        # Similar setup as above but test filtering
        mock_embedding_provider = MagicMock()

        # Simple embeddings
        embedding = [0.5] * 1536

        mock_embedding_provider.chunk_text = MagicMock(side_effect=lambda text, **kwargs: [
            (text[:500], 100)
        ])
        mock_embedding_provider.embed_texts = AsyncMock(return_value=[embedding] * 3)
        mock_embedding_provider.embed_text = AsyncMock(return_value=embedding)

        vault_repo = PostgresVaultRepository(session)
        document_repo = PostgresDocumentRepository(session)
        folder_repo = PostgresFolderRepository(session)
        link_repo = PostgresDocumentLinkRepository(session)
        tag_repo = PostgresTagRepository(session)
        embedding_repo = PostgresEmbeddingChunkRepository(session)

        ingest_use_case = IngestVaultUseCase(
            vault_repo=vault_repo,
            document_repo=document_repo,
            folder_repo=folder_repo,
            link_repo=link_repo,
            tag_repo=tag_repo,
            embedding_repo=embedding_repo,
            embedding_provider=mock_embedding_provider,
        )

        zip_content = create_test_vault_zip()
        vault_dto = await ingest_use_case.execute(
            user_id=test_user.id,
            vault_name="Filter Test Vault",
            zip_content=zip_content,
            generate_embeddings=True,
        )
        await session.commit()

        # Search with folder filter (all docs are in Notes/)
        search_use_case = SemanticSearchUseCase(
            vault_repo=vault_repo,
            document_repo=document_repo,
            embedding_repo=embedding_repo,
            embedding_provider=mock_embedding_provider,
        )

        # Should find documents in Notes folder
        results = await search_use_case.execute(
            user_id=test_user.id,
            vault_slug=vault_dto.slug,
            query=SearchQueryDTO(
                query="any query",
                limit=10,
                threshold=0.0,  # Low threshold to get all results
                folder="Notes",
            ),
        )

        assert len(results) == 3  # All 3 documents are in Notes
