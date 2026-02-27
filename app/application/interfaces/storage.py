"""Storage provider port interface."""

from typing import Protocol
from uuid import UUID


class StorageProvider(Protocol):
    """Port interface for file storage operations."""

    async def save_file(
        self,
        vault_id: UUID,
        path: str,
        content: bytes,
    ) -> str:
        """Save a file to storage.

        Args:
            vault_id: Vault UUID
            path: File path within vault
            content: File content as bytes

        Returns:
            Storage URL or path
        """
        ...

    async def get_file(self, vault_id: UUID, path: str) -> bytes:
        """Get a file from storage.

        Args:
            vault_id: Vault UUID
            path: File path within vault

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        ...

    async def delete_file(self, vault_id: UUID, path: str) -> None:
        """Delete a file from storage.

        Args:
            vault_id: Vault UUID
            path: File path within vault
        """
        ...

    async def file_exists(self, vault_id: UUID, path: str) -> bool:
        """Check if a file exists.

        Args:
            vault_id: Vault UUID
            path: File path within vault

        Returns:
            True if file exists
        """
        ...

    async def list_files(
        self,
        vault_id: UUID,
        prefix: str = "",
    ) -> list[str]:
        """List files in storage.

        Args:
            vault_id: Vault UUID
            prefix: Optional path prefix filter

        Returns:
            List of file paths
        """
        ...

    async def delete_vault_files(self, vault_id: UUID) -> int:
        """Delete all files for a vault.

        Args:
            vault_id: Vault UUID

        Returns:
            Number of files deleted
        """
        ...
