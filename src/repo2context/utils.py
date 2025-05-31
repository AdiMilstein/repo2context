"""Utility functions for repo2context."""

import mimetypes
from pathlib import Path

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

# === CONSTANTS ===

# Binary detection
BINARY_DETECTION_CHUNK_SIZE = 8192
NULL_BYTE = b"\0"

# Token estimation
CHARS_PER_TOKEN = 4  # Heuristic fallback for token estimation
TIKTOKEN_ENCODING = "cl100k_base"  # GPT-4, GPT-3.5-turbo encoding

# File size formatting
BYTES_PER_UNIT = 1024.0
SIZE_UNITS = ["B", "KB", "MB", "GB", "TB"]

# Text-based MIME types for binary detection
TEXT_MIME_PREFIXES = [
    "text/",
    "application/json",
    "application/xml",
    "application/yaml",
    "application/x-yaml",
    "application/toml",
    "application/javascript",
    "application/x-javascript",
    "application/x-sh",
    "application/x-shellscript",
]

# Language detection mapping
LANGUAGE_EXTENSIONS = {
    # Programming languages
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "jsx",
    ".tsx": "tsx",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    # Shell scripts
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    ".ps1": "powershell",
    # Web technologies
    ".html": "html",
    ".htm": "html",
    ".xml": "xml",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    # Data formats
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "conf",
    # Documentation
    ".md": "markdown",
    ".markdown": "markdown",
    ".rst": "rst",
    ".txt": "text",
    # Database and query languages
    ".sql": "sql",
    # Other languages
    ".r": "r",
    ".R": "r",
    ".m": "matlab",
    ".pl": "perl",
    ".lua": "lua",
    ".vim": "vim",
    # Build and config files
    ".dockerfile": "dockerfile",
    ".makefile": "makefile",
    ".make": "makefile",
    ".cmake": "cmake",
    # Other formats
    ".proto": "protobuf",
    ".graphql": "graphql",
    ".gql": "graphql",
}


def detect_binary(file_path: Path) -> bool:
    """
    Detect if a file is binary by checking for null bytes and MIME type.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file appears to be binary, False otherwise
    """
    try:
        # Check MIME type first
        if _is_binary_by_mime_type(file_path):
            return True

        # Check for null bytes in first chunk
        return _contains_null_bytes(file_path)

    except OSError:
        # If we can't read the file, assume it's binary
        return True


def _is_binary_by_mime_type(file_path: Path) -> bool:
    """Check if file is binary based on MIME type."""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        return False

    return not any(mime_type.startswith(prefix) for prefix in TEXT_MIME_PREFIXES)


def _contains_null_bytes(file_path: Path) -> bool:
    """Check if file contains null bytes in the first chunk."""
    with open(file_path, "rb") as f:
        chunk = f.read(BINARY_DETECTION_CHUNK_SIZE)
        return NULL_BYTE in chunk


def guess_language(file_path: Path) -> str:
    """
    Guess the programming language of a file.

    Args:
        file_path: Path to the file

    Returns:
        Language name for syntax highlighting, or empty string if unknown
    """
    suffix = file_path.suffix.lower()
    return LANGUAGE_EXTENSIONS.get(suffix, "")


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in text.

    Uses tiktoken if available, otherwise falls back to chars/4 heuristic.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated number of tokens
    """
    if TIKTOKEN_AVAILABLE:
        try:
            encoding = tiktoken.get_encoding(TIKTOKEN_ENCODING)
            return len(encoding.encode(text))
        except Exception:
            # Fall back to heuristic if tiktoken fails
            pass

    # Heuristic: roughly 4 characters per token
    return len(text) // CHARS_PER_TOKEN


def format_bytes(bytes_count: int) -> str:
    """
    Format byte count in human-readable format.

    Args:
        bytes_count: Number of bytes

    Returns:
        Formatted string (e.g., "1.2 KB", "3.4 MB")
    """
    count = float(bytes_count)

    for unit in SIZE_UNITS:
        if count < BYTES_PER_UNIT:
            return f"{count:.1f} {unit}"
        count /= BYTES_PER_UNIT

    # If we get here, it's in TB
    return f"{count:.1f} {SIZE_UNITS[-1]}"


def create_output_dir(output_path: Path) -> None:
    """
    Create output directory if it doesn't exist.

    Args:
        output_path: Path to the output directory
    """
    output_path.mkdir(parents=True, exist_ok=True)
