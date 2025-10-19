# Unity ASR Integration - Quick Setup Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Download Required Files
1. Download `UnityASRClient.cs` and `ASRUI.cs` from this repository
2. Place them in your Unity project's `Assets/Scripts/` folder

### Step 2: Install WebSocket Package
**Option A: WebSocketSharp (Recommended)**
1. Download WebSocketSharp.dll from: https://github.com/sta/websocket-sharp
2. Place it in `Assets/Plugins/` folder

**Option B: BestHTTP**
1. Add to `Packages/manifest.json`:
```json
{
  "dependencies": {
    "com.unity.nuget.newtonsoft-json": "3.0.2"
  }
}
```

### Step 3: Setup Scene
1. Create Empty GameObject named "ASRManager"
2. Add `UnityASRClient` component
3. Configure settings:
   - Server URL: `ws://localhost:8001/ws/asr-stream`
   - Language Code: `ar-EG` (or your preferred language)
   - Sample Rate: `16000`
   - Chunk Size: `4096`

### Step 4: Test Connection
1. Start your ASR server: `python run.py`
2. Play the Unity scene
3. Click "Connect" button
4. Click "Start Streaming" button
5. Speak into your microphone
6. Watch transcriptions appear in real-time!

## 🎯 Basic Usage

```csharp
public class MyASRController : MonoBehaviour
{
    public UnityASRClient asrClient;
    
    void Start()
    {
        // Subscribe to events
        asrClient.OnTranscriptReceived += OnTranscript;
        asrClient.OnErrorReceived += OnError;
        
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
    }
}
```

## 🔧 Configuration Options

### Audio Settings
- **Sample Rate**: 16000 Hz (recommended)
- **Chunk Size**: 4096 bytes (adjust for performance)
- **Chunk Delay**: 0.1 seconds (adjust for latency)

### Language Support
- Arabic: `ar-EG`
- English (US): `en-US`
- English (UK): `en-GB`
- French: `fr-FR`
- German: `de-DE`
- Spanish: `es-ES`

### Server Configuration
- **Local Development**: `ws://localhost:8001/ws/asr-stream`
- **Production**: `ws://your-server.com:8001/ws/asr-stream`

## 🎨 UI Integration

### Simple UI Setup
1. Create Canvas in your scene
2. Add buttons: Connect, Disconnect, Start Streaming, Stop Streaming
3. Add text elements: Status, Transcript, Word Count
4. Add `ASRUI` component to a GameObject
5. Assign UI references in the inspector

### Custom UI
```csharp
public class CustomASRUI : MonoBehaviour
{
    public UnityASRClient asrClient;
    public Text transcriptText;
    
    void Start()
    {
        asrClient.OnTranscriptReceived += UpdateTranscript;
    }
    
    private void UpdateTranscript(string text)
    {
        transcriptText.text += text + " ";
    }
}
```

## 🐛 Troubleshooting

### Common Issues

**1. WebSocket Connection Failed**
- ✅ Check if ASR server is running
- ✅ Verify server URL and port
- ✅ Check firewall settings

**2. Microphone Permission Denied**
- ✅ Request microphone permission in Unity
- ✅ Check Unity Player Settings
- ✅ Verify microphone is available

**3. No Audio Data**
- ✅ Check microphone is working
- ✅ Verify sample rate settings
- ✅ Check audio buffer size

**4. Poor Transcription Quality**
- ✅ Use 16kHz sample rate
- ✅ Speak clearly and close to microphone
- ✅ Reduce background noise

### Debug Commands

```csharp
// Enable debug logging
asrClient.enableDebugLogs = true;

// Check connection status
Debug.Log($"Connected: {asrClient.IsConnected}");
Debug.Log($"Streaming: {asrClient.IsStreaming}");

// Test audio capture
asrClient.StartStreaming();
```

## 📱 Mobile Considerations

### iOS
- Add microphone usage description to Info.plist
- Test on device (microphone doesn't work in simulator)

### Android
- Add microphone permission to AndroidManifest.xml
- Test on device for best performance

### Performance Tips
- Reduce chunk size for mobile
- Increase chunk delay for battery optimization
- Use mono audio (single channel)

## 🔄 Advanced Features

### Custom Audio Processing
```csharp
public class CustomAudioProcessor : MonoBehaviour
{
    public UnityASRClient asrClient;
    
    void Start()
    {
        // Override audio processing
        asrClient.OnAudioDataProcessed += ProcessAudio;
    }
    
    private void ProcessAudio(float[] audioData)
    {
        // Apply noise reduction, filtering, etc.
        // Then send to ASR client
    }
}
```

### Multiple Language Support
```csharp
public class MultiLanguageASR : MonoBehaviour
{
    public UnityASRClient asrClient;
    
    public void SwitchLanguage(string languageCode)
    {
        asrClient.SetLanguage(languageCode);
    }
}
```

### Error Recovery
```csharp
public class RobustASR : MonoBehaviour
{
    public UnityASRClient asrClient;
    
    void Start()
    {
        asrClient.OnErrorReceived += HandleError;
    }
    
    private void HandleError(string error)
    {
        // Implement retry logic
        StartCoroutine(RetryConnection());
    }
    
    private IEnumerator RetryConnection()
    {
        yield return new WaitForSeconds(5f);
        asrClient.Connect();
    }
}
```

## 📊 Performance Monitoring

```csharp
public class ASRPerformanceMonitor : MonoBehaviour
{
    public UnityASRClient asrClient;
    
    void Update()
    {
        // Monitor performance
        Debug.Log($"Audio Queue Size: {asrClient.AudioQueueSize}");
        Debug.Log($"Memory Usage: {GC.GetTotalMemory(false)}");
    }
}
```

## 🎯 Best Practices

1. **Audio Quality**
   - Use 16kHz sample rate
   - Implement noise reduction
   - Use mono audio

2. **Network Optimization**
   - Implement connection retry
   - Handle network interruptions
   - Use appropriate chunk sizes

3. **User Experience**
   - Provide visual feedback
   - Show confidence scores
   - Implement transcript editing

4. **Error Handling**
   - Implement comprehensive error handling
   - Provide user-friendly messages
   - Log errors for debugging

## 📚 Additional Resources

- [Complete Integration Guide](UNITY_INTEGRATION_GUIDE.md)
- [WebSocket Documentation](https://docs.unity3d.com/Manual/Networking.html)
- [Unity Audio System](https://docs.unity3d.com/Manual/Audio.html)
- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text)

## 🆘 Support

If you encounter issues:
1. Check the Unity Console for error messages
2. Verify ASR server is running and accessible
3. Test microphone permissions
4. Review network connectivity
5. Check audio settings and quality

Happy coding! 🎉
