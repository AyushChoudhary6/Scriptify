#!/bin/bash

# ========================================
# 🚀 Scriptify Multi-Repository Push Script
# ========================================
# This script pushes code to both GitHub and GitLab simultaneously
# and triggers GitLab CI/CD pipeline automatically

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}🚀 $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# Check if git is initialized
check_git_init() {
    if [ ! -d ".git" ]; then
        print_error "Git repository not initialized!"
        print_status "Initializing git repository..."
        git init
        print_success "Git repository initialized!"
    fi
}

# Setup remote repositories
setup_remotes() {
    print_header "Setting up Remote Repositories"
    
    # Check if GitHub remote exists
    if git remote | grep -q "^origin$"; then
        print_status "GitHub remote 'origin' already exists"
        git remote set-url origin https://github.com/AyushChoudhary6/Scriptify.git
    else
        print_status "Adding GitHub remote..."
        git remote add origin https://github.com/AyushChoudhary6/Scriptify.git
    fi
    
    # Check if GitLab remote exists
    if git remote | grep -q "^gitlab$"; then
        print_status "GitLab remote 'gitlab' already exists"
        git remote set-url gitlab https://gitlab.com/AyushChoudhary6/Scriptify.git
    else
        print_status "Adding GitLab remote..."
        git remote add gitlab https://gitlab.com/AyushChoudhary6/Scriptify.git
    fi
    
    print_success "Remote repositories configured!"
    echo ""
    print_status "Current remotes:"
    git remote -v
    echo ""
}

# Function to check if there are changes to commit
check_changes() {
    if [ -z "$(git status --porcelain)" ]; then
        print_warning "No changes detected in the repository"
        return 1
    fi
    return 0
}

# Function to display current status
show_status() {
    print_header "Repository Status"
    echo ""
    print_status "Current branch: $(git branch --show-current)"
    print_status "Repository status:"
    git status --short
    echo ""
    
    if [ -n "$(git status --porcelain)" ]; then
        print_status "Files to be committed:"
        git status --porcelain | while read line; do
            echo "  $line"
        done
        echo ""
    fi
}

# Function to commit changes
commit_changes() {
    print_header "Committing Changes"
    
    if [ -z "$1" ]; then
        echo ""
        print_status "Enter commit message (or press Enter for default):"
        read -r commit_message
        
        if [ -z "$commit_message" ]; then
            commit_message="Update: $(date '+%Y-%m-%d %H:%M:%S')"
        fi
    else
        commit_message="$1"
    fi
    
    print_status "Adding all changes..."
    git add .
    
    print_status "Committing with message: '$commit_message'"
    git commit -m "$commit_message"
    
    print_success "Changes committed successfully!"
}

# Function to push to repositories
push_to_repositories() {
    print_header "Pushing to Remote Repositories"
    
    # Get current branch
    current_branch=$(git branch --show-current)
    
    if [ -z "$current_branch" ]; then
        current_branch="main"
        print_status "Setting default branch to 'main'"
        git branch -M main
    fi
    
    print_status "Current branch: $current_branch"
    echo ""
    
    # Push to GitHub
    print_status "📤 Pushing to GitHub (origin)..."
    if git push origin "$current_branch"; then
        print_success "✅ Successfully pushed to GitHub!"
    else
        print_error "❌ Failed to push to GitHub"
        return 1
    fi
    
    echo ""
    
    # Push to GitLab (this will trigger CI/CD pipeline)
    print_status "📤 Pushing to GitLab (gitlab)..."
    if git push gitlab "$current_branch"; then
        print_success "✅ Successfully pushed to GitLab!"
        print_success "🔧 GitLab CI/CD Pipeline should be triggered automatically!"
    else
        print_error "❌ Failed to push to GitLab"
        return 1
    fi
}

# Function to show pipeline information
show_pipeline_info() {
    print_header "Pipeline Information"
    echo ""
    print_status "🔗 Repository Links:"
    echo "   📚 GitHub: https://github.com/AyushChoudhary6/Scriptify"
    echo "   🦊 GitLab: https://gitlab.com/AyushChoudhary6/Scriptify"
    echo ""
    print_status "🔧 Pipeline Monitoring:"
    echo "   📊 GitLab Pipelines: https://gitlab.com/AyushChoudhary6/Scriptify/-/pipelines"
    echo "   📋 GitLab CI/CD: https://gitlab.com/AyushChoudhary6/Scriptify/-/ci/pipelines"
    echo ""
    print_status "📱 Application URLs (after deployment):"
    echo "   🌐 Frontend: http://localhost:3000"
    echo "   🔧 Backend API: http://localhost:8000"
    echo "   📖 API Docs: http://localhost:8000/docs"
    echo ""
}

# Function to validate environment
validate_environment() {
    print_header "Environment Validation"
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed!"
        exit 1
    fi
    
    print_success "✅ Git is installed"
    
    # Check if docker is available (optional)
    if command -v docker &> /dev/null; then
        print_success "✅ Docker is available"
    else
        print_warning "⚠️  Docker not found (optional for deployment)"
    fi
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ] || [ ! -f "backend/main.py" ]; then
        print_error "❌ Not in Scriptify project directory!"
        print_error "Please run this script from the Scriptify project root"
        exit 1
    fi
    
    print_success "✅ In correct project directory"
    echo ""
}

# Main execution function
main() {
    clear
    print_header "Scriptify Multi-Repository Push Tool"
    echo ""
    print_status "🎥 Intelligent Video Summarization App"
    print_status "🚀 Pushing to GitHub + GitLab with CI/CD"
    echo ""
    
    # Validate environment
    validate_environment
    
    # Initialize git if needed
    check_git_init
    
    # Setup remotes
    setup_remotes
    
    # Show current status
    show_status
    
    # Check if there are changes
    if ! check_changes && [ "$1" != "--force" ]; then
        print_warning "No changes to commit. Use --force to push anyway."
        exit 0
    fi
    
    # Commit changes if there are any
    if [ -n "$(git status --porcelain)" ]; then
        commit_changes "$1"
    fi
    
    # Push to both repositories
    if push_to_repositories; then
        echo ""
        print_success "🎉 Successfully pushed to both repositories!"
        show_pipeline_info
    else
        print_error "❌ Push failed!"
        exit 1
    fi
}

# Handle script arguments
case "$1" in
    --help|-h)
        echo "Scriptify Multi-Repository Push Script"
        echo ""
        echo "Usage:"
        echo "  ./push-to-both.sh [commit_message]"
        echo "  ./push-to-both.sh --force"
        echo "  ./push-to-both.sh --help"
        echo ""
        echo "Options:"
        echo "  commit_message    Custom commit message"
        echo "  --force           Push even if no changes detected"
        echo "  --help, -h        Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./push-to-both.sh"
        echo "  ./push-to-both.sh 'Add new feature'"
        echo "  ./push-to-both.sh --force"
        exit 0
        ;;
    --force)
        main --force
        ;;
    *)
        main "$1"
        ;;
esac
