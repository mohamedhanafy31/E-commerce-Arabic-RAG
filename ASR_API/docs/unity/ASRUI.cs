using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ASR;

/// <summary>
/// Simple UI controller for Unity ASR Client
/// Provides basic interface for testing and demonstration
/// </summary>
public class ASRUI : MonoBehaviour
{
    [Header("UI References")]
    public Button connectButton;
    public Button disconnectButton;
    public Button startStreamingButton;
    public Button stopStreamingButton;
    public Button clearButton;
    
    public TextMeshProUGUI statusText;
    public TextMeshProUGUI transcriptText;
    public TextMeshProUGUI confidenceText;
    public TextMeshProUGUI wordCountText;
    public TextMeshProUGUI languageText;
    
    public Image recordingIndicator;
    public Slider confidenceSlider;
    
    [Header("ASR Client")]
    public UnityASRClient asrClient;
    
    [Header("Settings")]
    public string[] availableLanguages = { "ar-EG", "en-US", "en-GB", "fr-FR", "de-DE", "es-ES" };
    public TMP_Dropdown languageDropdown;
    
    // Private fields
    private string completeTranscript = "";
    private string currentInterimText = "";
    private int wordCount = 0;
    private float lastConfidence = 0f;
    
    void Start()
    {
        SetupUI();
        SetupASRClient();
        SetupLanguageDropdown();
    }
    
    private void SetupUI()
    {
        // Button event listeners
        connectButton.onClick.AddListener(Connect);
        disconnectButton.onClick.AddListener(Disconnect);
        startStreamingButton.onClick.AddListener(StartStreaming);
        stopStreamingButton.onClick.AddListener(StopStreaming);
        clearButton.onClick.AddListener(ClearTranscript);
        
        // Initial UI state
        UpdateUI();
        UpdateTranscriptDisplay();
    }
    
    private void SetupASRClient()
    {
        if (asrClient == null)
            asrClient = FindObjectOfType<UnityASRClient>();
        
        if (asrClient != null)
        {
            // Subscribe to ASR events
            asrClient.OnConnected += OnConnected;
            asrClient.OnDisconnected += OnDisconnected;
            asrClient.OnTranscriptReceived += OnTranscriptReceived;
            asrClient.OnErrorReceived += OnErrorReceived;
            asrClient.OnServerReady += OnServerReady;
        }
        else
        {
            Debug.LogError("UnityASRClient not found! Please assign it in the inspector.");
        }
    }
    
    private void SetupLanguageDropdown()
    {
        if (languageDropdown != null)
        {
            languageDropdown.ClearOptions();
            languageDropdown.AddOptions(new System.Collections.Generic.List<string>(availableLanguages));
            languageDropdown.onValueChanged.AddListener(OnLanguageChanged);
        }
    }
    
    private void Connect()
    {
        if (asrClient != null)
        {
            asrClient.Connect();
            statusText.text = "Connecting...";
        }
    }
    
    private void Disconnect()
    {
        if (asrClient != null)
        {
            asrClient.Disconnect();
            statusText.text = "Disconnected";
        }
    }
    
    private void StartStreaming()
    {
        if (asrClient != null)
        {
            asrClient.StartStreaming();
            statusText.text = "Streaming...";
            recordingIndicator.gameObject.SetActive(true);
        }
    }
    
    private void StopStreaming()
    {
        if (asrClient != null)
        {
            asrClient.StopStreaming();
            statusText.text = "Connected";
            recordingIndicator.gameObject.SetActive(false);
        }
    }
    
    private void ClearTranscript()
    {
        completeTranscript = "";
        currentInterimText = "";
        wordCount = 0;
        lastConfidence = 0f;
        UpdateTranscriptDisplay();
        UpdateConfidenceDisplay();
    }
    
    private void OnLanguageChanged(int index)
    {
        if (asrClient != null && index < availableLanguages.Length)
        {
            asrClient.SetLanguage(availableLanguages[index]);
            languageText.text = $"Language: {availableLanguages[index]}";
        }
    }
    
    // ASR Event Handlers
    private void OnConnected()
    {
        statusText.text = "Connected";
        UpdateUI();
    }
    
    private void OnDisconnected()
    {
        statusText.text = "Disconnected";
        recordingIndicator.gameObject.SetActive(false);
        UpdateUI();
    }
    
    private void OnServerReady()
    {
        statusText.text = "Server Ready";
        Debug.Log("Server is ready for audio streaming");
    }
    
    private void OnTranscriptReceived(string text)
    {
        // In a real implementation, you would parse the JSON to determine
        // if this is interim or final text. For simplicity, we'll treat
        // all received text as final.
        
        if (!string.IsNullOrEmpty(text))
        {
            completeTranscript += (completeTranscript.Length > 0 ? " " : "") + text.Trim();
            wordCount = completeTranscript.Split(' ').Length;
            UpdateTranscriptDisplay();
        }
    }
    
    private void OnErrorReceived(string error)
    {
        statusText.text = $"Error: {error}";
        Debug.LogError($"ASR Error: {error}");
    }
    
    private void UpdateUI()
    {
        bool isConnected = asrClient != null && asrClient.IsConnected;
        bool isStreaming = asrClient != null && asrClient.IsStreaming;
        
        connectButton.interactable = !isConnected;
        disconnectButton.interactable = isConnected;
        startStreamingButton.interactable = isConnected && !isStreaming;
        stopStreamingButton.interactable = isStreaming;
        clearButton.interactable = isConnected;
        
        if (languageDropdown != null)
            languageDropdown.interactable = !isConnected;
    }
    
    private void UpdateTranscriptDisplay()
    {
        transcriptText.text = completeTranscript;
        wordCountText.text = $"Words: {wordCount}";
    }
    
    private void UpdateConfidenceDisplay()
    {
        confidenceText.text = $"Confidence: {(lastConfidence * 100):F1}%";
        if (confidenceSlider != null)
        {
            confidenceSlider.value = lastConfidence;
        }
    }
    
    void Update()
    {
        // Update UI state
        UpdateUI();
        
        // Update language display
        if (asrClient != null)
        {
            languageText.text = $"Language: {asrClient.CurrentLanguage}";
        }
    }
    
    void OnDestroy()
    {
        // Unsubscribe from events
        if (asrClient != null)
        {
            asrClient.OnConnected -= OnConnected;
            asrClient.OnDisconnected -= OnDisconnected;
            asrClient.OnTranscriptReceived -= OnTranscriptReceived;
            asrClient.OnErrorReceived -= OnErrorReceived;
            asrClient.OnServerReady -= OnServerReady;
        }
    }
}
