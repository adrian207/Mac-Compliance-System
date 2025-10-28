#!/bin/bash
# Deploy Mac OS Zero Trust Platform to GitHub
# Author: Adrian Johnson <adrian207@gmail.com>

set -e

echo "=========================================="
echo "Mac OS Zero Trust Platform"
echo "GitHub Deployment Script v0.9.0"
echo "Author: Adrian Johnson <adrian207@gmail.com>"
echo "=========================================="
echo ""

# Configuration
REPO_URL="https://github.com/adrian207/Mac-Compliance-System.git"
VERSION="v0.9.0-beta"
BRANCH="main"

echo "📋 Pre-flight checks..."
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi
echo "✅ Git is installed"

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ README.md not found. Please run this script from the project root."
    exit 1
fi
echo "✅ In project root directory"

# Check if repository is already initialized
if [ ! -d ".git" ]; then
    echo ""
    echo "🔧 Initializing git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already initialized"
fi

# Configure git user if not set
if [ -z "$(git config user.name)" ]; then
    echo ""
    echo "⚙️  Configuring git user..."
    git config user.name "Adrian Johnson"
    git config user.email "adrian207@gmail.com"
    echo "✅ Git user configured"
fi

echo ""
echo "📦 Adding files to git..."

# Add all files
git add .

# Show status
echo ""
echo "📊 Repository status:"
git status --short

echo ""
read -p "Continue with commit? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled."
    exit 1
fi

echo ""
echo "💾 Creating commit..."

# Create commit
git commit -m "Initial release v0.9.0 Beta

Mac OS Zero Trust Endpoint Security Platform

Features:
- Device telemetry collection and risk assessment
- Compliance checking with CIS, NIST, Zero Trust policies
- Integration with Kandji, Zscaler, Seraphic
- Automated security workflow orchestration
- REST API with FastAPI
- Prometheus metrics and multi-channel alerting
- Docker deployment support
- Comprehensive documentation

Author: Adrian Johnson <adrian207@gmail.com>"

echo "✅ Commit created"

# Check if remote exists
if git remote | grep -q "origin"; then
    echo ""
    echo "✅ Remote 'origin' already configured"
    echo "   URL: $(git remote get-url origin)"
else
    echo ""
    echo "🔗 Adding remote repository..."
    git remote add origin "$REPO_URL"
    echo "✅ Remote added: $REPO_URL"
fi

# Get current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Rename to main if needed
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo ""
    echo "🔄 Renaming branch to '$BRANCH'..."
    git branch -M "$BRANCH"
    echo "✅ Branch renamed"
fi

echo ""
echo "🚀 Pushing to GitHub..."
echo ""

# Push to GitHub
git push -u origin "$BRANCH"

echo ""
echo "✅ Code pushed to GitHub!"

echo ""
echo "🏷️  Creating release tag..."

# Create annotated tag
git tag -a "$VERSION" -m "Release $VERSION

Mac OS Zero Trust Endpoint Security Platform - Beta Release

This is the initial beta release featuring:
- Comprehensive Mac OS device monitoring and risk assessment
- Multi-factor risk scoring (Security, Compliance, Behavioral, Threats)
- Integration with Kandji MDM, Zscaler, and Seraphic
- Automated security workflow orchestration
- CIS, NIST 800-53, and Zero Trust compliance checking
- REST API with OpenAPI documentation
- Prometheus metrics and alerting
- Docker deployment support

See RELEASE_NOTES_v0.9.0.md for complete details.

Author: Adrian Johnson <adrian207@gmail.com>
Date: $(date +%Y-%m-%d)"

echo "✅ Tag created: $VERSION"

echo ""
echo "📤 Pushing tag to GitHub..."
git push origin "$VERSION"

echo ""
echo "✅ Tag pushed!"

echo ""
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "Repository: $REPO_URL"
echo "Branch: $BRANCH"
echo "Version: $VERSION"
echo ""
echo "Next steps:"
echo ""
echo "1. Visit your repository:"
echo "   $REPO_URL"
echo ""
echo "2. Create a GitHub Release:"
echo "   - Go to: https://github.com/adrian207/Mac-Compliance-System/releases/new"
echo "   - Choose tag: $VERSION"
echo "   - Title: Mac OS Zero Trust Platform v0.9.0 Beta"
echo "   - Description: Copy from RELEASE_NOTES_v0.9.0.md"
echo "   - Mark as: Pre-release"
echo "   - Click: Publish release"
echo ""
echo "3. Share your release:"
echo "   git clone $REPO_URL"
echo ""
echo "=========================================="
echo ""

