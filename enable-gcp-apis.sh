#!/bin/bash

# Enable GCP APIs for Arabic RAG System
# This script enables all required APIs for the project

set -e

echo "🚀 Enabling GCP APIs for Arabic RAG System..."
echo "=============================================="

# Get project ID from environment or prompt
if [ -z "$PROJECT_ID" ]; then
    echo "Enter your GCP Project ID:"
    read PROJECT_ID
fi

echo "📋 Project ID: $PROJECT_ID"
echo ""

# Set project
gcloud config set project $PROJECT_ID

echo "🔧 Enabling required APIs..."
echo ""

# Enable Cloud Build API
echo "1️⃣ Enabling Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com

# Enable Cloud Run API
echo "2️⃣ Enabling Cloud Run API..."
gcloud services enable run.googleapis.com

# Enable Container Registry API
echo "3️⃣ Enabling Container Registry API..."
gcloud services enable containerregistry.googleapis.com

# Enable Artifact Registry API (newer alternative)
echo "4️⃣ Enabling Artifact Registry API..."
gcloud services enable artifactregistry.googleapis.com

# Enable Cloud Storage API
echo "5️⃣ Enabling Cloud Storage API..."
gcloud services enable storage.googleapis.com

# Enable Service Usage API
echo "6️⃣ Enabling Service Usage API..."
gcloud services enable serviceusage.googleapis.com

# Enable IAM API
echo "7️⃣ Enabling IAM API..."
gcloud services enable iam.googleapis.com

# Enable Resource Manager API
echo "8️⃣ Enabling Resource Manager API..."
gcloud services enable cloudresourcemanager.googleapis.com

echo ""
echo "✅ All APIs enabled successfully!"
echo ""

# Check enabled APIs
echo "📊 Enabled APIs:"
gcloud services list --enabled --filter="name:(cloudbuild.googleapis.com OR run.googleapis.com OR containerregistry.googleapis.com OR artifactregistry.googleapis.com OR storage.googleapis.com OR serviceusage.googleapis.com OR iam.googleapis.com OR cloudresourcemanager.googleapis.com)"

echo ""
echo "🎯 Next steps:"
echo "1. Wait 2-3 minutes for APIs to propagate"
echo "2. Run the deployment script"
echo "3. Check GitHub Actions workflow"
