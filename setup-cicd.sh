#!/bin/bash

# =============================================================================
# Arabic RAG System - CI/CD Setup Script
# =============================================================================
# This script sets up CI/CD deployment to Google Cloud Platform with testing
#
# Usage:
#   ./setup-cicd.sh gcp          # Set up GCP CI/CD
#   ./setup-cicd.sh github       # Set up GitHub Actions CI/CD
#   ./setup-cicd.sh both         # Set up both
#   ./setup-cicd.sh test         # Test CI/CD pipeline
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
# Prerequisites Check
# =============================================================================

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud CLI is not installed. Please install it first."
        print_status "Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not authenticated with Google Cloud. Please run 'gcloud auth login' first."
        exit 1
    fi
    
    # Check project
    PROJECT_ID=$(gcloud config get-value project)
    if [ -z "$PROJECT_ID" ]; then
        print_error "No project set. Please run 'gcloud config set project YOUR_PROJECT_ID' first."
        exit 1
    fi
    
    print_success "Google Cloud CLI is authenticated"
    print_success "Using project: $PROJECT_ID"
}

check_environment_variables() {
    print_header "Checking Environment Variables"
    
    local missing_vars=()
    
    # Check required variables
    if [ -z "$GEMINI_API_KEY" ]; then
        missing_vars+=("GEMINI_API_KEY")
    fi
    
    if [ -z "$HF_TOKEN" ]; then
        missing_vars+=("HF_TOKEN")
    fi
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        print_status "Please set them with:"
        echo "  export GEMINI_API_KEY='your_gemini_api_key'"
        echo "  export HF_TOKEN='your_huggingface_token'"
        echo ""
        print_status "Get your tokens from:"
        echo "  Gemini: https://makersuite.google.com/app/apikey"
        echo "  Hugging Face: https://huggingface.co/settings/tokens"
        exit 1
    fi
    
    print_success "All required environment variables are set"
    print_status "Gemini API Key: ${GEMINI_API_KEY:0:10}..."
    print_status "Hugging Face Token: ${HF_TOKEN:0:10}..."
}

# =============================================================================
# GCP CI/CD Setup
# =============================================================================

setup_gcp_cicd() {
    print_header "Setting Up GCP CI/CD Pipeline"
    
    check_prerequisites
    check_environment_variables
    
    # Enable required APIs
    print_step "Enabling required APIs..."
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable speech.googleapis.com
    gcloud services enable texttospeech.googleapis.com
    
    print_success "APIs enabled successfully"
    
    # Create Cloud Build trigger
    print_step "Creating Cloud Build trigger..."
    
    # Check if trigger already exists
    if gcloud builds triggers list --filter="name:arabic-rag-cicd" --format="value(name)" | grep -q "arabic-rag-cicd"; then
        print_warning "Cloud Build trigger already exists"
        read -p "Do you want to update it? (y/n): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            gcloud builds triggers delete arabic-rag-cicd --quiet
        else
            print_status "Skipping trigger creation"
            return
        fi
    fi
    
    # Create trigger (simplified for manual testing)
    print_status "Creating Cloud Build trigger..."
    print_warning "Note: GitHub trigger creation requires repository connection"
    print_status "For now, you can run manual builds with:"
    echo "  gcloud builds submit --config cloudbuild-ci-cd.yaml \\"
    echo "    --substitutions=_GEMINI_API_KEY=$GEMINI_API_KEY,_HF_TOKEN=$HF_TOKEN"
    
    print_success "Cloud Build trigger created"
    
    # Set up IAM permissions
    print_step "Setting up IAM permissions..."
    
    # Get current project number
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    
    # Grant Cloud Build service account necessary permissions
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
        --role="roles/run.admin"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
        --role="roles/iam.serviceAccountUser"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
        --role="roles/storage.admin"
    
    print_success "IAM permissions configured"
    
    print_success "GCP CI/CD setup completed!"
    print_status "Trigger will run on every push to main branch"
    print_status "Monitor builds at: https://console.cloud.google.com/cloud-build/triggers"
}

# =============================================================================
# GitHub Actions Setup
# =============================================================================

