# Unity ASR Example Scene Setup

## Scene Configuration

### 1. Create Main Scene
- Create new scene: `File > New Scene`
- Save as: `ASRExampleScene.unity`

### 2. Create ASR Manager GameObject
```
ASRManager (Empty GameObject)
├── UnityASRClient (Script)
└── ASRUI (Script)
```

### 3. Create UI Canvas
```
Canvas
├── Panel (Background)
├── StatusPanel
│   ├── StatusText (TextMeshPro)
│   ├── LanguageText (TextMeshPro)
│   └── WordCountText (TextMeshPro)
├── ControlPanel
│   ├── ConnectButton (Button)
│   ├── DisconnectButton (Button)
│   ├── StartStreamingButton (Button)
│   ├── StopStreamingButton (Button)
│   └── ClearButton (Button)
├── TranscriptPanel
│   ├── TranscriptText (TextMeshPro)
│   └── ConfidenceText (TextMeshPro)
└── RecordingIndicator (Image)
```

## Component Configuration

### UnityASRClient Settings
```csharp
// Inspector Settings
Server URL: ws://localhost:8001/ws/asr-stream
Language Code: ar-EG
Sample Rate: 16000
Encoding: LINEAR16
Chunk Size: 4096
Chunk Delay: 0.1
Buffer Size: 4096
Enable Debug Logs: true
```

### ASRUI Settings
```csharp
// Inspector References
Connect Button: ConnectButton
Disconnect Button: DisconnectButton
Start Streaming Button: StartStreamingButton
Stop Streaming Button: StopStreamingButton
Clear Button: ClearButton

Status Text: StatusText
Transcript Text: TranscriptText
Confidence Text: ConfidenceText
Word Count Text: WordCountText
Language Text: LanguageText

Recording Indicator: RecordingIndicator

ASR Client: ASRManager (UnityASRClient)
```

## UI Layout Example

### Canvas Settings
- Canvas Scaler: Scale With Screen Size
- Reference Resolution: 1920x1080
- Screen Match Mode: Match Width Or Height

### Panel Layout
```
┌─────────────────────────────────────┐
│ Status: Connected | Language: ar-EG │
│ Words: 15                           │
├─────────────────────────────────────┤
│ [Connect] [Disconnect] [Start] [Stop]│
│ [Clear]                             │
├─────────────────────────────────────┤
│ Transcript:                         │
│ Hello world this is a test...       │
│ Confidence: 95.2%                   │
├─────────────────────────────────────┤
│ ● Recording...                      │
└─────────────────────────────────────┘
```

## Script Setup

### 1. Create ASRManager GameObject
```csharp
// Add UnityASRClient component
// Configure settings in inspector
// Add ASRUI component
// Assign UI references
```

### 2. Setup Event Listeners
```csharp
// In ASRUI.Start()
asrClient.OnConnected += OnConnected;
asrClient.OnDisconnected += OnDisconnected;
asrClient.OnTranscriptReceived += OnTranscriptReceived;
asrClient.OnErrorReceived += OnErrorReceived;
```

### 3. Test Scene
```csharp
// Play scene
// Click Connect
// Click Start Streaming
// Speak into microphone
// Watch transcriptions appear
```

## Mobile Setup

### iOS Configuration
```xml
<!-- Info.plist -->
<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access for speech recognition</string>
```

### Android Configuration
```xml
<!-- AndroidManifest.xml -->
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

## Build Settings

### Player Settings
- **Company Name**: Your Company
- **Product Name**: ASR Example
- **Version**: 1.0.0
- **Icon**: Set app icon
- **Splash Screen**: Optional

### Build Configuration
- **Platform**: PC, Mac & Linux Standalone
- **Target Platform**: Windows/Mac/Linux
- **Architecture**: x86_64
- **Scripting Backend**: Mono
- **Api Compatibility Level**: .NET Standard 2.1

## Testing Checklist

### Pre-Build Testing
- [ ] ASR server is running
- [ ] WebSocket connection works
- [ ] Microphone permission granted
- [ ] Audio capture is working
- [ ] Transcriptions are received
- [ ] UI updates correctly
- [ ] Error handling works

### Post-Build Testing
- [ ] Standalone build runs
- [ ] Network connectivity works
- [ ] Audio system functions
- [ ] UI is responsive
- [ ] Performance is acceptable

## Performance Optimization

### Audio Settings
```csharp
// Optimize for performance
Chunk Size: 2048 (smaller for mobile)
Chunk Delay: 0.2 (higher for mobile)
Buffer Size: 2048 (smaller for mobile)
```

### UI Optimization
```csharp
// Reduce UI updates
Update frequency: 10 FPS
Text update threshold: 0.1 seconds
```

## Debugging

### Console Commands
```csharp
// Enable debug logging
asrClient.enableDebugLogs = true;

// Check status
Debug.Log($"Connected: {asrClient.IsConnected}");
Debug.Log($"Streaming: {asrClient.IsStreaming}");
```

### Common Issues
1. **Connection Failed**: Check server URL and port
2. **No Audio**: Check microphone permissions
3. **Poor Quality**: Adjust sample rate and chunk size
4. **UI Not Updating**: Check event subscriptions

## Example Scene File Structure

```
Assets/
├── Scenes/
│   └── ASRExampleScene.unity
├── Scripts/
│   ├── UnityASRClient.cs
│   └── ASRUI.cs
├── Plugins/
│   └── WebSocketSharp.dll
└── Prefabs/
    └── ASRManager.prefab
```

This setup provides a complete working example of Unity ASR integration that can be used as a starting point for more complex applications.
