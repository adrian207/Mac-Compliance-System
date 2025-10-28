# Deploy Mac OS Zero Trust Platform to GitHub
# Author: Adrian Johnson <adrian207@gmail.com>
# PowerShell script for Windows

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Mac OS Zero Trust Platform" -ForegroundColor Cyan
Write-Host "GitHub Deployment Script v0.9.0" -ForegroundColor Cyan
Write-Host "Author: Adrian Johnson <adrian207@gmail.com>" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$REPO_URL = "https://github.com/adrian207/Mac-Compliance-System.git"
$VERSION = "v0.9.0-beta"
$BRANCH = "main"

Write-Host "📋 Pre-flight checks..." -ForegroundColor Yellow
Write-Host ""

# Check if git is installed
try {
    $null = git --version
    Write-Host "✅ Git is installed" -ForegroundColor Green
}
catch {
    Write-Host "❌ Git is not installed. Please install git first." -ForegroundColor Red
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "README.md")) {
    Write-Host "❌ README.md not found. Please run this script from the project root." -ForegroundColor Red
    exit 1
}
Write-Host "✅ In project root directory" -ForegroundColor Green

# Check if repository is already initialized
if (-not (Test-Path ".git")) {
    Write-Host ""
    Write-Host "🔧 Initializing git repository..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
}
else {
    Write-Host "✅ Git repository already initialized" -ForegroundColor Green
}

# Configure git user if not set
$gitUser = git config user.name
if ([string]::IsNullOrEmpty($gitUser)) {
    Write-Host ""
    Write-Host "⚙️  Configuring git user..." -ForegroundColor Yellow
    git config user.name "Adrian Johnson"
    git config user.email "adrian207@gmail.com"
    Write-Host "✅ Git user configured" -ForegroundColor Green
}

Write-Host ""
Write-Host "📦 Adding files to git..." -ForegroundColor Yellow

# Add all files
git add .

# Show status
Write-Host ""
Write-Host "📊 Repository status:" -ForegroundColor Yellow
git status --short

Write-Host ""
$continue = Read-Host "Continue with commit? (y/n)"

if ($continue -ne "y" -and $continue -ne "Y") {
    Write-Host "❌ Deployment cancelled." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "💾 Creating commit..." -ForegroundColor Yellow

# Create commit
$commitMessage = @"
Initial release v0.9.0 Beta

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

Author: Adrian Johnson <adrian207@gmail.com>
"@

git commit -m $commitMessage

Write-Host "✅ Commit created" -ForegroundColor Green

# Check if remote exists
$remotes = git remote
if ($remotes -contains "origin") {
    Write-Host ""
    Write-Host "✅ Remote 'origin' already configured" -ForegroundColor Green
    $remoteUrl = git remote get-url origin
    Write-Host "   URL: $remoteUrl" -ForegroundColor Gray
}
else {
    Write-Host ""
    Write-Host "🔗 Adding remote repository..." -ForegroundColor Yellow
    git remote add origin $REPO_URL
    Write-Host "✅ Remote added: $REPO_URL" -ForegroundColor Green
}

# Get current branch name
$currentBranch = git rev-parse --abbrev-ref HEAD

# Rename to main if needed
if ($currentBranch -ne $BRANCH) {
    Write-Host ""
    Write-Host "🔄 Renaming branch to '$BRANCH'..." -ForegroundColor Yellow
    git branch -M $BRANCH
    Write-Host "✅ Branch renamed" -ForegroundColor Green
}

Write-Host ""
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Yellow
Write-Host ""

# Push to GitHub
git push -u origin $BRANCH

Write-Host ""
Write-Host "✅ Code pushed to GitHub!" -ForegroundColor Green

Write-Host ""
Write-Host "🏷️  Creating release tag..." -ForegroundColor Yellow

# Create annotated tag
$date = Get-Date -Format "yyyy-MM-dd"
$tagMessage = @"
Release $VERSION

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
Date: $date
"@

git tag -a $VERSION -m $tagMessage

Write-Host "✅ Tag created: $VERSION" -ForegroundColor Green

Write-Host ""
Write-Host "📤 Pushing tag to GitHub..." -ForegroundColor Yellow
git push origin $VERSION

Write-Host ""
Write-Host "✅ Tag pushed!" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repository: $REPO_URL" -ForegroundColor White
Write-Host "Branch: $BRANCH" -ForegroundColor White
Write-Host "Version: $VERSION" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Visit your repository:" -ForegroundColor White
Write-Host "   $REPO_URL" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Create a GitHub Release:" -ForegroundColor White
Write-Host "   - Go to: https://github.com/adrian207/Mac-Compliance-System/releases/new" -ForegroundColor Gray
Write-Host "   - Choose tag: $VERSION" -ForegroundColor Gray
Write-Host "   - Title: Mac OS Zero Trust Platform v0.9.0 Beta" -ForegroundColor Gray
Write-Host "   - Description: Copy from RELEASE_NOTES_v0.9.0.md" -ForegroundColor Gray
Write-Host "   - Mark as: Pre-release" -ForegroundColor Gray
Write-Host "   - Click: Publish release" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Share your release:" -ForegroundColor White
Write-Host "   git clone $REPO_URL" -ForegroundColor Gray
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

