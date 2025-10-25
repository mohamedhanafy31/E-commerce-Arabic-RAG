#!/bin/bash

# Assign IAM roles to service account for Arabic RAG System
# This script assigns all necessary roles for deployment

set -e

echo "🔐 Assigning IAM roles to service account..."
echo "==========================================="

# Get project ID from environment or prompt
if [ -z "$PROJECT_ID" ]; then
    echo "Enter your GCP Project ID:"
    read PROJECT_ID
fi

SERVICE_ACCOUNT="tts-779@tts-test-475407.iam.gserviceaccount.com"

echo "📋 Project ID: $PROJECT_ID"
echo "📋 Service Account: $SERVICE_ACCOUNT"
echo ""

# Set project
gcloud config set project $PROJECT_ID

echo "🔧 Assigning required roles..."
echo ""

# Cloud Build roles
echo "1️⃣ Assigning Cloud Build roles..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudbuild.builds.editor"

# Cloud Run roles
echo "2️⃣ Assigning Cloud Run roles..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.developer"

# Container Registry roles
echo "3️⃣ Assigning Container Registry roles..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/storage.admin"

# Service Usage roles
echo "4️⃣ Assigning Service Usage roles..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/serviceusage.serviceUsageConsumer"

# IAM roles
echo "5️⃣ Assigning IAM roles..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/iam.serviceAccountUser"

# Artifact Registry roles
echo "6️⃣ Assigning Artifact Registry roles..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/artifactregistry.admin"

echo ""
echo "✅ All roles assigned successfully!"
echo ""

# List assigned roles
echo "📊 Assigned roles for $SERVICE_ACCOUNT:"
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:$SERVICE_ACCOUNT"

echo ""
echo "🎯 Next steps:"
echo "1. Wait 2-3 minutes for permissions to propagate"
echo "2. Test the deployment"
echo "3. Check GitHub Actions workflow"
