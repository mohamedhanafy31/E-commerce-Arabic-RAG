using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using WebSocketSharp;
using Newtonsoft.Json;

namespace ASR
{
    /// <summary>
    /// Complete Unity WebSocket ASR Streaming Client
    /// Ready-to-use implementation for Unity applications
    /// </summary>
    public class UnityASRClient : MonoBehaviour
    {
        [Header("Connection Settings")]
        [SerializeField] private string serverUrl = "ws://localhost:8001/ws/asr-stream";
        [SerializeField] private string languageCode = "ar-EG";
        [SerializeField] private int sampleRate = 16000;
        [SerializeField] private string encoding = "LINEAR16";
        
        [Header("Audio Settings")]
        [SerializeField] private int chunkSize = 4096;
        [SerializeField] private float chunkDelay = 0.1f;
        [SerializeField] private int bufferSize = 4096;
        
        [Header("Debug")]
        [SerializeField] private bool enableDebugLogs = true;
        
        // Events
        public event Action<string> OnTranscriptReceived;
        public event Action<string> OnErrorReceived;
        public event Action OnConnected;
        public event Action OnDisconnected;
        public event Action OnServerReady;
        
        // Private fields
        private WebSocket webSocket;
        private bool isConnected = false;
        private bool isStreaming = false;
        private AudioClip audioClip;
        private float[] audioBuffer;
        private int bufferPosition = 0;
        private Queue<byte[]> audioQueue = new Queue<byte[]>();
        private Coroutine streamingCoroutine;
        
        // Properties
        public bool IsConnected => isConnected;
        public bool IsStreaming => isStreaming;
        public string CurrentLanguage => languageCode;
        
        void Start()
        {
            InitializeAudioBuffer();
        }
        
        void Update()
        {
            // Process audio data if streaming
            if (isStreaming && audioClip != null)
            {
                ProcessAudioData();
            }
        }
        
        /// <summary>
        /// Connect to the ASR WebSocket server
        /// </summary>
        public void Connect()
        {
            if (isConnected)
            {
                LogDebug("Already connected");
                return;
            }
            
            try
            {
                LogDebug($"Connecting to {serverUrl}");
                
                webSocket = new WebSocket(serverUrl);
                webSocket.OnOpen += OnWebSocketOpen;
                webSocket.OnMessage += OnWebSocketMessage;
                webSocket.OnError += OnWebSocketError;
                webSocket.OnClose += OnWebSocketClose;
                
                webSocket.Connect();
            }
            catch (Exception e)
            {
                LogError($"Failed to connect: {e.Message}");
                OnErrorReceived?.Invoke($"Connection failed: {e.Message}");
            }
        }
        
        /// <summary>
        /// Disconnect from the ASR WebSocket server
        /// </summary>
        public void Disconnect()
        {
            if (webSocket != null)
            {
                isStreaming = false;
                StopAudioCapture();
                
                if (streamingCoroutine != null)
                {
                    StopCoroutine(streamingCoroutine);
                    streamingCoroutine = null;
                }
                
                webSocket.Close();
            }
        }
        
        /// <summary>
        /// Start audio capture and streaming
        /// </summary>
        public void StartStreaming()
        {
            if (!isConnected)
            {
                LogError("Not connected to server");
                return;
            }
            
            if (isStreaming)
            {
                LogDebug("Already streaming");
                return;
            }
            
            StartAudioCapture();
        }
        
        /// <summary>
        /// Stop audio capture and streaming
        /// </summary>
        public void StopStreaming()
        {
            if (!isStreaming) return;
            
            isStreaming = false;
            StopAudioCapture();
            
            if (streamingCoroutine != null)
            {
                StopCoroutine(streamingCoroutine);
                streamingCoroutine = null;
            }
            
            LogDebug("Stopped streaming");
        }
        
        /// <summary>
        /// Change the language for transcription
        /// </summary>
        public void SetLanguage(string newLanguageCode)
        {
            languageCode = newLanguageCode;
            LogDebug($"Language changed to: {languageCode}");
        }
        
        private void InitializeAudioBuffer()
        {
            audioBuffer = new float[bufferSize];
        }
        
