"""LinkResolver service for resolving wiki-links to documents."""

from app.domain.entities.document import Document
from app.domain.value_objects.wiki_link import WikiLink


class LinkResolver:
    """Service for resolving wiki-links to target documents.

    Resolution priority:
    1. Exact title match (case-insensitive)
    2. Alias match
    3. Filename match (without extension)
    4. Path match
    """

    def resolve(
        self,
        link: WikiLink,
        documents: list[Document],
    ) -> Document | None:
        """Resolve a wiki-link to its target document.

        Args:
            link: The WikiLink to resolve
            documents: List of documents to search

        Returns:
            The target Document if found, None otherwise
        """
        target = link.target.strip()
        target_lower = target.lower()

        # 1. Exact title match (case-insensitive)
        for doc in documents:
            if doc.title.lower() == target_lower:
                return doc

        # 2. Alias match
        for doc in documents:
            for alias in doc.aliases:
                if alias.lower() == target_lower:
                    return doc

        # 3. Filename match (without extension)
        for doc in documents:
            filename_no_ext = doc.filename
            if filename_no_ext.lower().endswith(".md"):
                filename_no_ext = filename_no_ext[:-3]
            if filename_no_ext.lower() == target_lower:
                return doc

        # 4. Path match (full or partial)
        target_with_ext = target if target.lower().endswith(".md") else f"{target}.md"

        for doc in documents:
            # Full path match
            if doc.path.lower() == target_with_ext.lower():
                return doc
            # Partial path match (target could be relative)
            if doc.path.lower().endswith("/" + target_with_ext.lower()):
                return doc

        return None

    def resolve_all(
        self,
        links: list[WikiLink],
        documents: list[Document],
    ) -> dict[WikiLink, Document | None]:
        """Resolve multiple wiki-links.

        Args:
            links: List of WikiLinks to resolve
            documents: List of documents to search

        Returns:
            Dictionary mapping links to their resolved documents (or None)
        """
        return {link: self.resolve(link, documents) for link in links}

    def find_matching_documents(
        self,
        target: str,
        documents: list[Document],
    ) -> list[Document]:
        """Find all documents that could match a target.

        Useful for showing suggestions or handling ambiguous links.

        Args:
            target: The link target text
            documents: List of documents to search

        Returns:
            List of matching documents (may be empty)
        """
        target_lower = target.lower().strip()
        matches: list[Document] = []
        seen_ids = set()

        # Title matches
        for doc in documents:
            if target_lower in doc.title.lower() and doc.id not in seen_ids:
                matches.append(doc)
                seen_ids.add(doc.id)

        # Alias matches
        for doc in documents:
            if doc.id not in seen_ids:
                for alias in doc.aliases:
                    if target_lower in alias.lower():
                        matches.append(doc)
                        seen_ids.add(doc.id)
                        break

        # Filename matches
        for doc in documents:
            if doc.id not in seen_ids:
                filename = doc.filename
                if filename.lower().endswith(".md"):
                    filename = filename[:-3]
                if target_lower in filename.lower():
                    matches.append(doc)
                    seen_ids.add(doc.id)

        return matches
