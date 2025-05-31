"""repo2context - One-command repo → Markdown context generator for LLM workflows."""

__version__ = "0.1.0"

from .core import generate_context
from .utils import detect_binary, estimate_tokens, guess_language

__all__ = ["generate_context", "detect_binary", "estimate_tokens", "guess_language"]