        private void OnWebSocketOpen(object sender, EventArgs e)
        {
            LogDebug("WebSocket connected");
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
                LogError($"Error parsing message: {ex.Message}");
            }
        }
        
        private void OnWebSocketError(object sender, ErrorEventArgs e)
        {
            LogError($"WebSocket error: {e.Message}");
            OnErrorReceived?.Invoke($"WebSocket error: {e.Message}");
        }
        
        private void OnWebSocketClose(object sender, CloseEventArgs e)
        {
            LogDebug("WebSocket disconnected");
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
            LogDebug($"Sent configuration: {configJson}");
        }
        
        private void HandleMessage(Dictionary<string, object> message)
        {
            string type = message["type"].ToString();
            
            switch (type)
            {
                case "metadata":
                    if (message["status"].ToString() == "ready")
                    {
                        LogDebug("Server ready for audio streaming");
                        OnServerReady?.Invoke();
                    }
                    break;
                    
                case "transcript":
                    string text = message["text"].ToString();
                    bool isFinal = Convert.ToBoolean(message["is_final"]);
                    float confidence = message.ContainsKey("confidence") ? 
                        Convert.ToSingle(message["confidence"]) : 0f;
                    
                    LogDebug($"[{(isFinal ? "FINAL" : "INTERIM")}] {text} (confidence: {confidence:F2})");
                    OnTranscriptReceived?.Invoke(text);
                    break;
                    
                case "error":
                    string error = message["detail"].ToString();
                    LogError($"Server error: {error}");
                    OnErrorReceived?.Invoke($"Server error: {error}");
                    break;
                    
                case "complete":
                    LogDebug("Transcription completed");
                    break;
            }
        }
        
        private void StartAudioCapture()
        {
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
                LogError("Microphone permission denied");
                OnErrorReceived?.Invoke("Microphone permission denied");
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
                    LogError("Failed to start microphone");
                    return;
                }
                
                isStreaming = true;
                LogDebug($"Started microphone capture: {deviceName}");
                
                // Start streaming coroutine
                streamingCoroutine = StartCoroutine(StreamAudioData());
            }
            catch (Exception e)
            {
                LogError($"Microphone error: {e.Message}");
                OnErrorReceived?.Invoke($"Microphone error: {e.Message}");
            }
        }
        
        private void StopAudioCapture()
        {
            if (Microphone.IsRecording(null))
            {
                Microphone.End(null);
            }
            
            LogDebug("Stopped microphone capture");
        }
        
        private void ProcessAudioData()
        {
            if (audioClip == null) return;
            
            int currentPosition = Microphone.GetPosition(null);
            
            if (currentPosition >= bufferSize)
            {
                // Extract audio data
                audioClip.GetData(audioBuffer, currentPosition - bufferSize);
                
                // Convert to PCM and add to queue
                byte[] pcmData = ConvertToPCM(audioBuffer);
                audioQueue.Enqueue(pcmData);
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
                    LogDebug($"Sent audio chunk: {audioData.Length} bytes");
                }
                
                yield return new WaitForSeconds(chunkDelay);
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
        
        private void LogDebug(string message)
        {
            if (enableDebugLogs)
            {
                Debug.Log($"[UnityASRClient] {message}");
            }
        }
        
        private void LogError(string message)
        {
            Debug.LogError($"[UnityASRClient] {message}");
        }
        
        void OnDestroy()
        {
            Disconnect();
        }
        
        // Unity Editor GUI for testing
        void OnGUI()
        {
            if (!enableDebugLogs) return;
            
            GUILayout.BeginArea(new Rect(10, 10, 300, 200));
            GUILayout.Label($"ASR Client Status: {(isConnected ? "Connected" : "Disconnected")}");
            GUILayout.Label($"Streaming: {(isStreaming ? "Yes" : "No")}");
            GUILayout.Label($"Language: {languageCode}");
            GUILayout.Label($"Audio Queue: {audioQueue.Count}");
            
            if (GUILayout.Button("Connect"))
                Connect();
            
            if (GUILayout.Button("Disconnect"))
                Disconnect();
            
            if (GUILayout.Button("Start Streaming"))
                StartStreaming();
            
            if (GUILayout.Button("Stop Streaming"))
                StopStreaming();
            
            GUILayout.EndArea();
        }
    }
}
