#!/usr/bin/env python3
"""A simple test script for repo2context."""


def hello_world():
    """Print a friendly greeting."""
    print("Hello, world!")


def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


if __name__ == "__main__":
    hello_world()
    result = add_numbers(2, 3)
    print(f"2 + 3 = {result}")
