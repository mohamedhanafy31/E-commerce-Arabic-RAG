# Unity Integration Guide for Orchestrator

A comprehensive guide for integrating Unity applications with the Orchestrator Conversational AI System, including audio recording, WebSocket communication, and real-time conversation flow.

## 🎮 Overview

This guide shows how to integrate Unity with the Orchestrator service to create a complete conversational AI experience. The integration includes:

- **Audio Recording**: Start/Stop recording with UI buttons
- **WebSocket Communication**: Real-time communication with the Orchestrator
- **Audio Playback**: Playing TTS responses
- **UI Management**: Handling conversation states and user feedback
- **Error Handling**: Robust error recovery and user notifications

## 🏗️ Architecture Flow

```
Unity Client → WebSocket → Orchestrator → ASR → RAG → TTS → Unity Client
     ↓              ↓           ↓         ↓     ↓     ↓         ↓
  Record Audio → Send Chunks → Process → Transcribe → Generate → Play Audio
```

### **Communication Flow**
1. **Unity connects** to Orchestrator WebSocket
2. **User presses Record** → Unity starts audio recording
3. **Audio chunks** are sent to Orchestrator in real-time
4. **User presses Stop** → Unity sends audio_end signal
5. **Orchestrator processes** → ASR → RAG → TTS
6. **Unity receives** → Transcript → Response → Audio
7. **Unity plays** TTS audio and updates UI

## 🚀 Unity Project Setup

### **1. Create Unity Project**
```bash
# Create new Unity project
# File → New Project → 3D Template
# Name: "ConversationalAI"
```

### **2. Install Required Packages**
```bash
# Install WebSocket package
# Window → Package Manager → Add package from git URL
# URL: https://github.com/endel/NativeWebSocket.git

# Or install via Package Manager UI:
# - NativeWebSocket
# - Newtonsoft Json (if not already included)
```

### **3. Project Structure**
```
Assets/
├── Scripts/
│   ├── OrchestratorClient.cs
│   ├── AudioRecorder.cs
│   ├── AudioPlayer.cs
│   ├── UIController.cs
│   └── ConversationManager.cs
├── Scenes/
│   └── MainScene.unity
├── Prefabs/
│   ├── UI Canvas
│   └── Audio Sources
└── Materials/
    └── UI Materials
```

## 📝 Core Scripts Implementation

### **1. OrchestratorClient.cs**

This script handles WebSocket communication with the Orchestrator:

