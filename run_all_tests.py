#!/usr/bin/env python3
"""
Master Test Runner for E-commerce Arabic RAG System
Runs all test scripts and generates a comprehensive report
"""

import subprocess
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple
import os

class TestRunner:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {},
            "service_health": {},
            "basic_tests": {},
            "websocket_tests": {},
            "comprehensive_tests": {},
            "summary": {},
            "recommendations": []
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
    
    def check_system_info(self):
        """Check system information and running processes"""
        print("🔍 Checking System Information...")
        
        # Check conda environments
        success, stdout, stderr = self.run_command("conda env list")
        self.results["system_info"]["conda_envs"] = stdout if success else stderr
        
        # Check running Python processes
        success, stdout, stderr = self.run_command("ps aux | grep python | grep -E '(main\\.py|run\\.py)'")
        self.results["system_info"]["python_processes"] = stdout if success else stderr
        
        # Check listening ports
        success, stdout, stderr = self.run_command("netstat -tlnp | grep -E ':(8001|8002|8003|8004)'")
        self.results["system_info"]["listening_ports"] = stdout if success else stderr
        
        print("✅ System information collected")
    
    def test_service_health(self):
        """Test service health endpoints"""
        print("🏥 Testing Service Health...")
        
        services = {
            "rag_system": "http://localhost:8002/health",
            "asr_api": "http://localhost:8001/health",
            "tts_api": "http://localhost:8003/health",
            "orchestrator": "http://localhost:8004/health"
        }
        
        for service, url in services.items():
            success, stdout, stderr = self.run_command(f"curl -s {url}")
            if success and stdout:
                try:
                    response = json.loads(stdout)
                    self.results["service_health"][service] = {
                        "status": "healthy",
                        "response": response
                    }
                except json.JSONDecodeError:
                    self.results["service_health"][service] = {
                        "status": "unhealthy",
                        "response": stdout[:200]
                    }
            else:
                self.results["service_health"][service] = {
                    "status": "error",
                    "error": stderr
                }
        
        print("✅ Service health tests completed")
    
    def run_basic_tests(self):
        """Run basic HTTP endpoint tests"""
        print("🌐 Running Basic Tests...")
        
        # Run simple test script
        success, stdout, stderr = self.run_command("python simple_test.py", timeout=60)
        self.results["basic_tests"]["simple_test"] = {
            "success": success,
            "output": stdout,
            "error": stderr
        }
        
        # Test individual endpoints
        endpoints = {
            "asr_root": "http://localhost:8001/",
            "tts_voices": "http://localhost:8003/voices",
            "orchestrator_stats": "http://localhost:8004/stats",
            "rag_stats": "http://localhost:8002/stats"
        }
        
        for endpoint, url in endpoints.items():
            success, stdout, stderr = self.run_command(f"curl -s {url}")
            self.results["basic_tests"][endpoint] = {
                "success": success,
                "response_length": len(stdout) if stdout else 0,
                "error": stderr if stderr else None
            }
        
        print("✅ Basic tests completed")
    
    def run_websocket_tests(self):
        """Run WebSocket tests"""
        print("🔌 Running WebSocket Tests...")
        
        success, stdout, stderr = self.run_command("python websocket_test.py", timeout=120)
        self.results["websocket_tests"]["websocket_test"] = {
            "success": success,
            "output": stdout,
            "error": stderr
        }
        
        print("✅ WebSocket tests completed")
    
    def run_comprehensive_tests(self):
        """Run comprehensive pytest tests"""
        print("🧪 Running Comprehensive Tests...")
        
        # Test individual services
        services = ["asr", "tts", "orchestrator"]
        
        for service in services:
            success, stdout, stderr = self.run_command(f"python tests/run_tests.py --service {service}", timeout=180)
            self.results["comprehensive_tests"][f"{service}_tests"] = {
                "success": success,
                "output": stdout,
                "error": stderr
            }
        
        # Test WebSocket functionality
        success, stdout, stderr = self.run_command("python tests/run_tests.py --websocket", timeout=120)
        self.results["comprehensive_tests"]["websocket_tests"] = {
            "success": success,
            "output": stdout,
            "error": stderr
        }
        
        print("✅ Comprehensive tests completed")
    
    def generate_summary(self):
        """Generate test summary and recommendations"""
        print("📊 Generating Summary...")
        
        # Count healthy services
        healthy_services = sum(1 for service in self.results["service_health"].values() 
                              if service["status"] == "healthy")
        total_services = len(self.results["service_health"])
        
        # Count successful basic tests
        successful_basic_tests = sum(1 for test in self.results["basic_tests"].values() 
                                   if isinstance(test, dict) and test.get("success", False))
        
        # Count successful WebSocket tests
        websocket_success = self.results["websocket_tests"]["websocket_test"]["success"]
        
        # Count successful comprehensive tests
        successful_comprehensive_tests = sum(1 for test in self.results["comprehensive_tests"].values() 
                                            if isinstance(test, dict) and test.get("success", False))
        
        self.results["summary"] = {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "service_health_percentage": (healthy_services / total_services) * 100 if total_services > 0 else 0,
            "successful_basic_tests": successful_basic_tests,
            "websocket_tests_successful": websocket_success,
            "successful_comprehensive_tests": successful_comprehensive_tests,
            "overall_status": "EXCELLENT" if healthy_services == total_services and websocket_success else 
                             "GOOD" if healthy_services >= total_services * 0.75 else "NEEDS_ATTENTION"
        }
        
        # Generate recommendations
        recommendations = []
        
        if healthy_services < total_services:
            recommendations.append("Some services are not healthy - check logs and configuration")
        
        if not websocket_success:
            recommendations.append("WebSocket tests failed - check WebSocket connectivity")
        
        if successful_comprehensive_tests < len(self.results["comprehensive_tests"]):
            recommendations.append("Some comprehensive tests failed - review test results")
        
        if not recommendations:
            recommendations.append("All systems are working perfectly! Ready for production use.")
        
        self.results["recommendations"] = recommendations
        
        print("✅ Summary generated")
    
    def save_report(self):
        """Save detailed report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_file}")
        return report_file
    
    def print_summary_report(self):
        """Print a formatted summary report"""
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE TEST REPORT")
        print("="*80)
        print(f"🕒 Timestamp: {self.results['timestamp']}")
        print(f"📊 Overall Status: {self.results['summary']['overall_status']}")
        print()
        
        print("🏥 SERVICE HEALTH:")
        print("-" * 40)
        for service, status in self.results["service_health"].items():
            icon = "✅" if status["status"] == "healthy" else "❌" if status["status"] == "error" else "⚠️"
            print(f"{icon} {service.upper()}: {status['status']}")
        print()
        
        print("🧪 TEST RESULTS:")
        print("-" * 40)
        print(f"✅ Service Health: {self.results['summary']['healthy_services']}/{self.results['summary']['total_services']} services")
        print(f"✅ Basic Tests: {self.results['summary']['successful_basic_tests']} successful")
        print(f"✅ WebSocket Tests: {'PASSED' if self.results['summary']['websocket_tests_successful'] else 'FAILED'}")
        print(f"✅ Comprehensive Tests: {self.results['summary']['successful_comprehensive_tests']} successful")
        print()
        
        print("💡 RECOMMENDATIONS:")
        print("-" * 40)
        for i, rec in enumerate(self.results["recommendations"], 1):
            print(f"{i}. {rec}")
        print()
        
        print("🌐 SERVICE URLs:")
        print("-" * 40)
        print("RAG System: http://localhost:8002")
        print("ASR API: http://localhost:8001")
        print("TTS API: http://localhost:8003")
        print("Orchestrator: http://localhost:8004")
        print()
        
        print("="*80)
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 STARTING COMPREHENSIVE TEST SUITE")
        print("="*50)
        print()
        
        start_time = time.time()
        
        try:
            self.check_system_info()
            self.test_service_health()
            self.run_basic_tests()
            self.run_websocket_tests()
            self.run_comprehensive_tests()
            self.generate_summary()
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"\n⏱️ Total test duration: {duration:.2f} seconds")
            
            # Save detailed report
            report_file = self.save_report()
            
            # Print summary
            self.print_summary_report()
            
            print(f"\n📄 Full detailed report saved to: {report_file}")
            
            return self.results["summary"]["overall_status"] == "EXCELLENT"
            
        except KeyboardInterrupt:
            print("\n⚠️ Tests interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            return False

def main():
    """Main function"""
    runner = TestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! System is ready for use.")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Check the report for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
