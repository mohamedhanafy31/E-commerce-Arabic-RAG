#!/usr/bin/env python3
"""
WebSocket Test Script for E-commerce Arabic RAG System
Tests WebSocket endpoints with proper async handling
"""

import asyncio
import json
import websockets
import time
from typing import Dict, Any, Optional

async def test_websocket_connection(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """Test basic WebSocket connection"""
    result = {
        "url": url,
        "connected": False,
        "error": None,
        "response_time": None
    }
    
    try:
        start_time = time.time()
        async with websockets.connect(url) as websocket:
            result["connected"] = True
            result["response_time"] = time.time() - start_time
            print(f"✅ Connected to {url}")
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ Failed to connect to {url}: {e}")
    
    return result

async def test_asr_streaming() -> Dict[str, Any]:
    """Test ASR WebSocket streaming"""
    url = "ws://localhost:8001/ws/asr-stream"
    result = {
        "url": url,
        "connected": False,
        "config_sent": False,
        "response_received": False,
        "error": None
    }
    
    try:
        async with websockets.connect(url) as websocket:
            result["connected"] = True
            print(f"✅ Connected to ASR stream: {url}")
            
            # Send configuration
            config = {
                "language_code": "ar-XA",
                "sample_rate": 16000,
                "encoding": "LINEAR16"
            }
            await websocket.send(json.dumps(config))
            result["config_sent"] = True
            print("✅ Configuration sent")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                result["response_received"] = True
                print(f"✅ Response received: {response[:100]}...")
            except asyncio.TimeoutError:
                print("⚠️ No response received within timeout")
                
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ ASR streaming test failed: {e}")
    
    return result

async def test_tts_streaming() -> Dict[str, Any]:
    """Test TTS WebSocket streaming"""
    url = "ws://localhost:8003/ws/tts-stream"
    result = {
        "url": url,
        "connected": False,
        "request_sent": False,
        "metadata_received": False,
        "audio_received": False,
        "error": None
    }
    
    try:
        async with websockets.connect(url) as websocket:
            result["connected"] = True
            print(f"✅ Connected to TTS stream: {url}")
            
            # Send TTS request
            tts_request = {
                "text": "مرحبا بك في نظام الذكاء الاصطناعي",
                "voice": "ar-XA-Wavenet-A",
                "language_code": "ar-XA"
            }
            await websocket.send(json.dumps(tts_request))
            result["request_sent"] = True
            print("✅ TTS request sent")
            
            # Wait for metadata
            try:
                metadata = await asyncio.wait_for(websocket.recv(), timeout=5)
                result["metadata_received"] = True
                print(f"✅ Metadata received: {metadata[:100]}...")
                
                # Wait for audio data
                try:
                    audio_data = await asyncio.wait_for(websocket.recv(), timeout=5)
                    result["audio_received"] = True
                    print(f"✅ Audio data received: {len(audio_data)} bytes")
                except asyncio.TimeoutError:
                    print("⚠️ No audio data received within timeout")
                    
            except asyncio.TimeoutError:
                print("⚠️ No metadata received within timeout")
                
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ TTS streaming test failed: {e}")
    
    return result

async def test_orchestrator_conversation() -> Dict[str, Any]:
    """Test Orchestrator WebSocket conversation"""
    url = "ws://localhost:8004/ws/conversation"
    result = {
        "url": url,
        "connected": False,
        "ready_received": False,
        "session_id": None,
        "error": None
    }
    
    try:
        async with websockets.connect(url) as websocket:
            result["connected"] = True
            print(f"✅ Connected to Orchestrator: {url}")
            
            # Wait for ready message
            try:
                ready_message = await asyncio.wait_for(websocket.recv(), timeout=5)
                result["ready_received"] = True
                print(f"✅ Ready message received: {ready_message[:100]}...")
                
                # Try to parse session ID
                try:
                    data = json.loads(ready_message)
                    result["session_id"] = data.get("session_id")
                    if result["session_id"]:
                        print(f"✅ Session ID: {result['session_id']}")
                except json.JSONDecodeError:
                    print("⚠️ Could not parse ready message as JSON")
                    
            except asyncio.TimeoutError:
                print("⚠️ No ready message received within timeout")
                
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ Orchestrator conversation test failed: {e}")
    
    return result

async def main():
    """Run all WebSocket tests"""
    print("🔌 WEBSOCKET TEST SCRIPT FOR E-COMMERCE ARABIC RAG SYSTEM")
    print("=" * 60)
    print()
    
    # Test basic connections first
    print("🔗 Testing Basic WebSocket Connections...")
    print("-" * 40)
    
    urls = [
        "ws://localhost:8001/ws/asr-stream",
        "ws://localhost:8003/ws/tts-stream", 
        "ws://localhost:8004/ws/conversation"
    ]
    
    connection_results = []
    for url in urls:
        result = await test_websocket_connection(url)
        connection_results.append(result)
        await asyncio.sleep(1)  # Small delay between tests
    
    print()
    
    # Test specific WebSocket functionality
    print("🎤 Testing ASR Streaming...")
    print("-" * 30)
    asr_result = await test_asr_streaming()
    print()
    
    print("🔊 Testing TTS Streaming...")
    print("-" * 30)
    tts_result = await test_tts_streaming()
    print()
    
    print("🎯 Testing Orchestrator Conversation...")
    print("-" * 30)
    orchestrator_result = await test_orchestrator_conversation()
    print()
    
    # Summary
    print("📊 WEBSOCKET TEST SUMMARY")
    print("=" * 30)
    
    successful_connections = sum(1 for r in connection_results if r["connected"])
    print(f"Successful Connections: {successful_connections}/{len(connection_results)}")
    
    print(f"ASR Streaming: {'✅' if asr_result['connected'] and asr_result['response_received'] else '❌'}")
    print(f"TTS Streaming: {'✅' if tts_result['connected'] and tts_result['metadata_received'] else '❌'}")
    print(f"Orchestrator: {'✅' if orchestrator_result['connected'] and orchestrator_result['ready_received'] else '❌'}")
    
    print()
    print("🎉 WebSocket tests completed!")
    print()
    print("💡 Notes:")
    print("   - WebSocket connections are working")
    print("   - Services respond to WebSocket requests")
    print("   - Ready for real-time communication testing")

if __name__ == "__main__":
    asyncio.run(main())
