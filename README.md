# repo2context

> One-command repo → Markdown context generator for LLM workflows

[![CI](https://github.com/AdiMilstein/repo2context/workflows/CI/badge.svg)](https://github.com/AdiMilstein/repo2context/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Transform any Git repository into optimally-sized Markdown files ready for Large Language Model (LLM) context windows. Perfect for AI pair programming, code review assistance, and documentation generation.

## Features

- 🚀 **One-command operation** - Zero configuration required
- 📊 **Smart token management** - Automatic splitting for LLM context limits
- 🎯 **Intelligent filtering** - Skip binary files, respect `.gitignore`-style patterns
- 🔧 **Flexible options** - Filter by file types, custom ignore rules, output paths
- ⚡ **High performance** - Process 1000+ files in seconds with minimal memory
- 🌍 **Cross-platform** - Works on Linux, macOS, and Windows
- 📝 **Rich output** - Syntax highlighting, file metadata, proper formatting

## Quick Start

### Installation

```bash
# Install with Homebrew (macOS/Linux)
brew tap AdiMilstein/repo2context
brew install repo2context

# Install with pipx (recommended for all platforms)
pipx install repo2context

# Or with pip
pip install repo2context

# Install with optional features
pip install "repo2context[tiktoken]"     # Accurate token counting
pip install "repo2context[summary]"      # AI-powered summaries
pip install "repo2context[all]"          # All optional features
```

### Basic Usage

```bash
# Process current directory
repo2context

# Process specific repository
repo2context /path/to/repo

# Limit to specific file types
repo2context --only py,js,ts

# Custom output location and token limit
repo2context --output ./context --max-tokens 50000
```

## Command Line Options

```
repo2context [REPO_PATH] [OPTIONS]

Arguments:
  REPO_PATH    Repository path (defaults to current directory)

Options:
  --rules PATH          Custom ignore rules file (defaults to .repo2contextignore)
  --output PATH         Output directory (defaults to ./.repo2context)
  --max-tokens INTEGER  Maximum tokens per file (default: 85000, min: 1000, max: 1000000)
  --only TEXT          File extensions to include (comma-separated, e.g. 'py,js,ts')
  --summary            Generate AI-powered file summaries (requires OpenAI API key)
  --version            Show version and exit
  --help               Show help and exit
```

## Size Limits & Token Estimates

| Model | Context Window | Recommended `--max-tokens` | Use Case |
|-------|----------------|---------------------------|----------|
| GPT-4 | 128K | 85,000 (default) | Full repository context |
| GPT-3.5 Turbo | 16K | 12,000 | Smaller projects/modules |
| Claude 3 Sonnet | 200K | 150,000 | Large codebases |
| Claude 3 Haiku | 200K | 150,000 | Fast processing |
| Llama 2 70B | 4K | 3,000 | Local/private models |

## Example Output

Generated files follow this structure:

```markdown
src/main.py
```python
# byte_count: 1247
# est_tokens: 312
#!/usr/bin/env python3
"""Main application module."""

def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()
```
---

config/settings.json
```json
# byte_count: 156
# est_tokens: 39
{
  "debug": true,
  "max_connections": 100
}
```
---

## AI-Powered File Summaries

Enable intelligent file summaries with the `--summary` flag:

```bash
# Generate summaries for all files (requires OpenAI API key)
export OPENAI_API_KEY="your-api-key-here"
repo2context --summary

# Combine with other options
repo2context --summary --only py,js,ts --max-tokens 50000
```

When enabled, each file will include a concise AI-generated summary:

```markdown
src/api/users.py
**Summary:** This module implements user management API endpoints with CRUD operations, authentication middleware, and data validation using FastAPI and Pydantic models.

```python
# byte_count: 2,847
# est_tokens: 712
from fastapi import APIRouter, Depends, HTTPException
# ... rest of file content
```

### Requirements

- Install with summary support: `pip install 'repo2context[summary]'`
- Set `OPENAI_API_KEY` environment variable
- Requires OpenAI API access (uses GPT-3.5-turbo by default)

### Summary Features

- **Intelligent Analysis**: Understands code purpose, key components, and architectural patterns
- **Concise Format**: 2-3 sentence summaries that fit within token limits
- **Graceful Degradation**: Continues processing if API calls fail
- **Large File Handling**: Skips files over 8,000 tokens to avoid API limits
- **Error Resilience**: Shows warnings for failed summaries but completes processing

## Ignore Patterns

Create a `.repo2contextignore` file in your repository root to customize which files are excluded:

```gitignore
# Custom ignore patterns (same syntax as .gitignore)
*.log
temp/
secrets.json
large_dataset.csv

# Override defaults by creating your own .repo2contextignore
```

### Default Ignore Patterns

repo2context automatically ignores:

- Version control: `.git/`, `.svn/`, `.hg/`
- Build artifacts: `dist/`, `build/`, `*.egg-info/`
- Dependencies: `node_modules/`, `.venv/`, `venv/`
- Cache: `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`
- Binary files: `*.so`, `*.dylib`, `*.dll`, `*.exe`
- OS files: `.DS_Store`, `Thumbs.db`
- Logs: `*.log`, temporary files

## Advanced Usage

### Custom Rules File

```bash
# Use custom ignore patterns
repo2context --rules my-ignore-rules.txt
```

### Extension Filtering

```bash
# Only Python and JavaScript files
repo2context --only py,js

# Include files without extensions (use empty string)
repo2context --only py,js,""
```

### Processing Large Repositories

```bash
# Split large repos into smaller chunks
repo2context --max-tokens 25000

# Focus on source code only
repo2context --only py,js,ts,jsx,tsx,go,rs,java,cpp,c,h
```

## Performance Benchmarks

Tested on MacBook Pro M1, 16GB RAM:

| Repository Size | Files | Time | Memory | Output |
|----------------|-------|------|--------|--------|
| Small (< 50 files) | 23 | 0.1s | < 50MB | 1 file |
| Medium (< 500 files) | 247 | 0.8s | < 100MB | 1-2 files |
| Large (< 1000 files) | 891 | 2.1s | < 200MB | 2-4 files |
| Huge (> 1000 files) | 2,450 | 4.7s | < 400MB | 8-12 files |

## Exit Codes

- `0` - Success, single output file created
- `1` - Success, multiple files created due to size limits
- `2` - Error (missing files, permission issues, etc.)

## Integration Examples

### CI/CD Pipeline

```yaml
- name: Generate context for AI review
  run: |
    pipx install repo2context
    repo2context --only py,js,ts --max-tokens 50000
    
- name: Upload context
  uses: actions/upload-artifact@v3
  with:
    name: code-context
    path: .repo2context/
```

### Git Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "Generating repository context..."
repo2context --max-tokens 25000
git add .repo2context/
```

### Development Workflow

```bash
# Generate context for current feature branch
git checkout feature/new-api
repo2context --only py,js --output ./pr-context

# Share with AI assistant
cat pr-context/*.md | pbcopy  # macOS
```

## Contributing

1. Clone the repository
2. Install dependencies: `poetry install`
3. Run tests: `poetry run pytest`
4. Check linting: `poetry run ruff check src/ tests/`
5. Format code: `poetry run black src/ tests/`

## Development

### Project Structure

```
repo2context/
├── src/repo2context/
│   ├── __init__.py      # Package version and exports
│   ├── cli.py           # Typer CLI interface
│   ├── core.py          # Main processing logic
│   └── utils.py         # Helper functions
├── tests/               # Test suite
├── .github/workflows/   # CI/CD
└── pyproject.toml       # Poetry configuration
```