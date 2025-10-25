#!/usr/bin/env python3
"""
Simplified Test Runner for E-commerce Arabic RAG System
Runs essential tests and provides a clean report
"""

import subprocess
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple

class SimpleTestRunner:
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
                        "details": response.get("status", "ok")
                    }
                except json.JSONDecodeError:
                    self.results["services"][name] = {
                        "status": "⚠️ Partial",
                        "details": "Non-JSON response"
                    }
            else:
                self.results["services"][name] = {
                    "status": "❌ Error",
                    "details": stderr or "No response"
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
                    "response_size": len(stdout)
                }
            else:
                self.results["tests"][name] = {
                    "status": "❌ Failed",
                    "error": stderr
                }
    
    def test_websockets(self):
        """Test WebSocket functionality"""
        print("🔌 Testing WebSockets...")
        
        success, stdout, stderr = self.run_command("python websocket_test.py", timeout=60)
        
        if success and "Successful Connections: 3/3" in stdout:
            self.results["tests"]["WebSocket Tests"] = {
                "status": "✅ All Working",
                "details": "ASR, TTS, and Orchestrator WebSockets functional"
            }
        elif success:
            self.results["tests"]["WebSocket Tests"] = {
                "status": "⚠️ Partial",
                "details": "Some WebSocket issues detected"
            }
        else:
            self.results["tests"]["WebSocket Tests"] = {
                "status": "❌ Failed",
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
            "overall_status": "EXCELLENT" if healthy_services == total_services and working_tests == total_tests else
                             "GOOD" if healthy_services >= total_services * 0.75 else "NEEDS_ATTENTION"
        }
    
    def print_report(self):
        """Print formatted report"""
        print("\n" + "="*60)
        print("📋 SYSTEM TEST REPORT")
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
        print(f"Healthy Services: {self.results['summary']['healthy_services']}")
        print(f"Working Tests: {self.results['summary']['working_tests']}")
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
    
    def run_tests(self):
        """Run all tests"""
        print("🚀 RUNNING SYSTEM TESTS")
        print("="*30)
        
        start_time = time.time()
        
        self.test_services()
        self.test_endpoints()
        self.test_websockets()
        self.generate_summary()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ Completed in {duration:.2f} seconds")
        
        self.print_report()
        
        return self.results['summary']['overall_status'] in ["EXCELLENT", "GOOD"]

def main():
    """Main function"""
    runner = SimpleTestRunner()
    success = runner.run_tests()
    
    if success:
        print("\n🎯 System is ready for use!")
        sys.exit(0)
    else:
        print("\n⚠️ System needs attention")
        sys.exit(1)

if __name__ == "__main__":
    main()
