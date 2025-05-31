"""Command-line interface for repo2context."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import generate_context

# === CONSTANTS ===

# Validation limits
MIN_TOKENS = 1000
MAX_TOKENS = 1000000

# Error messages
ERROR_DEPENDENCY_MISSING = "Error: --summary requires OpenAI dependency. Install with: pip install 'repo2context[summary]'"
ERROR_REPO_NOT_EXISTS = "Error: Repository path '{}' does not exist"
ERROR_REPO_NOT_DIR = "Error: Repository path '{}' is not a directory"
ERROR_RULES_NOT_EXISTS = "Error: Rules file '{}' does not exist"
ERROR_TOKEN_RANGE = f"Error: --max-tokens must be between {MIN_TOKENS} and {MAX_TOKENS}"

# Program metadata
PROG_NAME = "repo2context"
DESCRIPTION = "One-command repo → Markdown context generator for LLM workflows"


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process current directory
  repo2context

  # Process specific repository
  repo2context /path/to/repo

  # Use custom ignore rules
  repo2context --rules my-ignore-rules.txt

  # Limit to specific file types
  repo2context --only py,js,ts

  # Custom output directory and token limit
  repo2context --output ./context --max-tokens 50000

  # Generate AI-powered file summaries (requires OpenAI API key)
  repo2context --summary
        """,
    )

    # Positional arguments
    parser.add_argument(
        "repo_path",
        nargs="?",
        help="Repository path to process (defaults to current directory)",
    )

    # Optional arguments
    parser.add_argument(
        "--rules",
        type=Path,
        help="Path to ignore rules file (defaults to .repo2contextignore)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory path (defaults to ./.repo2context)",
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=85000,
        help="Maximum tokens per output file (default: 85000)",
    )

    parser.add_argument(
        "--only",
        help="Only include files with these extensions (comma-separated, e.g., 'py,js,ts')",
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Generate AI-powered file summaries (requires OpenAI API key)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"{PROG_NAME} {__version__}",
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments and exit on error."""
    # Validate max_tokens range
    if args.max_tokens < MIN_TOKENS or args.max_tokens > MAX_TOKENS:
        print(ERROR_TOKEN_RANGE, file=sys.stderr)
        sys.exit(2)

    # Validate summary flag requirements
    if args.summary:
        try:
            import openai  # noqa: F401
        except ImportError:
            print(ERROR_DEPENDENCY_MISSING, file=sys.stderr)
            sys.exit(2)

    # Convert and validate repo path
    repo_path_obj = Path(args.repo_path) if args.repo_path else Path.cwd()

    if not repo_path_obj.exists():
        print(ERROR_REPO_NOT_EXISTS.format(repo_path_obj), file=sys.stderr)
        sys.exit(2)

    if not repo_path_obj.is_dir():
        print(ERROR_REPO_NOT_DIR.format(repo_path_obj), file=sys.stderr)
        sys.exit(2)

    # Validate rules file if provided
    if args.rules and not args.rules.exists():
        print(ERROR_RULES_NOT_EXISTS.format(args.rules), file=sys.stderr)
        sys.exit(2)

    # Store processed repo path back for later use
    args.repo_path_obj = repo_path_obj


def parse_extensions(extensions_str: str | None) -> list[str] | None:
    """Parse the comma-separated extensions string."""
    if not extensions_str:
        return None
    return [ext.strip() for ext in extensions_str.split(",")]


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate arguments
    validate_arguments(args)

    # Parse extensions
    only_extensions = parse_extensions(args.only)

    # Generate context
    try:
        exit_code = generate_context(
            repo_path=args.repo_path_obj,
            rules_file=args.rules,
            output_path=args.output,
            max_tokens=args.max_tokens,
            only_extensions=only_extensions,
            enable_summary=args.summary,
        )

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(2)


def app() -> None:
    """Entry point for the CLI application."""
    main()


if __name__ == "__main__":
    app()
