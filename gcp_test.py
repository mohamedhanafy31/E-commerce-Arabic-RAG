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
