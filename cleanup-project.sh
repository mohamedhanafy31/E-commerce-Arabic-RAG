#!/bin/bash

# =============================================================================
# Arabic RAG System - Project Cleanup Script
# =============================================================================
# This script identifies and removes unnecessary files before GitHub push
#
# Usage:
#   ./cleanup-project.sh list    # List files to be removed
#   ./cleanup-project.sh clean   # Remove unnecessary files
#   ./cleanup-project.sh backup  # Create backup before cleanup
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# =============================================================================
# Utility Functions
# =============================================================================

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_status() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# =============================================================================
# File Categories
# =============================================================================

# Files to definitely remove
REMOVE_FILES=(
    # Log files
    "logs/"
    "ASR_API/logs/"
    "Orchestrator/logs/"
    "simple-rag/temp/"
    "temp/"
    
    # Python cache files
    "**/__pycache__/"
    "**/*.pyc"
    "**/*.pyo"
    
    # Test audio files (large)
    "TTS_API/test1/"
    "TTS_API/test2/"
    
    # Large text files (keep one copy)
    # "simple-rag/large.txt"
    
    # Generated test reports (keep testing scripts)
    "test_report_*.json"
    "gcp_test_report_*.json"
)

# Files to keep but might be large
KEEP_BUT_LARGE=(
    "ASR_API/speaker.mp3"
    "simple-rag/data/"
    "data/"
)

# Files to review before removing
REVIEW_FILES=(
    "old_scripts/"
    "ASR_API/tts-key.json"
    "TTS_API/tts-key.json"
)

# Testing files to preserve (DO NOT REMOVE)
PRESERVE_TESTING=(
    "tests/"
    "pytest.ini"
    "gcp_test.py"
    "simple_test.py"
    "websocket_test.py"
    "test_demo.py"
    "quick_test.py"
    "master_test.py"
    "run_all_tests.py"
    "ASR_API/speaker.mp3"
    "large.txt"
)

# =============================================================================
# Cleanup Functions
# =============================================================================

list_files_to_remove() {
    print_header "Files and Directories to Remove"
    
    echo "🗑️  Files to definitely remove:"
    echo "================================"
    for item in "${REMOVE_FILES[@]}"; do
        if [ -e "$item" ] || [ -d "$item" ]; then
            size=$(du -sh "$item" 2>/dev/null | cut -f1 || echo "unknown")
            echo "  ❌ $item ($size)"
        else
            echo "  ⚪ $item (not found)"
        fi
    done
    
    echo ""
    echo "📁 Large files to review:"
    echo "=========================="
    for item in "${KEEP_BUT_LARGE[@]}"; do
        if [ -e "$item" ] || [ -d "$item" ]; then
            size=$(du -sh "$item" 2>/dev/null | cut -f1 || echo "unknown")
            echo "  ⚠️  $item ($size)"
        fi
    done
    
    echo ""
    echo "🔍 Files to review:"
    echo "==================="
    for item in "${REVIEW_FILES[@]}"; do
        if [ -e "$item" ] || [ -d "$item" ]; then
            size=$(du -sh "$item" 2>/dev/null | cut -f1 || echo "unknown")
            echo "  ❓ $item ($size)"
        fi
    done
    
    echo ""
    echo "🧪 Testing files to preserve:"
    echo "============================="
    for item in "${PRESERVE_TESTING[@]}"; do
        if [ -e "$item" ] || [ -d "$item" ]; then
            size=$(du -sh "$item" 2>/dev/null | cut -f1 || echo "unknown")
            echo "  ✅ $item ($size)"
        else
            echo "  ⚪ $item (not found)"
        fi
    done
}

