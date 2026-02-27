"""Ingest vault use case."""

import io
import logging
import zipfile
from uuid import UUID

from app.application.dto.vault_dto import VaultDTO
from app.application.interfaces.repositories import (
    DocumentLinkRepository,
    DocumentRepository,
    EmbeddingChunkRepository,
    FolderRepository,
    TagRepository,
    VaultRepository,
)
from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.application.interfaces.graph_provider import GraphProvider
from app.domain.entities.document import Document
from app.domain.entities.document_link import DocumentLink, LinkType
from app.domain.entities.embedding_chunk import EmbeddingChunk
from app.domain.entities.folder import Folder
from app.domain.entities.tag import Tag
from app.domain.entities.vault import Vault
from app.domain.exceptions import DuplicateVaultError
from app.domain.services.link_resolver import LinkResolver
from app.domain.services.markdown_processor import MarkdownProcessor
from app.domain.services.tag_parser import TagParser
from app.domain.value_objects.document_path import DocumentPath
from app.domain.value_objects.frontmatter import Frontmatter

logger = logging.getLogger(__name__)


class IngestVaultUseCase:
    """Use case for ingesting an Obsidian vault from a ZIP file."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        document_repo: DocumentRepository,
        folder_repo: FolderRepository,
        link_repo: DocumentLinkRepository,
        tag_repo: TagRepository,
        embedding_repo: EmbeddingChunkRepository | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        graph_provider: GraphProvider | None = None,
    ) -> None:
        self.vault_repo = vault_repo
        self.document_repo = document_repo
        self.folder_repo = folder_repo
        self.link_repo = link_repo
        self.tag_repo = tag_repo
        self.embedding_repo = embedding_repo
        self.embedding_provider = embedding_provider
        self.graph_provider = graph_provider

        self.markdown_processor = MarkdownProcessor()
        self.link_resolver = LinkResolver()
        self.tag_parser = TagParser()

    async def execute(
        self,
        user_id: UUID,
        vault_name: str,
        zip_content: bytes,
        generate_embeddings: bool = True,
    ) -> VaultDTO:
        """Ingest an Obsidian vault from a ZIP file.

        Args:
            user_id: Owner user ID
            vault_name: Name for the vault
            zip_content: ZIP file content
            generate_embeddings: Whether to generate embeddings

        Returns:
            Created vault DTO
        """
        # Create vault
        vault = Vault.create(user_id=user_id, name=vault_name)

        # Check for duplicate
        existing = await self.vault_repo.get_by_slug(user_id, vault.slug)
        if existing:
            raise DuplicateVaultError(vault.slug)

        vault = await self.vault_repo.create(vault)

        try:
            # Extract and process ZIP
            documents = await self._process_zip(vault, zip_content)

            # Update vault document count
            vault.set_document_count(len(documents))
            vault = await self.vault_repo.update(vault)

            # Resolve links
            await self._resolve_links(vault.id, documents)

            # Generate embeddings if requested
            if generate_embeddings and self.embedding_provider:
                await self._generate_embeddings(vault.id, documents)

            # Build graph (optional - failures here don't affect main data)
            if self.graph_provider:
                try:
                    await self._build_graph(vault.id, documents)
                except Exception as graph_error:
                    logger.warning(f"Graph building failed (non-fatal): {graph_error}")
                    # Graph is optional, continue without it

            return VaultDTO.from_entity(vault)

        except Exception as e:
            # Cleanup on failure
            logger.error(f"Vault ingestion failed: {e}")
            await self.vault_repo.delete(vault.id)
            raise

    async def _process_zip(
        self,
        vault: Vault,
        zip_content: bytes,
    ) -> list[Document]:
        """Extract and process ZIP contents."""
        documents: list[Document] = []
        folders_cache: dict[str, Folder] = {}

        with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zf:
            for file_info in zf.infolist():
                if file_info.is_dir():
                    continue

                path = file_info.filename

                # Skip hidden files and __MACOSX
                if any(part.startswith(".") or part.startswith("__") for part in path.split("/")):
                    continue

                doc_path = DocumentPath(path)

                # Only process markdown files
                if not doc_path.is_markdown:
                    # TODO: Handle attachments
                    continue

                # Read content
                content = zf.read(file_info).decode("utf-8", errors="replace")

                # Parse document
                parsed = self.markdown_processor.parse(content)

                # Get or create folder
                folder_id = None
                if doc_path.folder_path:
                    folder = await self._get_or_create_folder(
                        vault.id,
                        doc_path.folder_path,
                        folders_cache,
                    )
                    folder_id = folder.id

                # Create document
                document = Document.create(
                    vault_id=vault.id,
                    path=doc_path.path,
                    content=parsed.content,
                    frontmatter=parsed.frontmatter,
                    folder_id=folder_id,
                )
                document.set_link_count(len(parsed.links))

                document = await self.document_repo.create(document)
                documents.append(document)

                # Create tags
                await self._create_tags(vault.id, document.id, parsed.tags)

                # Create link records (unresolved for now)
                await self._create_links(vault.id, document, parsed.links)

        return documents

    async def _get_or_create_folder(
        self,
        vault_id: UUID,
        path: str,
        cache: dict[str, Folder],
    ) -> Folder:
        """Get or create a folder at the given path."""
        if path in cache:
            return cache[path]

        folder = await self.folder_repo.get_by_path(vault_id, path)
        if folder:
            cache[path] = folder
            return folder

        # Create parent folders first
        parts = path.split("/")
        parent_id = None

        for i in range(len(parts)):
            current_path = "/".join(parts[: i + 1])

            if current_path in cache:
                parent_id = cache[current_path].id
                continue

            existing = await self.folder_repo.get_by_path(vault_id, current_path)
            if existing:
                cache[current_path] = existing
                parent_id = existing.id
                continue

            folder = Folder(
                vault_id=vault_id,
                parent_id=parent_id,
                name=parts[i],
                path=current_path,
                depth=i,
            )
            folder = await self.folder_repo.create(folder)
            cache[current_path] = folder
            parent_id = folder.id

        return cache[path]

    async def _create_tags(
        self,
        vault_id: UUID,
        document_id: UUID,
        tags: list[str],
    ) -> None:
        """Create tags and associate with document."""
        for tag_name in tags:
            # Expand hierarchical tags
            hierarchy = self.tag_parser.parse_hierarchical_tag(tag_name)

            parent_id = None
            for level_tag in hierarchy:
                tag = await self.tag_repo.get_or_create(vault_id, level_tag)
                tag.increment_document_count()
                await self.tag_repo.update(tag)
                parent_id = tag.id

    async def _create_links(
        self,
        vault_id: UUID,
        document: Document,
        links: list,  # WikiLink
    ) -> None:
        """Create link records for a document."""
        link_entities = []

        for i, wiki_link in enumerate(links):
            link_type = LinkType.EMBED if wiki_link.is_embed else LinkType.WIKILINK
            if wiki_link.heading:
                link_type = LinkType.HEADER
            elif wiki_link.block_id:
                link_type = LinkType.BLOCK

            link = DocumentLink.create(
                vault_id=vault_id,
                source_document_id=document.id,
                link_text=wiki_link.target,
                display_text=wiki_link.display_text,
                link_type=link_type,
                position_start=i,  # Simplified position
            )
            link_entities.append(link)

        if link_entities:
            await self.link_repo.create_many(link_entities)

    async def _resolve_links(
        self,
        vault_id: UUID,
        documents: list[Document],
    ) -> None:
        """Resolve all links in the vault."""
        # Build lookup for resolution
        doc_by_title = {d.title.lower(): d for d in documents}
        doc_by_path = {d.path.lower(): d for d in documents}

        # Also add aliases
        for doc in documents:
            for alias in doc.aliases:
                doc_by_title[alias.lower()] = doc

        # Get all unresolved links
        unresolved = await self.link_repo.get_unresolved_links(vault_id)

        # Collect resolved links for batch update
        resolved_links: list[tuple] = []  # (link_id, target_document_id)

        for link in unresolved:
            target_lower = link.link_text.lower()

            # Try to resolve by title
            target_doc = doc_by_title.get(target_lower)
            if not target_doc:
                # Try with .md extension
                target_doc = doc_by_path.get(f"{target_lower}.md")

            if target_doc:
                link.resolve(target_doc.id)
                resolved_links.append((link.id, target_doc.id))
                target_doc.increment_backlink_count()

        # Persist resolved links to database
        if resolved_links:
            updated_count = await self.link_repo.update_resolved(resolved_links)
            logger.info(f"Resolved {updated_count} links out of {len(unresolved)} total")

        # Update documents with backlink counts
        for doc in documents:
            if doc.backlink_count > 0:
                await self.document_repo.update(doc)

    async def _generate_embeddings(
        self,
        vault_id: UUID,
        documents: list[Document],
    ) -> None:
        """Generate embeddings for all documents.

        This method:
        1. Chunks each document into smaller pieces
        2. Generates embeddings for all chunks in batches
        3. Stores the embedding chunks in the database
        """
        if not self.embedding_provider or not self.embedding_repo:
            logger.warning("Embedding provider or repository not configured, skipping embeddings")
            return

        logger.info(f"Generating embeddings for {len(documents)} documents")

        # Collect all chunks from all documents
        all_chunks: list[EmbeddingChunk] = []
        chunk_texts: list[str] = []

        for doc in documents:
            # Skip empty documents
            if not doc.content or not doc.content.strip():
                continue

            # Chunk the document content
            text_chunks = self.embedding_provider.chunk_text(
                doc.content,
                chunk_size=500,  # tokens
                overlap=50,      # token overlap
            )

            for idx, (chunk_text, token_count) in enumerate(text_chunks):
                chunk = EmbeddingChunk.create(
                    vault_id=vault_id,
                    document_id=doc.id,
                    chunk_index=idx,
                    content=chunk_text,
                    token_count=token_count,
                )
                all_chunks.append(chunk)
                chunk_texts.append(chunk_text)

        if not all_chunks:
            logger.info("No content to embed")
            return

        logger.info(f"Generated {len(all_chunks)} chunks, generating embeddings...")

        # Generate embeddings in batches (OpenAI has limits)
        batch_size = 100  # OpenAI allows up to 2048 inputs per request
        embeddings: list[list[float]] = []

        for i in range(0, len(chunk_texts), batch_size):
            batch = chunk_texts[i:i + batch_size]
            logger.info(f"Embedding batch {i // batch_size + 1}/{(len(chunk_texts) + batch_size - 1) // batch_size}")
            batch_embeddings = await self.embedding_provider.embed_texts(batch)
            embeddings.extend(batch_embeddings)

        # Assign embeddings to chunks
        for chunk, embedding in zip(all_chunks, embeddings):
            chunk.set_embedding(embedding)

        # Store all chunks
        await self.embedding_repo.create_many(all_chunks)

        logger.info(f"Successfully stored {len(all_chunks)} embedding chunks")

    async def _build_graph(
        self,
        vault_id: UUID,
        documents: list[Document],
    ) -> None:
        """Build the knowledge graph."""
        if not self.graph_provider:
            logger.info("Graph provider not configured, skipping graph building")
            return

        logger.info(f"Building graph for {len(documents)} documents")

        # Create nodes for all documents
        node_count = 0
        for doc in documents:
            await self.graph_provider.create_document_node(
                document_id=doc.id,
                vault_id=vault_id,
                title=doc.title,
                path=doc.path,
            )
            node_count += 1

        logger.info(f"Created {node_count} document nodes")

        # Create edges for resolved links
        edge_count = 0
        resolved_count = 0
        for doc in documents:
            links = await self.link_repo.get_outgoing_links(doc.id)
            for link in links:
                if link.is_resolved and link.target_document_id:
                    resolved_count += 1
                    try:
                        await self.graph_provider.create_link_edge(
                            source_id=doc.id,
                            target_id=link.target_document_id,
                            link_type=link.link_type.value,
                            display_text=link.display_text,
                        )
                        edge_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to create edge: {e}")

        logger.info(f"Created {edge_count} edges from {resolved_count} resolved links")
