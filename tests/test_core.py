"""Tests for repo2context.core module."""

import tempfile
from pathlib import Path

from repo2context.core import (
    FileFilterServiceImpl,
    IgnorePatternServiceImpl,
    generate_context,
)


class TestIgnorePatternService:
    """Tests for IgnorePatternServiceImpl class."""

    def test_default_patterns(self):
        """Test that default ignore patterns are loaded."""
        ignore_service = IgnorePatternServiceImpl()

        # Test some default patterns
        repo_root = Path("/fake/repo")
        assert ignore_service.should_ignore(repo_root / ".git" / "config", repo_root)
        assert ignore_service.should_ignore(repo_root / "file.pyc", repo_root)
        assert ignore_service.should_ignore(
            repo_root / "__pycache__" / "test.py", repo_root
        )

    def test_custom_ignore_file(self):
        """Test loading custom ignore patterns from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ignore", delete=False) as f:
            f.write("*.custom\n")
            f.write("custom_dir/\n")
            f.write("# Comment line\n")
            f.write("\n")  # Empty line
            f.flush()

            ignore_service = IgnorePatternServiceImpl(rules_file=Path(f.name))
            repo_root = Path("/fake/repo")

            assert ignore_service.should_ignore(repo_root / "test.custom", repo_root)
            assert ignore_service.should_ignore(
                repo_root / "custom_dir" / "file.txt", repo_root
            )
            assert not ignore_service.should_ignore(repo_root / "normal.txt", repo_root)

        Path(f.name).unlink()

    def test_nonexistent_ignore_file(self):
        """Test handling of nonexistent ignore file."""
        # Should not raise exception
        ignore_service = IgnorePatternServiceImpl(
            rules_file=Path("/nonexistent/ignore")
        )
        # Should still have default patterns
        repo_root = Path("/fake/repo")
        assert ignore_service.should_ignore(repo_root / ".git" / "config", repo_root)


class TestFileFilterService:
    """Tests for FileFilterServiceImpl class."""

    def test_no_extension_filter(self):
        """Test file filter service without extension filter."""
        filter_service = FileFilterServiceImpl()

        # All non-binary, non-ignored files should be processed
        # We'll need to mock the other conditions for a proper test
        assert filter_service.only_extensions is None

    def test_extension_filter(self):
        """Test file filter service with extension filter."""
        extensions = {".py", ".js"}
        filter_service = FileFilterServiceImpl(only_extensions=extensions)

        assert filter_service.only_extensions == extensions

    def test_should_process_file(self):
        """Test file processing decision."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            content = "Hello, world!\nThis is a test file."
            f.write(content)
            f.flush()

            filter_service = FileFilterServiceImpl()
            # This tests the should_process method which checks if file is binary and extension filter
            should_process = filter_service.should_process(
                Path(f.name), Path(f.name).parent
            )

            # Text files should be processed
            assert should_process

        Path(f.name).unlink()


class TestGenerateContext:
    """Tests for generate_context function."""

    def test_generate_context_for_fixture(self):
        """Test context generation for test fixture repository."""
        # Get the path to our test fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_repo"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)

            exit_code = generate_context(
                repo_path=fixture_path,
                output_path=output_path,
                max_tokens=10000,  # Small limit for testing
            )

            # Should succeed
            assert exit_code in [0, 1]  # 0 for single file, 1 for split

            # Check that output files were created
            output_files = list(output_path.glob("repocontext_part*.md"))
            assert len(output_files) >= 1

            # Check content across all files (files may be split across parts)
            all_content = ""
            for output_file in output_files:
                all_content += output_file.read_text()

            # Should contain our test files
            assert "main.py" in all_content
            assert "config.json" in all_content
            assert "README.md" in all_content

            # Should not contain ignored files
            assert "binary_file.bin" not in all_content
            assert "temp/ignored.txt" not in all_content
            assert ".cache/cache.txt" not in all_content

    def test_generate_context_with_extension_filter(self):
        """Test context generation with extension filter."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_repo"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)

            exit_code = generate_context(
                repo_path=fixture_path,
                output_path=output_path,
                only_extensions=["py"],  # Only Python files
            )

            assert exit_code == 0

            output_files = list(output_path.glob("repocontext_part*.md"))
            assert len(output_files) == 1

            content = output_files[0].read_text()

            # Should contain Python file
            assert "main.py" in content

            # Should not contain other files
            assert "config.json" not in content
            assert "README.md" not in content

    def test_nonexistent_repo(self):
        """Test handling of nonexistent repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_path = Path(temp_dir) / "nonexistent"
            output_path = Path(temp_dir) / "output"

            exit_code = generate_context(
                repo_path=nonexistent_path,
                output_path=output_path,
            )

            # Should fail with error code 2
            assert exit_code == 2
