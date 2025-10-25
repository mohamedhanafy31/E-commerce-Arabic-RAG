#!/usr/bin/env python3
"""
Comprehensive Test Runner for E-commerce Arabic RAG System
Runs all unit tests for all microservices
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestRunner:
    """Main test runner class"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.test_dir = self.project_root / "tests"
        self.results = {}
        
    def run_command(self, command: List[str], cwd: str = None) -> Dict[str, Any]:
        """Run a command and return results"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def check_service_health(self, service_name: str, port: int) -> bool:
        """Check if a service is running"""
        import requests
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_all_services(self) -> Dict[str, bool]:
        """Check health of all services"""
        services = {
            "rag_system": 8002,
            "asr_api": 8001,
            "tts_api": 8003,
            "orchestrator": 8004
        }
        
        health_status = {}
        for service, port in services.items():
            health_status[service] = self.check_service_health(service, port)
        
        return health_status
    
    def install_test_dependencies(self) -> bool:
        """Install test dependencies"""
        print("📦 Installing test dependencies...")
        
        dependencies = [
            "pytest",
            "pytest-asyncio",
            "httpx",
            "websockets",
            "requests"
        ]
        
        for dep in dependencies:
            result = self.run_command(["pip", "install", dep])
            if not result["success"]:
                print(f"❌ Failed to install {dep}: {result['stderr']}")
                return False
        
        print("✅ Test dependencies installed successfully")
        return True
    
    def run_pytest_tests(self, test_file: str = None, verbose: bool = False) -> Dict[str, Any]:
        """Run pytest tests"""
        print(f"🧪 Running pytest tests{' for ' + test_file if test_file else ''}...")
        
        cmd = ["python", "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        
        if test_file:
            cmd.append(str(self.test_dir / test_file))
        else:
            cmd.append(str(self.test_dir))
        
        cmd.extend([
            "--tb=short",
            "--color=yes",
            "-x"  # Stop on first failure
        ])
        
        result = self.run_command(cmd)
        
        if result["success"]:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            print(f"STDOUT: {result['stdout']}")
            print(f"STDERR: {result['stderr']}")
        
        return result
    
    def run_specific_service_tests(self, service: str, verbose: bool = False) -> Dict[str, Any]:
        """Run tests for a specific service"""
        test_files = {
            "rag": "test_rag_system.py",
            "asr": "test_asr_api.py",
            "tts": "test_tts_api.py",
            "orchestrator": "test_orchestrator.py"
        }
        
        if service not in test_files:
            print(f"❌ Unknown service: {service}")
            return {"success": False, "stderr": f"Unknown service: {service}"}
        
        return self.run_pytest_tests(test_files[service], verbose)
    
    def run_websocket_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run WebSocket-specific tests"""
        print("🔌 Running WebSocket tests...")
        
        # Check if services are running
        health_status = self.check_all_services()
        running_services = [service for service, status in health_status.items() if status]
        
        if not running_services:
            print("❌ No services are running. Please start services first.")
            return {"success": False, "stderr": "No services running"}
        
        print(f"✅ Found running services: {', '.join(running_services)}")
        
        # Run WebSocket tests
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "websocket_utils.py"),
            "-v" if verbose else "",
            "--tb=short",
            "--color=yes"
        ]
        
        # Filter out empty strings
        cmd = [c for c in cmd if c]
        
        result = self.run_command(cmd)
        
        if result["success"]:
            print("✅ WebSocket tests passed!")
        else:
            print("❌ WebSocket tests failed!")
            print(f"STDOUT: {result['stdout']}")
            print(f"STDERR: {result['stderr']}")
        
        return result
    
    def run_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run integration tests"""
        print("🔗 Running integration tests...")
        
        # Check if all services are running
        health_status = self.check_all_services()
        all_running = all(health_status.values())
        
        if not all_running:
            missing_services = [service for service, status in health_status.items() if not status]
            print(f"❌ Missing services: {', '.join(missing_services)}")
            print("Please start all services before running integration tests.")
            return {"success": False, "stderr": f"Missing services: {missing_services}"}
        
        print("✅ All services are running")
        
        # Run integration tests (marked with @pytest.mark.integration)
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "integration",
            "-v" if verbose else "",
            "--tb=short",
            "--color=yes"
        ]
        
        # Filter out empty strings
        cmd = [c for c in cmd if c]
        
        result = self.run_command(cmd)
        
        if result["success"]:
            print("✅ Integration tests passed!")
        else:
            print("❌ Integration tests failed!")
            print(f"STDOUT: {result['stdout']}")
            print(f"STDERR: {result['stderr']}")
        
        return result
    
    def generate_test_report(self) -> str:
        """Generate a test report"""
        report = []
        report.append("# Test Report")
        report.append(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Service health status
        health_status = self.check_all_services()
        report.append("## Service Health Status")
        for service, status in health_status.items():
            status_icon = "✅" if status else "❌"
            report.append(f"- {service}: {status_icon}")
        report.append("")
        
        # Test results summary
        report.append("## Test Results Summary")
        for test_name, result in self.results.items():
            status_icon = "✅" if result.get("success", False) else "❌"
            report.append(f"- {test_name}: {status_icon}")
        report.append("")
        
        return "\n".join(report)
    
    def run_all_tests(self, verbose: bool = False, skip_websocket: bool = False) -> bool:
        """Run all tests"""
        print("🚀 Starting comprehensive test suite...")
        print("=" * 50)
        
        # Install dependencies
        if not self.install_test_dependencies():
            return False
        
        # Check service health
        health_status = self.check_all_services()
        print("\n📊 Service Health Status:")
        for service, status in health_status.items():
            status_icon = "✅" if status else "❌"
            print(f"  {service}: {status_icon}")
        
        all_passed = True
        
        # Run individual service tests
        services = ["rag", "asr", "tts", "orchestrator"]
        for service in services:
            print(f"\n🧪 Testing {service.upper()} service...")
            result = self.run_specific_service_tests(service, verbose)
            self.results[f"{service}_tests"] = result
            if not result["success"]:
                all_passed = False
        
        # Run WebSocket tests if services are running and not skipped
        if not skip_websocket and any(health_status.values()):
            print(f"\n🔌 Testing WebSocket endpoints...")
            result = self.run_websocket_tests(verbose)
            self.results["websocket_tests"] = result
            if not result["success"]:
                all_passed = False
        
        # Run integration tests if all services are running
        if all(health_status.values()):
            print(f"\n🔗 Testing integration...")
            result = self.run_integration_tests(verbose)
            self.results["integration_tests"] = result
            if not result["success"]:
                all_passed = False
        
        # Generate report
        report = self.generate_test_report()
        print(f"\n📋 Test Report:")
        print("=" * 50)
        print(report)
        
        # Save report to file
        report_file = self.project_root / "test_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")
        
        return all_passed

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run tests for E-commerce Arabic RAG System")
    parser.add_argument("--service", choices=["rag", "asr", "tts", "orchestrator"], 
                       help="Run tests for specific service only")
    parser.add_argument("--websocket", action="store_true", 
                       help="Run WebSocket tests only")
    parser.add_argument("--integration", action="store_true", 
                       help="Run integration tests only")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--skip-websocket", action="store_true", 
                       help="Skip WebSocket tests")
    parser.add_argument("--install-deps", action="store_true", 
                       help="Install test dependencies only")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.install_deps:
        success = runner.install_test_dependencies()
        sys.exit(0 if success else 1)
    
    if args.service:
        success = runner.run_specific_service_tests(args.service, args.verbose)["success"]
    elif args.websocket:
        success = runner.run_websocket_tests(args.verbose)["success"]
    elif args.integration:
        success = runner.run_integration_tests(args.verbose)["success"]
    else:
        success = runner.run_all_tests(args.verbose, args.skip_websocket)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
