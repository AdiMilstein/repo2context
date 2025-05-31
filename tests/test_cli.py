"""Tests for repo2context.cli module."""

import subprocess
import tempfile
from pathlib import Path


class TestCLI:
    """Tests for the CLI interface."""

    def run_cli(self, args, cwd=None):
        """Helper to run the CLI and return result."""
        cmd = ["python", "-m", "repo2context.cli"] + args
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        return result

    def test_version(self):
        """Test version command."""
        result = self.run_cli(["--version"])
        assert result.returncode == 0
        assert "repo2context" in result.stdout

    def test_help(self):
        """Test help output."""
        result = self.run_cli(["--help"])
        assert result.returncode == 0
        assert "repo2context" in result.stdout
        assert "--rules" in result.stdout
        assert "--output" in result.stdout
        assert "--max-tokens" in result.stdout
        assert "--only" in result.stdout

    def test_run_on_fixture(self):
        """Test running CLI on test fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_repo"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)

            result = self.run_cli(
                [
                    str(fixture_path),
                    "--output",
                    str(output_path),
                    "--max-tokens",
                    "5000",
                ]
            )

            # Should succeed or split
            assert result.returncode in [0, 1]

            # Check output files were created
            output_files = list(output_path.glob("repocontext_part*.md"))
            assert len(output_files) >= 1

    def test_extension_filter(self):
        """Test --only extension filter."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_repo"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)

            result = self.run_cli(
                [str(fixture_path), "--output", str(output_path), "--only", "py"]
            )

            assert result.returncode == 0

            output_files = list(output_path.glob("repocontext_part*.md"))
            assert len(output_files) == 1

            content = output_files[0].read_text()
            assert "main.py" in content
            assert "config.json" not in content

    def test_custom_rules_file(self):
        """Test --rules option with custom ignore file."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_repo"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            rules_file = Path(temp_dir) / "custom.ignore"

            # Create custom rules that ignore Python files
            rules_file.write_text("*.py\n")

            result = self.run_cli(
                [
                    str(fixture_path),
                    "--output",
                    str(output_path),
                    "--rules",
                    str(rules_file),
                ]
            )

            assert result.returncode == 0

            output_files = list(output_path.glob("repocontext_part*.md"))
            assert len(output_files) == 1

            content = output_files[0].read_text()
            # Check that main.py file is not processed (should not have its own section)
            assert "main.py\n```python" not in content  # Should be ignored
            assert "config.json" in content  # Should be included

    def test_nonexistent_repo(self):
        """Test CLI with nonexistent repository."""
        result = self.run_cli(["/nonexistent/path"])
        assert result.returncode == 2
        assert "does not exist" in result.stderr

    def test_invalid_max_tokens(self):
        """Test CLI with invalid max-tokens value."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_repo"

        result = self.run_cli(
            [str(fixture_path), "--max-tokens", "500"]  # Below minimum
        )

        # Should fail validation
        assert result.returncode == 2
        assert "must be between" in result.stderr

    def test_current_directory_default(self):
        """Test that current directory is used by default."""
        # Change to fixture directory
        fixture_path = Path(__file__).parent / "fixtures" / "test_repo"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)

            # Run from fixture directory
            result = self.run_cli(["--output", str(output_path)], cwd=str(fixture_path))

            assert result.returncode in [0, 1]

            output_files = list(output_path.glob("repocontext_part*.md"))
            assert len(output_files) >= 1
