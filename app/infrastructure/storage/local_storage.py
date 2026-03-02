"""Local filesystem storage adapter."""

import logging
import shutil
from pathlib import Path
from uuid import UUID

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LocalStorageAdapter:
    """Local filesystem storage implementation."""

    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = Path(base_path or settings.storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _vault_path(self, vault_id: UUID) -> Path:
        """Get path for a vault's storage."""
        return self.base_path / str(vault_id)

    def _file_path(self, vault_id: UUID, path: str) -> Path:
        """Get full path for a file."""
        return self._vault_path(vault_id) / path

    async def save_file(
        self,
        vault_id: UUID,
        path: str,
        content: bytes,
    ) -> str:
        """Save a file to storage."""
        file_path = self._file_path(vault_id, path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(content)

        logger.debug(f"Saved file: {file_path}")
        return str(file_path)

    async def get_file(self, vault_id: UUID, path: str) -> bytes:
        """Get a file from storage."""
        file_path = self._file_path(vault_id, path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with open(file_path, "rb") as f:
            return f.read()

    async def delete_file(self, vault_id: UUID, path: str) -> None:
        """Delete a file from storage."""
        file_path = self._file_path(vault_id, path)

        if file_path.exists():
            file_path.unlink()
            logger.debug(f"Deleted file: {file_path}")

    async def file_exists(self, vault_id: UUID, path: str) -> bool:
        """Check if a file exists."""
        file_path = self._file_path(vault_id, path)
        return file_path.exists()

    async def list_files(
        self,
        vault_id: UUID,
        prefix: str = "",
    ) -> list[str]:
        """List files in storage."""
        vault_path = self._vault_path(vault_id)

        if not vault_path.exists():
            return []

        files = []
        search_path = vault_path / prefix if prefix else vault_path

        if search_path.exists():
            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(vault_path)
                    files.append(str(relative_path))

        return files

    async def delete_vault_files(self, vault_id: UUID) -> int:
        """Delete all files for a vault."""
        vault_path = self._vault_path(vault_id)

        if not vault_path.exists():
            return 0

        # Count files
        count = sum(1 for _ in vault_path.rglob("*") if _.is_file())

        # Remove entire directory
        shutil.rmtree(vault_path)
        logger.info(f"Deleted vault storage: {vault_path} ({count} files)")

        return count