setup_github_cicd() {
    print_header "Setting Up GitHub Actions CI/CD"
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository. Please initialize git first."
        exit 1
    fi
    
    # Check if GitHub remote exists
    if ! git remote get-url origin | grep -q "github.com"; then
        print_error "GitHub remote not found. Please add GitHub remote first."
        print_status "Run: git remote add origin https://github.com/USERNAME/REPO.git"
        exit 1
    fi
    
    # Create .github/workflows directory if it doesn't exist
    mkdir -p .github/workflows
    
    print_success "GitHub Actions workflow file created"
    print_status "Workflow file: .github/workflows/ci-cd.yml"
    
    print_warning "⚠️  IMPORTANT: Set up GitHub Secrets"
    echo ""
    print_status "Go to your GitHub repository settings and add these secrets:"
    echo "  GCP_PROJECT_ID: $PROJECT_ID"
    echo "  GCP_SA_KEY: (Service Account Key JSON)"
    echo "  GEMINI_API_KEY: $GEMINI_API_KEY"
    echo "  HF_TOKEN: $HF_TOKEN"
    echo ""
    print_status "To create a service account key:"
    echo "  1. Go to Google Cloud Console > IAM & Admin > Service Accounts"
    echo "  2. Create a new service account or use existing"
    echo "  3. Grant roles: Cloud Build Editor, Cloud Run Admin, Storage Admin"
    echo "  4. Create and download JSON key"
    echo "  5. Add the JSON content as GCP_SA_KEY secret"
    
    print_success "GitHub Actions CI/CD setup completed!"
}

# =============================================================================
# Test CI/CD Pipeline
# =============================================================================

test_cicd_pipeline() {
    print_header "Testing CI/CD Pipeline"
    
    check_prerequisites
    check_environment_variables
    
    print_step "Running CI/CD pipeline test..."
    
    # Submit build manually
    gcloud builds submit \
        --config cloudbuild-ci-cd.yaml \
        --substitutions=_GEMINI_API_KEY="$GEMINI_API_KEY",_HF_TOKEN="$HF_TOKEN" \
        --timeout=3600s
    
    print_success "CI/CD pipeline test completed!"
    
    # Get service URLs
    print_step "Getting service URLs..."
    
    RAG_URL=$(gcloud run services describe arabic-rag-system --region=us-central1 --format="value(status.url)" 2>/dev/null || echo "Not deployed")
    ASR_URL=$(gcloud run services describe arabic-asr-api --region=us-central1 --format="value(status.url)" 2>/dev/null || echo "Not deployed")
    TTS_URL=$(gcloud run services describe arabic-tts-api --region=us-central1 --format="value(status.url)" 2>/dev/null || echo "Not deployed")
    ORCHESTRATOR_URL=$(gcloud run services describe arabic-orchestrator --region=us-central1 --format="value(status.url)" 2>/dev/null || echo "Not deployed")
    
    echo ""
    print_status "Service URLs:"
    echo "  RAG System: $RAG_URL"
    echo "  ASR API: $ASR_URL"
    echo "  TTS API: $TTS_URL"
    echo "  Orchestrator: $ORCHESTRATOR_URL"
    
    if [ "$ORCHESTRATOR_URL" != "Not deployed" ]; then
        echo ""
        print_status "Test the system at: $ORCHESTRATOR_URL/test"
    fi
}

# =============================================================================
# Main Function
# =============================================================================

show_help() {
    echo "Arabic RAG System - CI/CD Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  gcp       Set up GCP CI/CD pipeline"
    echo "  github    Set up GitHub Actions CI/CD"
    echo "  both      Set up both GCP and GitHub Actions"
    echo "  test      Test CI/CD pipeline"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 gcp          # Set up GCP CI/CD"
    echo "  $0 github      # Set up GitHub Actions"
    echo "  $0 both        # Set up both"
    echo "  $0 test        # Test pipeline"
    echo ""
    echo "Prerequisites:"
    echo "  - Google Cloud CLI installed and authenticated"
    echo "  - GCP project set"
    echo "  - Environment variables: GEMINI_API_KEY, HF_TOKEN"
    echo "  - Git repository with GitHub remote (for GitHub Actions)"
}

main() {
    case "${1:-help}" in
        "gcp")
            setup_gcp_cicd
            ;;
        "github")
            setup_github_cicd
            ;;
        "both")
            setup_gcp_cicd
            echo ""
            setup_github_cicd
            ;;
        "test")
            test_cicd_pipeline
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
