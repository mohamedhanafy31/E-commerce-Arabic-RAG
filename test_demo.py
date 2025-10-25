#!/usr/bin/env python3
"""
Quick Test Demo for E-commerce Arabic RAG System
Demonstrates how to test the endpoints without running the full test suite
"""

import requests
import json
import os
from pathlib import Path

def test_service_health():
    """Test health endpoints of all services"""
    services = {
        "RAG System": "http://localhost:8002/health",
        "ASR API": "http://localhost:8001/health", 
        "TTS API": "http://localhost:8003/health",
        "Orchestrator": "http://localhost:8004/health"
    }
    
    print("🏥 Testing Service Health...")
    print("=" * 40)
    
    for service, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service}: Healthy")
            else:
                print(f"❌ {service}: Unhealthy (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ {service}: Not running ({str(e)[:50]}...)")
    
    print()

def test_rag_endpoints():
    """Test RAG System endpoints"""
    print("📚 Testing RAG System Endpoints...")
    print("=" * 40)
    
    base_url = "http://localhost:8002"
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: {data['name']} v{data['version']}")
        else:
            print(f"❌ Root endpoint: Failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Root endpoint: Error ({str(e)[:50]}...)")
    
    # Test stats endpoint
    try:
        response = requests.get(f"{base_url}/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats endpoint: {data['total_documents']} documents, {data['total_chunks']} chunks")
        else:
            print(f"❌ Stats endpoint: Failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Stats endpoint: Error ({str(e)[:50]}...)")
    
    # Test query endpoint
    try:
        query_data = {
            "query": "ما هو موضوع هذا المستند؟",
            "max_results": 3
        }
        response = requests.post(f"{base_url}/query", json=query_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query endpoint: Got response ({data['model_used']})")
        else:
            print(f"❌ Query endpoint: Failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Query endpoint: Error ({str(e)[:50]}...)")
    
    print()

def test_asr_endpoints():
    """Test ASR API endpoints"""
    print("🎤 Testing ASR API Endpoints...")
    print("=" * 40)
    
    base_url = "http://localhost:8001"
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Root endpoint: Web UI available")
        else:
            print(f"❌ Root endpoint: Failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Root endpoint: Error ({str(e)[:50]}...)")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint: {data['status']}")
        else:
            print(f"❌ Health endpoint: Failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Health endpoint: Error ({str(e)[:50]}...)")
    
    print()

def test_tts_endpoints():
    """Test TTS API endpoints"""
    print("🔊 Testing TTS API Endpoints...")
    print("=" * 40)
    
    base_url = "http://localhost:8003"
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Root endpoint: Web UI available")
        else:
            print(f"❌ Root endpoint: Failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Root endpoint: Error ({str(e)[:50]}...)")
    
    # Test voices endpoint
    try:
        response = requests.get(f"{base_url}/voices")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Voices endpoint: {len(data)} voices available")
        else:
            print(f"❌ Voices endpoint: Failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Voices endpoint: Error ({str(e)[:50]}...)")
    
    print()

def test_orchestrator_endpoints():
    """Test Orchestrator endpoints"""
    print("🎯 Testing Orchestrator Endpoints...")
    print("=" * 40)
    
    base_url = "http://localhost:8004"
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: {data['name']} v{data['version']}")
        else:
            print(f"❌ Root endpoint: Failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Root endpoint: Error ({str(e)[:50]}...)")
    
    # Test stats endpoint
    try:
        response = requests.get(f"{base_url}/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats endpoint: {data['active_conversations']} active conversations")
        else:
            print(f"❌ Stats endpoint: Failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Stats endpoint: Error ({str(e)[:50]}...)")
    
    print()

def test_file_availability():
    """Test if required test files are available"""
    print("📁 Testing File Availability...")
    print("=" * 40)
    
    project_root = Path(__file__).parent.parent
    
    # Test document file
    doc_file = project_root / "large.txt"
    if doc_file.exists():
        size_mb = doc_file.stat().st_size / (1024 * 1024)
        print(f"✅ Test document: {doc_file.name} ({size_mb:.2f} MB)")
    else:
        print(f"❌ Test document: {doc_file.name} not found")
    
    # Test audio file
    audio_file = project_root / "ASR_API" / "speaker.mp3"
    if audio_file.exists():
        size_mb = audio_file.stat().st_size / (1024 * 1024)
        print(f"✅ Test audio: {audio_file.name} ({size_mb:.2f} MB)")
    else:
        print(f"❌ Test audio: {audio_file.name} not found")
    
    print()

def main():
    """Main test demo function"""
    print("🧪 Quick Test Demo for E-commerce Arabic RAG System")
    print("=" * 60)
    print()
    
    # Test file availability
    test_file_availability()
    
    # Test service health
    test_service_health()
    
    # Test individual service endpoints
    test_rag_endpoints()
    test_asr_endpoints()
    test_tts_endpoints()
    test_orchestrator_endpoints()
    
    print("🎉 Test demo completed!")
    print()
    print("💡 To run the full test suite:")
    print("   python tests/run_tests.py")
    print()
    print("💡 To run specific service tests:")
    print("   python tests/run_tests.py --service rag")
    print("   python tests/run_tests.py --service asr")
    print("   python tests/run_tests.py --service tts")
    print("   python tests/run_tests.py --service orchestrator")

if __name__ == "__main__":
    main()
