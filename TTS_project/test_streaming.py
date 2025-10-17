#!/usr/bin/env python3
"""
Test script for WebSocket streaming TTS functionality.
"""

import asyncio
import websockets
import json
import base64
import wave
import io

async def test_streaming_tts():
    """Test the WebSocket streaming TTS endpoint."""
    uri = "ws://localhost:8000/ws/tts-stream"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send configuration
            config = {
                "text": "مرحبا بك في نظام تحويل النص إلى كلام",
                "temperature": 0.6,
                "language": "ar",
                "chunk_size": 100,
                "stream_chunk_size": 1024
            }
            await websocket.send(json.dumps(config))
            print("✅ Configuration sent")
            
            # Receive streaming data
            audio_chunks_received = 0
            total_audio_data = b""
            
            async for message in websocket:
                data = json.loads(message)
                
                if data["type"] == "metadata":
                    print(f"✅ Audio metadata: {data}")
                    
                elif data["type"] == "chunks_info":
                    print(f"✅ Text split into {data['total_chunks']} chunks")
                    
                elif data["type"] == "chunk_start":
                    print(f"✅ Processing chunk {data['chunk_index']}: {data['text'][:50]}...")
                    
                elif data["type"] == "audio_chunk":
                    # Decode and store audio chunk
                    audio_data = base64.b64decode(data["data"])
                    total_audio_data += audio_data
                    audio_chunks_received += 1
                    print(f"✅ Received audio chunk {data['audio_index']} for text chunk {data['chunk_index']} ({len(audio_data)} bytes)")
                    
                elif data["type"] == "chunk_complete":
                    print(f"✅ Completed chunk {data['chunk_index']}")
                    
                elif data["type"] == "complete":
                    print("✅ Streaming complete!")
                    break
                    
                elif data["type"] == "error":
                    print(f"❌ Error: {data['message']}")
                    break
            
            print(f"\n📊 Summary:")
            print(f"   - Audio chunks received: {audio_chunks_received}")
            print(f"   - Total audio data: {len(total_audio_data)} bytes")
            
            # Save the complete audio to a file for verification
            if total_audio_data:
                with open("test_streaming_output.wav", "wb") as f:
                    f.write(total_audio_data)
                print(f"   - Audio saved to: test_streaming_output.wav")
                
                # Try to read the WAV file to verify it's valid
                try:
                    with wave.open(io.BytesIO(total_audio_data), 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        channels = wav_file.getnchannels()
                        print(f"   - WAV file info: {frames} frames, {sample_rate}Hz, {channels} channels")
                        print("   - ✅ WAV file is valid!")
                except Exception as e:
                    print(f"   - ❌ WAV file validation failed: {e}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing WebSocket Streaming TTS...")
    asyncio.run(test_streaming_tts())
