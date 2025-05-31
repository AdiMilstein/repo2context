#!/usr/bin/env python3
"""Get SHA256 hash for repo2context PyPI package."""

import hashlib
import sys
import urllib.request
import json

def get_pypi_info():
    """Get package info from PyPI."""
    url = "https://pypi.org/pypi/repo2context/json"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"❌ Error fetching PyPI info: {e}")
        sys.exit(1)

def get_sha256(download_url):
    """Download package and calculate SHA256."""
    print(f"📥 Downloading from: {download_url}")
    try:
        with urllib.request.urlopen(download_url) as response:
            content = response.read()
            sha256_hash = hashlib.sha256(content).hexdigest()
            return sha256_hash
    except Exception as e:
        print(f"❌ Error downloading package: {e}")
        sys.exit(1)

def main():
    print("🔍 Getting repo2context package info from PyPI...")
    
    # Get package info
    pypi_data = get_pypi_info()
    version = pypi_data['info']['version']
    print(f"📦 Found version: {version}")
    
    # Find the source distribution
    releases = pypi_data['releases'][version]
    source_dist = None
    
    for release in releases:
        if release['packagetype'] == 'sdist' and release['filename'].endswith('.tar.gz'):
            source_dist = release
            break
    
    if not source_dist:
        print("❌ Could not find source distribution")
        sys.exit(1)
    
    download_url = source_dist['url']
    filename = source_dist['filename']
    
    # Calculate SHA256
    sha256 = get_sha256(download_url)
    
    print(f"✅ Package: {filename}")
    print(f"🔐 SHA256: {sha256}")
    print(f"🌐 URL: {download_url}")
    
    # Update formula
    try:
        with open('homebrew-formula.rb', 'r') as f:
            content = f.read()
        
        # Replace placeholders
        content = content.replace('repo2context-0.1.0.tar.gz', filename)
        content = content.replace('REPLACE_WITH_ACTUAL_SHA256', sha256)
        
        with open('homebrew-formula.rb', 'w') as f:
            f.write(content)
        
        print("✅ Updated homebrew-formula.rb with correct version and SHA256")
        
    except Exception as e:
        print(f"⚠️  Could not update formula file: {e}")
        print("Please manually update the formula with:")
        print(f"  url: {download_url}")
        print(f"  sha256: {sha256}")

if __name__ == "__main__":
    main() 