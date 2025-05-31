"""Core functionality for repo2context following Clean Architecture principles."""

import os
import sys
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TextIO

import pathspec

from .utils import (
    create_output_dir,
    detect_binary,
    estimate_tokens,
    format_bytes,
    guess_language,
)

# === CONSTANTS ===

# Token limits and formatting
MAX_SUMMARY_TOKENS = 8000
SUMMARY_MAX_RESPONSE_TOKENS = 200
SUMMARY_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 85000
CHARS_PER_TOKEN = 4  # Heuristic for token estimation

# File patterns
DEFAULT_IGNORE_PATTERNS = [
    ".git/",
    ".repo2context/",
    "*.pyc",
    "__pycache__/",
    ".DS_Store",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.exe",
    "node_modules/",
    ".venv/",
    "venv/",
    ".env",
    "*.log",
    "*.tmp",
    "*.temp",
    ".mypy_cache/",
    ".pytest_cache/",
    ".coverage",
    "htmlcov/",
    ".tox/",
    "dist/",
    "build/",
    "*.egg-info/",
]

# OpenAI configuration
DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"

# File processing
BINARY_DETECTION_CHUNK_SIZE = 8192

# Exit codes
EXIT_SUCCESS = 0
EXIT_SPLIT_FILES = 1
EXIT_ERROR = 2

# === DOMAIN LAYER: Entities and Value Objects ===


@dataclass(frozen=True)
class FileInfo:
    """Value object representing file information."""

    path: Path
    relative_path: Path
    content: str
    byte_count: int
    token_count: int
    language: str
    summary: str | None = None


@dataclass(frozen=True)
class ProcessingResult:
    """Value object representing the result of context generation."""

    total_files: int
    total_bytes: int
    total_tokens: int
    parts_written: int
    exit_code: int


@dataclass(frozen=True)
class ProcessingConfig:
    """Value object for processing configuration."""

    repo_path: Path
    rules_file: Path | None
    output_path: Path
    max_tokens: int
    only_extensions: set[str] | None
    enable_summary: bool = False


# === DOMAIN LAYER: Repository Interfaces ===


class FileSystemRepository(Protocol):
    """Protocol for file system operations."""

    def walk_directory(
        self, path: Path
    ) -> Generator[tuple[Path, list[str], list[str]], None, None]:
        """Walk directory structure."""
        ...

    def read_file(self, path: Path) -> str:
        """Read file content."""
        ...

    def create_directory(self, path: Path) -> None:
        """Create directory if it doesn't exist."""
        ...


# === DOMAIN LAYER: Service Interfaces ===


class IgnorePatternService(Protocol):
    """Protocol for handling ignore patterns."""

    def should_ignore(self, file_path: Path, relative_to: Path) -> bool:
        """Check if a file should be ignored."""
        ...


class FileFilterService(Protocol):
    """Protocol for filtering files."""

    def should_process(self, file_path: Path, repo_root: Path) -> bool:
        """Check if a file should be processed."""
        ...


class FileProcessorService(Protocol):
    """Protocol for processing individual files."""

    def process_file(self, file_path: Path, repo_root: Path) -> FileInfo | None:
        """Process a file and return file information."""
        ...


class SummaryService(Protocol):
    """Protocol for generating AI-powered file summaries."""

    def generate_summary(self, file_info: FileInfo) -> str | None:
        """Generate a summary for the given file."""
        ...


class ContextWriterService(Protocol):
    """Protocol for writing context files."""

    def write_file_section(self, file_info: FileInfo) -> None:
        """Write a file section to the current part."""
        ...

    def finalize(self) -> int:
        """Finalize writing and return number of parts written."""
        ...


# === APPLICATION LAYER: Use Cases ===


