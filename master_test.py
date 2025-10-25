#!/usr/bin/env python3
"""
Master Test Runner for E-commerce Arabic RAG System
Provides multiple testing options with comprehensive reporting
"""

import subprocess
import json
import time
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Any, Tuple

class MasterTestRunner:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "tests": {},
            "summary": {}
        }
        
    def run_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """Run a command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd="/media/hanafy/aa9ee400-c081-4d3b-b831-a2a8c83c9f447/MetaVR/E-commerce-Arabic-RAG"
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def test_services(self):
        """Test all services"""
        print("🏥 Testing Services...")
        
        services = {
            "RAG System": "http://localhost:8002/health",
            "ASR API": "http://localhost:8001/health",
            "TTS API": "http://localhost:8003/health",
            "Orchestrator": "http://localhost:8004/health"
        }
        
        for name, url in services.items():
            success, stdout, stderr = self.run_command(f"curl -s {url}")
            if success and stdout:
                try:
                    response = json.loads(stdout)
                    self.results["services"][name] = {
                        "status": "✅ Healthy",
                        "details": response.get("status", "ok"),
                        "full_response": response
                    }
                except json.JSONDecodeError:
                    self.results["services"][name] = {
                        "status": "⚠️ Partial",
                        "details": "Non-JSON response",
                        "response": stdout[:200]
                    }
            else:
                self.results["services"][name] = {
                    "status": "❌ Error",
                    "details": stderr or "No response",
                    "error": stderr
                }
    
    def test_endpoints(self):
        """Test key endpoints"""
        print("🌐 Testing Endpoints...")
        
        endpoints = {
            "ASR Web UI": "http://localhost:8001/",
            "TTS Voices": "http://localhost:8003/voices",
            "RAG Stats": "http://localhost:8002/stats",
            "Orchestrator Stats": "http://localhost:8004/stats"
        }
        
        for name, url in endpoints.items():
            success, stdout, stderr = self.run_command(f"curl -s {url}")
            if success and stdout:
                self.results["tests"][name] = {
                    "status": "✅ Working",
                    "response_size": len(stdout),
                    "url": url
                }
            else:
                self.results["tests"][name] = {
                    "status": "❌ Failed",
                    "error": stderr,
                    "url": url
                }
    
    def test_websockets(self):
        """Test WebSocket functionality"""
        print("🔌 Testing WebSockets...")
        
        success, stdout, stderr = self.run_command("python websocket_test.py", timeout=60)
        
        if success and "Successful Connections: 3/3" in stdout:
            self.results["tests"]["WebSocket Tests"] = {
                "status": "✅ All Working",
                "details": "ASR, TTS, and Orchestrator WebSockets functional",
                "output": stdout
            }
        elif success:
            self.results["tests"]["WebSocket Tests"] = {
                "status": "⚠️ Partial",
                "details": "Some WebSocket issues detected",
                "output": stdout
            }
        else:
            self.results["tests"]["WebSocket Tests"] = {
                "status": "❌ Failed",
                "error": stderr,
                "output": stdout
            }
    
    def run_comprehensive_tests(self):
        """Run comprehensive pytest tests"""
        print("🧪 Running Comprehensive Tests...")
        
        # Test individual services
        services = ["asr", "tts", "orchestrator"]
        
        for service in services:
            success, stdout, stderr = self.run_command(f"python tests/run_tests.py --service {service}", timeout=180)
            self.results["tests"][f"{service.upper()} Comprehensive"] = {
                "success": success,
                "output": stdout,
                "error": stderr
            }
    
    def generate_summary(self):
        """Generate summary"""
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
    
    def save_detailed_report(self):
        """Save detailed report to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"master_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return report_file
    
    def print_quick_report(self):
        """Print quick summary report"""
        print("\n" + "="*60)
        print("📋 QUICK TEST REPORT")
        print("="*60)
        print(f"🕒 {self.results['timestamp']}")
        print(f"📊 Status: {self.results['summary']['overall_status']}")
        print()
        
        print("🏥 SERVICES:")
        print("-" * 30)
        for name, status in self.results["services"].items():
            print(f"{status['status']} {name}")
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
        
        print("🌐 SERVICE URLs:")
        print("-" * 30)
        print("RAG System: http://localhost:8002")
        print("ASR API: http://localhost:8001")
        print("TTS API: http://localhost:8003")
        print("Orchestrator: http://localhost:8004")
        print()
        
        if self.results['summary']['overall_status'] == "EXCELLENT":
            print("🎉 ALL SYSTEMS OPERATIONAL!")
        elif self.results['summary']['overall_status'] == "GOOD":
            print("✅ MOST SYSTEMS WORKING WELL")
        else:
            print("⚠️ SOME ISSUES DETECTED")
        
        print("="*60)
    
    def print_detailed_report(self):
        """Print detailed report"""
        print("\n" + "="*80)
        print("📋 DETAILED TEST REPORT")
        print("="*80)
        print(f"🕒 Timestamp: {self.results['timestamp']}")
        print(f"📊 Overall Status: {self.results['summary']['overall_status']}")
        print()
        
        print("🏥 SERVICE DETAILS:")
        print("-" * 40)
        for name, status in self.results["services"].items():
            print(f"{status['status']} {name}")
            if 'full_response' in status:
                print(f"   Details: {status['full_response']}")
            elif 'response' in status:
                print(f"   Response: {status['response']}")
            print()
        
        print("🧪 TEST DETAILS:")
        print("-" * 40)
        for name, status in self.results["tests"].items():
            print(f"{status['status']} {name}")
            if 'details' in status:
                print(f"   Details: {status['details']}")
            if 'error' in status and status['error']:
                print(f"   Error: {status['error']}")
            print()
        
        print("📊 SUMMARY:")
        print("-" * 40)
        print(f"Healthy Services: {self.results['summary']['healthy_services']} ({self.results['summary']['service_percentage']:.1f}%)")
        print(f"Working Tests: {self.results['summary']['working_tests']} ({self.results['summary']['test_percentage']:.1f}%)")
        print()
        
        print("="*80)
    
    def run_tests(self, comprehensive=False, save_report=False):
        """Run tests based on options"""
        print("🚀 MASTER TEST RUNNER")
        print("="*30)
        
        start_time = time.time()
        
        self.test_services()
        self.test_endpoints()
        self.test_websockets()
        
        if comprehensive:
            self.run_comprehensive_tests()
        
        self.generate_summary()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ Completed in {duration:.2f} seconds")
        
        # Print report
        if comprehensive:
            self.print_detailed_report()
        else:
            self.print_quick_report()
        
        # Save report if requested
        if save_report:
            report_file = self.save_detailed_report()
            print(f"\n📄 Detailed report saved to: {report_file}")
        
        return self.results['summary']['overall_status'] in ["EXCELLENT", "GOOD"]

def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='Master Test Runner for E-commerce Arabic RAG System')
    parser.add_argument('--comprehensive', '-c', action='store_true', 
                       help='Run comprehensive tests (slower but more detailed)')
    parser.add_argument('--save-report', '-s', action='store_true',
                       help='Save detailed report to JSON file')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Run quick tests only (default)')
    
    args = parser.parse_args()
    
    # Default to quick if no specific option chosen
    if not args.comprehensive and not args.quick:
        args.quick = True
    
    runner = MasterTestRunner()
    success = runner.run_tests(
        comprehensive=args.comprehensive,
        save_report=args.save_report
    )
    
    if success:
        print("\n🎯 System is ready for use!")
        sys.exit(0)
    else:
        print("\n⚠️ System needs attention")
        sys.exit(1)

if __name__ == "__main__":
    main()
