#!/bin/bash

# =============================================================================
# Automatic Deployment Setup Script
# =============================================================================
# This script sets up automatic deployment when pushing to GitHub
#
# Usage: ./setup-auto-deploy.sh
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
# Setup Functions
# =============================================================================

install_gcloud() {
    print_header "Installing Google Cloud CLI"
    
    if command -v gcloud &> /dev/null; then
        print_success "Google Cloud CLI is already installed"
        gcloud version
        return 0
    fi
    
    print_step "Installing Google Cloud CLI..."
    sudo snap install google-cloud-cli
    
    if command -v gcloud &> /dev/null; then
        print_success "Google Cloud CLI installed successfully"
    else
        print_error "Failed to install Google Cloud CLI"
        return 1
    fi
}

authenticate_gcloud() {
    print_header "Google Cloud Authentication"
    
    print_step "Starting authentication..."
    gcloud auth login
    
    print_step "Setting project..."
    gcloud config set project arabic-rag-system
    
    print_success "Authentication completed"
    print_status "Project: $(gcloud config get-value project)"
}

enable_apis() {
    print_header "Enabling Required APIs"
    
    local apis=(
        "cloudbuild.googleapis.com"
        "run.googleapis.com"
        "containerregistry.googleapis.com"
        "speech.googleapis.com"
        "texttospeech.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        print_step "Enabling $api..."
        gcloud services enable "$api"
    done
    
    print_success "All APIs enabled"
}

create_service_account() {
    print_header "Creating Service Account"
    
    local sa_name="arabic-rag-sa"
    local sa_email="${sa_name}@arabic-rag-system.iam.gserviceaccount.com"
    
    # Check if service account already exists
    if gcloud iam service-accounts describe "$sa_email" &> /dev/null; then
        print_warning "Service account already exists"
    else
        print_step "Creating service account..."
        gcloud iam service-accounts create "$sa_name" \
            --display-name="Arabic RAG Service Account" \
            --description="Service account for Arabic RAG System CI/CD"
    fi
    
    print_step "Granting roles..."
    
    # Grant Cloud Run Admin role
    gcloud projects add-iam-policy-binding arabic-rag-system \
        --member="serviceAccount:$sa_email" \
        --role="roles/run.admin" \
        --quiet
    
    # Grant Cloud Build Editor role
    gcloud projects add-iam-policy-binding arabic-rag-system \
        --member="serviceAccount:$sa_email" \
        --role="roles/cloudbuild.builds.editor" \
        --quiet
    
    # Grant Storage Admin role
    gcloud projects add-iam-policy-binding arabic-rag-system \
        --member="serviceAccount:$sa_email" \
        --role="roles/storage.admin" \
        --quiet
    
    print_success "Service account created and configured"
}

create_service_account_key() {
    print_header "Creating Service Account Key"
    
    local sa_email="arabic-rag-sa@arabic-rag-system.iam.gserviceaccount.com"
    local key_file="tts-key.json"
    
    if [ -f "$key_file" ]; then
        print_warning "Service account key already exists"
        return 0
    fi
    
    print_step "Creating service account key..."
    gcloud iam service-accounts keys create "$key_file" \
        --iam-account="$sa_email"
    
    if [ -f "$key_file" ]; then
        print_success "Service account key created: $key_file"
        print_status "Key size: $(du -h "$key_file" | cut -f1)"
    else
        print_error "Failed to create service account key"
        return 1
    fi
}

show_github_secrets() {
    print_header "GitHub Secrets Setup"
    
    print_step "GitHub Secrets to Add:"
    echo ""
    echo "Go to: https://github.com/mohamedhanafy31/E-commerce-Arabic-RAG/settings/secrets/actions"
    echo ""
    echo "Add these 4 secrets:"
    echo ""
    echo "1. GEMINI_API_KEY"
    echo "   Value: [Your Gemini API Key]"
    echo ""
    echo "2. HF_TOKEN"
    echo "   Value: [Your Hugging Face Token]"
    echo ""
    echo "3. GCP_PROJECT_ID"
    echo "   Value: arabic-rag-system"
    echo ""
    echo "4. GCP_SA_KEY"
    echo "   Value: [Content of tts-key.json file]"
    echo ""
    
    if [ -f "tts-key.json" ]; then
        print_step "Service account key content:"
        echo "----------------------------------------"
        cat tts-key.json
        echo "----------------------------------------"
        print_warning "Copy the entire JSON content above as GCP_SA_KEY"
    else
        print_error "Service account key file not found"
    fi
}

test_deployment() {
    print_header "Testing Deployment"
    
    print_step "Testing Cloud Build..."
    echo "Please run this command manually with your API keys:"
    echo "gcloud builds submit --config cloudbuild-ci-cd.yaml \\"
    echo "    --substitutions=_GEMINI_API_KEY=\"YOUR_GEMINI_KEY\",_HF_TOKEN=\"YOUR_HF_TOKEN\" \\"
    echo "    --timeout=3600s"
    
    print_success "Deployment test completed"
}

show_final_instructions() {
    print_header "Final Instructions"
    
    echo "🎯 AUTOMATIC DEPLOYMENT IS NOW SET UP!"
    echo ""
    echo "✅ What's configured:"
    echo "   • Google Cloud CLI installed"
    echo "   • Authentication completed"
    echo "   • APIs enabled"
    echo "   • Service account created"
    echo "   • Service account key generated"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Add GitHub secrets (see above)"
    echo "   2. Test with: git push origin main"
    echo "   3. Monitor at: https://github.com/mohamedhanafy31/E-commerce-Arabic-RAG/actions"
    echo ""
    echo "🚀 Every push to main branch will now automatically deploy!"
    echo ""
    echo "📊 Monitor deployments:"
    echo "   • GitHub Actions: https://github.com/mohamedhanafy31/E-commerce-Arabic-RAG/actions"
    echo "   • Cloud Build: https://console.cloud.google.com/cloud-build"
    echo "   • Cloud Run: https://console.cloud.google.com/run"
}

# =============================================================================
# Main Function
# =============================================================================

main() {
    print_header "Arabic RAG System - Automatic Deployment Setup"
    
    echo "This script will set up automatic deployment when pushing to GitHub."
    echo "Every push to the main branch will trigger deployment to Google Cloud."
    echo ""
    
    read -p "Continue? (y/n): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    # Run setup steps
    install_gcloud
    authenticate_gcloud
    enable_apis
    create_service_account
    create_service_account_key
    show_github_secrets
    
    echo ""
    read -p "Test deployment now? (y/n): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_deployment
    fi
    
    show_final_instructions
}

# Run main function
main "$@"
