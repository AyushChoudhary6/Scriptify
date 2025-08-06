#!/bin/bash

# ========================================
# 🔧 Scriptify Git Repository Setup Script
# ========================================
# This script initializes the git repository and sets up remotes

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header "🔧 Scriptify Git Setup"

# Initialize git if not already done
if [ ! -d ".git" ]; then
    print_status "Initializing Git repository..."
    git init
    print_status "Git repository initialized!"
else
    print_status "Git repository already exists"
fi

# Set default branch to main
print_status "Setting default branch to 'main'..."
git branch -M main

# Add remotes
print_status "Setting up remote repositories..."

# GitHub
if git remote | grep -q "^origin$"; then
    print_warning "GitHub remote 'origin' already exists, updating URL..."
    git remote set-url origin https://github.com/AyushChoudhary6/Scriptify.git
else
    print_status "Adding GitHub remote..."
    git remote add origin https://github.com/AyushChoudhary6/Scriptify.git
fi

# GitLab
if git remote | grep -q "^gitlab$"; then
    print_warning "GitLab remote 'gitlab' already exists, updating URL..."
    git remote set-url gitlab https://gitlab.com/AyushChoudhary6/Scriptify.git
else
    print_status "Adding GitLab remote..."
    git remote add gitlab https://gitlab.com/AyushChoudhary6/Scriptify.git
fi

print_status "Configured remotes:"
git remote -v

print_status "✅ Git setup completed!"
print_status "📝 Now you can use './push-to-both.sh' to push to both repositories"
