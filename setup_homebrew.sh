#!/bin/bash

# Setup script for Homebrew tap
set -e

echo "🍺 Setting up Homebrew tap for repo2context"
echo "=========================================="

# Check if the package is published to PyPI
echo "📦 Checking if repo2context is published to PyPI..."
PYPI_URL="https://pypi.org/simple/repo2context/"
if curl -s "$PYPI_URL" | grep -q "repo2context"; then
    echo "✅ Found repo2context on PyPI"
else
    echo "❌ repo2context not found on PyPI. Please publish it first:"
    echo "   poetry build"
    echo "   poetry publish"
    exit 1
fi

# Get the latest version and download URL
echo "🔍 Getting latest version info..."
VERSION=$(python -c "
import requests
import json
response = requests.get('https://pypi.org/pypi/repo2context/json')
data = response.json()
print(data['info']['version'])
")

echo "📥 Found version: $VERSION"

# Get SHA256 for the source distribution
DOWNLOAD_URL="https://files.pythonhosted.org/packages/source/r/repo2context/repo2context-${VERSION}.tar.gz"
echo "📥 Downloading source package to get SHA256..."
wget -q "$DOWNLOAD_URL" -O "/tmp/repo2context-${VERSION}.tar.gz"
SHA256=$(shasum -a 256 "/tmp/repo2context-${VERSION}.tar.gz" | cut -d' ' -f1)
rm "/tmp/repo2context-${VERSION}.tar.gz"

echo "🔐 SHA256: $SHA256"

# Update the formula with correct version and SHA256
echo "📝 Updating formula with correct version and SHA256..."
sed -i.bak \
    -e "s/repo2context-0.1.0.tar.gz/repo2context-${VERSION}.tar.gz/g" \
    -e "s/REPLACE_WITH_ACTUAL_SHA256/${SHA256}/g" \
    homebrew-formula.rb

echo "✅ Formula updated!"

# Instructions for creating the tap
echo ""
echo "🚀 Next steps to create your Homebrew tap:"
echo "=========================================="
echo ""
echo "1. Create a new GitHub repository named 'homebrew-repo2context'"
echo "   (The name MUST start with 'homebrew-')"
echo ""
echo "2. Clone the repository and add the formula:"
echo "   git clone https://github.com/AdiMilstein/homebrew-repo2context.git"
echo "   cd homebrew-repo2context"
echo "   mkdir Formula"
echo "   cp $(pwd)/homebrew-formula.rb Formula/repo2context.rb"
echo "   git add Formula/repo2context.rb"
echo "   git commit -m 'Add repo2context formula'"
echo "   git push origin main"
echo ""
echo "3. Test the formula locally:"
echo "   brew tap AdiMilstein/repo2context"
echo "   brew install repo2context"
echo ""
echo "4. Users can then install with:"
echo "   brew tap AdiMilstein/repo2context"
echo "   brew install repo2context"
echo ""
echo "📋 Formula file ready: homebrew-formula.rb"
echo "📋 Copy this to Formula/repo2context.rb in your tap repository" 