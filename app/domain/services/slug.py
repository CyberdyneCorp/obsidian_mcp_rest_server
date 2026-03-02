"""Pure-Python slug generation for domain entities.

This module provides slug generation without external dependencies,
keeping the domain layer pure.
"""

import re
import unicodedata


def generate_slug(text: str, separator: str = "-", max_length: int = 100) -> str:
    """Generate a URL-safe slug from text.

    Args:
        text: The text to convert to a slug
        separator: Character to use as word separator (default: "-")
        max_length: Maximum length of the slug (default: 100)

    Returns:
        URL-safe slug string

    Examples:
        >>> generate_slug("Hello World")
        'hello-world'
        >>> generate_slug("Python 3.12!")
        'python-312'
        >>> generate_slug("café résumé")
        'cafe-resume'
    """
    if not text:
        return ""

    # Normalize unicode (convert accented chars to ASCII equivalents)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    text = text.lower()

    # Replace any non-alphanumeric character with separator
    text = re.sub(r"[^a-z0-9]+", separator, text)

    # Remove leading/trailing separators
    text = text.strip(separator)

    # Collapse multiple separators
    text = re.sub(f"{re.escape(separator)}+", separator, text)

    # Truncate to max_length
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip(separator)

    return text
