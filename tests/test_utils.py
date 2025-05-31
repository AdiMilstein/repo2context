"""Tests for repo2context.utils module."""

import tempfile
from pathlib import Path

from repo2context.utils import (
    detect_binary,
    estimate_tokens,
    format_bytes,
    guess_language,
)


class TestDetectBinary:
    """Tests for detect_binary function."""

    def test_text_file(self):
        """Test that text files are not detected as binary."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a text file")
            f.flush()
            assert not detect_binary(Path(f.name))
        Path(f.name).unlink()

    def test_binary_file(self):
        """Test that binary files are detected correctly."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            f.flush()
            assert detect_binary(Path(f.name))
        Path(f.name).unlink()

    def test_nonexistent_file(self):
        """Test that nonexistent files are treated as binary."""
        assert detect_binary(Path("/nonexistent/file.txt"))


class TestGuessLanguage:
    """Tests for guess_language function."""

    def test_python_file(self):
        """Test Python file detection."""
        assert guess_language(Path("test.py")) == "python"

    def test_javascript_file(self):
        """Test JavaScript file detection."""
        assert guess_language(Path("test.js")) == "javascript"

    def test_typescript_file(self):
        """Test TypeScript file detection."""
        assert guess_language(Path("test.ts")) == "typescript"

    def test_unknown_extension(self):
        """Test unknown file extension."""
        assert guess_language(Path("test.unknown")) == ""

    def test_no_extension(self):
        """Test file without extension."""
        assert guess_language(Path("README")) == ""


class TestEstimateTokens:
    """Tests for estimate_tokens function."""

    def test_empty_string(self):
        """Test token estimation for empty string."""
        assert estimate_tokens("") == 0

    def test_simple_text(self):
        """Test token estimation for simple text."""
        text = "Hello world"
        tokens = estimate_tokens(text)
        # Should be at least 1 token but reasonable
        assert 1 <= tokens <= len(text)

    def test_long_text(self):
        """Test token estimation for longer text."""
        text = "This is a longer text that should have more tokens. " * 10
        tokens = estimate_tokens(text)
        # Should scale with text length
        assert tokens > 10


class TestFormatBytes:
    """Tests for format_bytes function."""

    def test_bytes(self):
        """Test formatting for bytes."""
        assert format_bytes(512) == "512.0 B"

    def test_kilobytes(self):
        """Test formatting for kilobytes."""
        assert format_bytes(1536) == "1.5 KB"  # 1.5 * 1024

    def test_megabytes(self):
        """Test formatting for megabytes."""
        assert format_bytes(2 * 1024 * 1024) == "2.0 MB"

    def test_gigabytes(self):
        """Test formatting for gigabytes."""
        assert format_bytes(3 * 1024 * 1024 * 1024) == "3.0 GB"
