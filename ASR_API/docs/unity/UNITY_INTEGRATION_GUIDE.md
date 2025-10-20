# Unity WebSocket Streaming ASR Integration Guide

## Overview

This guide provides a complete solution for integrating real-time speech recognition into Unity applications using the ASR API WebSocket streaming endpoint. The integration enables Unity apps to capture microphone audio, stream it to the server, and receive real-time transcriptions.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Unity Setup](#unity-setup)
3. [WebSocket Implementation](#websocket-implementation)
4. [Audio Capture](#audio-capture)
5. [PCM Conversion](#pcm-conversion)
6. [Real-time Streaming](#real-time-streaming)
7. [UI Integration](#ui-integration)
8. [Error Handling](#error-handling)
9. [Testing & Debugging](#testing--debugging)
10. [Performance Optimization](#performance-optimization)
11. [Complete Example](#complete-example)

## Prerequisites

### Required Software
- Unity 2021.3 LTS or newer
- Visual Studio or Visual Studio Code
- ASR API server running on `localhost:8001`

### Required Packages
- Unity WebSocket implementation (BestHTTP/WebSocketSharp)
- Unity Audio System (built-in)

### Server Requirements
- ASR API server with WebSocket streaming enabled
- Google Cloud Speech-to-Text API credentials
- WebSocket endpoint: `ws://localhost:8001/ws/asr-stream`

## Unity Setup

### 1. Create New Unity Project

```bash
# Create new Unity project
Unity -createProject "ASRStreamingApp"
```

### 2. Install WebSocket Package

**Option A: BestHTTP (Recommended)**
```csharp
// Add to Packages/manifest.json
{
  "dependencies": {
    "com.unity.nuget.newtonsoft-json": "3.0.2",
    "com.unity.textmeshpro": "3.0.6"
  }
}
```

**Option B: WebSocketSharp**
```csharp
// Download WebSocketSharp.dll and place in Assets/Plugins/
// Available at: https://github.com/sta/websocket-sharp
```

### 3. Project Structure

```
Assets/
├── Scripts/
│   ├── ASR/
│   │   ├── ASRStreamingClient.cs
│   │   ├── AudioCapture.cs
│   │   ├── PCMConverter.cs
│   │   └── ASRManager.cs
│   ├── UI/
│   │   ├── ASRUI.cs
│   │   └── TranscriptDisplay.cs
│   └── Utils/
│       └── Logger.cs
├── Plugins/
│   └── WebSocketSharp.dll
└── Scenes/
    └── MainScene.unity
```

## WebSocket Implementation

### ASRStreamingClient.cs

```csharp
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using WebSocketSharp;
using Newtonsoft.Json;

namespace ASR
{
    public class ASRStreamingClient : MonoBehaviour
    {
        [Header("Connection Settings")]
        public string serverUrl = "ws://localhost:8001/ws/asr-stream";
        public string languageCode = "ar-EG";
        public int sampleRate = 16000;
        public string encoding = "LINEAR16";
        
        [Header("Audio Settings")]
        public int chunkSize = 4096;
        public float chunkDelay = 0.1f;
        
        [Header("Events")]
        public UnityEvent<string> OnTranscriptReceived;
        public UnityEvent<string> OnErrorReceived;
        public UnityEvent OnConnected;
        public UnityEvent OnDisconnected;
        
        private WebSocket webSocket;
        private bool isConnected = false;
        private bool isStreaming = false;
        private AudioCapture audioCapture;
        private Queue<byte[]> audioQueue = new Queue<byte[]>();
        
        void Start()
        {
            audioCapture = GetComponent<AudioCapture>();
            if (audioCapture == null)
            {
                audioCapture = gameObject.AddComponent<AudioCapture>();
            }
        }
        
        public void Connect()
        {
            if (isConnected) return;
            
            try
            {
                webSocket = new WebSocket(serverUrl);
                
                webSocket.OnOpen += OnWebSocketOpen;
                webSocket.OnMessage += OnWebSocketMessage;
                webSocket.OnError += OnWebSocketError;
                webSocket.OnClose += OnWebSocketClose;
                
                webSocket.Connect();
            }
            catch (Exception e)
            {
                Debug.LogError($"Failed to connect: {e.Message}");
                OnErrorReceived?.Invoke($"Connection failed: {e.Message}");
            }
        }
        
        public void Disconnect()
        {
            if (webSocket != null)
            {
                isStreaming = false;
                webSocket.Close();
            }
        }
        
        private void OnWebSocketOpen(object sender, EventArgs e)
        {
            Debug.Log("WebSocket connected");
            isConnected = true;
            OnConnected?.Invoke();
            
            // Send configuration
            SendConfiguration();
        }
        
        private void OnWebSocketMessage(object sender, MessageEventArgs e)
        {
            try
            {
                var message = JsonConvert.DeserializeObject<Dictionary<string, object>>(e.Data);
                HandleMessage(message);
            }
            catch (Exception ex)
            {
                Debug.LogError($"Error parsing message: {ex.Message}");
            }
        }
        
        private void OnWebSocketError(object sender, ErrorEventArgs e)
        {
            Debug.LogError($"WebSocket error: {e.Message}");
            OnErrorReceived?.Invoke($"WebSocket error: {e.Message}");
        }
        
        private void OnWebSocketClose(object sender, CloseEventArgs e)
        {
            Debug.Log("WebSocket disconnected");
            isConnected = false;
            isStreaming = false;
            OnDisconnected?.Invoke();
        }
        
        private void SendConfiguration()
        {
            var config = new
            {
                language_code = languageCode,
                sample_rate_hertz = sampleRate,
                encoding = encoding
            };
            
            string configJson = JsonConvert.SerializeObject(config);
            webSocket.Send(configJson);
            Debug.Log($"Sent configuration: {configJson}");
        }
        
        private void HandleMessage(Dictionary<string, object> message)
        {
            string type = message["type"].ToString();
            
            switch (type)
            {
                case "metadata":
                    if (message["status"].ToString() == "ready")
                    {
                        Debug.Log("Server ready for audio streaming");
                        StartAudioStreaming();
                    }
                    break;
                    
                case "transcript":
                    string text = message["text"].ToString();
                    bool isFinal = Convert.ToBoolean(message["is_final"]);
                    float confidence = message.ContainsKey("confidence") ? 
                        Convert.ToSingle(message["confidence"]) : 0f;
                    
                    Debug.Log($"[{(isFinal ? "FINAL" : "INTERIM")}] {text} (confidence: {confidence:F2})");
                    OnTranscriptReceived?.Invoke(text);
                    break;
                    
                case "error":
                    string error = message["detail"].ToString();
                    Debug.LogError($"Server error: {error}");
                    OnErrorReceived?.Invoke($"Server error: {error}");
                    break;
                    
                case "complete":
                    Debug.Log("Transcription completed");
                    break;
            }
        }
        
        private void StartAudioStreaming()
        {
            if (audioCapture != null)
            {
                audioCapture.StartCapture();
                isStreaming = true;
                StartCoroutine(StreamAudioData());
            }
        }
        
        private IEnumerator StreamAudioData()
        {
            while (isStreaming && isConnected)
            {
                if (audioQueue.Count > 0)
                {
                    byte[] audioData = audioQueue.Dequeue();
                    webSocket.Send(audioData);
                    Debug.Log($"Sent audio chunk: {audioData.Length} bytes");
                }
                
                yield return new WaitForSeconds(chunkDelay);
            }
        }
        
        public void AddAudioData(byte[] audioData)
        {
            if (isStreaming)
            {
                audioQueue.Enqueue(audioData);
            }
        }
        
        void OnDestroy()
        {
            Disconnect();
        }
    }
}
```

## Audio Capture

### AudioCapture.cs

```csharp
using System;
using System.Collections;
using UnityEngine;

namespace ASR
{
    public class AudioCapture : MonoBehaviour
    {
        [Header("Audio Settings")]
        public int sampleRate = 16000;
        public int bufferSize = 4096;
        public int channels = 1;
        
        private AudioClip audioClip;
        private float[] audioBuffer;
        private int bufferPosition = 0;
        private bool isCapturing = false;
        private ASRStreamingClient streamingClient;
        
        void Start()
        {
            streamingClient = GetComponent<ASRStreamingClient>();
            audioBuffer = new float[bufferSize];
        }
        
        public void StartCapture()
        {
            if (isCapturing) return;
            
            // Request microphone permission
            if (!Application.HasUserAuthorization(UserAuthorization.Microphone))
            {
                StartCoroutine(RequestMicrophonePermission());
                return;
            }
            
            StartMicrophoneCapture();
        }
        
        private IEnumerator RequestMicrophonePermission()
        {
            yield return Application.RequestUserAuthorization(UserAuthorization.Microphone);
            
            if (Application.HasUserAuthorization(UserAuthorization.Microphone))
            {
                StartMicrophoneCapture();
            }
            else
            {
                Debug.LogError("Microphone permission denied");
            }
        }
        
        private void StartMicrophoneCapture()
        {
            try
            {
                // Get the first available microphone
                string deviceName = Microphone.devices[0];
                
                // Create audio clip
                audioClip = Microphone.Start(deviceName, true, 1, sampleRate);
                
                if (audioClip == null)
                {
                    Debug.LogError("Failed to start microphone");
                    return;
                }
                
                isCapturing = true;
                Debug.Log($"Started microphone capture: {deviceName}");
                
                // Start processing audio data
                StartCoroutine(ProcessAudioData());
            }
            catch (Exception e)
            {
                Debug.LogError($"Microphone error: {e.Message}");
            }
        }
        
        public void StopCapture()
        {
            if (!isCapturing) return;
            
            isCapturing = false;
            
            if (Microphone.IsRecording(null))
            {
                Microphone.End(null);
            }
            
            Debug.Log("Stopped microphone capture");
        }
        
        private IEnumerator ProcessAudioData()
        {
            while (isCapturing)
            {
                if (audioClip != null)
                {
                    int currentPosition = Microphone.GetPosition(null);
                    
                    if (currentPosition >= bufferSize)
                    {
                        // Extract audio data
                        audioClip.GetData(audioBuffer, currentPosition - bufferSize);
                        
                        // Convert to PCM and send
                        byte[] pcmData = ConvertToPCM(audioBuffer);
                        
                        if (streamingClient != null)
                        {
                            streamingClient.AddAudioData(pcmData);
                        }
                    }
                }
                
                yield return new WaitForSeconds(0.1f);
            }
        }
        
        private byte[] ConvertToPCM(float[] floatArray)
        {
            byte[] pcmData = new byte[floatArray.Length * 2];
            
            for (int i = 0; i < floatArray.Length; i++)
            {
                // Convert float (-1.0 to 1.0) to 16-bit PCM
                float sample = Mathf.Clamp(floatArray[i], -1f, 1f);
                short pcmSample = (short)(sample * 32767f);
                
                // Convert to little-endian bytes
                pcmData[i * 2] = (byte)(pcmSample & 0xFF);
                pcmData[i * 2 + 1] = (byte)((pcmSample >> 8) & 0xFF);
            }
            
            return pcmData;
        }
        
        void OnDestroy()
        {
            StopCapture();
        }
    }
}
```

## PCM Conversion

### PCMConverter.cs

```csharp
using System;
using UnityEngine;

namespace ASR
{
    public static class PCMConverter
    {
        /// <summary>
        /// Convert Unity AudioClip to PCM byte array
        /// </summary>
        public static byte[] AudioClipToPCM(AudioClip audioClip)
        {
            float[] samples = new float[audioClip.samples * audioClip.channels];
            audioClip.GetData(samples, 0);
            
            return FloatArrayToPCM(samples);
        }
        
        /// <summary>
        /// Convert float array to 16-bit PCM byte array
        /// </summary>
        public static byte[] FloatArrayToPCM(float[] floatArray)
        {
            byte[] pcmData = new byte[floatArray.Length * 2];
            
            for (int i = 0; i < floatArray.Length; i++)
            {
                // Clamp and convert to 16-bit PCM
                float sample = Mathf.Clamp(floatArray[i], -1f, 1f);
                short pcmSample = (short)(sample * 32767f);
                
                // Little-endian byte order
                pcmData[i * 2] = (byte)(pcmSample & 0xFF);
                pcmData[i * 2 + 1] = (byte)((pcmSample >> 8) & 0xFF);
            }
            
            return pcmData;
        }
        
        /// <summary>
        /// Convert PCM byte array to float array
        /// </summary>
        public static float[] PCMToFloatArray(byte[] pcmData)
        {
            float[] floatArray = new float[pcmData.Length / 2];
            
            for (int i = 0; i < floatArray.Length; i++)
            {
                // Little-endian byte order
                short pcmSample = (short)((pcmData[i * 2 + 1] << 8) | pcmData[i * 2]);
                floatArray[i] = pcmSample / 32767f;
            }
            
            return floatArray;
        }
        
        /// <summary>
        /// Resample audio data to target sample rate
        /// </summary>
        public static float[] Resample(float[] input, int inputSampleRate, int outputSampleRate)
        {
            if (inputSampleRate == outputSampleRate)
                return input;
            
            float ratio = (float)inputSampleRate / outputSampleRate;
            int outputLength = Mathf.RoundToInt(input.Length / ratio);
            float[] output = new float[outputLength];
            
            for (int i = 0; i < outputLength; i++)
            {
                float index = i * ratio;
                int indexInt = Mathf.FloorToInt(index);
                float fraction = index - indexInt;
                
                if (indexInt + 1 < input.Length)
                {
                    output[i] = Mathf.Lerp(input[indexInt], input[indexInt + 1], fraction);
                }
                else
                {
                    output[i] = input[indexInt];
                }
            }
            
            return output;
        }
    }
}
```

## UI Integration

### ASRUI.cs

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ASR;

public class ASRUI : MonoBehaviour
{
    [Header("UI References")]
    public Button connectButton;
    public Button disconnectButton;
    public Button startRecordingButton;
    public Button stopRecordingButton;
    public Button clearTranscriptButton;
    
    public TextMeshProUGUI statusText;
    public TextMeshProUGUI transcriptText;
    public TextMeshProUGUI confidenceText;
    public TextMeshProUGUI wordCountText;
    
    public Image recordingIndicator;
    
    [Header("ASR Client")]
    public ASRStreamingClient asrClient;
    
    private string completeTranscript = "";
    private string currentInterimText = "";
    private int wordCount = 0;
    
    void Start()
    {
        SetupUI();
        SetupASRClient();
    }
    
    private void SetupUI()
    {
        connectButton.onClick.AddListener(Connect);
        disconnectButton.onClick.AddListener(Disconnect);
        startRecordingButton.onClick.AddListener(StartRecording);
        stopRecordingButton.onClick.AddListener(StopRecording);
        clearTranscriptButton.onClick.AddListener(ClearTranscript);
        
        UpdateUI();
    }
    
    private void SetupASRClient()
    {
        if (asrClient == null)
            asrClient = FindObjectOfType<ASRStreamingClient>();
        
        asrClient.OnConnected.AddListener(OnConnected);
        asrClient.OnDisconnected.AddListener(OnDisconnected);
        asrClient.OnTranscriptReceived.AddListener(OnTranscriptReceived);
        asrClient.OnErrorReceived.AddListener(OnErrorReceived);
    }
    
    private void Connect()
    {
        asrClient.Connect();
        statusText.text = "Connecting...";
    }
    
    private void Disconnect()
    {
        asrClient.Disconnect();
        statusText.text = "Disconnected";
    }
    
    private void StartRecording()
    {
        // Recording will start automatically after connection
        statusText.text = "Recording...";
        recordingIndicator.gameObject.SetActive(true);
    }
    
    private void StopRecording()
    {
        statusText.text = "Connected";
        recordingIndicator.gameObject.SetActive(false);
    }
    
    private void ClearTranscript()
    {
        completeTranscript = "";
        currentInterimText = "";
        wordCount = 0;
        UpdateTranscriptDisplay();
    }
    
    private void OnConnected()
    {
        statusText.text = "Connected";
        UpdateUI();
    }
    
    private void OnDisconnected()
    {
        statusText.text = "Disconnected";
        UpdateUI();
    }
    
    private void OnTranscriptReceived(string text)
    {
        // This is a simplified version - in practice, you'd parse the JSON
        // to determine if it's interim or final
        if (text.Length > 0)
        {
            completeTranscript += (completeTranscript.Length > 0 ? " " : "") + text;
            wordCount = completeTranscript.Split(' ').Length;
            UpdateTranscriptDisplay();
        }
    }
    
    private void OnErrorReceived(string error)
    {
        statusText.text = $"Error: {error}";
        Debug.LogError($"ASR Error: {error}");
    }
    
    private void UpdateTranscriptDisplay()
    {
        transcriptText.text = completeTranscript;
        wordCountText.text = $"Words: {wordCount}";
    }
    
    private void UpdateUI()
    {
        bool isConnected = asrClient != null && asrClient.isConnected;
        
        connectButton.interactable = !isConnected;
        disconnectButton.interactable = isConnected;
        startRecordingButton.interactable = isConnected;
        stopRecordingButton.interactable = isConnected;
        clearTranscriptButton.interactable = isConnected;
    }
}
```

## Error Handling

### Logger.cs

```csharp
using UnityEngine;
using System;

namespace ASR.Utils
{
    public static class Logger
    {
        public enum LogLevel
        {
            Debug,
            Info,
            Warning,
            Error
        }
        
        public static LogLevel currentLevel = LogLevel.Info;
        
        public static void Log(string message, LogLevel level = LogLevel.Info)
        {
            if (level < currentLevel) return;
            
            string timestamp = DateTime.Now.ToString("HH:mm:ss");
            string logMessage = $"[{timestamp}] [{level}] {message}";
            
            switch (level)
            {
                case LogLevel.Debug:
                    Debug.Log(logMessage);
                    break;
                case LogLevel.Info:
                    Debug.Log(logMessage);
                    break;
                case LogLevel.Warning:
                    Debug.LogWarning(logMessage);
                    break;
                case LogLevel.Error:
                    Debug.LogError(logMessage);
                    break;
            }
        }
        
        public static void LogError(string message, Exception exception = null)
        {
            string errorMessage = message;
            if (exception != null)
            {
                errorMessage += $"\nException: {exception.Message}\nStack Trace: {exception.StackTrace}";
            }
            Log(errorMessage, LogLevel.Error);
        }
    }
}
```

## Testing & Debugging

### 1. Unity Console Testing

```csharp
// Add to ASRStreamingClient for debugging
private void OnGUI()
{
    if (GUI.Button(new Rect(10, 10, 100, 30), "Connect"))
        Connect();
    
    if (GUI.Button(new Rect(120, 10, 100, 30), "Disconnect"))
        Disconnect();
    
    GUI.Label(new Rect(10, 50, 200, 20), $"Connected: {isConnected}");
    GUI.Label(new Rect(10, 70, 200, 20), $"Streaming: {isStreaming}");
    GUI.Label(new Rect(10, 90, 200, 20), $"Audio Queue: {audioQueue.Count}");
}
```

### 2. Network Testing

```csharp
// Test WebSocket connection
public void TestConnection()
{
    StartCoroutine(TestWebSocketConnection());
}

private IEnumerator TestWebSocketConnection()
{
    // Test basic connectivity
    using (var request = UnityWebRequest.Get("http://localhost:8001/health"))
    {
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("Server is running");
        }
        else
        {
            Debug.LogError($"Server not accessible: {request.error}");
        }
    }
}
```

## Performance Optimization

### 1. Audio Buffer Management

```csharp
public class AudioBufferManager
{
    private Queue<byte[]> audioBuffers = new Queue<byte[]>();
    private int maxBufferSize = 10;
    
    public void AddBuffer(byte[] buffer)
    {
        if (audioBuffers.Count >= maxBufferSize)
        {
            audioBuffers.Dequeue(); // Remove oldest buffer
        }
        audioBuffers.Enqueue(buffer);
    }
    
    public byte[] GetBuffer()
    {
        return audioBuffers.Count > 0 ? audioBuffers.Dequeue() : null;
    }
}
```

### 2. Thread-Safe Operations

```csharp
using System.Collections.Concurrent;

public class ThreadSafeAudioQueue
{
    private ConcurrentQueue<byte[]> audioQueue = new ConcurrentQueue<byte[]>();
    
    public void Enqueue(byte[] audioData)
    {
        audioQueue.Enqueue(audioData);
    }
    
    public bool TryDequeue(out byte[] audioData)
    {
        return audioQueue.TryDequeue(out audioData);
    }
    
    public int Count => audioQueue.Count;
}
```

## Complete Example

### MainScene Setup

1. **Create Empty GameObject** named "ASRManager"
2. **Add Components**:
   - ASRStreamingClient
   - AudioCapture
   - ASRUI (if using UI)

3. **Configure Settings**:
   ```csharp
   // ASRStreamingClient settings
   serverUrl = "ws://localhost:8001/ws/asr-stream"
   languageCode = "ar-EG"
   sampleRate = 16000
   encoding = "LINEAR16"
   chunkSize = 4096
   chunkDelay = 0.1f
   ```

4. **Setup UI** (if using):
   - Create Canvas
   - Add buttons and text elements
   - Assign references in ASRUI script

### Usage Example

```csharp
public class ExampleUsage : MonoBehaviour
{
    public ASRStreamingClient asrClient;
    
    void Start()
    {
        // Setup event listeners
        asrClient.OnTranscriptReceived.AddListener(OnTranscript);
        asrClient.OnErrorReceived.AddListener(OnError);
        
        // Connect to server
        asrClient.Connect();
    }
    
    private void OnTranscript(string text)
    {
        Debug.Log($"Transcription: {text}");
        // Process transcription here
    }
    
    private void OnError(string error)
    {
        Debug.LogError($"ASR Error: {error}");
        // Handle error here
    }
}
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if ASR server is running
   - Verify server URL and port
   - Check firewall settings

2. **Microphone Permission Denied**
   - Request microphone permission
   - Check Unity Player Settings
   - Verify microphone is available

3. **Audio Quality Issues**
   - Adjust sample rate (16000 Hz recommended)
   - Check microphone settings
   - Verify PCM conversion

4. **Performance Issues**
   - Reduce chunk size
   - Increase chunk delay
   - Optimize audio buffer management

### Debug Commands

```csharp
// Enable debug logging
Logger.currentLevel = Logger.LogLevel.Debug;

// Test audio capture
audioCapture.StartCapture();

// Test WebSocket connection
asrClient.Connect();

// Monitor performance
Debug.Log($"Audio Queue Size: {audioQueue.Count}");
Debug.Log($"Memory Usage: {GC.GetTotalMemory(false)}");
```

## Best Practices

1. **Audio Quality**
   - Use 16kHz sample rate for optimal performance
   - Implement noise reduction if needed
   - Use mono audio (single channel)

2. **Network Optimization**
   - Implement connection retry logic
   - Handle network interruptions gracefully
   - Use appropriate chunk sizes

3. **User Experience**
   - Provide visual feedback for recording status
   - Show confidence scores
   - Implement transcript editing capabilities

4. **Error Handling**
   - Implement comprehensive error handling
   - Provide user-friendly error messages
   - Log errors for debugging

This guide provides a complete solution for integrating WebSocket streaming ASR into Unity applications. The implementation supports real-time audio capture, streaming, and transcription with proper error handling and UI integration.