```csharp
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using NativeWebSocket;
using Newtonsoft.Json;

[System.Serializable]
public class AudioConfig
{
    public string language_code = "ar-EG";
    public int sample_rate_hertz = 16000;
    public string encoding = "LINEAR16";
    public int channels = 1;
}

[System.Serializable]
public class ReadyMessage
{
    public string type = "ready";
    public string session_id;
    public AudioConfig audio_config;
    public string timestamp;
}

[System.Serializable]
public class TranscriptMessage
{
    public string type = "transcript";
    public string text;
    public bool is_final;
    public float confidence;
    public string timestamp;
}

[System.Serializable]
public class RAGResponseMessage
{
    public string type = "rag_response";
    public string text;
    public object[] sources;
    public int processing_time_ms;
    public string model_used;
    public string timestamp;
}

[System.Serializable]
public class TTSAudioMessage
{
    public string type = "audio_chunk_tts";
    public string audio_data;
    public int chunk_index;
    public bool is_final_chunk;
    public int sentence_index;
    public string timestamp;
}

[System.Serializable]
public class StateMessage
{
    public string type = "state_update";
    public string state;
    public string previous_state;
    public string timestamp;
}

[System.Serializable]
public class ErrorMessage
{
    public string type = "error";
    public string error_code;
    public string detail;
    public string timestamp;
}

[System.Serializable]
public class CompleteMessage
{
    public string type = "complete";
    public string session_id;
    public int total_processing_time_ms;
    public string timestamp;
}

public class OrchestratorClient : MonoBehaviour
{
    [Header("Connection Settings")]
    public string orchestratorUrl = "ws://localhost:8004/ws/conversation";
    
    [Header("Debug")]
    public bool enableDebugLogs = true;
    
    // WebSocket connection
    private WebSocket websocket;
    private bool isConnected = false;
    private string sessionId;
    
    // Events
    public System.Action<string> OnTranscriptReceived;
    public System.Action<string, object[]> OnRAGResponseReceived;
    public System.Action<byte[], int, bool> OnTTSAudioReceived;
    public System.Action<string, string> OnStateChanged;
    public System.Action<string, string> OnErrorReceived;
    public System.Action<int> OnConversationComplete;
    public System.Action OnConnected;
    public System.Action OnDisconnected;
    
    // Connection state
    private bool isConnecting = false;
    private int reconnectAttempts = 0;
    private int maxReconnectAttempts = 3;
    private float reconnectDelay = 2f;
    
    void Start()
    {
        // Auto-connect on start
        ConnectToOrchestrator();
    }
    
    void Update()
    {
        // Handle WebSocket messages on main thread
        if (websocket != null)
        {
            websocket.DispatchMessageQueue();
        }
    }
    
    public async void ConnectToOrchestrator()
    {
        if (isConnecting || isConnected)
        {
            LogDebug("Already connecting or connected");
            return;
        }
        
        isConnecting = true;
        LogDebug($"Connecting to Orchestrator: {orchestratorUrl}");
        
        try
        {
            websocket = new WebSocket(orchestratorUrl);
            
            // Set up event handlers
            websocket.OnOpen += OnWebSocketOpen;
            websocket.OnMessage += OnWebSocketMessage;
            websocket.OnError += OnWebSocketError;
            websocket.OnClose += OnWebSocketClose;
            
            // Connect
            await websocket.Connect();
        }
        catch (Exception e)
        {
            LogDebug($"Connection failed: {e.Message}");
            isConnecting = false;
            OnErrorReceived?.Invoke("connection_failed", e.Message);
        }
    }
    
    private void OnWebSocketOpen()
    {
        LogDebug("WebSocket connected successfully");
        isConnected = true;
        isConnecting = false;
        reconnectAttempts = 0;
        OnConnected?.Invoke();
    }
    
    private void OnWebSocketMessage(byte[] data)
    {
        try
        {
            string message = System.Text.Encoding.UTF8.GetString(data);
            LogDebug($"Received message: {message}");
            
            // Try to parse as JSON
            var jsonMessage = JsonConvert.DeserializeObject<Dictionary<string, object>>(message);
            string messageType = jsonMessage["type"].ToString();
            
            switch (messageType)
            {
                case "ready":
                    HandleReadyMessage(message);
                    break;
                case "transcript":
                    HandleTranscriptMessage(message);
                    break;
                case "rag_response":
                    HandleRAGResponseMessage(message);
                    break;
                case "audio_chunk_tts":
                    HandleTTSAudioMessage(message);
                    break;
                case "state_update":
                    HandleStateMessage(message);
                    break;
                case "error":
                    HandleErrorMessage(message);
                    break;
                case "complete":
                    HandleCompleteMessage(message);
                    break;
                default:
                    LogDebug($"Unknown message type: {messageType}");
                    break;
            }
        }
        catch (Exception e)
        {
            LogDebug($"Error parsing message: {e.Message}");
            // Handle binary audio data
            OnTTSAudioReceived?.Invoke(data, 0, false);
        }
    }
    
    private void OnWebSocketError(string error)
    {
        LogDebug($"WebSocket error: {error}");
        OnErrorReceived?.Invoke("websocket_error", error);
    }
    
    private void OnWebSocketClose(WebSocketCloseCode closeCode)
    {
        LogDebug($"WebSocket closed: {closeCode}");
        isConnected = false;
        OnDisconnected?.Invoke();
        
        // Attempt to reconnect
        if (reconnectAttempts < maxReconnectAttempts)
        {
            reconnectAttempts++;
            LogDebug($"Attempting to reconnect ({reconnectAttempts}/{maxReconnectAttempts})");
            StartCoroutine(ReconnectAfterDelay());
        }
    }
    
    private IEnumerator ReconnectAfterDelay()
    {
        yield return new WaitForSeconds(reconnectDelay);
        ConnectToOrchestrator();
    }
    
    // Message handlers
    private void HandleReadyMessage(string message)
    {
        var readyMsg = JsonConvert.DeserializeObject<ReadyMessage>(message);
        sessionId = readyMsg.session_id;
        LogDebug($"Session ready: {sessionId}");
        LogDebug($"Audio config: {JsonConvert.SerializeObject(readyMsg.audio_config)}");
    }
    
    private void HandleTranscriptMessage(string message)
    {
        var transcriptMsg = JsonConvert.DeserializeObject<TranscriptMessage>(message);
        LogDebug($"Transcript: {transcriptMsg.text} (final: {transcriptMsg.is_final})");
        OnTranscriptReceived?.Invoke(transcriptMsg.text);
    }
    
    private void HandleRAGResponseMessage(string message)
    {
        var ragMsg = JsonConvert.DeserializeObject<RAGResponseMessage>(message);
        LogDebug($"RAG Response: {ragMsg.text}");
        OnRAGResponseReceived?.Invoke(ragMsg.text, ragMsg.sources);
    }
    
    private void HandleTTSAudioMessage(string message)
    {
        var ttsMsg = JsonConvert.DeserializeObject<TTSAudioMessage>(message);
        LogDebug($"TTS Audio chunk: {ttsMsg.chunk_index} (final: {ttsMsg.is_final_chunk})");
        
        // Convert base64 to bytes
        byte[] audioBytes = Convert.FromBase64String(ttsMsg.audio_data);
        OnTTSAudioReceived?.Invoke(audioBytes, ttsMsg.chunk_index, ttsMsg.is_final_chunk);
    }
    
    private void HandleStateMessage(string message)
    {
        var stateMsg = JsonConvert.DeserializeObject<StateMessage>(message);
        LogDebug($"State changed: {stateMsg.previous_state} → {stateMsg.state}");
        OnStateChanged?.Invoke(stateMsg.state, stateMsg.previous_state);
    }
    
    private void HandleErrorMessage(string message)
    {
        var errorMsg = JsonConvert.DeserializeObject<ErrorMessage>(message);
        LogDebug($"Error: {errorMsg.error_code} - {errorMsg.detail}");
        OnErrorReceived?.Invoke(errorMsg.error_code, errorMsg.detail);
    }
    
    private void HandleCompleteMessage(string message)
    {
        var completeMsg = JsonConvert.DeserializeObject<CompleteMessage>(message);
        LogDebug($"Conversation complete in {completeMsg.total_processing_time_ms}ms");
        OnConversationComplete?.Invoke(completeMsg.total_processing_time_ms);
    }
    
    // Public methods for sending data
    public async void SendAudioChunk(byte[] audioData)
    {
        if (isConnected && websocket != null)
        {
            await websocket.Send(audioData);
            LogDebug($"Sent audio chunk: {audioData.Length} bytes");
        }
        else
        {
            LogDebug("Cannot send audio chunk - not connected");
        }
    }
    
    public async void EndAudioInput()
    {
        if (isConnected && websocket != null)
        {
            var endMessage = new { type = "audio_end" };
            string jsonMessage = JsonConvert.SerializeObject(endMessage);
            await websocket.SendText(jsonMessage);
            LogDebug("Sent audio_end signal");
        }
        else
        {
            LogDebug("Cannot send audio_end - not connected");
        }
    }
    
    public void Disconnect()
    {
        if (websocket != null)
        {
            websocket.Close();
        }
    }
    
    private void LogDebug(string message)
    {
        if (enableDebugLogs)
        {
            Debug.Log($"[OrchestratorClient] {message}");
        }
    }
    
    void OnDestroy()
    {
        Disconnect();
    }
    
    void OnApplicationPause(bool pauseStatus)
    {
        if (pauseStatus)
        {
            Disconnect();
        }
        else
        {
            ConnectToOrchestrator();
        }
    }
}
```

