#!/usr/bin/env python3
"""
Simple Test Script for E-commerce Arabic RAG System
Tests basic functionality without complex dependencies
"""

import requests
import json
import time
from typing import Dict, Any

def test_service_health() -> Dict[str, Any]:
    """Test health endpoints of all services"""
    results = {
        "asr_api": {"status": "unknown", "response": None},
        "tts_api": {"status": "unknown", "response": None},
        "orchestrator": {"status": "unknown", "response": None},
        "rag_system": {"status": "unknown", "response": None}
    }
    
    services = {
        "asr_api": "http://localhost:8001/health",
        "tts_api": "http://localhost:8003/health", 
        "orchestrator": "http://localhost:8004/health",
        "rag_system": "http://localhost:8002/health"
    }
    
    for service, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            results[service]["status"] = "healthy" if response.status_code == 200 else "unhealthy"
            results[service]["response"] = response.text[:100] if response.text else "No response"
        except Exception as e:
            results[service]["status"] = "error"
            results[service]["response"] = str(e)[:100]
    
    return results

def test_basic_endpoints() -> Dict[str, Any]:
    """Test basic endpoints of working services"""
    results = {
        "asr_root": {"status": "unknown", "response": None},
        "tts_voices": {"status": "unknown", "response": None},
        "orchestrator_stats": {"status": "unknown", "response": None}
    }
    
    endpoints = {
        "asr_root": "http://localhost:8001/",
        "tts_voices": "http://localhost:8003/voices",
        "orchestrator_stats": "http://localhost:8004/stats"
    }
    
    for endpoint, url in endpoints.items():
        try:
            response = requests.get(url, timeout=5)
            results[endpoint]["status"] = "success" if response.status_code == 200 else "failed"
            results[endpoint]["response"] = response.text[:200] if response.text else "No response"
        except Exception as e:
            results[endpoint]["status"] = "error"
            results[endpoint]["response"] = str(e)[:100]
    
    return results

def test_websocket_availability() -> Dict[str, Any]:
    """Test WebSocket endpoint availability"""
    results = {
        "asr_stream": {"status": "unknown", "url": "ws://localhost:8001/ws/asr-stream"},
        "tts_stream": {"status": "unknown", "url": "ws://localhost:8003/ws/tts-stream"},
        "conversation": {"status": "unknown", "url": "ws://localhost:8004/ws/conversation"}
    }
    
    # Simple HTTP check to see if WebSocket endpoints exist
    for endpoint, data in results.items():
        try:
            # Convert WebSocket URL to HTTP for basic check
            http_url = data["url"].replace("ws://", "http://")
            response = requests.get(http_url, timeout=3)
            results[endpoint]["status"] = "available" if response.status_code in [400, 405, 426] else "unknown"
        except Exception as e:
            results[endpoint]["status"] = "error"
            results[endpoint]["error"] = str(e)[:100]
    
    return results

def main():
    """Run all simple tests"""
    print("🧪 SIMPLE TEST SCRIPT FOR E-COMMERCE ARABIC RAG SYSTEM")
    print("=" * 60)
    print()
    
    print("🏥 Testing Service Health...")
    print("-" * 30)
    health_results = test_service_health()
    for service, result in health_results.items():
        status_icon = "✅" if result["status"] == "healthy" else "❌" if result["status"] == "error" else "⚠️"
        print(f"{status_icon} {service.upper()}: {result['status']}")
        if result["response"]:
            print(f"   Response: {result['response']}")
    print()
    
    print("🌐 Testing Basic Endpoints...")
    print("-" * 30)
    endpoint_results = test_basic_endpoints()
    for endpoint, result in endpoint_results.items():
        status_icon = "✅" if result["status"] == "success" else "❌" if result["status"] == "error" else "⚠️"
        print(f"{status_icon} {endpoint.upper()}: {result['status']}")
        if result["response"]:
            print(f"   Response: {result['response']}")
    print()
    
    print("🔌 Testing WebSocket Availability...")
    print("-" * 30)
    websocket_results = test_websocket_availability()
    for endpoint, result in websocket_results.items():
        status_icon = "✅" if result["status"] == "available" else "❌" if result["status"] == "error" else "⚠️"
        print(f"{status_icon} {endpoint.upper()}: {result['status']}")
        print(f"   URL: {result['url']}")
        if "error" in result:
            print(f"   Error: {result['error']}")
    print()
    
    print("📊 SUMMARY")
    print("=" * 30)
    healthy_services = sum(1 for r in health_results.values() if r["status"] == "healthy")
    total_services = len(health_results)
    print(f"Healthy Services: {healthy_services}/{total_services}")
    
    working_endpoints = sum(1 for r in endpoint_results.values() if r["status"] == "success")
    total_endpoints = len(endpoint_results)
    print(f"Working Endpoints: {working_endpoints}/{total_endpoints}")
    
    available_websockets = sum(1 for r in websocket_results.values() if r["status"] == "available")
    total_websockets = len(websocket_results)
    print(f"Available WebSockets: {available_websockets}/{total_websockets}")
    
    print()
    print("🎉 Simple test completed!")
    print()
    print("💡 Next steps:")
    print("   - Fix configuration issues for RAG system")
    print("   - Set up Google Cloud credentials for ASR/TTS")
    print("   - Test WebSocket connections with proper clients")
    print("   - Run full integration tests")

if __name__ == "__main__":
    main()