class GenerateContextUseCase:
    """Use case for generating context files from a repository."""

    def __init__(
        self,
        file_system_repo: FileSystemRepository,
        ignore_service: IgnorePatternService,
        filter_service: FileFilterService,
        processor_service: FileProcessorService,
        writer_service: ContextWriterService,
        summary_service: SummaryService | None = None,
    ):
        """Initialize use case with dependencies."""
        self.file_system_repo = file_system_repo
        self.ignore_service = ignore_service
        self.filter_service = filter_service
        self.processor_service = processor_service
        self.writer_service = writer_service
        self.summary_service = summary_service

    def execute(self, config: ProcessingConfig) -> ProcessingResult:
        """Execute the context generation use case."""
        try:
            if not self._validate_inputs(config):
                return ProcessingResult(0, 0, 0, 0, EXIT_ERROR)

            self.file_system_repo.create_directory(config.output_path)

            total_files, total_bytes, total_tokens = self._process_files(config)
            parts_written = self.writer_service.finalize()

            self._print_summary(total_files, total_bytes, total_tokens, parts_written)

            exit_code = EXIT_SPLIT_FILES if parts_written > 1 else EXIT_SUCCESS
            return ProcessingResult(
                total_files, total_bytes, total_tokens, parts_written, exit_code
            )

        except KeyboardInterrupt:
            print("\nOperation cancelled by user", file=sys.stderr)
            return ProcessingResult(0, 0, 0, 0, EXIT_ERROR)
        except Exception as e:
            print(f"Fatal error: {e}", file=sys.stderr)
            return ProcessingResult(0, 0, 0, 0, EXIT_ERROR)

    def _validate_inputs(self, config: ProcessingConfig) -> bool:
        """Validate input configuration."""
        if not config.repo_path.exists():
            print(
                f"Error: Repository path '{config.repo_path}' does not exist",
                file=sys.stderr,
            )
            return False

        if not config.repo_path.is_dir():
            print(
                f"Error: Repository path '{config.repo_path}' is not a directory",
                file=sys.stderr,
            )
            return False

        return True

    def _process_files(self, config: ProcessingConfig) -> tuple[int, int, int]:
        """Process all files and return counts."""
        total_files = 0
        total_bytes = 0
        total_tokens = 0

        print(f"Scanning repository: {config.repo_path}")

        for file_path in self._find_repository_files(config.repo_path):
            if not self.filter_service.should_process(file_path, config.repo_path):
                continue

            file_info = self.processor_service.process_file(file_path, config.repo_path)
            if file_info and file_info.content:
                file_info = self._add_summary_if_enabled(file_info, config)
                self.writer_service.write_file_section(file_info)

                total_files += 1
                total_bytes += file_info.byte_count
                total_tokens += file_info.token_count

        return total_files, total_bytes, total_tokens

    def _add_summary_if_enabled(
        self, file_info: FileInfo, config: ProcessingConfig
    ) -> FileInfo:
        """Add summary to file info if summary is enabled."""
        if not config.enable_summary or not self.summary_service:
            return file_info

        try:
            summary = self.summary_service.generate_summary(file_info)
            if summary:
                file_info = FileInfo(
                    path=file_info.path,
                    relative_path=file_info.relative_path,
                    content=file_info.content,
                    byte_count=file_info.byte_count,
                    token_count=file_info.token_count,
                    language=file_info.language,
                    summary=summary,
                )
                print(f"Added summary for file {file_info.relative_path}")
        except Exception as e:
            print(
                f"Warning: Failed to generate summary for {file_info.relative_path}: {e}",
                file=sys.stderr,
            )

        return file_info

    def _print_summary(
        self, total_files: int, total_bytes: int, total_tokens: int, parts_written: int
    ) -> None:
        """Print processing summary."""
        print("\nContext generation complete:")
        print(f"  Files processed: {total_files}")
        print(f"  Total size: {format_bytes(total_bytes)}")
        print(f"  Estimated tokens: {total_tokens:,}")
        print(f"  Parts written: {parts_written}")

        if parts_written > 1:
            print(f"  Output split into {parts_written} parts due to token limit")

    def _find_repository_files(self, repo_root: Path) -> Generator[Path, None, None]:
        """Find all files in repository that should be processed."""
        for root, dirs, files in self.file_system_repo.walk_directory(repo_root):
            # Filter directories
            dirs[:] = [
                d
                for d in dirs
                if not self.ignore_service.should_ignore(root / d, repo_root)
            ]

            for file in files:
                file_path = root / file
                if not self.ignore_service.should_ignore(file_path, repo_root):
                    yield file_path


# === INFRASTRUCTURE LAYER: Concrete Implementations ===


class FileSystemRepositoryImpl:
    """Concrete implementation of file system operations."""

    def walk_directory(
        self, path: Path
    ) -> Generator[tuple[Path, list[str], list[str]], None, None]:
        """Walk directory structure."""
        for root, dirs, files in os.walk(path):
            yield Path(root), dirs, files

    def read_file(self, path: Path) -> str:
        """Read file content."""
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError as e:
            print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
            return ""

    def create_directory(self, path: Path) -> None:
        """Create directory if it doesn't exist."""
        create_output_dir(path)