### **2. AudioRecorder.cs**

This script handles audio recording with start/stop functionality:

```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

public class AudioRecorder : MonoBehaviour
{
    [Header("Audio Settings")]
    public int sampleRate = 16000;
    public int channels = 1;
    public int maxRecordingTime = 60; // seconds
    
    [Header("UI References")]
    public Button recordButton;
    public Button stopButton;
    public Text statusText;
    public Slider recordingProgress;
    
    [Header("Visual Feedback")]
    public GameObject recordingIndicator;
    public Color recordingColor = Color.red;
    public Color idleColor = Color.white;
    
    // Audio components
    private AudioSource audioSource;
    private AudioClip recordingClip;
    private string microphoneDevice;
    
    // Recording state
    private bool isRecording = false;
    private bool isProcessing = false;
    private float recordingStartTime;
    private int recordingSamples;
    
    // Orchestrator client reference
    private OrchestratorClient orchestratorClient;
    
    // Recording parameters
    private int recordingFrequency = 16000; // 16kHz for ASR
    private int recordingChunkSize = 1024; // Chunk size for streaming
    private float chunkInterval = 0.1f; // Send chunks every 100ms
    
    void Start()
    {
        // Get references
        orchestratorClient = FindObjectOfType<OrchestratorClient>();
        audioSource = GetComponent<AudioSource>();
        
        // Initialize UI
        InitializeUI();
        
        // Initialize microphone
        InitializeMicrophone();
        
        // Set up event handlers
        SetupEventHandlers();
    }
    
    private void InitializeUI()
    {
        // Set initial button states
        recordButton.interactable = true;
        stopButton.interactable = false;
        
        // Set initial status
        UpdateStatusText("Ready to record");
        
        // Hide recording indicator
        if (recordingIndicator != null)
        {
            recordingIndicator.SetActive(false);
        }
        
        // Reset progress bar
        if (recordingProgress != null)
        {
            recordingProgress.value = 0f;
        }
    }
    
    private void InitializeMicrophone()
    {
        // Get available microphones
        string[] devices = Microphone.devices;
        
        if (devices.Length > 0)
        {
            microphoneDevice = devices[0]; // Use first available microphone
            Debug.Log($"Using microphone: {microphoneDevice}");
        }
        else
        {
            Debug.LogError("No microphone devices found!");
            recordButton.interactable = false;
        }
    }
    
    private void SetupEventHandlers()
    {
        // Button click handlers
        recordButton.onClick.AddListener(StartRecording);
        stopButton.onClick.AddListener(StopRecording);
        
        // Orchestrator event handlers
        if (orchestratorClient != null)
        {
            orchestratorClient.OnConnected += OnOrchestratorConnected;
            orchestratorClient.OnDisconnected += OnOrchestratorDisconnected;
            orchestratorClient.OnStateChanged += OnConversationStateChanged;
            orchestratorClient.OnErrorReceived += OnOrchestratorError;
        }
    }
    
    public void StartRecording()
    {
        if (isRecording || isProcessing)
        {
            Debug.Log("Already recording or processing");
            return;
        }
        
        if (!Microphone.IsRecording(microphoneDevice))
        {
            StartCoroutine(StartRecordingCoroutine());
        }
    }
    
    private IEnumerator StartRecordingCoroutine()
    {
        // Update UI
        recordButton.interactable = false;
        stopButton.interactable = true;
        UpdateStatusText("Recording...");
        
        // Show recording indicator
        if (recordingIndicator != null)
        {
            recordingIndicator.SetActive(true);
        }
        
        // Start microphone recording
        recordingClip = Microphone.Start(microphoneDevice, true, maxRecordingTime, recordingFrequency);
        recordingStartTime = Time.time;
        recordingSamples = 0;
        isRecording = true;
        
        Debug.Log("Recording started");
        
        // Start sending audio chunks
        StartCoroutine(SendAudioChunks());
        
        yield return null;
    }
    
    public void StopRecording()
    {
        if (!isRecording)
        {
            Debug.Log("Not currently recording");
            return;
        }
        
        StartCoroutine(StopRecordingCoroutine());
    }
    
    private IEnumerator StopRecordingCoroutine()
    {
        // Stop microphone
        Microphone.End(microphoneDevice);
        isRecording = false;
        isProcessing = true;
        
        // Update UI
        recordButton.interactable = false;
        stopButton.interactable = false;
        UpdateStatusText("Processing...");
        
        // Hide recording indicator
        if (recordingIndicator != null)
        {
            recordingIndicator.SetActive(false);
        }
        
        // Send audio end signal to orchestrator
        if (orchestratorClient != null)
        {
            orchestratorClient.EndAudioInput();
        }
        
        Debug.Log("Recording stopped, processing...");
        
        yield return null;
    }
    
    private IEnumerator SendAudioChunks()
    {
        while (isRecording)
        {
            if (recordingClip != null && orchestratorClient != null)
            {
                // Get current recording position
                int currentPosition = Microphone.GetPosition(microphoneDevice);
                
                // Calculate samples to send
                int samplesToSend = currentPosition - recordingSamples;
                
                if (samplesToSend > 0)
                {
                    // Create audio data array
                    float[] audioData = new float[samplesToSend];
                    recordingClip.GetData(audioData, recordingSamples);
                    
                    // Convert to bytes (16-bit PCM)
                    byte[] audioBytes = ConvertFloatArrayToByteArray(audioData);
                    
                    // Send to orchestrator
                    orchestratorClient.SendAudioChunk(audioBytes);
                    
                    // Update recording samples
                    recordingSamples = currentPosition;
                    
                    Debug.Log($"Sent audio chunk: {audioBytes.Length} bytes");
                }
            }
            
            // Update progress bar
            if (recordingProgress != null)
            {
                float recordingTime = Time.time - recordingStartTime;
                recordingProgress.value = recordingTime / maxRecordingTime;
            }
            
            // Wait for next chunk
            yield return new WaitForSeconds(chunkInterval);
        }
    }
    
    private byte[] ConvertFloatArrayToByteArray(float[] floatArray)
    {
        byte[] byteArray = new byte[floatArray.Length * 2]; // 16-bit = 2 bytes per sample
        
        for (int i = 0; i < floatArray.Length; i++)
        {
            // Convert float (-1.0 to 1.0) to 16-bit integer
            short sample = (short)(floatArray[i] * 32767f);
            
            // Convert to bytes (little-endian)
            byteArray[i * 2] = (byte)(sample & 0xFF);
            byteArray[i * 2 + 1] = (byte)((sample >> 8) & 0xFF);
        }
        
        return byteArray;
    }
    
    // Event handlers
    private void OnOrchestratorConnected()
    {
        Debug.Log("Orchestrator connected");
        recordButton.interactable = true;
        UpdateStatusText("Connected - Ready to record");
    }
    
    private void OnOrchestratorDisconnected()
    {
        Debug.Log("Orchestrator disconnected");
        recordButton.interactable = false;
        stopButton.interactable = false;
        UpdateStatusText("Disconnected");
        
        // Stop recording if active
        if (isRecording)
        {
            StopRecording();
        }
    }
    
    private void OnConversationStateChanged(string newState, string previousState)
    {
        Debug.Log($"Conversation state: {previousState} → {newState}");
        
        switch (newState)
        {
            case "listening":
                UpdateStatusText("Listening...");
                break;
            case "processing":
                UpdateStatusText("Processing...");
                break;
            case "speaking":
                UpdateStatusText("Speaking...");
                break;
            case "idle":
                UpdateStatusText("Ready to record");
                recordButton.interactable = true;
                stopButton.interactable = false;
                isProcessing = false;
                break;
            case "error":
                UpdateStatusText("Error occurred");
                recordButton.interactable = true;
                stopButton.interactable = false;
                isProcessing = false;
                break;
        }
    }
    
    private void OnOrchestratorError(string errorCode, string detail)
    {
        Debug.LogError($"Orchestrator error: {errorCode} - {detail}");
        UpdateStatusText($"Error: {detail}");
        
        // Reset UI
        recordButton.interactable = true;
        stopButton.interactable = false;
        isProcessing = false;
        
        // Stop recording if active
        if (isRecording)
        {
            StopRecording();
        }
    }
    
    private void UpdateStatusText(string status)
    {
        if (statusText != null)
        {
            statusText.text = status;
        }
    }
    
    void Update()
    {
        // Update recording progress
        if (isRecording && recordingProgress != null)
        {
            float recordingTime = Time.time - recordingStartTime;
            recordingProgress.value = recordingTime / maxRecordingTime;
            
            // Auto-stop if max time reached
            if (recordingTime >= maxRecordingTime)
            {
                StopRecording();
            }
        }
    }
    
    void OnDestroy()
    {
        // Stop recording if active
        if (isRecording)
        {
            Microphone.End(microphoneDevice);
        }
    }
}
```

