#!/bin/bash

# =============================================================================
# Arabic RAG System - Unified Deployment Script
# =============================================================================
# This script provides a complete deployment solution for the Arabic RAG System
# Supports both local Docker deployment and Google Cloud Platform deployment
#
# Usage:
#   ./deploy.sh local          # Deploy locally with Docker Compose
#   ./deploy.sh gcp            # Deploy to Google Cloud Platform
#   ./deploy.sh cleanup        # Clean up GCP deployment
#   ./deploy.sh status         # Check deployment status
#   ./deploy.sh test           # Run comprehensive tests
#   ./deploy.sh test-quick     # Run quick tests
#   ./deploy.sh test-report    # Generate detailed test report
# =============================================================================

set -e

# =============================================================================
# Configuration
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Service configuration
SERVICES=("rag-system" "asr-api" "tts-api" "orchestrator")
PORTS=("8002" "8001" "8003" "8004")
GCP_SERVICES=("arabic-rag-system" "arabic-asr-api" "arabic-tts-api" "arabic-orchestrator")
REGION="us-central1"

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
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    print_success "Docker is installed and running"
    
    # Check Docker Compose (v2)
    if ! docker compose version > /dev/null 2>&1; then
        print_error "Docker Compose is not available. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker Compose is available"
}

check_gcp_prerequisites() {
    print_header "Checking Google Cloud Prerequisites"
    
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

check_credentials() {
    print_header "Checking Google Cloud Credentials"
    
    local missing_creds=()
    
    if [ ! -f "ASR_API/tts-key.json" ]; then
        missing_creds+=("ASR_API/tts-key.json")
    fi
    
    if [ ! -f "TTS_API/tts-key.json" ]; then
        missing_creds+=("TTS_API/tts-key.json")
    fi
    
    if [ ${#missing_creds[@]} -gt 0 ]; then
        print_error "Missing Google Cloud credentials:"
        for cred in "${missing_creds[@]}"; do
            echo "  - $cred"
        done
        echo ""
        print_status "Please add your Google Cloud service account key files."
        print_status "Download from: https://console.cloud.google.com/iam-admin/serviceaccounts"
        exit 1
    fi
    
    print_success "Google Cloud credentials found"
}

# =============================================================================
# Local Deployment Functions
# =============================================================================

deploy_local() {
    print_header "Deploying Arabic RAG System Locally"
    
    check_prerequisites
    check_environment_variables
    check_credentials
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating .env file from template..."
        cp env.example .env
        print_warning "Please edit .env file with your actual API keys before proceeding"
        read -p "Press Enter to continue after updating .env file..."
    fi
    
    # Build and start services
    print_step "Building Docker images..."
    docker compose build
    
    print_step "Starting services..."
    docker compose up -d
    
    print_step "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    check_local_health
    
    # Show service URLs
    show_local_urls
    
    # Ask if user wants to run tests
    echo ""
    read -p "Would you like to run tests to verify the deployment? (y/n): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        run_quick_tests
    fi
    
    print_success "Local deployment completed!"
}

check_local_health() {
    print_header "Checking Service Health"
    
    for i in "${!SERVICES[@]}"; do
        local service="${SERVICES[$i]}"
        local port="${PORTS[$i]}"
        
        print_status "Checking $service..."
        if curl -f "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "$service is healthy ✅"
        else
            print_warning "$service is not responding ❌"
        fi
    done
}

show_local_urls() {
    print_header "Service URLs"
    
    echo "🌐 Service Endpoints:"
    for i in "${!SERVICES[@]}"; do
        local service="${SERVICES[$i]}"
        local port="${PORTS[$i]}"
        echo "  $service:     http://localhost:$port"
    done
    
    echo ""
    echo "📚 API Documentation:"
    for i in "${!SERVICES[@]}"; do
        local service="${SERVICES[$i]}"
        local port="${PORTS[$i]}"
        echo "  $service:     http://localhost:$port/docs"
    done
    
    echo ""
    echo "🧪 Test Pages:"
    echo "  Orchestrator:   http://localhost:8004/test"
    echo "  RAG Management: http://localhost:8002/manage"
}

# =============================================================================
# Google Cloud Platform Deployment Functions
# =============================================================================

deploy_gcp() {
    print_header "Deploying Arabic RAG System to Google Cloud Platform"
    
    check_gcp_prerequisites
    check_environment_variables
    
    # Enable required APIs
    print_step "Enabling required APIs..."
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable speech.googleapis.com
    gcloud services enable texttospeech.googleapis.com
    
    print_success "APIs enabled successfully"
    
    # Build and deploy using Cloud Build
    print_step "Starting Cloud Build..."
    gcloud builds submit \
        --config cloudbuild.yaml \
        --substitutions=_GEMINI_API_KEY="$GEMINI_API_KEY",_HF_TOKEN="$HF_TOKEN"
    
    print_success "Build completed successfully!"
    
    # Get service URLs
    get_gcp_urls
    
    # Test health endpoints
    test_gcp_health
    
    # Ask if user wants to run tests
    echo ""
    read -p "Would you like to run tests to verify the GCP deployment? (y/n): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        test_gcp_deployment
    fi
    
    print_success "GCP deployment completed!"
}

get_gcp_urls() {
    print_header "Service URLs"
    
    echo "🌐 Deployed Services:"
    for service in "${GCP_SERVICES[@]}"; do
        local url=$(gcloud run services describe "$service" --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "Not deployed")
        echo "  $service: $url"
    done
    
    echo ""
    echo "🧪 Test the system at:"
    local orchestrator_url=$(gcloud run services describe "arabic-orchestrator" --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "Not deployed")
    if [ "$orchestrator_url" != "Not deployed" ]; then
        echo "  $orchestrator_url/test"
    fi
}

test_gcp_health() {
    print_header "Testing Service Health"
    
    for service in "${GCP_SERVICES[@]}"; do
        local url=$(gcloud run services describe "$service" --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "")
        if [ -n "$url" ]; then
            print_status "Testing $service..."
            if curl -s "$url/health" | jq . > /dev/null 2>&1; then
                print_success "$service: Healthy ✅"
            else
                print_warning "$service: Health check failed ❌"
            fi
        else
            print_warning "$service: Not deployed"
        fi
    done
}

test_gcp_deployment() {
    print_header "Testing GCP Deployment"
    
    # Check if Python is available
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed. Please install Python first."
        return 1
    fi
    
    # Install test dependencies if needed
    print_step "Installing test dependencies..."
    python -m pip install pytest pytest-asyncio httpx websockets requests --quiet
    
    # Create GCP-specific test script
    create_gcp_test_script
    
    # Run GCP tests
    print_step "Running GCP deployment tests..."
    if python gcp_test.py; then
        print_success "GCP deployment tests completed successfully! ✅"
        
        # Show test report location
        local report_file=$(ls -t gcp_test_report_*.json 2>/dev/null | head -1)
        if [ -n "$report_file" ]; then
            print_status "GCP test report saved: $report_file"
        fi
    else
        print_warning "Some GCP tests failed. Check the output above for details."
        return 1
    fi
}

create_gcp_test_script() {
    print_step "Creating GCP test script..."
    
    cat > gcp_test.py << 'EOF'
#!/usr/bin/env python3
"""
GCP Deployment Test Script for E-commerce Arabic RAG System
Tests deployed services on Google Cloud Platform
"""

import requests
import json
import time
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple

class GCPTestRunner:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "deployment_type": "GCP",
            "services": {},
            "tests": {},
            "summary": {}
        }
        self.service_urls = {}
        
    def get_gcp_urls(self) -> Dict[str, str]:
        """Get GCP service URLs using gcloud CLI"""
        services = {
            "rag_system": "arabic-rag-system",
            "asr_api": "arabic-asr-api", 
            "tts_api": "arabic-tts-api",
            "orchestrator": "arabic-orchestrator"
        }
        
        region = "us-central1"
        urls = {}
        
        for service_name, gcp_service in services.items():
            try:
                result = subprocess.run([
                    "gcloud", "run", "services", "describe", gcp_service,
                    "--region", region, "--format", "value(status.url)"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and result.stdout.strip():
                    urls[service_name] = result.stdout.strip()
                    print(f"✅ {service_name}: {urls[service_name]}")
                else:
                    print(f"❌ {service_name}: Not deployed")
                    
            except Exception as e:
                print(f"❌ {service_name}: Error getting URL - {e}")
        
        return urls
    
    def test_service_health(self):
        """Test GCP service health endpoints"""
        print("🏥 Testing GCP Service Health...")
        
        for service_name, url in self.service_urls.items():
            try:
                response = requests.get(f"{url}/health", timeout=10)
                if response.status_code == 200:
                    try:
                        health_data = response.json()
                        self.results["services"][service_name] = {
                            "status": "✅ Healthy",
                            "url": url,
                            "response": health_data
                        }
                        print(f"✅ {service_name}: Healthy")
                    except json.JSONDecodeError:
                        self.results["services"][service_name] = {
                            "status": "⚠️ Partial",
                            "url": url,
                            "response": response.text[:200]
                        }
                        print(f"⚠️ {service_name}: Non-JSON response")
                else:
                    self.results["services"][service_name] = {
                        "status": "❌ Error",
                        "url": url,
                        "error": f"HTTP {response.status_code}"
                    }
                    print(f"❌ {service_name}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.results["services"][service_name] = {
                    "status": "❌ Error",
                    "url": url,
                    "error": str(e)
                }
                print(f"❌ {service_name}: {e}")
    
    def test_endpoints(self):
        """Test key GCP endpoints"""
        print("🌐 Testing GCP Endpoints...")
        
        endpoints = {
            "asr_web_ui": ("asr_api", "/"),
            "tts_voices": ("tts_api", "/voices"),
            "rag_stats": ("rag_system", "/stats"),
            "orchestrator_stats": ("orchestrator", "/stats")
        }
        
        for test_name, (service_name, path) in endpoints.items():
            if service_name in self.service_urls:
                url = f"{self.service_urls[service_name]}{path}"
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        self.results["tests"][test_name] = {
                            "status": "✅ Working",
                            "url": url,
                            "response_size": len(response.text)
                        }
                        print(f"✅ {test_name}: Working")
                    else:
                        self.results["tests"][test_name] = {
                            "status": "❌ Failed",
                            "url": url,
                            "error": f"HTTP {response.status_code}"
                        }
                        print(f"❌ {test_name}: HTTP {response.status_code}")
                except Exception as e:
                    self.results["tests"][test_name] = {
                        "status": "❌ Failed",
                        "url": url,
                        "error": str(e)
                    }
                    print(f"❌ {test_name}: {e}")
            else:
                self.results["tests"][test_name] = {
                    "status": "❌ Skipped",
                    "reason": f"Service {service_name} not deployed"
                }
                print(f"⚠️ {test_name}: Service not deployed")
    
    def generate_summary(self):
        """Generate test summary"""
        healthy_services = sum(1 for s in self.results["services"].values() if "✅" in s["status"])
        total_services = len(self.results["services"])
        
        working_tests = sum(1 for t in self.results["tests"].values() if "✅" in t["status"])
        total_tests = len(self.results["tests"])
        
        self.results["summary"] = {
            "healthy_services": f"{healthy_services}/{total_services}",
            "working_tests": f"{working_tests}/{total_tests}",
            "service_percentage": (healthy_services / total_services) * 100 if total_services > 0 else 0,
            "test_percentage": (working_tests / total_tests) * 100 if total_tests > 0 else 0,
            "overall_status": "EXCELLENT" if healthy_services == total_services and working_tests == total_tests else
                             "GOOD" if healthy_services >= total_services * 0.75 else "NEEDS_ATTENTION"
        }
    
    def save_report(self):
        """Save detailed report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"gcp_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return report_file
    
    def print_report(self):
        """Print formatted report"""
        print("\n" + "="*60)
        print("📋 GCP DEPLOYMENT TEST REPORT")
        print("="*60)
        print(f"🕒 {self.results['timestamp']}")
        print(f"📊 Status: {self.results['summary']['overall_status']}")
        print()
        
        print("🏥 SERVICES:")
        print("-" * 30)
        for name, status in self.results["services"].items():
            print(f"{status['status']} {name}")
            print(f"   URL: {status['url']}")
        print()
        
        print("🧪 TESTS:")
        print("-" * 30)
        for name, status in self.results["tests"].items():
            print(f"{status['status']} {name}")
        print()
        
        print("📊 SUMMARY:")
        print("-" * 30)
        print(f"Healthy Services: {self.results['summary']['healthy_services']} ({self.results['summary']['service_percentage']:.1f}%)")
        print(f"Working Tests: {self.results['summary']['working_tests']} ({self.results['summary']['test_percentage']:.1f}%)")
        print()
        
        if self.results['summary']['overall_status'] == "EXCELLENT":
            print("🎉 GCP DEPLOYMENT FULLY OPERATIONAL!")
        elif self.results['summary']['overall_status'] == "GOOD":
            print("✅ GCP DEPLOYMENT MOSTLY WORKING")
        else:
            print("⚠️ GCP DEPLOYMENT NEEDS ATTENTION")
        
        print("="*60)
    
    def run_tests(self):
        """Run all GCP tests"""
        print("🚀 TESTING GCP DEPLOYMENT")
        print("="*30)
        
        start_time = time.time()
        
        # Get service URLs
        print("🔍 Getting GCP service URLs...")
        self.service_urls = self.get_gcp_urls()
        
        if not self.service_urls:
            print("❌ No GCP services found. Please deploy first.")
            return False
        
        self.test_service_health()
        self.test_endpoints()
        self.generate_summary()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ Completed in {duration:.2f} seconds")
        
        self.print_report()
        
        # Save report
        report_file = self.save_report()
        print(f"\n📄 Report saved: {report_file}")
        
        return self.results['summary']['overall_status'] in ["EXCELLENT", "GOOD"]

def main():
    """Main function"""
    runner = GCPTestRunner()
    success = runner.run_tests()
    
    if success:
        print("\n🎯 GCP deployment is working correctly!")
        sys.exit(0)
    else:
        print("\n⚠️ GCP deployment needs attention")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF
    
    print_success "GCP test script created"
}

# =============================================================================
# Cleanup Functions
# =============================================================================

cleanup_gcp() {
    print_header "Cleaning Up Google Cloud Platform Deployment"
    
    check_gcp_prerequisites
    
    # Confirm deletion
    print_warning "⚠️  This will delete ALL Arabic RAG System resources:"
    echo "   • Cloud Run services"
    echo "   • Container images"
    echo "   • Build history (preserved for audit)"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_status "Cleanup cancelled."
        exit 0
    fi
    
    print_step "Deleting Cloud Run services..."
    for service in "${GCP_SERVICES[@]}"; do
        print_status "Deleting service: $service"
        if gcloud run services describe "$service" --region="$REGION" --platform=managed >/dev/null 2>&1; then
            gcloud run services delete "$service" --region="$REGION" --platform=managed --quiet
            print_success "Deleted: $service"
        else
            print_warning "Service $service not found (may already be deleted)"
        fi
    done
    
    print_step "Deleting container images..."
    PROJECT_ID=$(gcloud config get-value project)
    for service in "${GCP_SERVICES[@]}"; do
        print_status "Deleting image: gcr.io/$PROJECT_ID/$service"
        if gcloud container images list-tags "gcr.io/$PROJECT_ID/$service" --format="value(digest)" >/dev/null 2>&1; then
            gcloud container images delete "gcr.io/$PROJECT_ID/$service" --force-delete-tags --quiet
            print_success "Deleted image: $service"
        else
            print_warning "Image $service not found (may already be deleted)"
        fi
    done
    
    print_success "Cleanup completed!"
}

# =============================================================================
# Testing Functions
# =============================================================================

run_comprehensive_tests() {
    print_header "Running Comprehensive Test Suite"
    
    # Check if test scripts exist
    if [ ! -f "run_all_tests.py" ]; then
        print_error "Test script 'run_all_tests.py' not found"
        exit 1
    fi
    
    # Check if Python is available
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed. Please install Python first."
        exit 1
    fi
    
    # Install test dependencies if needed
    print_step "Installing test dependencies..."
    python -m pip install pytest pytest-asyncio httpx websockets requests --quiet
    
    # Run comprehensive tests
    print_step "Running comprehensive test suite..."
    if python run_all_tests.py; then
        print_success "All comprehensive tests passed! ✅"
        
        # Show test report location
        local report_file=$(ls -t test_report_*.json 2>/dev/null | head -1)
        if [ -n "$report_file" ]; then
            print_status "Detailed report saved: $report_file"
        fi
    else
        print_warning "Some tests failed. Check the output above for details."
        return 1
    fi
}

run_quick_tests() {
    print_header "Running Quick Test Suite"
    
    # Check if test scripts exist
    if [ ! -f "master_test.py" ]; then
        print_error "Test script 'master_test.py' not found"
        exit 1
    fi
    
    # Check if Python is available
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed. Please install Python first."
        exit 1
    fi
    
    # Install test dependencies if needed
    print_step "Installing test dependencies..."
    python -m pip install pytest pytest-asyncio httpx websockets requests --quiet
    
    # Run quick tests
    print_step "Running quick test suite..."
    if python master_test.py --quick; then
        print_success "Quick tests completed successfully! ✅"
    else
        print_warning "Some quick tests failed. Check the output above for details."
        return 1
    fi
}

generate_test_report() {
    print_header "Generating Detailed Test Report"
    
    # Check if test scripts exist
    if [ ! -f "run_all_tests.py" ]; then
        print_error "Test script 'run_all_tests.py' not found"
        exit 1
    fi
    
    # Check if Python is available
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed. Please install Python first."
        exit 1
    fi
    
    # Install test dependencies if needed
    print_step "Installing test dependencies..."
    python -m pip install pytest pytest-asyncio httpx websockets requests --quiet
    
    # Run tests and generate report
    print_step "Running tests and generating detailed report..."
    if python run_all_tests.py; then
        print_success "Test report generated successfully! ✅"
        
        # Show report details
        local report_file=$(ls -t test_report_*.json 2>/dev/null | head -1)
        if [ -n "$report_file" ]; then
            local report_size=$(du -h "$report_file" | cut -f1)
            print_status "Report file: $report_file"
            print_status "Report size: $report_size"
            
            # Show summary from report
            print_step "Report Summary:"
            python -c "
import json
try:
    with open('$report_file', 'r') as f:
        data = json.load(f)
    print(f'  Timestamp: {data[\"timestamp\"]}')
    print(f'  Overall Status: {data[\"summary\"][\"overall_status\"]}')
    print(f'  Healthy Services: {data[\"summary\"][\"healthy_services\"]}/{data[\"summary\"][\"total_services\"]}')
    print(f'  Service Health: {data[\"summary\"][\"service_health_percentage\"]:.1f}%')
    print(f'  WebSocket Tests: {\"PASSED\" if data[\"summary\"][\"websocket_tests_successful\"] else \"FAILED\"}')
except Exception as e:
    print(f'  Error reading report: {e}')
"
        fi
    else
        print_warning "Test report generation failed. Check the output above for details."
        return 1
    fi
}

test_deployment() {
    print_header "Testing Deployment"
    
    # Check if services are running
    local services_running=true
    
    print_step "Checking if services are running..."
    for i in "${!SERVICES[@]}"; do
        local service="${SERVICES[$i]}"
        local port="${PORTS[$i]}"
        
        if curl -f "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "$service is running on port $port ✅"
        else
            print_warning "$service is not responding on port $port ❌"
            services_running=false
        fi
    done
    
    if [ "$services_running" = false ]; then
        print_error "Some services are not running. Please deploy first with:"
        echo "  ./deploy.sh local"
        return 1
    fi
    
    # Run appropriate tests based on deployment type
    if [ -n "$1" ] && [ "$1" = "quick" ]; then
        run_quick_tests
    else
        run_comprehensive_tests
    fi
}

# =============================================================================
# Status Functions
# =============================================================================

check_status() {
    print_header "Checking Deployment Status"
    
    # Check local deployment
    print_step "Checking local deployment..."
    if docker compose ps | grep -q "Up"; then
        print_success "Local services are running"
        check_local_health
    else
        print_warning "No local services running"
    fi
    
    echo ""
    
    # Check GCP deployment
    print_step "Checking GCP deployment..."
    if command -v gcloud &> /dev/null && gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        PROJECT_ID=$(gcloud config get-value project)
        if [ -n "$PROJECT_ID" ]; then
            print_success "GCP project: $PROJECT_ID"
            get_gcp_urls
        else
            print_warning "No GCP project set"
        fi
    else
        print_warning "GCP CLI not authenticated"
    fi
}

# =============================================================================
# Main Function
# =============================================================================

show_help() {
    echo "Arabic RAG System - Unified Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  local       Deploy locally with Docker Compose"
    echo "  gcp         Deploy to Google Cloud Platform"
    echo "  cleanup     Clean up GCP deployment"
    echo "  status      Check deployment status"
    echo "  test        Run comprehensive tests"
    echo "  test-quick  Run quick tests"
    echo "  test-report Generate detailed test report"
    echo "  test-gcp    Test GCP deployment"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 local          # Deploy locally"
    echo "  $0 gcp            # Deploy to GCP"
    echo "  $0 cleanup        # Clean up GCP"
    echo "  $0 status         # Check status"
    echo "  $0 test           # Run comprehensive tests"
    echo "  $0 test-quick     # Run quick tests"
    echo "  $0 test-report    # Generate detailed report"
    echo "  $0 test-gcp       # Test GCP deployment"
    echo ""
    echo "Prerequisites:"
    echo "  Local: Docker, Docker Compose, API keys, Google Cloud credentials"
    echo "  GCP:   Google Cloud CLI, authenticated, project set, API keys"
    echo "  Tests: Python, pip, test dependencies (auto-installed)"
}

main() {
    case "${1:-help}" in
        "local")
            deploy_local
            ;;
        "gcp")
            deploy_gcp
            ;;
        "cleanup")
            cleanup_gcp
            ;;
        "status")
            check_status
            ;;
        "test")
            test_deployment
            ;;
        "test-quick")
            test_deployment "quick"
            ;;
        "test-report")
            generate_test_report
            ;;
        "test-gcp")
            test_gcp_deployment
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