class IgnorePatternServiceImpl:
    """Concrete implementation of ignore pattern service."""

    def __init__(self, rules_file: Path | None = None, repo_root: Path | None = None):
        """Initialize ignore service."""
        self.patterns: list[str] = []
        self.spec: pathspec.PathSpec | None = None

        self.patterns.extend(DEFAULT_IGNORE_PATTERNS)

        # Load from rules file or default .repo2contextignore
        if rules_file:
            self._load_patterns_from_file(rules_file)
        elif repo_root:
            ignore_file = repo_root / ".repo2contextignore"
            if ignore_file.exists():
                self._load_patterns_from_file(ignore_file)

        self._compile_patterns()

    def _load_patterns_from_file(self, file_path: Path) -> None:
        """Load ignore patterns from a file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self.patterns.append(line)
        except OSError as e:
            print(
                f"Warning: Could not read ignore file {file_path}: {e}", file=sys.stderr
            )

    def _compile_patterns(self) -> None:
        """Compile patterns into a PathSpec for efficient matching."""
        self.spec = pathspec.PathSpec.from_lines("gitwildmatch", self.patterns)

    def should_ignore(self, file_path: Path, relative_to: Path) -> bool:
        """Check if a file should be ignored."""
        if not self.spec:
            return False

        try:
            relative_path = file_path.relative_to(relative_to)
            return self.spec.match_file(str(relative_path))
        except ValueError:
            # File is not relative to the base path
            return True


class FileFilterServiceImpl:
    """Concrete implementation of file filter service."""

    def __init__(self, only_extensions: set[str] | None = None):
        """Initialize file filter service."""
        self.only_extensions = only_extensions

    def should_process(self, file_path: Path, repo_root: Path) -> bool:
        """Check if a file should be processed."""
        # Check if file is binary
        if detect_binary(file_path):
            return False

        # Check extension filter
        if self.only_extensions:
            extension = file_path.suffix.lower()
            if extension not in self.only_extensions:
                return False

        return True


class FileProcessorServiceImpl:
    """Concrete implementation of file processor service."""

    def __init__(self, file_system_repo: FileSystemRepository):
        """Initialize file processor service."""
        self.file_system_repo = file_system_repo

    def process_file(self, file_path: Path, repo_root: Path) -> FileInfo | None:
        """Process a file and return file information."""
        content = self.file_system_repo.read_file(file_path)
        if not content:
            return None

        try:
            relative_path = file_path.relative_to(repo_root)
        except ValueError:
            relative_path = file_path

        byte_count = len(content.encode("utf-8"))
        token_count = estimate_tokens(content)
        language = guess_language(file_path)

        return FileInfo(
            path=file_path,
            relative_path=relative_path,
            content=content,
            byte_count=byte_count,
            token_count=token_count,
            language=language,
        )


class ContextWriterServiceImpl:
    """Concrete implementation of context writer service."""

    def __init__(self, output_dir: Path, max_tokens: int):
        """Initialize context writer service."""
        self.output_dir = output_dir
        self.max_tokens = max_tokens
        self.current_part = 1
        self.current_tokens = 0
        self.current_file: TextIO | None = None
        self.files_written = 0

    def write_file_section(self, file_info: FileInfo) -> None:
        """Write a file section to the current part."""
        # Check if we need a new part
        if self._should_start_new_part(file_info):
            self.current_part += 1
            self._start_new_part()
        elif self.current_file is None:
            self._start_new_part()

        self._write_file_content(file_info)
        self.current_tokens += file_info.token_count

    def finalize(self) -> int:
        """Finalize writing and return number of parts written."""
        if self.current_file:
            self.current_file.close()
            self.current_file = None

        return self.files_written

    def _should_start_new_part(self, file_info: FileInfo) -> bool:
        """Check if we should start a new part for this file."""
        return (
            self.current_file is not None
            and self.current_tokens + file_info.token_count > self.max_tokens
            and self.current_tokens > 0
        )

    def _write_file_content(self, file_info: FileInfo) -> None:
        """Write the actual file content to the output."""
        assert self.current_file is not None  # For mypy

        self.current_file.write(f"{file_info.relative_path}\n")
        if file_info.summary:
            self.current_file.write(f"**Summary:** {file_info.summary}\n\n")

        self.current_file.write(f"```{file_info.language}\n")
        self.current_file.write(f"# byte_count: {file_info.byte_count}\n")
        self.current_file.write(f"# est_tokens: {file_info.token_count}\n")
        self.current_file.write(file_info.content)

        if not file_info.content.endswith("\n"):
            self.current_file.write("\n")

        self.current_file.write("```\n")
        self.current_file.write("---\n\n")

    def _get_part_filename(self) -> str:
        """Get filename for current part."""
        return f"repocontext_part{self.current_part:02d}.md"

    def _start_new_part(self) -> None:
        """Start a new part file."""
        if self.current_file:
            self.current_file.close()

        part_path = self.output_dir / self._get_part_filename()
        self.current_file = open(part_path, "w", encoding="utf-8")
        self.current_tokens = 0
        self.files_written += 1

        print(f"Writing part {self.current_part}: {part_path}")


class OpenAISummaryServiceImpl:
    """Concrete implementation of summary service using OpenAI."""

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_OPENAI_MODEL):
        """Initialize OpenAI summary service."""
        try:
            import openai
        except ImportError as e:
            raise RuntimeError(
                "OpenAI package not available. Install with: pip install 'repo2context[summary]'"
            ) from e

        # Check for API key
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable."
            )

        try:
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}") from e

    def generate_summary(self, file_info: FileInfo) -> str | None:
        """Generate a summary for the given file."""
        if not file_info.content.strip():
            return None

        # Skip very large files to avoid token limits
        if file_info.token_count > MAX_SUMMARY_TOKENS:
            return f"File too large for summary generation ({file_info.token_count:,} tokens)"

        try:
            prompt = self._create_summary_prompt(file_info)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a code analysis expert. Generate concise, informative summaries of code files.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=SUMMARY_MAX_RESPONSE_TOKENS,
                temperature=SUMMARY_TEMPERATURE,
            )

            summary = response.choices[0].message.content
            return summary.strip() if summary else None

        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}") from e

    def _create_summary_prompt(self, file_info: FileInfo) -> str:
        """Create a prompt for summarizing the file."""
        return f"""Analyze this {file_info.language} file and provide a concise summary (2-3 sentences) that covers:
