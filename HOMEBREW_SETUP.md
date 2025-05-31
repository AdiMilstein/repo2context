# Homebrew Setup Guide for repo2context

This guide will help you set up Homebrew (brew) distribution for repo2context, making it easy for users to install with `brew install repo2context`.

## Prerequisites

1. **Publish to PyPI first**: Your package must be available on PyPI before creating a Homebrew formula
2. **GitHub repository**: You'll need a separate GitHub repository for your Homebrew tap

## Step 1: Publish to PyPI (if not done already)

```bash
# Build the package
poetry build

# Publish to PyPI (you'll need PyPI credentials)
poetry publish
```

## Step 2: Get Package SHA256

Run the Python script to get the correct SHA256 hash and update the formula:

```bash
python get_sha256.py
```

This will automatically update `homebrew-formula.rb` with the correct version and SHA256.

## Step 3: Create Homebrew Tap Repository

1. **Create a new GitHub repository** named `homebrew-repo2context`
   - The name MUST start with `homebrew-`
   - Make it public (required for Homebrew taps)

2. **Clone and set up the repository:**
   ```bash
   git clone https://github.com/AdiMilstein/homebrew-repo2context.git
   cd homebrew-repo2context
   
   # Create Formula directory
   mkdir Formula
   
   # Copy the formula (update path as needed)
   cp /path/to/repo2context/homebrew-formula.rb Formula/repo2context.rb
   
   # Commit and push
   git add Formula/repo2context.rb
   git commit -m "Add repo2context formula"
   git push origin main
   ```

## Step 4: Test the Formula

Test your formula locally before announcing it:

```bash
# Add your tap
brew tap AdiMilstein/repo2context

# Install from your tap
brew install repo2context

# Test it works
repo2context --version
repo2context --help

# Clean up test installation
brew uninstall repo2context
brew untap AdiMilstein/repo2context
```

## Step 5: Update Documentation

Add installation instructions to your main README.md:

```markdown
### Installation via Homebrew (macOS/Linux)

```bash
# Add the tap
brew tap AdiMilstein/repo2context

# Install repo2context
brew install repo2context

# Verify installation
repo2context --version
```

### Alternative installation methods

```bash
# Install with pipx (recommended for Python packages)
pipx install repo2context

# Or with pip
pip install repo2context
```
```

## Formula Details

The Homebrew formula (`homebrew-formula.rb`) includes:

- **Dependencies**: Python 3.11
- **Resources**: All required Python packages (pathspec, tiktoken, openai)
- **Installation**: Uses Python virtualenv for clean installation
- **Testing**: Basic functionality tests

## Maintaining the Formula

When you release a new version:

1. **Update PyPI** with the new version
2. **Run the update script**:
   ```bash
   python get_sha256.py
   ```
3. **Update the tap repository**:
   ```bash
   cd homebrew-repo2context
   cp /path/to/repo2context/homebrew-formula.rb Formula/repo2context.rb
   git add Formula/repo2context.rb
   git commit -m "Update repo2context to v1.x.x"
   git push origin main
   ```

## User Installation Instructions

Once set up, users can install with:

```bash
# One-time tap addition
brew tap AdiMilstein/repo2context

# Install/update the package
brew install repo2context

# Or install/update in one command
brew install AdiMilstein/repo2context/repo2context
```

## Troubleshooting

### Formula validation
```bash
# Validate formula syntax
brew install --build-from-source repo2context

# Audit the formula
brew audit --strict repo2context
```

### Update issues
If users report installation issues after an update:
1. Check the SHA256 hash is correct
2. Verify the PyPI package is available
3. Test the formula locally

## Advanced: Submit to Homebrew Core

For maximum visibility, you can eventually submit your formula to the main Homebrew repository (homebrew-core). This requires:

1. **Popularity**: Your package should have significant usage
2. **Stability**: No frequent breaking changes
3. **Quality**: Comprehensive tests and documentation
4. **Review process**: Submit a pull request to homebrew-core

See [Homebrew's contribution guidelines](https://docs.brew.sh/How-To-Open-a-Homebrew-Pull-Request) for details. 