### **3. AudioPlayer.cs**

This script handles TTS audio playback:

```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

public class AudioPlayer : MonoBehaviour
{
    [Header("Audio Settings")]
    public AudioSource audioSource;
    public float audioVolume = 1.0f;
    
    [Header("UI References")]
    public Slider volumeSlider;
    public Button playButton;
    public Button stopButton;
    public Text audioStatusText;
    
    [Header("Visual Feedback")]
    public GameObject playingIndicator;
    public Slider audioProgressSlider;
    
    // Audio state
    private bool isPlaying = false;
    private AudioClip currentClip;
    private Coroutine audioCoroutine;
    
    // Orchestrator client reference
    private OrchestratorClient orchestratorClient;
    
    // Audio queue for streaming
    private Queue<byte[]> audioQueue = new Queue<byte[]>();
    private bool isProcessingAudio = false;
    
    void Start()
    {
        // Get references
        orchestratorClient = FindObjectOfType<OrchestratorClient>();
        
        // Initialize audio source
        if (audioSource == null)
        {
            audioSource = GetComponent<AudioSource>();
        }
        
        audioSource.volume = audioVolume;
        
        // Initialize UI
        InitializeUI();
        
        // Set up event handlers
        SetupEventHandlers();
    }
    
    private void InitializeUI()
    {
        // Set initial button states
        playButton.interactable = false;
        stopButton.interactable = false;
        
        // Set initial status
        UpdateAudioStatusText("Ready");
        
        // Hide playing indicator
        if (playingIndicator != null)
        {
            playingIndicator.SetActive(false);
        }
        
        // Reset progress slider
        if (audioProgressSlider != null)
        {
            audioProgressSlider.value = 0f;
        }
        
        // Set up volume slider
        if (volumeSlider != null)
        {
            volumeSlider.value = audioVolume;
            volumeSlider.onValueChanged.AddListener(OnVolumeChanged);
        }
    }
    
    private void SetupEventHandlers()
    {
        // Button click handlers
        playButton.onClick.AddListener(PlayAudio);
        stopButton.onClick.AddListener(StopAudio);
        
        // Orchestrator event handlers
        if (orchestratorClient != null)
        {
            orchestratorClient.OnTTSAudioReceived += OnTTSAudioReceived;
            orchestratorClient.OnStateChanged += OnConversationStateChanged;
        }
    }
    
    private void OnTTSAudioReceived(byte[] audioData, int chunkIndex, bool isFinalChunk)
    {
        Debug.Log($"Received TTS audio chunk {chunkIndex} (final: {isFinalChunk})");
        
        // Add to audio queue
        audioQueue.Enqueue(audioData);
        
        // Start processing if not already processing
        if (!isProcessingAudio)
        {
            StartCoroutine(ProcessAudioQueue());
        }
    }
    
    private IEnumerator ProcessAudioQueue()
    {
        isProcessingAudio = true;
        
        while (audioQueue.Count > 0)
        {
            byte[] audioData = audioQueue.Dequeue();
            
            // Convert bytes to AudioClip
            AudioClip clip = ConvertBytesToAudioClip(audioData);
            
            if (clip != null)
            {
                // Play the audio clip
                yield return StartCoroutine(PlayAudioClip(clip));
            }
            
            yield return null;
        }
        
        isProcessingAudio = false;
    }
    
    private AudioClip ConvertBytesToAudioClip(byte[] audioData)
    {
        try
        {
            // Convert byte array to float array (assuming 16-bit PCM)
            float[] audioSamples = new float[audioData.Length / 2];
            
            for (int i = 0; i < audioSamples.Length; i++)
            {
                // Convert 16-bit PCM to float
                short sample = (short)((audioData[i * 2]) | (audioData[i * 2 + 1] << 8));
                audioSamples[i] = sample / 32768f;
            }
            
            // Create AudioClip
            AudioClip clip = AudioClip.Create("TTSAudio", audioSamples.Length, 1, 16000, false);
            clip.SetData(audioSamples, 0);
            
            return clip;
        }
        catch (System.Exception e)
        {
            Debug.LogError($"Error converting audio data: {e.Message}");
            return null;
        }
    }
    
    private IEnumerator PlayAudioClip(AudioClip clip)
    {
        if (clip == null) yield break;
        
        // Update UI
        playButton.interactable = false;
        stopButton.interactable = true;
        UpdateAudioStatusText("Playing...");
        
        // Show playing indicator
        if (playingIndicator != null)
        {
            playingIndicator.SetActive(true);
        }
        
        // Play the clip
        audioSource.clip = clip;
        audioSource.Play();
        
        // Update progress while playing
        while (audioSource.isPlaying)
        {
            if (audioProgressSlider != null)
            {
                audioProgressSlider.value = audioSource.time / audioSource.clip.length;
            }
            yield return null;
        }
        
        // Reset UI
        playButton.interactable = true;
        stopButton.interactable = false;
        UpdateAudioStatusText("Ready");
        
        // Hide playing indicator
        if (playingIndicator != null)
        {
            playingIndicator.SetActive(false);
        }
        
        // Reset progress slider
        if (audioProgressSlider != null)
        {
            audioProgressSlider.value = 0f;
        }
    }
    
    public void PlayAudio()
    {
        if (currentClip != null && !isPlaying)
        {
            StartCoroutine(PlayAudioClip(currentClip));
        }
    }
    
    public void StopAudio()
    {
        if (audioSource.isPlaying)
        {
            audioSource.Stop();
            StopCoroutine(audioCoroutine);
            
            // Reset UI
            playButton.interactable = true;
            stopButton.interactable = false;
            UpdateAudioStatusText("Stopped");
            
            // Hide playing indicator
            if (playingIndicator != null)
            {
                playingIndicator.SetActive(false);
            }
        }
    }
    
    private void OnVolumeChanged(float volume)
    {
        audioVolume = volume;
        audioSource.volume = volume;
    }
    
    private void OnConversationStateChanged(string newState, string previousState)
    {
        switch (newState)
        {
            case "speaking":
                UpdateAudioStatusText("Speaking...");
                break;
            case "idle":
                UpdateAudioStatusText("Ready");
                break;
            case "error":
                UpdateAudioStatusText("Error");
                break;
        }
    }
    
    private void UpdateAudioStatusText(string status)
    {
        if (audioStatusText != null)
        {
            audioStatusText.text = status;
        }
    }
    
    void Update()
    {
        // Update progress slider while playing
        if (audioSource.isPlaying && audioProgressSlider != null)
        {
            audioProgressSlider.value = audioSource.time / audioSource.clip.length;
        }
    }
}
```