1. What this file does/its purpose
2. Key functions, classes, or components
3. Notable patterns or architectural decisions

File: {file_info.relative_path}
Language: {file_info.language}
Size: {file_info.byte_count} bytes

Content:
{file_info.content}

Summary:"""


class NoOpSummaryServiceImpl:
    """No-op implementation of summary service when AI features are disabled."""

    def generate_summary(self, file_info: FileInfo) -> str | None:
        """Return None as no summary is generated."""
        return None


# === APPLICATION LAYER: Service Factory ===


class ContextGenerationServiceFactory:
    """Factory for creating context generation services with dependency injection."""

    @staticmethod
    def create_use_case(
        repo_path: Path | None = None,
        rules_file: Path | None = None,
        output_path: Path | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        only_extensions: list[str] | None = None,
        enable_summary: bool = False,
    ) -> tuple[GenerateContextUseCase, ProcessingConfig]:
        """Create use case with all dependencies injected."""
        # Set defaults
        repo_path = repo_path or Path.cwd()
        output_path = output_path or repo_path / ".repo2context"

        # Process extensions
        extensions_set = None
        if only_extensions:
            extensions_set = {
                ext if ext.startswith(".") else f".{ext}" for ext in only_extensions
            }

        config = ProcessingConfig(
            repo_path=repo_path,
            rules_file=rules_file,
            output_path=output_path,
            max_tokens=max_tokens,
            only_extensions=extensions_set,
            enable_summary=enable_summary,
        )

        # Create dependencies
        file_system_repo = FileSystemRepositoryImpl()
        ignore_service = IgnorePatternServiceImpl(rules_file, repo_path)
        filter_service = FileFilterServiceImpl(extensions_set)
        processor_service = FileProcessorServiceImpl(file_system_repo)
        writer_service = ContextWriterServiceImpl(output_path, max_tokens)

        # Create summary service
        summary_service = ContextGenerationServiceFactory._create_summary_service(
            enable_summary
        )

        # Create use case with injected dependencies
        use_case = GenerateContextUseCase(
            file_system_repo=file_system_repo,
            ignore_service=ignore_service,
            filter_service=filter_service,
            processor_service=processor_service,
            writer_service=writer_service,
            summary_service=summary_service,
        )

        return use_case, config

    @staticmethod
    def _create_summary_service(enable_summary: bool) -> SummaryService:
        """Create appropriate summary service based on configuration."""
        if not enable_summary:
            return NoOpSummaryServiceImpl()

        try:
            service = OpenAISummaryServiceImpl()
            print("AI-powered summaries enabled (OpenAI)")
            return service
        except RuntimeError as e:
            print(f"Warning: {e}. Proceeding without summaries.", file=sys.stderr)
            return NoOpSummaryServiceImpl()


# === PUBLIC API: Facade for backward compatibility ===


def generate_context(
    repo_path: Path | None = None,
    rules_file: Path | None = None,
    output_path: Path | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    only_extensions: list[str] | None = None,
    enable_summary: bool = False,
) -> int:
    """
    Generate context files from a repository.

    This function provides a facade for the clean architecture implementation,
    maintaining backward compatibility with the original API.

    Args:
        repo_path: Repository path (defaults to current directory)
        rules_file: Custom ignore rules file
        output_path: Output directory (defaults to ./.repo2context)
        max_tokens: Maximum tokens per output file
        only_extensions: List of file extensions to include
        enable_summary: Whether to generate AI-powered file summaries

    Returns:
        Exit code: 0 for success, 1 if files were split, 2 for fatal error
    """
    use_case, config = ContextGenerationServiceFactory.create_use_case(
        repo_path=repo_path,
        rules_file=rules_file,
        output_path=output_path,
        max_tokens=max_tokens,
        only_extensions=only_extensions,
        enable_summary=enable_summary,
    )

    result = use_case.execute(config)
    return result.exit_code