create_backup() {
    print_header "Creating Backup"
    
    local backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
    print_step "Creating backup directory: $backup_dir"
    
    mkdir -p "$backup_dir"
    
    # Backup important files
    print_step "Backing up important files..."
    
    # Backup configuration files
    cp -r ASR_API/tts-key.json "$backup_dir/" 2>/dev/null || true
    cp -r TTS_API/tts-key.json "$backup_dir/" 2>/dev/null || true
    cp -r simple-rag/data/ "$backup_dir/" 2>/dev/null || true
    cp -r data/ "$backup_dir/" 2>/dev/null || true
    
    # Backup test files
    cp -r tests/ "$backup_dir/" 2>/dev/null || true
    cp -r ASR_API/speaker.mp3 "$backup_dir/" 2>/dev/null || true
    
    print_success "Backup created: $backup_dir"
    print_status "Backup size: $(du -sh "$backup_dir" | cut -f1)"
}

clean_files() {
    print_header "Cleaning Project Files"
    
    local removed_count=0
    local total_size=0
    
    # Remove files and directories
    for item in "${REMOVE_FILES[@]}"; do
        if [ -e "$item" ] || [ -d "$item" ]; then
            size=$(du -sb "$item" 2>/dev/null | cut -f1 || echo "0")
            total_size=$((total_size + size))
            
            print_step "Removing: $item"
            rm -rf "$item"
            removed_count=$((removed_count + 1))
        fi
    done
    
    # Remove Python cache files globally
    print_step "Removing Python cache files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    
    # Remove test report files
    print_step "Removing test report files..."
    rm -f test_report_*.json 2>/dev/null || true
    rm -f gcp_test_report_*.json 2>/dev/null || true
    
    print_success "Cleanup completed!"
    print_status "Files removed: $removed_count"
    print_status "Space freed: $(numfmt --to=iec $total_size)"
}

create_gitignore() {
    print_header "Creating/Updating .gitignore"
    
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/
.conda/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs/
*.log

# Data files
data/
simple-rag/data/
*.faiss
*.pkl

# Temporary files
temp/
simple-rag/temp/
*.tmp

# Test report files (keep testing scripts)
test_report_*.json
gcp_test_report_*.json

# Audio files (large)
TTS_API/test1/
TTS_API/test2/
*.mp3
*.wav
*.m4a

# API Keys (security)
*key.json
*.key
.env

# Docker
.dockerignore

# Backup files
backup_*/
old_scripts/

# Large text files
large.txt
*.txt.bak
EOF

    print_success ".gitignore created/updated"
}

show_project_size() {
    print_header "Project Size Analysis"
    
    echo "📊 Current project size:"
    echo "======================="
    
    # Overall size
    total_size=$(du -sh . | cut -f1)
    echo "Total project size: $total_size"
    echo ""
    
    # Size by directory
    echo "Size by directory:"
    du -sh */ 2>/dev/null | sort -hr | head -10
    echo ""
    
    # Largest files
    echo "Largest files:"
    find . -type f -size +1M -exec du -sh {} \; 2>/dev/null | sort -hr | head -10
}

show_help() {
    echo "Arabic RAG System - Project Cleanup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  list     List files to be removed"
    echo "  clean    Remove unnecessary files"
    echo "  backup   Create backup before cleanup"
    echo "  size     Show project size analysis"
    echo "  gitignore Create/update .gitignore"
    echo "  help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 list      # See what will be removed"
    echo "  $0 backup    # Create backup first"
    echo "  $0 clean     # Remove unnecessary files"
    echo "  $0 size      # Analyze project size"
    echo ""
    echo "Recommended workflow:"
    echo "  1. $0 list      # Review files to remove"
    echo "  2. $0 backup    # Create backup"
    echo "  3. $0 clean     # Remove files"
    echo "  4. $0 gitignore # Update .gitignore"
    echo "  5. git add . && git commit && git push"
}

# =============================================================================
# Main Function
# =============================================================================

main() {
    case "${1:-help}" in
        "list")
            list_files_to_remove
            ;;
        "clean")
            clean_files
            ;;
        "backup")
            create_backup
            ;;
        "size")
            show_project_size
            ;;
        "gitignore")
            create_gitignore
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
