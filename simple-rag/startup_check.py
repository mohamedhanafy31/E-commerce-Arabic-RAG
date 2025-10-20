#!/usr/bin/env python3
"""
Simple Arabic RAG System - Startup Script
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def check_dependencies():
    """Check if required dependencies are installed"""
    # Map package names to their import names
    package_imports = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn', 
        'sentence-transformers': 'sentence_transformers',
        'faiss-cpu': 'faiss',
        'httpx': 'httpx',
        'PyPDF2': 'PyPDF2',
        'python-docx': 'docx'
    }
    
    missing_packages = []
    
    for package_name, import_name in package_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True


def check_environment():
    """Check environment configuration"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("Copy env.example to .env and configure your settings")
        return False
    
    print("✅ Environment file found")
    return True


def check_ollama():
    """Check if Ollama is available"""
    try:
        import httpx
        import asyncio
        
        async def check():
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:11434/api/tags")
                return response.status_code == 200
        
        if asyncio.run(check()):
            print("✅ Ollama is running")
            return True
        else:
            print("⚠️  Ollama is not running (optional)")
            return False
    except Exception:
        print("⚠️  Ollama is not available (optional)")
        return False


def main():
    """Main startup function"""
    print("🚀 Simple Arabic RAG System - Startup Check")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    check_environment()
    
    # Check Ollama (optional)
    check_ollama()
    
    print("\n" + "=" * 50)
    print("✅ System checks completed!")
    print("\nTo start the server:")
    print("  python main.py")
    print("\nOr with uvicorn:")
    print("  uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
    print("\nAPI will be available at: http://localhost:8000")


if __name__ == "__main__":
    main()