### **4. UIController.cs**

This script manages the UI elements and user interactions:

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class UIController : MonoBehaviour
{
    [Header("Main UI Elements")]
    public GameObject mainPanel;
    public GameObject connectionPanel;
    public GameObject conversationPanel;
    public GameObject errorPanel;
    
    [Header("Connection UI")]
    public TextMeshProUGUI connectionStatusText;
    public Button connectButton;
    public Button disconnectButton;
    public InputField urlInputField;
    
    [Header("Conversation UI")]
    public TextMeshProUGUI transcriptText;
    public TextMeshProUGUI responseText;
    public TextMeshProUGUI statusText;
    public Button recordButton;
    public Button stopButton;
    public Slider recordingProgressSlider;
    public GameObject recordingIndicator;
    
    [Header("Audio UI")]
    public Slider volumeSlider;
    public TextMeshProUGUI volumeText;
    public Button playButton;
    public Button stopAudioButton;
    public Slider audioProgressSlider;
    public GameObject playingIndicator;
    
    [Header("Error UI")]
    public TextMeshProUGUI errorText;
    public Button retryButton;
    public Button closeErrorButton;
    
    [Header("Settings")]
    public bool autoConnect = true;
    public string defaultOrchestratorUrl = "ws://localhost:8004/ws/conversation";
    
    // References
    private OrchestratorClient orchestratorClient;
    private AudioRecorder audioRecorder;
    private AudioPlayer audioPlayer;
    
    // UI State
    private bool isConnected = false;
    private bool isRecording = false;
    private bool isProcessing = false;
    
    void Start()
    {
        // Get references
        orchestratorClient = FindObjectOfType<OrchestratorClient>();
        audioRecorder = FindObjectOfType<AudioRecorder>();
        audioPlayer = FindObjectOfType<AudioPlayer>();
        
        // Initialize UI
        InitializeUI();
        
        // Set up event handlers
        SetupEventHandlers();
        
        // Auto-connect if enabled
        if (autoConnect)
        {
            ConnectToOrchestrator();
        }
    }
    
    private void InitializeUI()
    {
        // Set initial panel states
        mainPanel.SetActive(true);
        connectionPanel.SetActive(true);
        conversationPanel.SetActive(false);
        errorPanel.SetActive(false);
        
        // Initialize connection UI
        if (urlInputField != null)
        {
            urlInputField.text = defaultOrchestratorUrl;
        }
        
        UpdateConnectionStatus("Disconnected");
        
        // Initialize conversation UI
        UpdateTranscriptText("");
        UpdateResponseText("");
        UpdateStatusText("Ready");
        
        // Initialize audio UI
        if (volumeSlider != null)
        {
            volumeSlider.value = 1.0f;
            UpdateVolumeText(volumeSlider.value);
        }
        
        // Set initial button states
        UpdateButtonStates();
    }
    
    private void SetupEventHandlers()
    {
        // Connection button handlers
        if (connectButton != null)
        {
            connectButton.onClick.AddListener(ConnectToOrchestrator);
        }
        
        if (disconnectButton != null)
        {
            disconnectButton.onClick.AddListener(DisconnectFromOrchestrator);
        }
        
        // Conversation button handlers
        if (recordButton != null)
        {
            recordButton.onClick.AddListener(StartRecording);
        }
        
        if (stopButton != null)
        {
            stopButton.onClick.AddListener(StopRecording);
        }
        
        // Audio button handlers
        if (playButton != null)
        {
            playButton.onClick.AddListener(PlayAudio);
        }
        
        if (stopAudioButton != null)
        {
            stopAudioButton.onClick.AddListener(StopAudio);
        }
        
        // Volume slider handler
        if (volumeSlider != null)
        {
            volumeSlider.onValueChanged.AddListener(OnVolumeChanged);
        }
        
        // Error button handlers
        if (retryButton != null)
        {
            retryButton.onClick.AddListener(RetryConnection);
        }
        
        if (closeErrorButton != null)
        {
            closeErrorButton.onClick.AddListener(CloseErrorPanel);
        }
        
        // Orchestrator event handlers
        if (orchestratorClient != null)
        {
            orchestratorClient.OnConnected += OnOrchestratorConnected;
            orchestratorClient.OnDisconnected += OnOrchestratorDisconnected;
            orchestratorClient.OnTranscriptReceived += OnTranscriptReceived;
            orchestratorClient.OnRAGResponseReceived += OnRAGResponseReceived;
            orchestratorClient.OnStateChanged += OnConversationStateChanged;
            orchestratorClient.OnErrorReceived += OnOrchestratorError;
        }
    }
    
    // Connection methods
    public void ConnectToOrchestrator()
    {
        if (orchestratorClient != null)
        {
            // Update URL if changed
            if (urlInputField != null && !string.IsNullOrEmpty(urlInputField.text))
            {
                orchestratorClient.orchestratorUrl = urlInputField.text;
            }
            
            UpdateConnectionStatus("Connecting...");
            orchestratorClient.ConnectToOrchestrator();
        }
    }
    
    public void DisconnectFromOrchestrator()
    {
        if (orchestratorClient != null)
        {
            orchestratorClient.Disconnect();
        }
    }
    
    // Recording methods
    public void StartRecording()
    {
        if (audioRecorder != null && isConnected && !isProcessing)
        {
            audioRecorder.StartRecording();
        }
    }
    
    public void StopRecording()
    {
        if (audioRecorder != null && isRecording)
        {
            audioRecorder.StopRecording();
        }
    }
    
    // Audio methods
    public void PlayAudio()
    {
        if (audioPlayer != null)
        {
            audioPlayer.PlayAudio();
        }
    }
    
    public void StopAudio()
    {
        if (audioPlayer != null)
        {
            audioPlayer.StopAudio();
        }
    }
    
    // Event handlers
    private void OnOrchestratorConnected()
    {
        isConnected = true;
        UpdateConnectionStatus("Connected");
        
        // Switch to conversation panel
        connectionPanel.SetActive(false);
        conversationPanel.SetActive(true);
        
        UpdateButtonStates();
    }
    
    private void OnOrchestratorDisconnected()
    {
        isConnected = false;
        UpdateConnectionStatus("Disconnected");
        
        // Switch to connection panel
        conversationPanel.SetActive(false);
        connectionPanel.SetActive(true);
        
        UpdateButtonStates();
    }
    
    private void OnTranscriptReceived(string transcript)
    {
        UpdateTranscriptText(transcript);
    }
    
    private void OnRAGResponseReceived(string response, object[] sources)
    {
        UpdateResponseText(response);
    }
    
    private void OnConversationStateChanged(string newState, string previousState)
    {
        UpdateStatusText($"State: {newState}");
        
        switch (newState)
        {
            case "listening":
                isRecording = true;
                isProcessing = false;
                break;
            case "processing":
                isRecording = false;
                isProcessing = true;
                break;
            case "speaking":
                isRecording = false;
                isProcessing = false;
                break;
            case "idle":
                isRecording = false;
                isProcessing = false;
                break;
            case "error":
                isRecording = false;
                isProcessing = false;
                break;
        }
        
        UpdateButtonStates();
    }
    
    private void OnOrchestratorError(string errorCode, string detail)
    {
        ShowErrorPanel($"Error: {errorCode}\n{detail}");
    }
    
    // UI update methods
    private void UpdateConnectionStatus(string status)
    {
        if (connectionStatusText != null)
        {
            connectionStatusText.text = status;
        }
    }
    
    private void UpdateTranscriptText(string text)
    {
        if (transcriptText != null)
        {
            transcriptText.text = text;
        }
    }
    
    private void UpdateResponseText(string text)
    {
        if (responseText != null)
        {
            responseText.text = text;
        }
    }
    
    private void UpdateStatusText(string status)
    {
        if (statusText != null)
        {
            statusText.text = status;
        }
    }
    
    private void UpdateButtonStates()
    {
        // Connection buttons
        if (connectButton != null)
        {
            connectButton.interactable = !isConnected;
        }
        
        if (disconnectButton != null)
        {
            disconnectButton.interactable = isConnected;
        }
        
        // Recording buttons
        if (recordButton != null)
        {
            recordButton.interactable = isConnected && !isRecording && !isProcessing;
        }
        
        if (stopButton != null)
        {
            stopButton.interactable = isRecording;
        }
        
        // Audio buttons
        if (playButton != null)
        {
            playButton.interactable = isConnected;
        }
        
        if (stopAudioButton != null)
        {
            stopAudioButton.interactable = isConnected;
        }
    }
    
    private void OnVolumeChanged(float volume)
    {
        UpdateVolumeText(volume);
        
        if (audioPlayer != null)
        {
            audioPlayer.OnVolumeChanged(volume);
        }
    }
    
    private void UpdateVolumeText(float volume)
    {
        if (volumeText != null)
        {
            volumeText.text = $"Volume: {Mathf.RoundToInt(volume * 100)}%";
        }
    }
    
    private void ShowErrorPanel(string errorMessage)
    {
        if (errorText != null)
        {
            errorText.text = errorMessage;
        }
        
        errorPanel.SetActive(true);
    }
    
    private void CloseErrorPanel()
    {
        errorPanel.SetActive(false);
    }
    
    private void RetryConnection()
    {
        CloseErrorPanel();
        ConnectToOrchestrator();
    }
}
```

## 🎨 Unity Scene Setup

### **1. Create UI Canvas**

1. **Create Canvas**:
   - Right-click in Hierarchy → UI → Canvas
   - Set Canvas Scaler to "Scale With Screen Size"
   - Set Reference Resolution to 1920x1080

2. **Create Main Panel**:
   - Right-click Canvas → UI → Panel
   - Name it "MainPanel"
   - Add Image component with background color

3. **Create Connection Panel**:
   - Right-click MainPanel → UI → Panel
   - Name it "ConnectionPanel"
   - Add connection UI elements:
     - Text for status
     - InputField for URL
     - Button for Connect
     - Button for Disconnect

4. **Create Conversation Panel**:
   - Right-click MainPanel → UI → Panel
   - Name it "ConversationPanel"
   - Add conversation UI elements:
     - Text for transcript
     - Text for response
     - Text for status
     - Button for Record
     - Button for Stop
     - Slider for recording progress
     - GameObject for recording indicator

5. **Create Audio Panel**:
   - Right-click MainPanel → UI → Panel
   - Name it "AudioPanel"
   - Add audio UI elements:
     - Slider for volume
     - Text for volume
     - Button for Play
     - Button for Stop
     - Slider for audio progress
     - GameObject for playing indicator

### **2. Create GameObjects**

1. **Create Empty GameObject**:
   - Name it "OrchestratorClient"
   - Add OrchestratorClient script

2. **Create AudioRecorder GameObject**:
   - Name it "AudioRecorder"
   - Add AudioRecorder script
   - Add AudioSource component

3. **Create AudioPlayer GameObject**:
   - Name it "AudioPlayer"
   - Add AudioPlayer script
   - Add AudioSource component

4. **Create UIController GameObject**:
   - Name it "UIController"
   - Add UIController script

### **3. Configure Components**

1. **OrchestratorClient**:
   - Set Orchestrator URL
   - Enable Debug Logs

2. **AudioRecorder**:
   - Set Sample Rate to 16000
   - Set Channels to 1
   - Assign UI references
   - Set Recording Indicator

3. **AudioPlayer**:
   - Assign AudioSource
   - Assign UI references
   - Set Playing Indicator

4. **UIController**:
   - Assign all UI references
   - Set Default Orchestrator URL
   - Enable Auto Connect

## 🔧 Configuration

### **1. Audio Settings**

```csharp
// In AudioRecorder.cs
public int sampleRate = 16000;        // 16kHz for ASR
public int channels = 1;              // Mono audio
public int maxRecordingTime = 60;     // 60 seconds max
public float chunkInterval = 0.1f;    // Send chunks every 100ms
```

### **2. WebSocket Settings**

```csharp
// In OrchestratorClient.cs
public string orchestratorUrl = "ws://localhost:8004/ws/conversation";
public bool enableDebugLogs = true;
public int maxReconnectAttempts = 3;
public float reconnectDelay = 2f;
```

### **3. UI Settings**

```csharp
// In UIController.cs
public bool autoConnect = true;
public string defaultOrchestratorUrl = "ws://localhost:8004/ws/conversation";
```

## 🧪 Testing

### **1. Build Settings**

1. **File → Build Settings**
2. **Add Open Scenes**
3. **Select Platform** (Windows, Mac, Linux)
4. **Build**

### **2. Test Scenarios**

#### **Scenario 1: Basic Connection**
1. Start Orchestrator service
2. Run Unity application
3. Verify connection status shows "Connected"
4. Check that Record button is enabled

#### **Scenario 2: Recording and Playback**
1. Click Record button
2. Speak into microphone
3. Click Stop button
4. Verify transcript appears
5. Verify response appears
6. Verify TTS audio plays

#### **Scenario 3: Error Handling**
1. Disconnect Orchestrator service
2. Try to record
3. Verify error message appears
4. Reconnect service
5. Verify recovery

### **3. Debug Information**

Enable debug logs to see detailed communication:

```csharp
// In OrchestratorClient.cs
public bool enableDebugLogs = true;
```

## 🐛 Troubleshooting

### **Common Issues**

#### **1. WebSocket Connection Failed**
```csharp
// Check if Orchestrator is running
// Verify URL is correct
// Check firewall settings
```

#### **2. Microphone Not Working**
```csharp
// Check microphone permissions
// Verify microphone device selection
// Check audio settings
```

#### **3. Audio Playback Issues**
```csharp
// Check AudioSource configuration
// Verify audio data format
// Check volume settings
```

#### **4. UI Not Updating**
```csharp
// Check UI references in inspector
// Verify event handlers are set up
// Check button states
```

### **Debug Steps**

1. **Enable Debug Logs**:
   ```csharp
   public bool enableDebugLogs = true;
   ```

2. **Check Console**:
   - Look for WebSocket messages
   - Check audio recording status
   - Verify UI updates

3. **Test Individual Components**:
   - Test WebSocket connection
   - Test microphone recording
   - Test audio playback
   - Test UI interactions

## 🚀 Production Deployment

### **1. Build Configuration**

```csharp
// Production settings
public bool enableDebugLogs = false;
public string orchestratorUrl = "wss://your-domain.com/ws/conversation";
public bool autoConnect = true;
```

### **2. Error Handling**

```csharp
// Robust error handling
public int maxReconnectAttempts = 5;
public float reconnectDelay = 3f;
public bool showErrorMessages = true;
```

### **3. Performance Optimization**

```csharp
// Optimize audio settings
public int audioChunkSize = 1024;
public float chunkInterval = 0.1f;
public int maxRecordingTime = 30;
```

## 📚 Additional Resources

- **Orchestrator Integration Guide**: `docs/ORCHESTRATOR_INTEGRATION_GUIDE.md`
- **Unity WebSocket Package**: https://github.com/endel/NativeWebSocket
- **Unity Audio Documentation**: https://docs.unity3d.com/Manual/Audio.html

## 🤝 Support

For Unity integration support:
1. Check the troubleshooting section
2. Enable debug logs for detailed information
3. Test individual components
4. Verify all UI references are set

**Ready to build conversational AI in Unity! 🎮**
